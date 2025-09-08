import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from services.trading_service import trading_service
from services.order import map_fill, map_time, place_order
from services.mt5_service import mt5_service
from utils.response_helpers import validate_required_fields

logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__)

@trading_bp.route('/order', methods=['POST'])
def send_order():
    """Send a trading order"""
    try:
        req = request.get_json()
        type_filling = map_fill(req['type_filling'])
        type_time = map_time(req['type_time'])
        result = place_order(
            symbol=req.get('symbol'),
            side=req.get('side'),
            volume=req.get('volume'),
            kind=req.get('kind'),
            price=req.get('price'),
            stoplimit=req.get("stoplimit"),
            deviation=req.get("deviation"),
            sl_points=req.get('sl_points'),
            tp_points=req.get('tp_points'),
            sl_price=req.get('sl_price'),
            tp_price=req.get('tp_price'),
            magic=req.get('magic'),
            comment=req.get('comment'),
            do_order_check=req.get('do_order_check'),
            type_filling=type_filling,
            type_time=type_time,
            expiration=req.get('expiration'),
        )

        return jsonify(result), 200 if result.ok else 400

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


@trading_bp.route('/calculate-margin', methods=['POST'])
def calculate_margin():
    """Calculate margin requirement for a given position size - for Alertwatch React app"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbol', 'volume']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result["valid"]:
            return jsonify({"success": False, "error": validation_result["error"]}), 400
        
        symbol = data.get('symbol').upper()
        volume = float(data.get('volume'))
        leverage = data.get('leverage', 100)  # Default leverage 1:100
        action = data.get('action', 'BUY').upper()  # BUY or SELL
        
        # Validate inputs
        if volume <= 0:
            return jsonify({"success": False, "error": "Volume must be greater than 0"}), 400
        
        if leverage <= 0:
            return jsonify({"success": False, "error": "Leverage must be greater than 0"}), 400
        
        # Calculate margin using trading service
        result = trading_service.calculate_margin(
            symbol=symbol,
            volume=volume,
            leverage=leverage,
            action=action
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in calculate margin endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@trading_bp.route('/history/orders', methods=['GET'])
def get_historical_orders():
    """
    Get historical orders with mapped data
    
    Query Parameters:
    - from_date: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - to_date: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - symbol: Symbol filter (optional)
    - map_data: Whether to map numeric codes to text (default: true)
    
    Example URLs:
    /api/trading/history/orders
    /api/trading/history/orders?symbol=XAUUSD
    /api/trading/history/orders?from_date=2024-01-01&to_date=2024-01-31
    /api/trading/history/orders?map_data=false
    """
    try:
        # Parse query parameters
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        symbol = request.args.get('symbol')
        map_data = request.args.get('map_data', 'true').lower() == 'true'
        
        # Parse dates if provided
        from_date = None
        to_date = None
        
        if from_date_str:
            try:
                # Try different date formats
                if len(from_date_str) == 10:  # YYYY-MM-DD
                    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM:SS
                    from_date = datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid from_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                }), 400
        
        if to_date_str:
            try:
                # Try different date formats
                if len(to_date_str) == 10:  # YYYY-MM-DD
                    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM:SS
                    to_date = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid to_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                }), 400
        
        # Get historical orders
        result = mt5_service.get_historical_orders(
            from_date=from_date,
            to_date=to_date,
            symbol=symbol,
            map_data=map_data
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        logger.error(f"Error in historical orders endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@trading_bp.route('/history/orders/summary', methods=['GET'])
def get_orders_summary():
    """
    Get a summary of historical orders with key statistics
    
    Query Parameters:
    - from_date: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - to_date: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - symbol: Symbol filter (optional)
    """
    try:
        # Parse query parameters (same as above)
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        symbol = request.args.get('symbol')
        
        # Parse dates if provided
        from_date = None
        to_date = None
        
        if from_date_str:
            try:
                if len(from_date_str) == 10:  # YYYY-MM-DD
                    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM:SS
                    from_date = datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid from_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                }), 400
        
        if to_date_str:
            try:
                if len(to_date_str) == 10:  # YYYY-MM-DD
                    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM:SS
                    to_date = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid to_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                }), 400
        
        # Get historical orders with mapping
        result = mt5_service.get_historical_orders(
            from_date=from_date,
            to_date=to_date,
            symbol=symbol,
            map_data=True
        )
        
        if not result["success"]:
            return jsonify(result), 400
        
        orders = result["data"]["orders"]
        
        # Calculate summary statistics
        total_orders = len(orders)
        buy_orders = len([o for o in orders if o.get('direction') == 'BUY'])
        sell_orders = len([o for o in orders if o.get('direction') == 'SELL'])
        filled_orders = len([o for o in orders if o.get('state_text') == 'FILLED'])
        canceled_orders = len([o for o in orders if o.get('state_text') == 'CANCELED'])
        pending_orders = len([o for o in orders if o.get('is_pending', False)])
        
        # Group by order types
        order_types = {}
        for order in orders:
            order_type = order.get('type_text', 'UNKNOWN')
            order_types[order_type] = order_types.get(order_type, 0) + 1
        
        # Group by symbols
        symbols = {}
        for order in orders:
            symbol_name = order.get('symbol', 'UNKNOWN')
            symbols[symbol_name] = symbols.get(symbol_name, 0) + 1
        
        # Group by order sources
        sources = {}
        for order in orders:
            source = order.get('reason_text', 'UNKNOWN')
            sources[source] = sources.get(source, 0) + 1
        
        summary = {
            "success": True,
            "data": {
                "period": {
                    "from_date": result["data"]["from_date"],
                    "to_date": result["data"]["to_date"],
                    "symbol_filter": symbol
                },
                "totals": {
                    "total_orders": total_orders,
                    "buy_orders": buy_orders,
                    "sell_orders": sell_orders,
                    "filled_orders": filled_orders,
                    "canceled_orders": canceled_orders,
                    "pending_orders": pending_orders
                },
                "breakdown": {
                    "by_type": order_types,
                    "by_symbol": symbols,
                    "by_source": sources
                },
                "execution_rate": round((filled_orders / total_orders * 100), 2) if total_orders > 0 else 0
            }
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error in orders summary endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@trading_bp.route('/history/positions', methods=['GET'])
def get_position_summaries():
    """
    Get position summaries by grouping orders with same position_id
    
    Query Parameters:
    - period: Predefined period (TODAY, YESTERDAY, CURR_WEEK, LAST_WEEK, LAST_2_WEEKS, CURR_MONTH, LAST_MONTH)
    - from_date: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) - ignored if period is provided
    - to_date: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) - ignored if period is provided
    - symbol: Symbol filter (optional)
    
    Examples:
    /api/trading/history/positions?period=TODAY
    /api/trading/history/positions?period=LAST_WEEK&symbol=XAUUSD
    /api/trading/history/positions?from_date=2025-01-01&to_date=2025-01-31
    """
    try:
        # Parse query parameters
        period = request.args.get('period')
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        symbol = request.args.get('symbol')
        
        # Handle period-based filtering
        from_date = None
        to_date = None
        
        if period:
            # Use period conversion
            try:
                from utils.date_utils import convert_period_to_dates
                from_date, to_date = convert_period_to_dates(period)
            except ValueError as e:
                return jsonify({
                    "success": False, 
                    "error": str(e)
                }), 400
        else:
            # Parse manual date inputs
            if from_date_str:
                try:
                    if len(from_date_str) == 10:  # YYYY-MM-DD
                        from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
                    else:  # YYYY-MM-DD HH:MM:SS
                        from_date = datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return jsonify({
                        "success": False, 
                        "error": "Invalid from_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    }), 400
            
            if to_date_str:
                try:
                    if len(to_date_str) == 10:  # YYYY-MM-DD
                        to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
                    else:  # YYYY-MM-DD HH:MM:SS
                        to_date = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return jsonify({
                        "success": False, 
                        "error": "Invalid to_date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    }), 400
        
        # Get historical orders with mapping
        orders_result = mt5_service.get_historical_orders(
            from_date=from_date,
            to_date=to_date,
            symbol=symbol,
            map_data=True
        )
        
        if not orders_result["success"]:
            return jsonify(orders_result), 400
        
        orders = orders_result["data"]["orders"]
        
        # Create position summaries
        from utils.mt5_data_mapper import create_position_summaries
        position_summaries = create_position_summaries(orders)
        
        # Calculate summary statistics
        total_positions = len(position_summaries)
        profitable_positions = len([p for p in position_summaries if p['is_profitable']])
        loss_positions = total_positions - profitable_positions
        
        total_profit_loss = sum(p['profit_loss'] for p in position_summaries)
        
        # Calculate win rate
        win_rate = (profitable_positions / total_positions * 100) if total_positions > 0 else 0
        
        # Include period information in response
        filter_info = {
            "symbol": symbol,
            "total_orders_processed": len(orders)
        }
        
        if period:
            from utils.date_utils import PeriodDateConverter
            filter_info.update({
                "period": period,
                "period_description": PeriodDateConverter.get_period_description(period),
                "calculated_from_date": from_date.strftime("%Y-%m-%d %H:%M:%S") if from_date else None,
                "calculated_to_date": to_date.strftime("%Y-%m-%d %H:%M:%S") if to_date else None
            })
        else:
            filter_info.update({
                "from_date": orders_result["data"]["from_date"],
                "to_date": orders_result["data"]["to_date"]
            })

        return jsonify({
            "success": True,
            "data": {
                "positions": position_summaries,
                "summary": {
                    "total_positions": total_positions,
                    "profitable_positions": profitable_positions,
                    "loss_positions": loss_positions,
                    "win_rate": round(win_rate, 2),
                    "total_profit_loss": round(total_profit_loss, 2),
                    "average_profit_loss": round(total_profit_loss / total_positions, 2) if total_positions > 0 else 0
                },
                "filter": filter_info
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in position summaries endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
