import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register error handlers for the Flask application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        logger.warning(f"Bad Request: {error.description}")
        return jsonify({
            "success": False,
            "error": "Bad Request",
            "message": error.description if hasattr(error, 'description') else "Invalid request"
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        logger.warning(f"Unauthorized: {error.description}")
        return jsonify({
            "success": False,
            "error": "Unauthorized",
            "message": "Authentication required"
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        logger.warning(f"Forbidden: {error.description}")
        return jsonify({
            "success": False,
            "error": "Forbidden",
            "message": "Access denied"
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        logger.info(f"Not Found: {error.description}")
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": "The requested resource was not found"
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        logger.warning(f"Method Not Allowed: {error.description}")
        return jsonify({
            "success": False,
            "error": "Method Not Allowed",
            "message": "The requested method is not allowed for this endpoint"
        }), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        logger.warning(f"Unprocessable Entity: {error.description}")
        return jsonify({
            "success": False,
            "error": "Unprocessable Entity",
            "message": "The request was well-formed but contains semantic errors"
        }), 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors"""
        logger.warning(f"Rate Limit Exceeded: {error.description}")
        return jsonify({
            "success": False,
            "error": "Rate Limit Exceeded",
            "message": "Too many requests. Please try again later."
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {str(error)}")
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        """Handle 502 Bad Gateway errors"""
        logger.error(f"Bad Gateway: {error.description}")
        return jsonify({
            "success": False,
            "error": "Bad Gateway",
            "message": "Unable to connect to MetaTrader 5. Please check your connection."
        }), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors"""
        logger.error(f"Service Unavailable: {error.description}")
        return jsonify({
            "success": False,
            "error": "Service Unavailable",
            "message": "MetaTrader 5 service is temporarily unavailable"
        }), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle general HTTP exceptions"""
        logger.warning(f"HTTP Exception {error.code}: {error.description}")
        return jsonify({
            "success": False,
            "error": error.name,
            "message": error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(error):
        """Handle general exceptions"""
        logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }), 500
