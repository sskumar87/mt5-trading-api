import MetaTrader5 as mt5

def _pip_size(info: mt5.SymbolInfo) -> float:
    """Return pip size in price units for this symbol."""
    point = info.point or 0.0
    # For most FX: 5-digit (e.g., 1.23456) or 3-digit JPY quotes → pip = 10 * point
    # Otherwise pip = point
    return point * 10 if info.digits in (3, 5) else point

def _pip_value_per_lot(info: mt5.SymbolInfo) -> float:
    """USD (account-currency) value of 1 pip for 1.00 lot (uses broker-provided tick values)."""
    tick_size = getattr(info, "trade_tick_size", info.point) or info.point
    # Prefer *_profit (some brokers set both; *_profit reflects P/L currency)
    tick_value = getattr(info, "trade_tick_value_profit", 0.0) or getattr(info, "trade_tick_value", 0.0)
    pip = _pip_size(info)
    if not tick_size or not tick_value or not pip:
        return 0.0
    # pip_value = (# of ticks in one pip) * tick_value_per_tick_for_1lot
    return (pip / tick_size) * float(tick_value)

def calc_lot_size(symbol: str, risk_amount: float, sl_pips: float) -> float:
    """
    Calculate lot size so that (sl_pips * pip_value_per_lot * lots) ≈ risk_amount.
    Floors to broker volume_step so risk is not exceeded.

    Returns:
        lots (float): volume you can send in order requests.
    """
    if sl_pips <= 0:
        raise ValueError("sl_pips must be > 0")
    if risk_amount <= 0:
        raise ValueError("risk_amount must be > 0")

    info = mt5.symbol_info(symbol)
    if info is None:
        raise ValueError(f"Symbol '{symbol}' not found")
    if not info.visible:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"symbol_select({symbol}) failed")

    pip_val_1lot = _pip_value_per_lot(info)
    if pip_val_1lot <= 0:
        raise RuntimeError(f"Cannot determine pip value for {symbol} (tick_value/size missing)")

    raw_lots = risk_amount / (sl_pips * pip_val_1lot)

    # Snap to broker constraints
    step = getattr(info, "volume_step", 0.01) or 0.01
    vmin = getattr(info, "volume_min", step) or step
    vmax = getattr(info, "volume_max", raw_lots) or raw_lots

    # Floor to step so we don't exceed risk
    steps = int(raw_lots / step)
    lots = steps * step
    if lots < vmin:
        lots = vmin  # if even the minimum exceeds risk, you’ll risk slightly more than requested
    if lots > vmax:
        lots = vmax

    # round to a sensible precision
    return round(lots, 4)

# --------- Example ----------
# mt5.initialize()  # make sure MT5 is initialized before calling
# lots = calc_lot_size("XAUUSD", risk_amount=200.0, sl_pips=50)
# print(lots)
