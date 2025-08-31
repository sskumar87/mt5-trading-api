# Margin Calculation API Documentation
## For Alertwatch React App Integration

### Endpoint
```
POST /api/trading/calculate-margin
```

### Purpose
Calculate margin requirements for position sizes in the Risk Management & Lot Calculator component.

### Request Format
```json
{
  "symbol": "EURUSD",     // Required: Trading symbol
  "volume": 1.0,          // Required: Position size in lots
  "leverage": 100,        // Optional: Leverage ratio (default: 100)
  "action": "BUY"         // Optional: BUY or SELL (default: BUY)
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "symbol": "EURUSD",
    "volume": 1.0,
    "leverage": 100,
    "action": "BUY",
    "price": 1.08,
    "contract_size": 100000,
    "margin": 1080.0,
    "margin_currency": "USD",
    "base_currency": "EUR",
    "quote_currency": "USD",
    "calculation_method": "MT5 order_calc_margin",
    "calculation": "MT5 calculated margin: 1080.00 USD",
    "note": "Live MT5 calculation with current prices"
  }
}
```

### Calculation Methods
The API uses two calculation methods:

1. **MT5 order_calc_margin** (Preferred): When MT5 connection is available
   - Uses `mt5.order_calc_margin()` for accurate broker-specific calculations
   - Includes account currency detection with `mt5.account_info().currency`
   - Automatically enables symbols if not visible
   - Returns exact margin as calculated by your broker

2. **Fallback estimation** (Demo mode): When MT5 connection unavailable
   - Uses standard contract sizes and estimated prices
   - Provides consistent calculations for testing
   - Includes "note" field indicating estimation mode

### Supported Instruments

#### Forex Pairs
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, EURGBP
- Contract Size: 100,000 units

#### Commodities
- XAUUSD (Gold): Contract Size: 100 oz
- XAGUSD (Silver): Contract Size: 5,000 oz

#### Cryptocurrencies
- BTCUSD, ETHUSD
- Contract Size: 1 unit

#### Indices
- NAS100, SPX500, GER40
- Contract Size: 1 unit

### React App Integration

#### JavaScript/TypeScript Example
```javascript
const calculateMargin = async (symbol, volume, leverage = 100, action = 'BUY') => {
  try {
    const response = await fetch('/api/trading/calculate-margin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol: symbol.toUpperCase(),
        volume: parseFloat(volume),
        leverage: parseInt(leverage),
        action: action.toUpperCase()
      })
    });

    const result = await response.json();
    
    if (result.success) {
      return {
        marginRequired: result.data.margin,
        calculation: result.data.calculation,
        calculationMethod: result.data.calculation_method,
        contractSize: result.data.contract_size,
        price: result.data.price,
        currency: result.data.margin_currency,
        isLiveCalculation: result.data.calculation_method === 'MT5 order_calc_margin'
      };
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Margin calculation error:', error);
    throw error;
  }
};

// Usage in Risk Management component
const handlePositionSizeChange = async (positionSize) => {
  if (selectedSymbol && positionSize > 0) {
    try {
      const marginData = await calculateMargin(
        selectedSymbol,
        positionSize,
        accountLeverage,
        tradeDirection
      );
      
      setMarginRequired(marginData.marginRequired);
      setCalculationDetails(marginData.calculation);
    } catch (error) {
      setError('Failed to calculate margin: ' + error.message);
    }
  }
};
```

#### React Hook Example
```javascript
import { useState, useCallback } from 'react';

export const useMarginCalculator = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateMargin = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/trading/calculate-margin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error);
      }

      return result.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { calculateMargin, loading, error };
};
```

### Error Handling

#### Common Error Responses
```json
{
  "success": false,
  "error": "Volume must be greater than 0"
}

{
  "success": false,
  "error": "Leverage must be greater than 0"
}

{
  "success": false,
  "error": "Symbol INVALID not found"
}
```

### Integration Tips

1. **Real-time Updates**: Call the endpoint whenever position size or leverage changes
2. **Input Validation**: Validate inputs on frontend before API calls
3. **Error Display**: Show calculation errors to users in the UI
4. **Fallback Prices**: API includes fallback calculations when MT5 is unavailable
5. **Currency Display**: Use the `margin_currency` field for proper currency display

### Testing Examples

#### Test with different instruments
```bash
# Forex
curl -X POST "/api/trading/calculate-margin" -d '{"symbol":"EURUSD","volume":1.0,"leverage":100}'

# Gold
curl -X POST "/api/trading/calculate-margin" -d '{"symbol":"XAUUSD","volume":0.1,"leverage":50}'

# Crypto
curl -X POST "/api/trading/calculate-margin" -d '{"symbol":"BTCUSD","volume":0.01,"leverage":10}'
```