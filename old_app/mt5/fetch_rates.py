import logging
from datetime import datetime, timezone, time
import pandas as pd
import MetaTrader5 as mt5
import tzlocal
from typing import Optional
import pytz

logger = logging.getLogger(__name__)

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate the Relative Strength Index (RSI)."""
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_broker_offset(symbol: str = "EURUSD") -> float:
    """Fetch broker's UTC offset in hours using tick time."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to fetch tick for {symbol}")
        return 0.0  # fallback to UTC


    # Broker server time from tick (UTC aware)
    server_time = datetime.fromtimestamp(tick.time, tz=timezone.utc)
    utc_now = datetime.now(timezone.utc)
    local_time = datetime.now()
    logger.info(f"Server time {server_time} local time {local_time}")


    # Offset in hours (broker time - UTC time)
    return (server_time - utc_now).total_seconds() / 60


try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    LOCAL_TZ = ZoneInfo("Australia/Sydney")
    BROKER_TZ = pytz.FixedOffset(get_broker_offset())  # Broker UTC+3 -> reverse sign for Etc/GMT zones
except Exception:
    LOCAL_TZ = pytz.timezone("Australia/Sydney")
    BROKER_TZ = pytz.FixedOffset(get_broker_offset())  # UTC+3 offset in minutes


def get_local_offset() -> float:
    """Fetch system's local UTC offset in hours."""
    local_tz = tzlocal.get_localzone()
    local_time = datetime.now(local_tz)
    return local_time.utcoffset().total_seconds() / 3600



def mt5_fetch_rates(symbol: str,
                    timeframe,
                    bars: int = 1500) -> Optional[pd.DataFrame]:
    """Fetch OHLCV bars from MT5, convert broker UTC+3 timestamps to Australia/Sydney (DST-aware),
    format date, and filter candles for forex market hours only.
    Skips filtering for BTCUSD and ETHUSD (24x7 trading)."""

    print("Fetching rates for symbol with updated function:", symbol)

    # Ensure symbol exists in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol: {symbol}")
        return None

    # Fetch OHLC data from MT5
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        print(f"No rates returned for {symbol}. Error: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    if df.empty:
        print("Empty rates DataFrame.")
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
    df["time"] = df["time"].dt.strftime('%#d-%#m-%Y %H:%M')

    # Set index to formatted time
    df.set_index("time", inplace=True)

    return df


def mt5_fetch_rates_range(symbol: str,
                          timeframe,
                          start_date: str,  # "dd/mm/yyyy"
                          end_date: str    # "dd/mm/yyyy"
                          ) -> Optional[pd.DataFrame]:
    """Fetch OHLCV bars for a date range, convert broker UTC+3 timestamps to Australia/Sydney (DST-aware),
    skip candle filtering for BTCUSD/ETHUSD, otherwise keep only Mon 08:00 → Sat 06:55 and 08:00 → 06:55 window.
    Format time as '%#d-%#m-%Y %H:%M' and set as index."""

    # --- Parse input dates as LOCAL dates, then convert to BROKER tz for the request ---
    try:
        st_day, st_month, st_year = start_date.split("/")
        en_day, en_month, en_year = end_date.split("/")

        # Local midnight bounds
        local_from = datetime(int(st_year), int(st_month), int(st_day), 0, 0, tzinfo=LOCAL_TZ)
        # Use end-of-day inclusive for the end date
        local_to   = datetime(int(en_year), int(en_month), int(en_day), 23, 59, tzinfo=LOCAL_TZ)

        # Convert to broker tz for the MT5 query window
        broker_from = local_from.astimezone(BROKER_TZ)
        broker_to   = local_to.astimezone(BROKER_TZ)
    except Exception as e:
        print(f"Failed to parse dates '{start_date}' - '{end_date}': {e}")
        return None

    # --- Fetch rates from MT5 in the broker window ---
    rates = mt5.copy_rates_range(symbol, timeframe, broker_from, broker_to)
    if rates is None:
        print(f"No rates returned for {symbol}. Error: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    if df.empty:
        print("Empty rates DataFrame.")
        return None

    # --- Convert broker timestamps (UTC+3) → Australia/Sydney (DST-aware) ---
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize(BROKER_TZ)  # treat epoch as broker-local
    df["time"] = df["time"].dt.tz_convert(LOCAL_TZ)    # convert to local (handles DST)

    # --- Optionally filter trading window (skip for crypto 24x7) ---
    crypto_symbols = {"BTCUSD", "ETHUSD"}
    if symbol.upper() not in crypto_symbols:
        # Time-of-day window (overnight): 08:00 → 06:55 next day
        start_t = time(8, 0)
        end_t   = time(6, 55)
        tod = df["time"].dt.time
        base_mask = (tod >= start_t) | (tod <= end_t)

        # Restrict to Monday 08:00 → Saturday 06:55 (local)
        wd = df["time"].dt.weekday  # Monday=0 ... Sunday=6
        mask = base_mask.copy()
        mask &= (wd <= 5)                                # drop Sundays
        mask &= ~((wd == 0) & (tod < start_t))           # early Monday before 08:00
        mask &= ~((wd == 5) & (tod > end_t))             # late Saturday after 06:55

        df = df[mask].copy()

    # --- Final formatting: add symbol, format time, set index ---
    df["symbol"] = symbol
    df["time"] = df["time"].dt.strftime('%#d-%#m-%Y %H:%M')  # requested format
    df.set_index("time", inplace=True)

    return df


