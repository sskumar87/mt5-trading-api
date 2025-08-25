import os
import logging
from flask import Flask, render_template
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Import route blueprints
from routes.account_routes import account_bp
from routes.trading_routes import trading_bp
from routes.market_data_routes import market_data_bp

# Import error handlers
from utils.error_handlers import register_error_handlers

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_api.log'),
        logging.StreamHandler()
    ]
)

def create_app():
    """Application factory pattern for creating Flask app"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config.from_object('config.Config')
    
    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Enable CORS for frontend integration
    CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Register blueprints
    app.register_blueprint(account_bp, url_prefix='/api/account')
    app.register_blueprint(trading_bp, url_prefix='/api/trading')
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Main routes
    @app.route('/')
    def index():
        """Main landing page with API overview"""
        return render_template('index.html')
    
    @app.route('/docs')
    def api_docs():
        """API documentation page"""
        return render_template('api_docs.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "MT5 Trading API",
            "version": "1.0.0"
        }
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
