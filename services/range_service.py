import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta, time, timezone
import logging
from services.mt5_service import mt5_service
from constants.instruments import InstrumentConstants
# Will import old_app functions dynamically to avoid MT5 import issues
try:
    import MetaTrader5 as mt5
except ImportError:
    import services.mock_mt5 as mt5

# Timezone setup (copied from old_app logic)
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    LOCAL_TZ = ZoneInfo("Australia/Sydney")
    BROKER_TZ = ZoneInfo("Etc/GMT-3")  # Broker UTC+3 -> reverse sign for Etc/GMT zones
except Exception:
    import pytz
    LOCAL_TZ = pytz.timezone("Australia/Sydney")
    BROKER_TZ = pytz.FixedOffset(180)  # UTC+3 offset in minutes

logger = logging.getLogger(__name__)

class RangeService:
    """Service for detecting and caching trading ranges"""
    
    def __init__(self):
        self.mt5_service = mt5_service
        self.cache = {}  # In-memory cache for calculated ranges
        self.rates_data = {}  # Local storage for all symbol data as DataFrames
        self.calculated_ranges = {}  # Local storage for raw body ranges as DataFrames
        self.merged_ranges = {}  # Local storage for merged ranges as DataFrames
    
    def get_cache_key(self, symbol: str, timeframe: int, bars: int) -> str:
        """Generate cache key for storing range data"""
        return f"{symbol}_{timeframe}_{bars}"
    
    def mt5_fetch_rates(self, symbol: str, timeframe: int, bars: int = 1500) -> Optional[pd.DataFrame]:
        """Fetch OHLCV bars from MT5 with timezone conversion (based on old_app logic)"""
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
            
            logger.info(f"Fetching rates for symbol with updated function: {symbol}")
            
            # Ensure symbol exists in Market Watch
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol: {symbol}")
                return None
            
            # Fetch OHLC data from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
            if rates is None:
                logger.error(f"No rates returned for {symbol}. Error: {mt5.last_error()}")
                return None
            
            df = pd.DataFrame(rates)
            if df.empty:
                logger.error("Empty rates DataFrame.")
                return None
            
            # --- Convert broker timestamps (UTC+3) → Australia/Sydney (DST-aware) ---
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df["time"] = df["time"].dt.tz_localize(BROKER_TZ)  # Localize MT5 broker time
            df["time"] = df["time"].dt.tz_convert(LOCAL_TZ)    # Convert to Australia/Sydney
            
            # --- Check if crypto symbol → skip trading window filter ---
            crypto_symbols = ["BTCUSD", "ETHUSD"]
            if symbol.upper() not in crypto_symbols:
                # Trading window: 08:00 → 06:55 (next day)
                start_t = time(8, 0)
                end_t = time(6, 55)
                tod = df["time"].dt.time
                base_mask = (tod >= start_t) | (tod <= end_t)
                
                # Restrict to Monday 08:00 → Saturday 06:55
                wd = df["time"].dt.weekday  # Monday=0 ... Sunday=6
                mask = base_mask.copy()
                mask &= (wd <= 5)                                # Drop Sundays entirely
                mask &= ~((wd == 0) & (tod < start_t))           # Drop early Monday before 08:00
                mask &= ~((wd == 5) & (tod > end_t))             # Drop late Saturday after 06:55
                
                df = df[mask].copy()
            
            # Add symbol column
            df["symbol"] = symbol
            
            # Format time column → day-month-year hour:minute
            df["time_formatted"] = df["time"].dt.strftime('%d-%m-%Y %H:%M')
            
            logger.info(f"Fetched {len(df)} bars for {symbol} using old_app logic")
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
    
    def merge_ranges_oldapp(self, range_df: pd.DataFrame) -> pd.DataFrame:
        """Merge ranges using the original old_app merge_ranges function"""
        try:
            if range_df.empty:
                return range_df
            
            # Convert time columns to the format expected by old_app function
            range_df_copy = range_df.copy()
            
            # Ensure time columns are in the correct format for merge_ranges function
            if 'time' in range_df_copy.columns and 'end_time' in range_df_copy.columns:
                range_df_copy['time'] = pd.to_datetime(range_df_copy['time'], format='%d-%m-%Y %H:%M')
                range_df_copy['end_time'] = pd.to_datetime(range_df_copy['end_time'], format='%d-%m-%Y %H:%M')
                
                merged = []
                group_rows = [range_df_copy.iloc[0]]

                for idx in range(1, len(range_df_copy)):
                    row = range_df_copy.iloc[idx]
                    last = group_rows[-1]
                    if last['time'] <= row['time'] <= last['end_time']:
                        group_rows.append(row)
                    else:
                        group_df = pd.DataFrame(group_rows)
                        merged_row = group_rows[0].copy()
                        merged_row['end_time'] = group_df['end_time'].max()
                        merged_row['top'] = group_df['top'].max()
                        merged_row['bottom'] = group_df['bottom'].min()
                        merged_row['duration_bars'] = group_df['duration_bars'].sum()
                        merged_row['range_value'] = round(merged_row['top'] - merged_row['bottom'], 2)
                        merged_row['mid'] = round((merged_row['top'] + merged_row['bottom']) / 2, 2)
                        merged.append(merged_row)
                        group_rows = [row]
                
                # Handle last group
                group_df = pd.DataFrame(group_rows)
                merged_row = group_rows[0].copy()
                merged_row['end_time'] = group_df['end_time'].max()
                merged_row['top'] = group_df['top'].max()
                merged_row['bottom'] = group_df['bottom'].min()
                merged_row['duration_bars'] = group_df['duration_bars'].sum()
                merged_row['range_value'] = round(merged_row['top'] - merged_row['bottom'], 2)
                merged_row['mid'] = round((merged_row['top'] + merged_row['bottom']) / 2, 2)
                merged.append(merged_row)

                result = pd.DataFrame(merged)
                result['time'] = result['time'].dt.strftime('%d-%m-%Y %H:%M')
                result['end_time'] = result['end_time'].dt.strftime('%d-%m-%Y %H:%M')
                result = result.iloc[::-1]  # Reverse order as in original function
                
                return result
            else:
                logger.warning("Missing time columns for merge_ranges function")
                return range_df_copy
            
        except Exception as e:
            logger.error(f"Error merging ranges with old_app function: {str(e)}")
            return range_df

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
            
            # Merge consecutive ranges using old_app merge_ranges function
            merged_ranges = self.merge_ranges_oldapp(body_ranges)
            
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
    
    def fetch_all_symbols_data(self, timeframe: int = 5, bars: int = 1500) -> Dict[str, pd.DataFrame]:
        """Sequential workflow: For each symbol -> mt5_fetch_rates -> ranges -> merge_ranges"""
        try:
            all_symbols = InstrumentConstants.get_all_symbols()
            logger.info(f"Sequential processing for {len(all_symbols)} symbols: {all_symbols}")
            
            # Clear existing data in separate storage variables
            self.rates_data = {}
            self.calculated_ranges = {}
            self.merged_ranges = {}
            
            for symbol_key in all_symbols:
                try:
                    # Get the actual MT5 symbol name
                    instrument = InstrumentConstants.get_instrument(symbol_key)
                    if not instrument:
                        continue
                        
                    mt5_symbol = instrument.symbol
                    logger.info(f"Sequential processing: {symbol_key} -> {mt5_symbol}")
                    
                    # Step 1: Fetch rates using built-in mt5_fetch_rates method
                    rates_df = self.mt5_fetch_rates(mt5_symbol, timeframe, bars)
                    
                    if rates_df is not None and not rates_df.empty:
                        # Store rates data as DataFrame
                        self.rates_data[symbol_key] = rates_df
                        logger.info(f"Step 1 - Fetched {len(rates_df)} rates for {symbol_key}")
                        
                        # Step 2: Calculate body ranges using old_app logic and store as DataFrame
                        try:
                            # Get appropriate range size for symbol
                            range_size = self.get_symbol_range_size(symbol_key)
                            body_ranges_df = self.find_body_ranges(rates_df, 4, range_size)
                            
                            if not body_ranges_df.empty:
                                self.calculated_ranges[symbol_key] = body_ranges_df
                                logger.info(f"Step 2 - Calculated {len(body_ranges_df)} ranges for {symbol_key}")
                                
                                # Step 3: Merge ranges using old_app logic and store as DataFrame
                                merged_ranges_df = self.merge_overlapping_ranges(body_ranges_df)
                                if not merged_ranges_df.empty:
                                    self.merged_ranges[symbol_key] = merged_ranges_df
                                    logger.info(f"Step 3 - Merged to {len(merged_ranges_df)} ranges for {symbol_key}")
                                else:
                                    logger.warning(f"No merged ranges for {symbol_key}")
                                    self.merged_ranges[symbol_key] = pd.DataFrame()
                            else:
                                logger.warning(f"No calculated ranges for {symbol_key}")
                                self.calculated_ranges[symbol_key] = pd.DataFrame()
                                self.merged_ranges[symbol_key] = pd.DataFrame()
                        except Exception as e:
                            logger.error(f"Error calculating ranges for {symbol_key}: {e}")
                            self.calculated_ranges[symbol_key] = pd.DataFrame()
                            self.merged_ranges[symbol_key] = pd.DataFrame()
                    else:
                        logger.warning(f"No rates data for {symbol_key} ({mt5_symbol})")
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol_key}: {str(e)}")
                    continue
            
            logger.info(f"Sequential processing completed - Rates: {len(self.rates_data)}, Ranges: {len(self.calculated_ranges)}, Merged: {len(self.merged_ranges)}")
            return self.rates_data
            
        except Exception as e:
            logger.error(f"Error in sequential fetch: {str(e)}")
            return {}
    
    def get_symbol_data(self, symbol_key: str) -> Optional[pd.DataFrame]:
        """Get stored rates data for a specific symbol"""
        return self.rates_data.get(symbol_key)
    
    def get_all_stored_symbols(self) -> List[str]:
        """Get list of all symbols with stored rates data"""
        return list(self.rates_data.keys())
    
    def calculate_ranges_for_all_symbols(self, lookback: int = 4) -> Dict[str, Dict]:
        """Calculate ranges for all symbols that have stored data"""
        try:
            all_ranges = {}
            logger.info(f"Calculating ranges for {len(self.symbol_data)} symbols")
            
            for symbol_key, df in self.symbol_data.items():
                try:
                    if df is None or df.empty:
                        logger.warning(f"No data available for {symbol_key}")
                        continue
                    
                    # Get appropriate range size for symbol
                    range_size = self.get_symbol_range_size(symbol_key)
                    
                    # Calculate body ranges using the ranges function from old_app
                    body_ranges = self.find_body_ranges(df, lookback, range_size)
                    
                    if body_ranges.empty:
                        logger.info(f"No ranges found for {symbol_key}")
                        
                        # Store empty results in calculated_ranges
                        self.calculated_ranges[symbol_key] = {
                            "symbol": symbol_key,
                            "lookback": lookback,
                            "range_size": range_size,
                            "body_ranges_count": 0,
                            "body_ranges": [],
                            "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                            "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None,
                            "calculation_timestamp": datetime.now().isoformat()
                        }
                        
                        # Store empty results in merged_ranges
                        self.merged_ranges[symbol_key] = {
                            "symbol": symbol_key,
                            "lookback": lookback,
                            "range_size": range_size,
                            "merged_ranges_count": 0,
                            "merged_ranges": [],
                            "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                            "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None,
                            "merge_timestamp": datetime.now().isoformat()
                        }
                        
                        # Store combined empty results for backward compatibility
                        all_ranges[symbol_key] = {
                            "symbol": symbol_key,
                            "lookback": lookback,
                            "range_size": range_size,
                            "body_ranges_count": 0,
                            "merged_ranges_count": 0,
                            "body_ranges": [],
                            "merged_ranges": [],
                            "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                            "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None
                        }
                        continue
                    
                    # Merge consecutive ranges using old_app merge_ranges function
                    merged_ranges = self.merge_ranges_oldapp(body_ranges)
                    
                    # Store raw body ranges in calculated_ranges
                    self.calculated_ranges[symbol_key] = {
                        "symbol": symbol_key,
                        "lookback": lookback,
                        "range_size": range_size,
                        "body_ranges_count": len(body_ranges),
                        "body_ranges": body_ranges.to_dict('records'),
                        "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                        "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None,
                        "calculation_timestamp": datetime.now().isoformat()
                    }
                    
                    # Store merged ranges in merged_ranges
                    self.merged_ranges[symbol_key] = {
                        "symbol": symbol_key,
                        "lookback": lookback,
                        "range_size": range_size,
                        "merged_ranges_count": len(merged_ranges),
                        "merged_ranges": merged_ranges.to_dict('records'),
                        "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                        "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None,
                        "merge_timestamp": datetime.now().isoformat()
                    }
                    
                    # Store combined results for backward compatibility
                    all_ranges[symbol_key] = {
                        "symbol": symbol_key,
                        "lookback": lookback,
                        "range_size": range_size,
                        "body_ranges_count": len(body_ranges),
                        "merged_ranges_count": len(merged_ranges),
                        "body_ranges": body_ranges.to_dict('records'),
                        "merged_ranges": merged_ranges.to_dict('records'),
                        "data_start_time": str(df.iloc[0]["time"]) if not df.empty else None,
                        "data_end_time": str(df.iloc[-1]["time"]) if not df.empty else None
                    }
                    
                    logger.info(f"Calculated {len(body_ranges)} body ranges, {len(merged_ranges)} merged ranges for {symbol_key}")
                    
                except Exception as e:
                    logger.error(f"Error calculating ranges for {symbol_key}: {str(e)}")
                    continue
            
            # Store calculated ranges in local variable
            self.calculated_ranges = all_ranges
            
            logger.info(f"Successfully calculated ranges for {len(all_ranges)} symbols")
            return all_ranges
            
        except Exception as e:
            logger.error(f"Error calculating ranges for all symbols: {str(e)}")
            return {}
    
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
    
    def clear_symbol_data(self, symbol_key: Optional[str] = None):
        """Clear stored symbol data for specific symbol or all symbols"""
        if symbol_key:
            if symbol_key in self.symbol_data:
                del self.symbol_data[symbol_key]
                logger.info(f"Cleared stored data for {symbol_key}")
        else:
            self.symbol_data.clear()
            logger.info("Cleared all stored symbol data")
    
    def get_calculated_ranges(self, symbol_key: Optional[str] = None) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Get calculated ranges DataFrame for a specific symbol or all symbols"""
        if symbol_key:
            return self.calculated_ranges.get(symbol_key, pd.DataFrame())
        return self.calculated_ranges
    
    def get_merged_ranges(self, symbol_key: Optional[str] = None) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Get merged ranges DataFrame for a specific symbol or all symbols"""
        if symbol_key:
            return self.merged_ranges.get(symbol_key, pd.DataFrame())
        return self.merged_ranges
    
    def clear_calculated_ranges(self, symbol_key: Optional[str] = None):
        """Clear calculated ranges for specific symbol or all symbols"""
        if symbol_key:
            if symbol_key in self.calculated_ranges:
                del self.calculated_ranges[symbol_key]
                logger.info(f"Cleared calculated ranges for {symbol_key}")
        else:
            self.calculated_ranges.clear()
            logger.info("Cleared all calculated ranges")
    
    def clear_merged_ranges(self, symbol_key: Optional[str] = None):
        """Clear merged ranges for specific symbol or all symbols"""
        if symbol_key:
            if symbol_key in self.merged_ranges:
                del self.merged_ranges[symbol_key]
                logger.info(f"Cleared merged ranges for {symbol_key}")
        else:
            self.merged_ranges.clear()
            logger.info("Cleared all merged ranges")

# Global instance
range_service = RangeService()

# Function to initialize all symbol data on startup
def initialize_all_symbols_data(timeframe: int = 5, bars: int = 1500) -> Dict[str, pd.DataFrame]:
    """Initialize data for all symbols from constants"""
    return range_service.fetch_all_symbols_data(timeframe, bars)