def pip_value_usd(info, volume=1.0):
    """
    info: mt5.symbol_info(symbol)
    Returns USD pip value for the given volume (assumes profit currency = USD).
    """
    point = info.point or 0.0
    digits = info.digits
    tick_size = getattr(info, "trade_tick_size", point) or point
    tick_value = getattr(info, "trade_tick_value", 0.0) or getattr(info, "trade_tick_value_profit", 0.0)

    # pip size: for 5-digit (or 3-digit JPY-style) instruments, pip = 10 * point; else pip = point
    pip_size = point * 10 if digits in (3, 5) else point

    return (pip_size / tick_size) * tick_value * float(volume)
