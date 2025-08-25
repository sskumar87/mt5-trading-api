import re
from typing import Dict, Any, Optional
from config import Config

def validate_trading_params(symbol: str, volume: float, action: str, 
                          order_type: str, price: Optional[float] = None) -> Dict[str, Any]:
    """Validate trading parameters"""
    config = Config()
    
    # Validate symbol format
    if not symbol or not isinstance(symbol, str):
        return {"valid": False, "error": "Symbol must be a non-empty string"}
    
    # Basic symbol format validation (alphanumeric + some special chars)
    if not re.match(r'^[A-Za-z0-9._-]+$', symbol):
        return {"valid": False, "error": "Invalid symbol format"}
    
    # Validate volume
    if not isinstance(volume, (int, float)) or volume <= 0:
        return {"valid": False, "error": "Volume must be a positive number"}
    
    if volume > config.MAX_POSITION_SIZE:
        return {"valid": False, "error": f"Volume exceeds maximum position size of {config.MAX_POSITION_SIZE}"}
    
    # Validate action
    valid_actions = ['BUY', 'SELL']
    if action.upper() not in valid_actions:
        return {"valid": False, "error": f"Action must be one of: {', '.join(valid_actions)}"}
    
    # Validate order type
    valid_order_types = ['market', 'limit', 'stop']
    if order_type.lower() not in valid_order_types:
        return {"valid": False, "error": f"Order type must be one of: {', '.join(valid_order_types)}"}
    
    # Validate price for limit/stop orders
    if order_type.lower() in ['limit', 'stop'] and (price is None or price <= 0):
        return {"valid": False, "error": f"Price is required and must be positive for {order_type} orders"}
    
    return {"valid": True}

def validate_symbol(symbol: str) -> Dict[str, Any]:
    """Validate symbol format"""
    if not symbol or not isinstance(symbol, str):
        return {"valid": False, "error": "Symbol must be a non-empty string"}
    
    if not re.match(r'^[A-Za-z0-9._-]+$', symbol):
        return {"valid": False, "error": "Invalid symbol format"}
    
    return {"valid": True}

def validate_timeframe(timeframe: str) -> Dict[str, Any]:
    """Validate timeframe parameter"""
    valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1']
    
    if not timeframe or timeframe.upper() not in valid_timeframes:
        return {
            "valid": False, 
            "error": f"Timeframe must be one of: {', '.join(valid_timeframes)}"
        }
    
    return {"valid": True}

def validate_volume(volume: float) -> Dict[str, Any]:
    """Validate trading volume"""
    config = Config()
    
    if not isinstance(volume, (int, float)) or volume <= 0:
        return {"valid": False, "error": "Volume must be a positive number"}
    
    if volume > config.MAX_POSITION_SIZE:
        return {
            "valid": False, 
            "error": f"Volume exceeds maximum position size of {config.MAX_POSITION_SIZE}"
        }
    
    return {"valid": True}

def validate_price(price: float) -> Dict[str, Any]:
    """Validate price parameter"""
    if not isinstance(price, (int, float)) or price <= 0:
        return {"valid": False, "error": "Price must be a positive number"}
    
    return {"valid": True}

def validate_ticket(ticket: int) -> Dict[str, Any]:
    """Validate ticket number"""
    if not isinstance(ticket, int) or ticket <= 0:
        return {"valid": False, "error": "Ticket must be a positive integer"}
    
    return {"valid": True}

def validate_count(count: int, max_count: int = 10000) -> Dict[str, Any]:
    """Validate count parameter for data requests"""
    if not isinstance(count, int) or count <= 0:
        return {"valid": False, "error": "Count must be a positive integer"}
    
    if count > max_count:
        return {"valid": False, "error": f"Count cannot exceed {max_count}"}
    
    return {"valid": True}
