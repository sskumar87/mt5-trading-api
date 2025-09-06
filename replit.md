# Overview

This is a Flask-based REST API that provides a web interface to MetaTrader 5 (MT5) trading platform. The application enables programmatic trading operations, market data retrieval, account management, and advanced range detection functionality through HTTP endpoints. It's designed as a production-ready API that bridges web applications with the MT5 desktop trading terminal.

The system serves as middleware between web clients and the MT5 platform, handling authentication, order management, market data queries, account information retrieval, and intelligent range detection with caching. It includes comprehensive error handling, request validation, and logging capabilities.

# Recent Changes

## 2025-09-05: MT5 Historical Orders Data Mapper & Position Analysis
- **Data Mapper Implementation**: Created comprehensive `MT5OrderDataMapper` class to convert numeric codes from MT5 historical orders to meaningful text
- **Complete Field Mapping**: Maps order types, states, reasons, time types, and filling types with human-readable descriptions
- **Timezone Conversion**: Integrated same timezone logic as ranges service using `pd.to_datetime`, `tz_localize`, and `tz_convert` for Australia/Sydney time
- **Enhanced Order Data**: Adds calculated fields like execution percentage, direction, market/pending flags, and timezone-aware timestamps
- **Position Summaries**: Created position grouping by `position_id` with entry/exit analysis, profit/loss calculations, and comprehensive position metrics
- **Historical Orders API**: Added `/api/trading/history/orders` endpoint for retrieving and mapping historical order data
- **Orders Summary API**: Added `/api/trading/history/orders/summary` endpoint for statistical analysis of order history
- **Position Analysis API**: Added `/api/trading/history/positions` endpoint for position-based profit/loss analysis and trading performance metrics
- **Flexible Date Filtering**: Support for date range filtering and symbol-specific queries with optional data mapping
- **Trading Analytics**: Automatic calculation of execution rates, win rates, profit/loss analysis, and comprehensive trading pattern analysis

## 2025-09-02: Timezone Handling Enhancement
- **Timezone Support**: Added Australia/Sydney local timezone and broker timezone handling to MT5 service
- **Broker Offset Detection**: Implemented `get_broker_offset()` method to fetch broker's UTC offset using tick data
- **Timezone Information API**: Added `/api/account/timezone` endpoint for timezone debugging and display
- **Class Variables**: Added `LOCAL_TZ` and `BROKER_TZ` as class-level variables for consistent timezone handling
- **Time Conversion Ready**: Infrastructure prepared for accurate time conversions between local, broker, and UTC times

## 2025-08-31: Margin Calculation API for Alertwatch React App
- **New Endpoint**: Added `/api/trading/calculate-margin` endpoint for position margin calculations
- **Risk Management Integration**: Designed specifically for Alertwatch React app's Risk Management & Lot Calculator component
- **Comprehensive Calculation**: Supports all major instruments (forex, commodities, crypto, indices) with accurate margin calculations
- **Fallback System**: Includes robust fallback calculations when MT5 connection is unavailable
- **Detailed Response**: Returns margin amount, calculation breakdown, contract sizes, and currency information

## 2025-08-26: Separate Storage Variables for Raw Calculations
- **Scheduler Enhancement**: Modified scheduled fetch process to calculate ranges after fetching data for all symbols
- **Raw Data Storage**: All MT5 price data stored in `range_service.symbol_data` local variable on startup and every 5 minutes
- **Separate Calculation Storage**: Raw calculations stored in dedicated local variables:
  - **calculated_ranges**: Raw body ranges from old_app ranges function stored in `range_service.calculated_ranges`
  - **merged_ranges**: Processed ranges from old_app merge_ranges function stored in `range_service.merged_ranges`
  - **metadata**: Symbol info, range counts, timestamps, and calculation parameters for each storage type
- **Dedicated API Endpoints**: 
  - `/api/ranges/calculated` - Access raw body ranges from ranges function
  - `/api/ranges/merged` - Access merged ranges from merge_ranges function
- **Automated Processing**: Every 5 minutes, the system fetches 5-minute candle data and runs complete old_app pipeline
- **Original Function Integration**: Uses exact old_app ranges and merge_ranges functions for authentic calculations
- **Dual Storage Pattern**: All calculation steps stored separately in dedicated local variables on startup and scheduled execution

## 2025-08-25: Range Detection & Code Organization
- **Resolved merge conflicts**: Fixed git conflicts in routes and service files for clean codebase
- **Range Detection API**: Implemented advanced range detection functionality from user notebooks with in-memory caching
- **Constants Refactoring**: Extracted instrument mapping into clean dataclass-based `InstrumentConstants` class for better type safety
- **URL Encoding Fix**: Fixed symbol handling for instruments with + suffix (EURUSD+, XAUUSD+) using proper URL decoding
- **Performance Optimization**: Added in-memory caching system to avoid recalculation delays on repeated requests

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
- **Flask Application Factory Pattern**: Uses the factory pattern in `app.py` with blueprint-based route organization for modularity and scalability
- **Service Layer Architecture**: Business logic separated into dedicated service classes (`mt5_service`, `trading_service`, `market_data_service`, `range_service`) that handle MT5 platform interactions
- **Blueprint-based Routing**: Routes organized by functionality into separate blueprints (account, trading, market data, ranges) for better code organization
- **Constants Organization**: Instrument mappings and configuration organized in dedicated constants classes with dataclass structure

## API Design
- **RESTful Endpoints**: Four main API categories under `/api/account`, `/api/trading`, `/api/market`, and `/api/ranges` prefixes
- **Range Detection API**: Advanced endpoints for fetching range data, symbol mapping, and cache management
- **Trading Operations**: Complete trading API including margin calculations for risk management
- **Margin Calculation API**: Dedicated endpoint for position size margin calculations supporting all major instruments
- **Standardized JSON Responses**: Consistent response format with `success` boolean and appropriate data/error fields
- **Request Validation**: Input validation using utility functions for required fields and trading parameter validation
- **CORS Enabled**: Cross-origin requests allowed for frontend integration

## MT5 Integration
- **Connection Management**: Persistent connection handling with automatic reconnection logic in the MT5 service layer
- **Trading Operations**: Support for market and limit orders with stop loss and take profit functionality
- **Market Data Access**: Real-time tick data, historical rates, and symbol information retrieval
- **Account Management**: Account info, terminal status, and connection monitoring

## Error Handling & Logging
- **Centralized Error Handlers**: HTTP error handlers registered globally with standardized JSON error responses
- **Comprehensive Logging**: File and console logging with configurable levels, including audit trails for trading operations
- **Validation Layer**: Input validation utilities for trading parameters and request data integrity

## Configuration Management
- **Environment-based Config**: MT5 credentials, API settings, and risk management parameters loaded from environment variables
- **Risk Management Settings**: Configurable position size limits, daily loss limits, and drawdown protection
- **Security Options**: Optional API key authentication and rate limiting configuration

# External Dependencies

## Core Framework
- **Flask**: Web framework providing the HTTP server and request handling
- **Flask-CORS**: Cross-origin resource sharing support for frontend integration
- **Werkzeug ProxyFix**: Middleware for handling proxy headers in production deployments

## MetaTrader Integration
- **MetaTrader5 Python Package**: Official MT5 Python API for platform communication
- **MT5 Terminal**: Windows-based MT5 desktop application required for broker connectivity

## Data Processing
- **Pandas**: Data manipulation for market data processing and historical rate handling

## Infrastructure
- **Bootstrap & Feather Icons**: Frontend styling and iconography for the documentation interface
- **Python Logging**: Built-in logging framework for application monitoring and debugging