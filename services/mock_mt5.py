# Mock MetaTrader5 module for demonstration purposes
# This replaces the actual MT5 module which only works on Windows

import time
from datetime import datetime
from typing import Optional, List, Dict, Any, NamedTuple

# Mock MT5 constants
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_REMOVE = 2

ORDER_TIME_GTC = 0
ORDER_FILLING_IOC = 1

TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H4 = 16388
TIMEFRAME_D1 = 16408
TIMEFRAME_W1 = 32769
TIMEFRAME_MN1 = 49153

COPY_TICKS_ALL = 3

TRADE_RETCODE_DONE = 10009

# Mock data structures
class AccountInfo(NamedTuple):
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    fifo_close: bool
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    assets: float
    liabilities: float
    commission_blocked: float
    name: str
    server: str
    currency: str
    company: str

class TerminalInfo(NamedTuple):
    community_account: bool
    community_connection: bool
    connected: bool
    dlls_allowed: bool
    trade_allowed: bool
    tradeapi_disabled: bool
    email_enabled: bool
    ftp_enabled: bool
    notifications_enabled: bool
    mqid: bool
    build: int
    maxbars: int
    codepage: int
    ping_last: int
    community_balance: float
    retransmission: float
    company: str
    name: str
    language: int
    path: str
    data_path: str
    commondata_path: str

class SymbolInfo(NamedTuple):
    custom: bool
    chart_mode: int
    select: bool
    visible: bool
    session_deals: int
    session_buy_orders: int
    session_sell_orders: int
    volume: int
    volumehigh: int
    volumelow: int
    time: int
    digits: int
    spread: int
    spread_float: bool
    ticks_bookdepth: int
    trade_calc_mode: int
    trade_mode: int
    start_time: int
    expiration_time: int
    trade_stops_level: int
    trade_freeze_level: int
    trade_exemode: int
    swap_mode: int
    swap_rollover3days: int
    margin_hedged_use_leg: bool
    expiration_mode: int
    filling_mode: int
    order_mode: int
    order_gtc_mode: int
    option_mode: int
    option_right: int
    bid: float
    bidhigh: float
    bidlow: float
    ask: float
    askhigh: float
    asklow: float
    last: float
    lasthigh: float
    lastlow: float
    volume_real: float
    volumehigh_real: float
    volumelow_real: float
    option_strike: float
    point: float
    trade_tick_value: float
    trade_tick_value_profit: float
    trade_tick_value_loss: float
    trade_tick_size: float
    trade_contract_size: float
    trade_accrued_interest: float
    trade_face_value: float
    trade_liquidity_rate: float
    volume_min: float
    volume_max: float
    volume_step: float
    volume_limit: float
    swap_long: float
    swap_short: float
    margin_initial: float
    margin_maintenance: float
    session_volume: float
    session_turnover: float
    session_interest: float
    session_buy_orders_volume: float
    session_sell_orders_volume: float
    session_open: float
    session_close: float
    session_aw: float
    session_price_settlement: float
    session_price_limit_min: float
    session_price_limit_max: float
    margin_hedged: float
    price_change: float
    price_volatility: float
    price_theoretical: float
    price_greeks_delta: float
    price_greeks_theta: float
    price_greeks_gamma: float
    price_greeks_vega: float
    price_greeks_rho: float
    price_greeks_omega: float
    price_sensitivity: float
    basis: str
    category: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    description: str
    exchange: str
    formula: str
    isin: str
    name: str
    page: str
    path: str

class Tick(NamedTuple):
    time: int
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int
    volume_real: float

class OrderSendResult(NamedTuple):
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request_id: int
    retcode_external: int

class Position(NamedTuple):
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str

class Order(NamedTuple):
    ticket: int
    time_setup: int
    time_setup_msc: int
    time_done: int
    time_done_msc: int
    time_expiration: int
    type: int
    type_time: int
    type_filling: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str

# Mock global state
_connected = False
_account_info = None
_symbols = {}
_positions = []
_orders = []

def initialize(path: str = None) -> bool:
    """Mock MT5 initialize"""
    global _connected
    _connected = True
    return True

def login(login: int, password: str, server: str) -> bool:
    """Mock MT5 login"""
    global _account_info
    _account_info = AccountInfo(
        login=login,
        trade_mode=0,
        leverage=100,
        limit_orders=200,
        margin_so_mode=0,
        trade_allowed=True,
        trade_expert=True,
        margin_mode=0,
        currency_digits=2,
        fifo_close=False,
        balance=10000.0,
        credit=0.0,
        profit=0.0,
        equity=10000.0,
        margin=0.0,
        margin_free=10000.0,
        margin_level=0.0,
        margin_so_call=50.0,
        margin_so_so=20.0,
        margin_initial=0.0,
        margin_maintenance=0.0,
        assets=10000.0,
        liabilities=0.0,
        commission_blocked=0.0,
        name="Demo Account",
        server=server,
        currency="USD",
        company="Demo Company"
    )
    return True

def shutdown():
    """Mock MT5 shutdown"""
    global _connected, _account_info
    _connected = False
    _account_info = None

def account_info() -> Optional[AccountInfo]:
    """Mock get account info"""
    return _account_info

def terminal_info() -> TerminalInfo:
    """Mock get terminal info"""
    return TerminalInfo(
        community_account=True,
        community_connection=True,
        connected=_connected,
        dlls_allowed=True,
        trade_allowed=True,
        tradeapi_disabled=False,
        email_enabled=False,
        ftp_enabled=False,
        notifications_enabled=True,
        mqid=False,
        build=3815,
        maxbars=65000,
        codepage=1252,
        ping_last=15,
        community_balance=0.0,
        retransmission=0.0,
        company="Demo Company",
        name="Demo Terminal",
        language=1033,
        path="/demo/path",
        data_path="/demo/data",
        commondata_path="/demo/common"
    )

def symbol_info(symbol: str) -> Optional[SymbolInfo]:
    """Mock get symbol info"""
    if symbol == "EURUSD":
        return SymbolInfo(
            custom=False, chart_mode=0, select=True, visible=True,
            session_deals=0, session_buy_orders=0, session_sell_orders=0,
            volume=0, volumehigh=0, volumelow=0, time=int(time.time()),
            digits=5, spread=1, spread_float=True, ticks_bookdepth=10,
            trade_calc_mode=0, trade_mode=4, start_time=0, expiration_time=0,
            trade_stops_level=0, trade_freeze_level=0, trade_exemode=0,
            swap_mode=1, swap_rollover3days=3, margin_hedged_use_leg=False,
            expiration_mode=15, filling_mode=1, order_mode=127, order_gtc_mode=0,
            option_mode=0, option_right=0,
            bid=1.1149, bidhigh=1.1160, bidlow=1.1140,
            ask=1.1151, askhigh=1.1162, asklow=1.1142,
            last=1.1150, lasthigh=1.1161, lastlow=1.1141,
            volume_real=0.0, volumehigh_real=0.0, volumelow_real=0.0,
            option_strike=0.0, point=0.00001,
            trade_tick_value=1.0, trade_tick_value_profit=1.0,
            trade_tick_value_loss=1.0, trade_tick_size=0.00001,
            trade_contract_size=100000.0, trade_accrued_interest=0.0,
            trade_face_value=0.0, trade_liquidity_rate=0.0,
            volume_min=0.01, volume_max=500.0, volume_step=0.01, volume_limit=0.0,
            swap_long=-0.76, swap_short=-4.12,
            margin_initial=0.0, margin_maintenance=0.0,
            session_volume=0.0, session_turnover=0.0, session_interest=0.0,
            session_buy_orders_volume=0.0, session_sell_orders_volume=0.0,
            session_open=1.1145, session_close=1.1150, session_aw=0.0,
            session_price_settlement=0.0, session_price_limit_min=0.0,
            session_price_limit_max=0.0, margin_hedged=50000.0,
            price_change=0.0005, price_volatility=0.0, price_theoretical=0.0,
            price_greeks_delta=0.0, price_greeks_theta=0.0, price_greeks_gamma=0.0,
            price_greeks_vega=0.0, price_greeks_rho=0.0, price_greeks_omega=0.0,
            price_sensitivity=0.0,
            basis="", category="Forex", currency_base="EUR",
            currency_profit="USD", currency_margin="EUR",
            description="Euro vs US Dollar", exchange="",
            formula="", isin="", name="EURUSD", page="", path=""
        )
    return None

def symbol_info_tick(symbol: str) -> Optional[Tick]:
    """Mock get current tick"""
    if symbol == "EURUSD":
        return Tick(
            time=int(time.time()),
            bid=1.1149,
            ask=1.1151,
            last=1.1150,
            volume=0,
            time_msc=int(time.time() * 1000),
            flags=6,
            volume_real=0.0
        )
    return None

def symbol_select(symbol: str, enable: bool) -> bool:
    """Mock symbol select"""
    return True

def symbols_get(pattern: str = None) -> List[SymbolInfo]:
    """Mock get symbols"""
    if pattern is None or "EUR" in pattern:
        return [symbol_info("EURUSD")]
    return []

def order_send(request: Dict[str, Any]) -> Optional[OrderSendResult]:
    """Mock send order"""
    return OrderSendResult(
        retcode=TRADE_RETCODE_DONE,
        deal=123456789,
        order=123456790,
        volume=request.get("volume", 0.1),
        price=request.get("price", 1.1150),
        bid=1.1149,
        ask=1.1151,
        comment=request.get("comment", ""),
        request_id=1,
        retcode_external=0
    )

def positions_get(ticket: int = None) -> List[Position]:
    """Mock get positions"""
    if ticket:
        return [pos for pos in _positions if pos.ticket == ticket]
    return _positions

def orders_get() -> List[Order]:
    """Mock get orders"""
    return _orders

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int):
    """Mock get rates from position"""
    import numpy as np
    
    # Generate mock OHLC data
    base_price = 1.1150
    rates = []
    
    for i in range(count):
        open_price = base_price + np.random.uniform(-0.0020, 0.0020)
        high_price = open_price + np.random.uniform(0, 0.0015)
        low_price = open_price - np.random.uniform(0, 0.0015)
        close_price = open_price + np.random.uniform(-0.0010, 0.0010)
        
        rates.append({
            'time': int(time.time()) - (count - i) * 3600,
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'tick_volume': np.random.randint(100, 1000),
            'spread': 1,
            'real_volume': 0
        })
    
    return np.array(rates, dtype=[
        ('time', 'i8'),
        ('open', 'f8'),
        ('high', 'f8'),
        ('low', 'f8'),
        ('close', 'f8'),
        ('tick_volume', 'i8'),
        ('spread', 'i4'),
        ('real_volume', 'i8')
    ])

def copy_rates_from(symbol: str, timeframe: int, date_from: datetime, count: int):
    """Mock get rates from date"""
    return copy_rates_from_pos(symbol, timeframe, 0, count)

def copy_ticks_from(symbol: str, date_from: datetime, count: int, flags: int):
    """Mock get ticks"""
    import numpy as np
    
    ticks = []
    base_time = int(date_from.timestamp())
    
    for i in range(count):
        bid = 1.1149 + np.random.uniform(-0.0005, 0.0005)
        ask = bid + 0.0002
        
        ticks.append({
            'time': base_time + i,
            'bid': round(bid, 5),
            'ask': round(ask, 5),
            'last': round((bid + ask) / 2, 5),
            'volume': np.random.randint(1, 100),
            'flags': 6
        })
    
    return np.array(ticks, dtype=[
        ('time', 'i8'),
        ('bid', 'f8'),
        ('ask', 'f8'),
        ('last', 'f8'),
        ('volume', 'i8'),
        ('flags', 'i4')
    ])

def last_error() -> tuple:
    """Mock get last error"""
    return (0, "No error")