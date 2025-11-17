from flask import Blueprint, jsonify, request
import logging
from services.mt5_service import mt5_service
from config import Config

logger = logging.getLogger(__name__)

account_bp = Blueprint('account', __name__)

@account_bp.route('/connect', methods=['POST'])
def connect():
    """Initialize connection to MetaTrader 5"""
    try:
        result = mt5_service.initialize_connection()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in connect endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@account_bp.route('/info', methods=['GET'])
def get_account_info():
    """Get account information"""
    try:
        account_size = float(Config().MT5_ACCOUNT_SIZE)
        result = mt5_service.get_account_info()
        balance  = round(result.get("data", {}).get("equity", 0), 2) if result["success"] else 0
        profit = round(balance - account_size, 2)
        result["data"]["profit"] = profit if profit > 0 else 0
        result["data"]["loss"] = profit if profit < 0 else 0
        result["data"]["account_size"] = Config().MT5_ACCOUNT_SIZE
        result["data"]["platform"] = Config().MT5_SERVER
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in account info endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@account_bp.route('/terminal', methods=['GET'])
def get_terminal_info():
    """Get terminal information"""
    try:
        result = mt5_service.get_terminal_info()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in terminal info endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@account_bp.route('/status', methods=['GET'])
def get_connection_status():
    """Check connection status"""
    try:
        is_connected = mt5_service.check_connection()
        return jsonify({
            "success": True,
            "connected": is_connected,
            "account_info": mt5_service.connection_info if is_connected else None
        }), 200
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@account_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Shutdown MT5 connection"""
    try:
        result = mt5_service.shutdown()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in disconnect endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@account_bp.route('/timezone', methods=['GET'])
def timezone_info():
    """Get timezone information for broker and local time"""
    try:
        result = mt5_service.get_timezone_info()
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        logger.error(f"Error in timezone info endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
