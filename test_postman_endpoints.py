#!/usr/bin/env python3
"""
Test script to validate all Postman collection endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        # Check if response is valid JSON
        try:
            json_response = response.json()
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {method} {endpoint} - {response.status_code} - {description}")
            return True
        except json.JSONDecodeError:
            print(f"❌ {method} {endpoint} - Invalid JSON response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Connection error: {e}")
        return False

def main():
    """Test all endpoints from Postman collection"""
    print("🧪 Testing MT5 API Postman Collection Endpoints\n")
    
    # Account Management
    print("📊 Account Management:")
    test_endpoint("GET", "/api/account/info", description="Get account info")
    test_endpoint("GET", "/api/account/balance", description="Get account balance")
    test_endpoint("GET", "/api/account/terminal", description="Get terminal info")
    
    print("\n💰 Trading Operations:")
    # Trading Operations
    test_endpoint("POST", "/api/trading/calculate-margin", 
                 {"symbol": "EURUSD", "volume": 1.0, "leverage": 100, "action": "BUY"}, 
                 "Calculate margin - EURUSD")
    test_endpoint("POST", "/api/trading/calculate-margin", 
                 {"symbol": "XAUUSD", "volume": 0.1, "leverage": 50, "action": "BUY"}, 
                 "Calculate margin - Gold")
    test_endpoint("POST", "/api/trading/calculate-margin", 
                 {"symbol": "BTCUSD", "volume": 0.01, "leverage": 10, "action": "BUY"}, 
                 "Calculate margin - Crypto")
    test_endpoint("GET", "/api/trading/positions", description="Get positions")
    test_endpoint("GET", "/api/trading/orders", description="Get orders")
    
    print("\n📈 Market Data:")
    # Market Data
    test_endpoint("GET", "/api/market/symbol/EURUSD", description="Get EURUSD symbol info")
    test_endpoint("GET", "/api/market/symbol/XAUUSD", description="Get Gold symbol info")
    test_endpoint("GET", "/api/market/tick/EURUSD", description="Get EURUSD tick")
    test_endpoint("POST", "/api/market/rates", 
                 {"symbol": "EURUSD", "timeframe": "M5", "count": 100}, 
                 "Get historical rates")
    
    print("\n🎯 Range Detection:")
    # Range Detection
    test_endpoint("GET", "/api/ranges/symbols", description="Get symbol mapping")
    test_endpoint("GET", "/api/ranges/calculated", description="Get calculated ranges")
    test_endpoint("GET", "/api/ranges/merged", description="Get merged ranges")
    test_endpoint("GET", "/api/ranges/calculated?symbol=EURUSD", description="Get EURUSD ranges")
    
    print("\n✅ Postman collection endpoint validation complete!")
    print("\n📋 Notes:")
    print("• ✅ = Endpoint working (200 status)")
    print("• ⚠️ = Endpoint accessible but may have errors (non-200 status)")
    print("• ❌ = Endpoint not accessible or invalid response")
    print("• Some endpoints require MT5 connection for full functionality")
    print("• Margin calculation works with fallback data when MT5 disconnected")

if __name__ == "__main__":
    main()