try:
    import MetaTrader5 as mt5
except ImportError:
    # Fallback to mock MT5 for non-Windows platforms
    import services.mock_mt5 as mt5
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
try:
    import pandas as pd
except ImportError:
    # Mock pandas functionality if not available
    class pd:
        @staticmethod
        def DataFrame(data):
            return data
        @staticmethod
        def to_datetime(data, unit=None):
            return data
from services.mt5_service import mt5_service
from utils.validators import validate_trading_params

logger = logging.getLogger(__name__)

class TradingService:
    """Service class for trading operations"""
    
    def __init__(self):
        self.mt5_service = mt5_service
    
    def send_order(self, action: str, symbol: str, volume: float, 
                   order_type: str = "market", price: Optional[float] = None,
                   sl: Optional[float] = None, tp: Optional[float] = None, 
                   comment: str = "") -> Dict[str, Any]:
        """Send a trading order to MT5"""
        try:
            # Validate connection
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Validate parameters
            validation_result = validate_trading_params(symbol, volume, action, order_type, price)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {"success": False, "error": f"Symbol {symbol} not found"}
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return {"success": False, "error": f"Failed to select symbol {symbol}"}
            
            # Determine order type
            if action.upper() == "BUY":
                order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "market" else mt5.ORDER_TYPE_BUY_LIMIT
                trade_type = mt5.TRADE_ACTION_DEAL if order_type == "market" else mt5.TRADE_ACTION_PENDING
                order_price = mt5.symbol_info_tick(symbol).ask if price is None else price
            else:  # SELL
                order_type_mt5 = mt5.ORDER_TYPE_SELL if order_type == "market" else mt5.ORDER_TYPE_SELL_LIMIT
                trade_type = mt5.TRADE_ACTION_DEAL if order_type == "market" else mt5.TRADE_ACTION_PENDING
                order_price = mt5.symbol_info_tick(symbol).bid if price is None else price
            
            # Prepare the request
            request = {
                "action": trade_type,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": order_price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add stop loss and take profit if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send the order
            result = mt5.order_send(request)
            
            if result is None:
                return {"success": False, "error": "Failed to send order"}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False, 
                    "error": f"Order failed: {result.retcode} - {result.comment}"
                }
            
            logger.info(f"Order executed successfully: {result.order}")
            
            return {
                "success": True,
                "data": {
                    "order": result.order,
                    "deal": result.deal,
                    "volume": result.volume,
                    "price": result.price,
                    "comment": result.comment,
                    "retcode": result.retcode
                }
            }
            
        except Exception as e:
            logger.error(f"Error sending order: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all open positions"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            positions = mt5.positions_get()
            if positions is None:
                return {"success": False, "error": "Failed to get positions"}
            
            positions_list = []
            for position in positions:
                positions_list.append({
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "type": "BUY" if position.type == 0 else "SELL",
                    "volume": position.volume,
                    "price_open": position.price_open,
                    "price_current": position.price_current,
                    "profit": position.profit,
                    "swap": position.swap,
                    "time": datetime.fromtimestamp(position.time).isoformat(),
                    "comment": position.comment
                })
            
            return {
                "success": True,
                "data": positions_list,
                "count": len(positions_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close a specific position"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": f"Position {ticket} not found"}
            
            position = position[0]
            
            # Determine close action (opposite of position type)
            if position.type == 0:  # BUY position
                close_type = mt5.ORDER_TYPE_SELL
                close_price = mt5.symbol_info_tick(position.symbol).bid
            else:  # SELL position
                close_type = mt5.ORDER_TYPE_BUY
                close_price = mt5.symbol_info_tick(position.symbol).ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "price": close_price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Close position {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None:
                return {"success": False, "error": "Failed to close position"}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False, 
                    "error": f"Close failed: {result.retcode} - {result.comment}"
                }
            
            logger.info(f"Position {ticket} closed successfully")
            
            return {
                "success": True,
                "data": {
                    "closed_ticket": ticket,
                    "deal": result.deal,
                    "volume": result.volume,
                    "price": result.price,
                    "profit": getattr(result, 'profit', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_orders(self) -> Dict[str, Any]:
        """Get all pending orders"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            orders = mt5.orders_get()
            if orders is None:
                return {"success": False, "error": "Failed to get orders"}
            
            orders_list = []
            for order in orders:
                orders_list.append({
                    "ticket": order.ticket,
                    "symbol": order.symbol,
                    "type": self._get_order_type_string(order.type),
                    "volume": order.volume_initial,
                    "price_open": order.price_open,
                    "sl": order.sl,
                    "tp": order.tp,
                    "time_setup": datetime.fromtimestamp(order.time_setup).isoformat(),
                    "comment": order.comment
                })
            
            return {
                "success": True,
                "data": orders_list,
                "count": len(orders_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def cancel_order(self, ticket: int) -> Dict[str, Any]:
        """Cancel a pending order"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Prepare cancel request
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
                "comment": f"Cancel order {ticket}",
            }
            
            # Send cancel request
            result = mt5.order_send(request)
            
            if result is None:
                return {"success": False, "error": "Failed to cancel order"}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False, 
                    "error": f"Cancel failed: {result.retcode} - {result.comment}"
                }
            
            logger.info(f"Order {ticket} cancelled successfully")
            
            return {
                "success": True,
                "data": {
                    "cancelled_ticket": ticket,
                    "retcode": result.retcode
                }
            }
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_order_type_string(self, order_type: int) -> str:
        """Convert MT5 order type to string"""
        order_types = {
            0: "BUY",
            1: "SELL",
            2: "BUY_LIMIT",
            3: "SELL_LIMIT",
            4: "BUY_STOP",
            5: "SELL_STOP",
            6: "BUY_STOP_LIMIT",
            7: "SELL_STOP_LIMIT"
        }
        return order_types.get(order_type, "UNKNOWN")

# Global instance
trading_service = TradingService()
