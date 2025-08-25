from flask import Blueprint, jsonify, request
import logging
from services.trading_service import trading_service
from utils.response_helpers import validate_required_fields

logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__)

@trading_bp.route('/order', methods=['POST'])
def send_order():
    """Send a trading order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['action', 'symbol', 'volume']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result["valid"]:
            return jsonify({"success": False, "error": validation_result["error"]}), 400
        
        # Extract parameters
        action = data.get('action').upper()
        symbol = data.get('symbol').upper()
        volume = float(data.get('volume'))
        order_type = data.get('order_type', 'market').lower()
        price = data.get('price')
        sl = data.get('sl')
        tp = data.get('tp')
        comment = data.get('comment', '')
        
        if price is not None:
            price = float(price)
        if sl is not None:
            sl = float(sl)
        if tp is not None:
            tp = float(tp)
        
        result = trading_service.send_order(
            action=action,
            symbol=symbol,
            volume=volume,
            order_type=order_type,
            price=price,
            sl=sl,
            tp=tp,
            comment=comment
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in send order endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/positions', methods=['GET'])
def get_positions():
    """Get all open positions"""
    try:
        result = trading_service.get_positions()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in get positions endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/positions/<int:ticket>', methods=['DELETE'])
def close_position(ticket):
    """Close a specific position"""
    try:
        result = trading_service.close_position(ticket)
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in close position endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all pending orders"""
    try:
        result = trading_service.get_orders()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in get orders endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/orders/<int:ticket>', methods=['DELETE'])
def cancel_order(ticket):
    """Cancel a pending order"""
    try:
        result = trading_service.cancel_order(ticket)
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in cancel order endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/buy', methods=['POST'])
def buy_order():
    """Simplified buy order endpoint"""
    try:
        data = request.get_json()
        
        required_fields = ['symbol', 'volume']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result["valid"]:
            return jsonify({"success": False, "error": validation_result["error"]}), 400
        
        symbol = data.get('symbol').upper()
        volume = float(data.get('volume'))
        sl = data.get('sl')
        tp = data.get('tp')
        comment = data.get('comment', 'Buy order via API')
        
        if sl is not None:
            sl = float(sl)
        if tp is not None:
            tp = float(tp)
        
        result = trading_service.send_order(
            action='BUY',
            symbol=symbol,
            volume=volume,
            order_type='market',
            sl=sl,
            tp=tp,
            comment=comment
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in buy order endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@trading_bp.route('/sell', methods=['POST'])
def sell_order():
    """Simplified sell order endpoint"""
    try:
        data = request.get_json()
        
        required_fields = ['symbol', 'volume']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result["valid"]:
            return jsonify({"success": False, "error": validation_result["error"]}), 400
        
        symbol = data.get('symbol').upper()
        volume = float(data.get('volume'))
        sl = data.get('sl')
        tp = data.get('tp')
        comment = data.get('comment', 'Sell order via API')
        
        if sl is not None:
            sl = float(sl)
        if tp is not None:
            tp = float(tp)
        
        result = trading_service.send_order(
            action='SELL',
            symbol=symbol,
            volume=volume,
            order_type='market',
            sl=sl,
            tp=tp,
            comment=comment
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in sell order endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
