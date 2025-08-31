# Postman Collection Setup Guide

## Import Instructions

1. **Download Collection File**: Use the `MT5_API_Postman_Collection.json` file from this repository
2. **Import to Postman**:
   - Open Postman application
   - Click "Import" button (top left)
   - Select "Upload Files" tab
   - Choose `MT5_API_Postman_Collection.json`
   - Click "Import"

## Environment Configuration

### Base URL Variable
The collection uses a `{{base_url}}` variable set to `http://localhost:5000` by default.

**To change the base URL**:
1. In Postman, click the environment dropdown (top right)
2. Click "Manage Environments"
3. Create new environment or edit existing
4. Add variable:
   - **Key**: `base_url`
   - **Value**: `http://localhost:5000` (or your deployment URL)

## API Endpoints Overview

### 1. Account Management
- **GET /api/account/info** - Get complete account information
- **GET /api/account/balance** - Get account balance summary
- **GET /api/account/terminal** - Get terminal connection status

### 2. Trading Operations
- **POST /api/trading/calculate-margin** - Calculate position margin requirements
- **POST /api/trading/buy** - Place buy order
- **POST /api/trading/sell** - Place sell order
- **GET /api/trading/positions** - Get all open positions
- **POST /api/trading/close** - Close specific position
- **GET /api/trading/orders** - Get pending orders
- **POST /api/trading/cancel** - Cancel pending order

### 3. Market Data
- **GET /api/market/symbol/{symbol}** - Get symbol information
- **GET /api/market/tick/{symbol}** - Get current tick data
- **POST /api/market/rates** - Get historical price data

### 4. Range Detection
- **GET /api/ranges/fetch-data** - Get all stored market data
- **GET /api/ranges/symbols** - Get symbol mapping
- **GET /api/ranges/calculated** - Get calculated ranges
- **GET /api/ranges/merged** - Get merged ranges
- **POST /api/ranges/clear-cache** - Clear stored data cache

## Sample Request Bodies

### Calculate Margin (Forex)
```json
{
  "symbol": "EURUSD",
  "volume": 1.0,
  "leverage": 100,
  "action": "BUY"
}
```

### Calculate Margin (Gold)
```json
{
  "symbol": "XAUUSD",
  "volume": 0.1,
  "leverage": 50,
  "action": "BUY"
}
```

### Calculate Margin (Crypto)
```json
{
  "symbol": "BTCUSD",
  "volume": 0.01,
  "leverage": 10,
  "action": "BUY"
}
```

### Place Buy Order
```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "sl": 1.0500,
  "tp": 1.1000,
  "comment": "Test buy order"
}
```

### Get Historical Rates (Count-based)
```json
{
  "symbol": "EURUSD",
  "timeframe": "M5",
  "count": 100
}
```

### Get Historical Rates (Date Range)
```json
{
  "symbol": "EURUSD",
  "timeframe": "M5",
  "date_from": "2025-08-30",
  "date_to": "2025-08-31"
}
```

## Response Format

All endpoints return standardized JSON responses:

### Success Response
```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description"
}
```

## Testing Tips

1. **Start with Account endpoints** to verify MT5 connection
2. **Use Market Data endpoints** to check symbol availability
3. **Test Margin Calculation** before placing actual trades
4. **Range Detection endpoints** work with cached data from the scheduler

## Common Symbols for Testing

- **Forex**: EURUSD, GBPUSD, USDJPY, USDCHF
- **Commodities**: XAUUSD (Gold), XAGUSD (Silver)
- **Crypto**: BTCUSD, ETHUSD
- **Indices**: NAS100, SPX500, GER40

## Notes

- The API includes fallback calculations when MT5 is not connected
- Range detection runs automatically every 5 minutes
- All trading operations require valid MT5 connection
- Margin calculations work in both live and demo modes