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
from config import Config
# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
    # Preserve key order in JSON responses
    app.config['JSON_SORT_KEYS'] = False
    app.json.sort_keys = False
    
    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Enable CORS for frontend integration
    CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Log important configuration at startup
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Flask App Configuration:")
    logger.info(f"GOOGLE_CLIENT_ID: {'SET' if app.config.get('GOOGLE_CLIENT_ID') else 'NOT SET'}")
    logger.info(f"DISABLE_AUTH: {app.config.get('DISABLE_AUTH', 'False')}")
    logger.info(f"ALLOWED_EMAILS: '{app.config.get('ALLOWED_EMAILS', '')}'")
    logger.info("=" * 50)
    
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

    @app.route('/api/fetch_symbol_map')
    def symbol_map():
        platform = Config().MT5_SERVER
        symbol_maps = {
            'vantage': {
                "XAUUSD": ["XAUUSD+", 1.5],
                "BTCUSD": ["BTCUSD", 50],
                "ETHUSD": ["ETHUSD", 5],
                "NAS100": ["NAS100", 5],
                "GBPUSD": ["GBPUSD+", 0.00030],
                "EURUSD": ["EURUSD+", 0.00030],
                "USDJPY": ["USDJPY+", 0.003]
            },
            'default': {
                "XAUUSD": ["XAUUSD", 1.5],
                "BTCUSD": ["BTCUSD", 50],
                "ETHUSD": ["ETHUSD", 5],
                "NAS100": ["NAS100", 5],
                "GBPUSD": ["GBPUSD", 0.00030],
                "EURUSD": ["EURUSD", 0.00030],
                "USDJPY": ["USDJPY", 0.003]
            }
        }
        data = symbol_maps['vantage'] if 'vantage' in platform.lower() else symbol_maps['default']
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "MT5 Trading API",
            "data": data
        }


    
    return app

def start_scheduler():
    """Start the background scheduler for fetching symbol data"""
    from config import Config
    
    scheduler = BackgroundScheduler()
    
    def fetch_all_data_job():
        """Background job to fetch data for all symbols and calculate ranges"""
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
    
    # Get configurable interval and seconds from configuration
    # This will run every N minutes at the specified seconds
    interval_minutes = Config.SCHEDULER_INTERVAL_MINUTES
    seconds = Config.SCHEDULER_SECONDS
    
    # Create the trigger to run every N minutes at specified seconds
    # Generate minute values: 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55 for 5-minute intervals
    minute_values = list(range(0, 60, interval_minutes))
    
    trigger = CronTrigger(
        minute=','.join(map(str, minute_values)),  # Run at specific minutes (e.g., "0,5,10,15,20,25,30,35,40,45,50,55")
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
    logger.info(f"Background scheduler started - will fetch symbol data every {interval_minutes} minutes at XX:XX:{seconds:02d}")
    logger.info(f"Schedule pattern: Every {interval_minutes} minutes at {','.join([f'{m:02d}:{seconds:02d}' for m in minute_values])}")
    
    # Run initial fetch on startup
    try:
        logger.info("Running initial symbol data fetch on startup...")
        result = range_service.fetch_all_symbols_data(
            timeframe=Config.SCHEDULER_TIMEFRAME,
            bars=Config.SCHEDULER_BARS
        )
        logger.info(f"Initial fetch completed. Retrieved data for {len(result)} symbols")
        
        # Calculate ranges for initial data
        if result:
            logger.info("Calculating ranges for initial data...")
            ranges_result = range_service.fetch_all_symbols_data()
            logger.info(f"Initial range calculation completed. Calculated ranges for {len(ranges_result)} symbols")
        else:
            logger.warning("No initial data available for range calculation")
    except Exception as e:
        logger.error(f"Error in initial fetch: {str(e)}")

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
