try:
    import MetaTrader5 as mt5
except ImportError:
    # Fallback to mock MT5 for non-Windows platforms
    import services.mock_mt5 as mt5
import logging
import os
import pytz
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class MT5Service:
    """Service class for MetaTrader 5 operations"""
    
    def __init__(self):
        self.config = Config()
        self.is_connected = False
        self.connection_info = None
        # Initialize timezone handling
        self.LOCAL_TZ = pytz.timezone("Australia/Sydney")
        self.BROKER_TZ = pytz.FixedOffset(self.get_broker_offset())
    
    def initialize_connection(self) -> Dict[str, Any]:
        """Initialize connection to MetaTrader 5 terminal"""
        try:
            # Initialize MT5 connection
            if not mt5.initialize(path=self.config.MT5_PATH):
                error_msg = f"MT5 initialization failed: {mt5.last_error()}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Login to account if credentials provided
            if all([self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER]):
                login_result = mt5.login(
                    login=int(self.config.MT5_LOGIN),
                    password=self.config.MT5_PASSWORD,
                    server=self.config.MT5_SERVER
                )
                
                if not login_result:
                    error_msg = f"MT5 login failed: {mt5.last_error()}"
                    logger.error(error_msg)
                    mt5.shutdown()
                    return {"success": False, "error": error_msg}
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                error_msg = "Failed to get account information"
                logger.error(error_msg)
                mt5.shutdown()
                return {"success": False, "error": error_msg}
            
            self.is_connected = True
            self.connection_info = account_info._asdict()
            
            logger.info(f"Successfully connected to MT5 - Account: {account_info.login}")
            
            return {
                "success": True,
                "account_info": self.connection_info,
                "message": "Successfully connected to MetaTrader 5"
            }
            
        except Exception as e:
            error_msg = f"Exception during MT5 initialization: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def check_connection(self) -> bool:
        """Check if MT5 connection is active"""
        try:
            account_info = mt5.account_info()
            return account_info is not None
        except:
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        try:
            if not self.check_connection():
                reconnect_result = self.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            account_info = mt5.account_info()
            if account_info is None:
                return {"success": False, "error": "Failed to retrieve account information"}
            
            return {
                "success": True,
                "data": account_info._asdict()
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_terminal_info(self) -> Dict[str, Any]:
        """Get MetaTrader 5 terminal information"""
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return {"success": False, "error": "Failed to retrieve terminal information"}
            
            return {
                "success": True,
                "data": terminal_info._asdict()
            }
            
        except Exception as e:
            logger.error(f"Error getting terminal info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_broker_offset(self, symbol: str = "XAUUSD") -> float:
        """Fetch broker's UTC offset in minutes using tick time."""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.info(f"Failed to fetch tick for {symbol}")
                return 0.0  # fallback to UTC

            # Broker server time from tick (UTC aware)
            server_time = datetime.fromtimestamp(tick.time, tz=timezone.utc)
            utc_now = datetime.now(timezone.utc)
            local_time = datetime.now()
            logger.info(f"Server time {server_time} local time {local_time}")

            # Offset in minutes (broker time - UTC time)
            return (server_time - utc_now).total_seconds() / 60
        except Exception as e:
            logger.warning(f"Error getting broker offset: {str(e)}")
            return 0.0  # fallback to UTC
    
    def get_timezone_info(self) -> Dict[str, Any]:
        """Get timezone information for debugging and display"""
        try:
            broker_offset_minutes = self.get_broker_offset()
            broker_offset_hours = broker_offset_minutes / 60
            
            return {
                "success": True,
                "data": {
                    "local_timezone": str(self.LOCAL_TZ),
                    "broker_offset_minutes": broker_offset_minutes,
                    "broker_offset_hours": broker_offset_hours,
                    "broker_timezone": str(self.BROKER_TZ),
                    "current_utc": datetime.now(timezone.utc).isoformat(),
                    "current_local": datetime.now(self.LOCAL_TZ).isoformat(),
                    "current_broker": datetime.now(self.BROKER_TZ).isoformat() if hasattr(self, 'BROKER_TZ') else "Not available"
                }
            }
        except Exception as e:
            logger.error(f"Error getting timezone info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_historical_orders(self, from_date: datetime = None, to_date: datetime = None, 
                            symbol: str = None, map_data: bool = True) -> Dict[str, Any]:
        """
        Get historical orders with optional data mapping
        
        Args:
            from_date: Start date for order history (defaults to 30 days ago)
            to_date: End date for order history (defaults to now)
            symbol: Optional symbol filter
            map_data: Whether to map numeric codes to text (default: True)
            
        Returns:
            Dict with success status and order data
        """
        try:
            if not self.check_connection():
                reconnect_result = self.initialize_connection()
                if not reconnect_result["success"]:
                    return reconnect_result
            
            # Set default date range if not provided
            if to_date is None:
                to_date = datetime.now()
            if from_date is None:
                from_date = datetime.now().replace(day=1)  # Start of current month
            
            # Get historical orders
            if symbol:
                # Filter by symbol
                orders = mt5.history_orders_get(from_date, to_date, group=symbol)
            else:
                # Get all orders
                orders = mt5.history_orders_get(from_date, to_date)
            
            if orders is None:
                return {
                    "success": False, 
                    "error": "Failed to retrieve historical orders",
                    "mt5_error": mt5.last_error()
                }
            
            # Convert orders to list of dicts
            orders_data = [order._asdict() if hasattr(order, '_asdict') else order for order in orders]
            
            # Apply data mapping if requested
            if map_data:
                from utils.mt5_data_mapper import map_orders_list
                orders_data = map_orders_list(orders_data)
            
            return {
                "success": True,
                "data": {
                    "orders": orders_data,
                    "count": len(orders_data),
                    "from_date": from_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "to_date": to_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol_filter": symbol,
                    "data_mapped": map_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting historical orders: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def shutdown(self) -> Dict[str, Any]:
        """Shutdown MT5 connection"""
        try:
            mt5.shutdown()
            self.is_connected = False
            self.connection_info = None
            logger.info("MT5 connection shutdown successfully")
            
            return {
                "success": True,
                "message": "MT5 connection shutdown successfully"
            }
            
        except Exception as e:
            logger.error(f"Error during MT5 shutdown: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance
mt5_service = MT5Service()
