try:
    import MetaTrader5 as mt5
except ImportError:
    # Fallback to mock MT5 for non-Windows platforms
    import services.mock_mt5 as mt5
import logging
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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from services.mt5_service import mt5_service

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service class for market data operations"""
    
    def __init__(self):
        self.mt5_service = mt5_service
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {"success": False, "error": f"Symbol {symbol} not found"}
            
            return {
                "success": True,
                "data": {
                    "name": symbol_info.name,
                    "basis": symbol_info.basis,
                    "category": symbol_info.category,
                    "currency_base": symbol_info.currency_base,
                    "currency_profit": symbol_info.currency_profit,
                    "currency_margin": symbol_info.currency_margin,
                    "digits": symbol_info.digits,
                    "trade_calc_mode": symbol_info.trade_calc_mode,
                    "trade_mode": symbol_info.trade_mode,
                    "min_volume": symbol_info.volume_min,
                    "max_volume": symbol_info.volume_max,
                    "volume_step": symbol_info.volume_step,
                    "spread": symbol_info.spread,
                    "spread_float": symbol_info.spread_float,
                    "point": symbol_info.point,
                    "tick_value": symbol_info.trade_tick_value,
                    "tick_size": symbol_info.trade_tick_size,
                    "contract_size": symbol_info.trade_contract_size
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_tick_data(self, symbol: str) -> Dict[str, Any]:
        """Get current tick data for a symbol"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"success": False, "error": f"Failed to get tick data for {symbol}"}
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "time": datetime.fromtimestamp(tick.time).isoformat(),
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last,
                    "volume": tick.volume,
                    "spread": tick.ask - tick.bid,
                    "flags": tick.flags
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tick data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_rates(self, symbol: str, timeframe: str, count: int = 100, 
                  start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get historical rates data"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Convert timeframe string to MT5 constant
            timeframe_map = {
                "M1": mt5.TIMEFRAME_M1,
                "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15,
                "M30": mt5.TIMEFRAME_M30,
                "H1": mt5.TIMEFRAME_H1,
                "H4": mt5.TIMEFRAME_H4,
                "D1": mt5.TIMEFRAME_D1,
                "W1": mt5.TIMEFRAME_W1,
                "MN1": mt5.TIMEFRAME_MN1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe.upper())
            if mt5_timeframe is None:
                return {"success": False, "error": f"Invalid timeframe: {timeframe}"}
            
            # Get rates
            if start_time:
                rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_time, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            
            if rates is None:
                return {"success": False, "error": f"Failed to get rates for {symbol}"}
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Convert to list of dictionaries
            rates_list = []
            for _, row in df.iterrows():
                rates_list.append({
                    "time": row['time'].isoformat(),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "tick_volume": int(row['tick_volume']),
                    "spread": int(row['spread']),
                    "real_volume": int(row['real_volume'])
                })
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "count": len(rates_list),
                    "rates": rates_list
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rates: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_ticks(self, symbol: str, count: int = 100, 
                  start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get historical tick data"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Get ticks
            if start_time:
                ticks = mt5.copy_ticks_from(symbol, start_time, count, mt5.COPY_TICKS_ALL)
            else:
                # Get ticks from 1 hour ago if no start time specified
                start_time = datetime.now() - timedelta(hours=1)
                ticks = mt5.copy_ticks_from(symbol, start_time, count, mt5.COPY_TICKS_ALL)
            
            if ticks is None:
                return {"success": False, "error": f"Failed to get ticks for {symbol}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Convert to list of dictionaries
            ticks_list = []
            for _, row in df.iterrows():
                ticks_list.append({
                    "time": row['time'].isoformat(),
                    "bid": float(row['bid']),
                    "ask": float(row['ask']),
                    "last": float(row['last']),
                    "volume": int(row['volume']),
                    "flags": int(row['flags'])
                })
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "count": len(ticks_list),
                    "ticks": ticks_list
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting ticks: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_symbols(self) -> Dict[str, Any]:
        """Get list of available symbols"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            symbols = mt5.symbols_get()
            if symbols is None:
                return {"success": False, "error": "Failed to get symbols list"}
            
            symbols_list = []
            for symbol in symbols:
                symbols_list.append({
                    "name": symbol.name,
                    "description": symbol.description,
                    "category": symbol.category,
                    "currency_base": symbol.currency_base,
                    "currency_profit": symbol.currency_profit,
                    "visible": symbol.visible,
                    "digits": symbol.digits,
                    "spread": symbol.spread
                })
            
            return {
                "success": True,
                "data": symbols_list,
                "count": len(symbols_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_symbols(self, pattern: str) -> Dict[str, Any]:
        """Search for symbols matching a pattern"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            symbols = mt5.symbols_get(pattern)
            if symbols is None:
                return {"success": False, "error": f"No symbols found matching pattern: {pattern}"}
            
            symbols_list = []
            for symbol in symbols:
                symbols_list.append({
                    "name": symbol.name,
                    "description": symbol.description,
                    "category": symbol.category,
                    "currency_base": symbol.currency_base,
                    "currency_profit": symbol.currency_profit,
                    "visible": symbol.visible
                })
            
            return {
                "success": True,
                "data": symbols_list,
                "count": len(symbols_list)
            }
            
        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance
market_data_service = MarketDataService()
