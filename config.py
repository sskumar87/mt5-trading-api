import os

class Config:
    """Configuration class for the Flask application"""
    
    # MetaTrader 5 Configuration
    MT5_LOGIN = os.environ.get('MT5_LOGIN')
    MT5_PASSWORD = os.environ.get('MT5_PASSWORD')
    MT5_SERVER = os.environ.get('MT5_SERVER')
    MT5_PATH = os.environ.get('MT5_PATH', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe')
    
    # API Configuration
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100 per hour')
    MAX_POSITION_SIZE = float(os.environ.get('MAX_POSITION_SIZE', '10.0'))
    
    # Risk Management
    MAX_DAILY_LOSS = float(os.environ.get('MAX_DAILY_LOSS', '1000.0'))
    MAX_DRAWDOWN_PERCENT = float(os.environ.get('MAX_DRAWDOWN_PERCENT', '5.0'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'mt5_api.log')
    
    # Security
    REQUIRE_API_KEY = os.environ.get('REQUIRE_API_KEY', 'False').lower() == 'true'
    API_KEY = os.environ.get('API_KEY')
