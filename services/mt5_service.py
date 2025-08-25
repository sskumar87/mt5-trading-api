try:
    import MetaTrader5 as mt5
except ImportError:
    # Fallback to mock MT5 for non-Windows platforms
    import services.mock_mt5 as mt5
import logging
import os
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class MT5Service:
    """Service class for MetaTrader 5 operations"""
    
    def __init__(self):
        self.config = Config()
        self.is_connected = False
        self.connection_info = None
    
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
