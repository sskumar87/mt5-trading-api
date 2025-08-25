# Overview

This is a Flask-based REST API that provides a web interface to MetaTrader 5 (MT5) trading platform. The application enables programmatic trading operations, market data retrieval, and account management through HTTP endpoints. It's designed as a production-ready API that bridges web applications with the MT5 desktop trading terminal.

The system serves as middleware between web clients and the MT5 platform, handling authentication, order management, market data queries, and account information retrieval. It includes comprehensive error handling, request validation, and logging capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
- **Flask Application Factory Pattern**: Uses the factory pattern in `app.py` with blueprint-based route organization for modularity and scalability
- **Service Layer Architecture**: Business logic separated into dedicated service classes (`mt5_service`, `trading_service`, `market_data_service`) that handle MT5 platform interactions
- **Blueprint-based Routing**: Routes organized by functionality into separate blueprints (account, trading, market data) for better code organization

## API Design
- **RESTful Endpoints**: Three main API categories under `/api/account`, `/api/trading`, and `/api/market` prefixes
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