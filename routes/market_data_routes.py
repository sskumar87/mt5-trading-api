from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
from services.market_data_service import market_data_service
from utils.response_helpers import validate_required_fields

logger = logging.getLogger(__name__)

market_data_bp = Blueprint('market_data', __name__)

@market_data_bp.route('/symbol/<string:symbol>', methods=['GET'])
def get_symbol_info(symbol):
    """Get detailed information about a symbol"""
    try:
        result = market_data_service.get_symbol_info(symbol.upper())
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in symbol info endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/tick/<string:symbol>', methods=['GET'])
def get_tick_data(symbol):
    """Get current tick data for a symbol"""
    try:
        result = market_data_service.get_tick_data(symbol.upper())
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in tick data endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/rates/<string:symbol>', methods=['GET'])
def get_rates(symbol):
    """Get historical rates data"""
    try:
        # Get query parameters
        timeframe = request.args.get('timeframe', 'H1').upper()
        count = int(request.args.get('count', 100))
        start_time_str = request.args.get('start_time')
        
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid start_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                }), 400
        
        result = market_data_service.get_rates(
            symbol=symbol.upper(),
            timeframe=timeframe,
            count=count,
            start_time=start_time
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in rates endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/ticks/<string:symbol>', methods=['GET'])
def get_ticks(symbol):
    """Get historical tick data"""
    try:
        # Get query parameters
        count = int(request.args.get('count', 100))
        start_time_str = request.args.get('start_time')
        
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid start_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                }), 400
        
        result = market_data_service.get_ticks(
            symbol=symbol.upper(),
            count=count,
            start_time=start_time
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in ticks endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """Get list of available symbols"""
    try:
        result = market_data_service.get_symbols()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in symbols endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/symbols/search', methods=['GET'])
def search_symbols():
    """Search for symbols matching a pattern"""
    try:
        pattern = request.args.get('pattern', '*')
        if not pattern:
            return jsonify({"success": False, "error": "Pattern parameter is required"}), 400
        
        result = market_data_service.search_symbols(pattern)
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        logger.error(f"Error in symbol search endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@market_data_bp.route('/quotes', methods=['POST'])
def get_multiple_quotes():
    """Get current quotes for multiple symbols"""
    try:
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({"success": False, "error": "symbols list is required"}), 400
        
        symbols = data.get('symbols', [])
        if not isinstance(symbols, list) or not symbols:
            return jsonify({"success": False, "error": "symbols must be a non-empty list"}), 400
        
        quotes = []
        for symbol in symbols:
            result = market_data_service.get_tick_data(symbol.upper())
            if result["success"]:
                quotes.append(result["data"])
            else:
                quotes.append({
                    "symbol": symbol.upper(),
                    "error": result["error"]
                })
        
        return jsonify({
            "success": True,
            "data": quotes,
            "count": len(quotes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in multiple quotes endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
