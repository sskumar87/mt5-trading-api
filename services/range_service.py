import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from services.mt5_service import mt5_service
from constants.instruments import InstrumentConstants
try:
    import MetaTrader5 as mt5
except ImportError:
    import services.mock_mt5 as mt5

logger = logging.getLogger(__name__)

class RangeService:
    """Service for detecting and caching trading ranges"""
    
    def __init__(self):
        self.mt5_service = mt5_service
        self.cache = {}  # In-memory cache for calculated ranges
    
    def get_cache_key(self, symbol: str, timeframe: int, bars: int) -> str:
        """Generate cache key for storing range data"""
        return f"{symbol}_{timeframe}_{bars}"
    
    def mt5_fetch_rates(self, symbol: str, timeframe: int, bars: int = 1500) -> Optional[pd.DataFrame]:
        """Fetch OHLCV bars from MT5 with proper formatting"""
        try:
            if not self.mt5_service.check_connection():
                reconnect_result = self.mt5_service.initialize_connection()
                if not reconnect_result["success"]:
                    return None
            
            # Map timeframe to MT5 constant
            timeframe_map = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1,
                240: mt5.TIMEFRAME_H4,
                1440: mt5.TIMEFRAME_D1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M5)
            
            # Clean and validate symbol
            symbol = symbol.strip()
            logger.info(f"Attempting to fetch rates for symbol: '{symbol}'")
            
            # Ensure symbol exists
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol '{symbol}' not found")
                return None
                
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Failed to select symbol {symbol}")
                    return None
            
            # Fetch rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
            if rates is None:
                logger.error(f"No rates returned for {symbol}")
                return None
            
            df = pd.DataFrame(rates)
            if df.empty:
                return None
            
            # Convert timestamp and add symbol
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df["symbol"] = symbol
            
            # Format time for display
            df["time_formatted"] = df["time"].dt.strftime('%d-%m-%Y %H:%M')
            
            logger.info(f"Fetched {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching rates for {symbol}: {str(e)}")
            return None
    
    def find_body_ranges(self, df: pd.DataFrame, lookback: int, range_size: float,
                        step: Optional[int] = None) -> pd.DataFrame:
        """
        Find windows where the range of candle bodies stays within range_size.
        
        Args:
            df: DataFrame with OHLC data
            lookback: Window size for range detection
            range_size: Maximum allowed body range
            step: Step size (None for sliding window)
        
        Returns:
            DataFrame with detected ranges
        """
        try:
            out = []
            if df is None or df.empty or not {"open", "close"}.issubset(df.columns):
                return pd.DataFrame(out)
            
            o = df["open"].astype(float).values
            c = df["close"].astype(float).values
            n = len(df)
            
            if n < lookback:
                return pd.DataFrame(out)
            
            hop = 1 if step is None else max(1, int(step))
            
            for start in range(0, n - lookback + 1, hop):
                end = start + lookback - 1
                
                # Slice window data
                win_o = o[start:end + 1]
                win_c = c[start:end + 1]
                
                # Compute body tops/bottoms
                win_body_top = np.maximum(win_o, win_c)
                win_body_bot = np.minimum(win_o, win_c)
                
                window_top = float(win_body_top.max())
                window_bot = float(win_body_bot.min())
                body_range = window_top - window_bot
                
                if body_range <= range_size:
                    start_time = df.iloc[start]["time_formatted"] if "time_formatted" in df.columns else str(df.iloc[start]["time"])
                    end_time = df.iloc[end]["time_formatted"] if "time_formatted" in df.columns else str(df.iloc[end]["time"])
                    
                    out.append({
                        "symbol": df.iloc[start]["symbol"] if "symbol" in df.columns else None,
                        "time": start_time,
                        "end_time": end_time,
                        "top": round(window_top, 5),
                        "bottom": round(window_bot, 5),
                        "mid": round((window_top + window_bot) / 2.0, 5),
                        "range_value": round(body_range, 5),
                        "duration_bars": lookback,
                        "start_idx": start,
                        "end_idx": end
                    })
            
            return pd.DataFrame(out)
            
        except Exception as e:
            logger.error(f"Error finding body ranges: {str(e)}")
            return pd.DataFrame()
    
    def merge_ranges(self, range_df: pd.DataFrame) -> pd.DataFrame:
        """Merge consecutive overlapping ranges"""
        try:
            if range_df.empty:
                return range_df
            
            # Sort by start time
            range_df = range_df.sort_values('start_idx').reset_index(drop=True)
            
            merged = []
            current_group = [range_df.iloc[0].to_dict()]
            
            for idx in range(1, len(range_df)):
                row = range_df.iloc[idx].to_dict()
                last = current_group[-1]
                
                # Check if ranges overlap
                if last['start_idx'] <= row['start_idx'] <= last['end_idx']:
                    current_group.append(row)
                else:
                    # Merge current group
                    if len(current_group) > 1:
                        merged_row = self._merge_group(current_group)
                        merged.append(merged_row)
                    else:
                        merged.append(current_group[0])
                    current_group = [row]
            
            # Handle last group
            if len(current_group) > 1:
                merged_row = self._merge_group(current_group)
                merged.append(merged_row)
            else:
                merged.append(current_group[0])
            
            return pd.DataFrame(merged)
            
        except Exception as e:
            logger.error(f"Error merging ranges: {str(e)}")
            return range_df
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """Merge a group of overlapping ranges"""
        merged = group[0].copy()
        
        # Update end time and indices
        merged['end_time'] = group[-1]['end_time']
        merged['end_idx'] = max(r['end_idx'] for r in group)
        
        # Update range bounds
        merged['top'] = round(max(r['top'] for r in group), 5)
        merged['bottom'] = round(min(r['bottom'] for r in group), 5)
        merged['mid'] = round((merged['top'] + merged['bottom']) / 2, 5)
        merged['range_value'] = round(merged['top'] - merged['bottom'], 5)
        merged['duration_bars'] = sum(r['duration_bars'] for r in group)
        
        return merged
    
    def get_symbol_range_size(self, symbol: str) -> float:
        """Get the appropriate range size for a symbol"""
        return InstrumentConstants.get_range_size(symbol)
    
    def fetch_and_calculate_ranges(self, symbol: str, timeframe: int = 5, 
                                  bars: int = 5520, lookback: int = 4,
                                  force_refresh: bool = False) -> Dict:
        """
        Fetch data and calculate ranges with caching
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe in minutes
            bars: Number of bars to fetch
            lookback: Lookback period for range detection
            force_refresh: Force recalculation even if cached
        
        Returns:
            Dictionary with ranges data and metadata
        """
        try:
            cache_key = self.get_cache_key(symbol, timeframe, bars)
            
            # Check cache first
            if not force_refresh and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                cache_age = datetime.now() - cached_data['timestamp']
                
                # Cache for 5 minutes
                if cache_age < timedelta(minutes=5):
                    logger.info(f"Returning cached ranges for {symbol}")
                    return {
                        "success": True,
                        "cached": True,
                        "cache_age_seconds": cache_age.total_seconds(),
                        **cached_data['data']
                    }
            
            # Fetch fresh data
            logger.info(f"Calculating ranges for {symbol} (tf={timeframe}, bars={bars})")
            
            # Get market data
            df = self.mt5_fetch_rates(symbol, timeframe, bars)
            if df is None or df.empty:
                return {"success": False, "error": f"No data available for {symbol}"}
            
            # Get appropriate range size for symbol
            range_size = self.get_symbol_range_size(symbol)
            
            # Calculate body ranges
            body_ranges = self.find_body_ranges(df, lookback, range_size)
            if body_ranges.empty:
                return {
                    "success": True,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bars": bars,
                    "lookback": lookback,
                    "range_size": range_size,
                    "body_ranges_count": 0,
                    "merged_ranges_count": 0,
                    "body_ranges": [],
                    "merged_ranges": [],
                    "cached": False
                }
            
            # Merge consecutive ranges
            merged_ranges = self.merge_ranges(body_ranges)
            
            # Prepare result
            result_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": bars,
                "lookback": lookback,
                "range_size": range_size,
                "body_ranges_count": len(body_ranges),
                "merged_ranges_count": len(merged_ranges),
                "body_ranges": body_ranges.to_dict('records'),
                "merged_ranges": merged_ranges.to_dict('records'),
                "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': result_data
            }
            
            logger.info(f"Calculated {len(body_ranges)} body ranges, {len(merged_ranges)} merged ranges for {symbol}")
            
            return {
                "success": True,
                "cached": False,
                **result_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating ranges for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_cached_symbols(self) -> List[str]:
        """Get list of symbols currently in cache"""
        symbols = []
        for key in self.cache.keys():
            symbol = key.split('_')[0]
            if symbol not in symbols:
                symbols.append(symbol)
        return symbols
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for specific symbol or all symbols"""
        if symbol:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Cleared cache for {symbol}")
        else:
            self.cache.clear()
            logger.info("Cleared all cache")

# Global instance
range_service = RangeService()