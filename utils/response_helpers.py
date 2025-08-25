from typing import Dict, Any, List, Optional
from flask import jsonify

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate that all required fields are present in the request data"""
    if not data:
        return {"valid": False, "error": "Request body is required"}
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            "valid": False, 
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {"valid": True}

def create_success_response(data: Any = None, message: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {"success": True}
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    # Add any additional kwargs
    response.update(kwargs)
    
    return response

def create_error_response(error: str, code: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Create a standardized error response"""
    response = {
        "success": False,
        "error": error
    }
    
    if code:
        response["code"] = code
    
    # Add any additional kwargs
    response.update(kwargs)
    
    return response

def create_paginated_response(data: List[Any], page: int = 1, per_page: int = 100, 
                            total: Optional[int] = None) -> Dict[str, Any]:
    """Create a paginated response"""
    if total is None:
        total = len(data)
    
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def format_position_data(position: Dict[str, Any]) -> Dict[str, Any]:
    """Format position data for API response"""
    return {
        "ticket": position.get("ticket"),
        "symbol": position.get("symbol"),
        "type": position.get("type"),
        "volume": round(position.get("volume", 0), 2),
        "price_open": round(position.get("price_open", 0), 5),
        "price_current": round(position.get("price_current", 0), 5),
        "profit": round(position.get("profit", 0), 2),
        "swap": round(position.get("swap", 0), 2),
        "time": position.get("time"),
        "comment": position.get("comment", "")
    }

def format_order_data(order: Dict[str, Any]) -> Dict[str, Any]:
    """Format order data for API response"""
    return {
        "ticket": order.get("ticket"),
        "symbol": order.get("symbol"),
        "type": order.get("type"),
        "volume": round(order.get("volume", 0), 2),
        "price_open": round(order.get("price_open", 0), 5),
        "sl": round(order.get("sl", 0), 5) if order.get("sl") else None,
        "tp": round(order.get("tp", 0), 5) if order.get("tp") else None,
        "time_setup": order.get("time_setup"),
        "comment": order.get("comment", "")
    }

def format_tick_data(tick: Dict[str, Any]) -> Dict[str, Any]:
    """Format tick data for API response"""
    return {
        "symbol": tick.get("symbol"),
        "time": tick.get("time"),
        "bid": round(tick.get("bid", 0), 5),
        "ask": round(tick.get("ask", 0), 5),
        "last": round(tick.get("last", 0), 5),
        "volume": tick.get("volume", 0),
        "spread": round(tick.get("spread", 0), 5),
        "flags": tick.get("flags", 0)
    }

def format_rate_data(rate: Dict[str, Any]) -> Dict[str, Any]:
    """Format rate/candlestick data for API response"""
    return {
        "time": rate.get("time"),
        "open": round(rate.get("open", 0), 5),
        "high": round(rate.get("high", 0), 5),
        "low": round(rate.get("low", 0), 5),
        "close": round(rate.get("close", 0), 5),
        "tick_volume": rate.get("tick_volume", 0),
        "spread": rate.get("spread", 0),
        "real_volume": rate.get("real_volume", 0)
    }

def sanitize_symbol(symbol: str) -> str:
    """Sanitize symbol input"""
    if not symbol:
        return ""
    
    # Remove any potentially dangerous characters and convert to uppercase
    return symbol.strip().upper().replace(" ", "")

def format_error_for_logging(error: Exception, context: Optional[str] = None) -> str:
    """Format error for logging purposes"""
    error_msg = f"{type(error).__name__}: {str(error)}"
    if context:
        error_msg = f"[{context}] {error_msg}"
    return error_msg
