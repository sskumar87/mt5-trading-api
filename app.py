import os
import logging
import atexit
from datetime import datetime
from flask import Flask, render_template
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Import route blueprints
from routes.account_routes import account_bp
from routes.trading_routes import trading_bp
from routes.market_data_routes import market_data_bp
from routes.range_routes import range_bp

# Import error handlers
from utils.error_handlers import register_error_handlers

# Import range service for scheduled tasks
from services.range_service import range_service

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
    app.register_blueprint(range_bp, url_prefix='/api/ranges')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize and start the scheduler
    start_scheduler()
    
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

def start_scheduler():
    """Start the background scheduler for fetching symbol data"""
    from config import Config
    
    scheduler = BackgroundScheduler()
    
    def fetch_all_data_job():
        """Background job to fetch data for all symbols"""
        try:
            logger = logging.getLogger(__name__)
            logger.info("Starting scheduled fetch for all symbols...")
            
            # Use configurable timeframe and bars
            result = range_service.fetch_all_symbols_data(
                timeframe=Config.SCHEDULER_TIMEFRAME,
                bars=Config.SCHEDULER_BARS
            )
            
            logger.info(f"Scheduled fetch completed. Retrieved data for {len(result)} symbols")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in scheduled fetch job: {str(e)}")
    
    # Get configurable minutes and seconds from configuration
    # This will run every hour at the specified minutes and seconds
    minutes = Config.SCHEDULER_MINUTE
    seconds = Config.SCHEDULER_SECONDS
    
    # Create the trigger to run every hour at specified minutes:seconds
    trigger = CronTrigger(
        minute=minutes,  # Minutes past the hour (e.g., 5 for XX:05:XX)
        second=seconds   # Seconds past the minute (e.g., 30 for XX:XX:30)
    )
    
    scheduler.add_job(
        func=fetch_all_data_job,
        trigger=trigger,
        id='fetch_symbols_job',
        name='Fetch All Symbols Data',
        replace_existing=True
    )
    
    scheduler.start()
    
    # Ensure scheduler shuts down gracefully
    atexit.register(lambda: scheduler.shutdown())
    
    logger = logging.getLogger(__name__)
    logger.info(f"Background scheduler started - will fetch symbol data every hour at :{minutes:02d}:{seconds:02d}")
    logger.info(f"Schedule pattern: Every hour at XX:{minutes:02d}:{seconds:02d}")
    
    # Run initial fetch on startup
    try:
        logger.info("Running initial symbol data fetch on startup...")
        result = range_service.fetch_all_symbols_data(
            timeframe=Config.SCHEDULER_TIMEFRAME,
            bars=Config.SCHEDULER_BARS
        )
        logger.info(f"Initial fetch completed. Retrieved data for {len(result)} symbols")
    except Exception as e:
        logger.error(f"Error in initial fetch: {str(e)}")

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
