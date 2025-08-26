from flask import Blueprint, jsonify, request
import logging
from urllib.parse import unquote_plus
from services.range_service import range_service
from constants.instruments import InstrumentConstants
from utils.response_helpers import validate_required_fields

logger = logging.getLogger(__name__)

range_bp = Blueprint('range', __name__)


@range_bp.route('/fetch_data', methods=['GET'])
def fetch_data():
    """Fetch market data and calculate ranges with caching"""
    try:
        # Get query parameters - handle URL encoding properly
        raw_symbol = request.args.get('symbol', 'EURUSD')
        symbol = unquote_plus(
            raw_symbol).strip().upper()  # Handle + and spaces
        tf = int(request.args.get('tf', 5))  # timeframe in minutes
        candles = int(request.args.get('candles', 5520))  # number of bars
        lookback = int(request.args.get('lookback', 4))  # lookback period
        force_refresh = request.args.get('force_refresh',
                                         'false').lower() == 'true'

        # Validate parameters
        if tf not in [1, 5, 15, 30, 60, 240, 1440]:
            return jsonify({
                "success":
                False,
                "error":
                "Invalid timeframe. Use: 1, 5, 15, 30, 60, 240, 1440"
            }), 400

        if candles < 1 or candles > 10000:
            return jsonify({
                "success": False,
                "error": "Candles must be between 1 and 10000"
            }), 400

        # Calculate ranges
        result = range_service.fetch_and_calculate_ranges(
            symbol=symbol,
            timeframe=tf,
            bars=candles,
            lookback=lookback,
            force_refresh=force_refresh)

        return jsonify(result), 200 if result["success"] else 400

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in fetch_data endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/symbols', methods=['GET'])
def get_supported_symbols():
    """Get list of supported symbols with their range sizes"""
    try:
        # Convert instruments to dict format for JSON response
        result = {}
        for key, instrument in InstrumentConstants.INSTRUMENT_MAP.items():
            result[key] = {
                "symbol": instrument.symbol,
                "range": instrument.range
            }

        return jsonify({
            "success": True,
            "data": result,
            "count": len(result)
        }), 200
    except Exception as e:
        logger.error(f"Error in symbols endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """Get cache status and cached symbols"""
    try:
        cached_symbols = range_service.get_cached_symbols()
        cache_keys = list(range_service.cache.keys())

        cache_info = []
        for key, data in range_service.cache.items():
            symbol, tf, bars = key.split('_')
            cache_info.append({
                "key":
                key,
                "symbol":
                symbol,
                "timeframe":
                int(tf),
                "bars":
                int(bars),
                "timestamp":
                data['timestamp'].isoformat(),
                "ranges_count":
                data['data']['body_ranges_count'],
                "merged_count":
                data['data']['merged_ranges_count']
            })

        return jsonify({
            "success": True,
            "cached_symbols": cached_symbols,
            "cache_entries": len(cache_keys),
            "cache_info": cache_info
        }), 200
    except Exception as e:
        logger.error(f"Error in cache status endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache for specific symbol or all symbols"""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')

        if symbol:
            range_service.clear_cache(symbol.upper())
            message = f"Cache cleared for {symbol.upper()}"
        else:
            range_service.clear_cache()
            message = "All cache cleared"

        return jsonify({"success": True, "message": message}), 200
    except Exception as e:
        logger.error(f"Error in clear cache endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/calculated', methods=['GET'])
def get_calculated_ranges():
    """Get all calculated ranges from the scheduled fetch process"""
    try:
        symbol = request.args.get('symbol')
        
        if symbol:
            # Get ranges for specific symbol
            symbol = unquote_plus(symbol).strip().upper()
            ranges_df = range_service.get_calculated_ranges(symbol)
            
            if ranges_df.empty:
                return jsonify({
                    "success": False,
                    "error": f"No calculated ranges found for {symbol}"
                }), 404
            
            # Convert DataFrame to dict for JSON response
            return jsonify({
                "success": True,
                "symbol": symbol,
                "data": ranges_df.to_dict('records'),
                "count": len(ranges_df),
                "description": "Raw body ranges calculated using old_app ranges function"
            }), 200
        else:
            # Get all calculated ranges
            all_ranges = range_service.get_calculated_ranges()
            stored_symbols = range_service.get_all_stored_symbols()
            
            # Convert all DataFrames to dict for JSON response
            serialized_data = {}
            for symbol, df in all_ranges.items():
                if not df.empty:
                    serialized_data[symbol] = {
                        "data": df.to_dict('records'),
                        "count": len(df)
                    }
            
            return jsonify({
                "success": True,
                "symbols_with_data": stored_symbols,
                "symbols_with_ranges": list(serialized_data.keys()),
                "total_symbols": len(serialized_data),
                "data": serialized_data,
                "description": "Raw body ranges calculated using old_app ranges function"
            }), 200

    except Exception as e:
        logger.error(f"Error in get calculated ranges endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/merged', methods=['GET'])
def get_merged_ranges():
    """Get merged ranges calculated by the scheduler for all symbols"""
    try:
        symbol = request.args.get('symbol')
        
        if symbol:
            # Get merged ranges for specific symbol
            symbol = unquote_plus(symbol).strip().upper()
            merged_df = range_service.get_merged_ranges(symbol)
            
            if merged_df.empty:
                return jsonify({
                    "success": False,
                    "error": f"No merged ranges found for {symbol}"
                }), 404
            
            # Convert DataFrame to dict for JSON response
            return jsonify({
                "success": True,
                "symbol": symbol,
                "data": merged_df.to_dict('records'),
                "count": len(merged_df),
                "description": "Merged ranges processed using old_app merge_ranges function"
            }), 200
        else:
            # Get all merged ranges
            all_merged = range_service.get_merged_ranges()
            stored_symbols = range_service.get_all_stored_symbols()
            
            # Convert all DataFrames to dict for JSON response
            serialized_data = {}
            for symbol, df in all_merged.items():
                if not df.empty:
                    serialized_data[symbol] = {
                        "data": df.to_dict('records'),
                        "count": len(df)
                    }
            
            symbols_with_ranges = list(serialized_data.keys())
            
            return jsonify({
                "success": True,
                "symbols_with_data": stored_symbols,
                "symbols_with_ranges": symbols_with_ranges,
                "total_symbols": len(serialized_data),
                "data": serialized_data,
                "description": "Merged ranges processed using old_app merge_ranges function"
            }), 200

    except Exception as e:
        logger.error(f"Error in get merged ranges endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/ranges/<string:symbol>', methods=['GET'])
def get_symbol_ranges(symbol):
    """Get cached ranges for a specific symbol"""
    try:
        symbol = unquote_plus(symbol).strip().upper()  # Handle URL encoding
        tf = int(request.args.get('tf', 5))
        candles = int(request.args.get('candles', 5520))

        cache_key = range_service.get_cache_key(symbol, tf, candles)

        if cache_key not in range_service.cache:
            return jsonify({
                "success":
                False,
                "error":
                f"No cached data for {symbol} with tf={tf}, candles={candles}. Use /fetch_data first."
            }), 404

        cached_data = range_service.cache[cache_key]

        return jsonify({
            "success": True,
            "cached": True,
            "cache_timestamp": cached_data['timestamp'].isoformat(),
            **cached_data['data']
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in get symbol ranges endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@range_bp.route('/quick_scan', methods=['POST'])
def quick_scan():
    """Scan multiple symbols for ranges quickly"""
    try:
        data = request.get_json()

        if not data or 'symbols' not in data:
            return jsonify({
                "success": False,
                "error": "symbols list is required"
            }), 400

        symbols = data.get('symbols', [])
        if not isinstance(symbols, list) or not symbols:
            return jsonify({
                "success": False,
                "error": "symbols must be a non-empty list"
            }), 400

        tf = data.get('tf', 5)
        candles = data.get('candles', 1000)  # Fewer candles for quick scan
        lookback = data.get('lookback', 4)

        results = []
        for symbol in symbols:
            try:
                result = range_service.fetch_and_calculate_ranges(
                    symbol=symbol.upper(),
                    timeframe=tf,
                    bars=candles,
                    lookback=lookback,
                    force_refresh=False  # Use cache if available
                )

                # Simplified result for quick scan
                if result["success"]:
                    results.append({
                        "symbol":
                        symbol.upper(),
                        "ranges_found":
                        result.get("merged_ranges_count", 0),
                        "cached":
                        result.get("cached", False),
                        "latest_range":
                        result["merged_ranges"][0]
                        if result.get("merged_ranges") else None
                    })
                else:
                    results.append({
                        "symbol":
                        symbol.upper(),
                        "ranges_found":
                        0,
                        "error":
                        result.get("error", "Unknown error"),
                        "cached":
                        False
                    })
            except Exception as e:
                results.append({
                    "symbol": symbol.upper(),
                    "ranges_found": 0,
                    "error": str(e),
                    "cached": False
                })

        return jsonify({
            "success":
            True,
            "scan_results":
            results,
            "symbols_scanned":
            len(symbols),
            "successful_scans":
            len([r for r in results if "error" not in r])
        }), 200

    except Exception as e:
        logger.error(f"Error in quick scan endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
