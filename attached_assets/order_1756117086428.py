# main.py
from __future__ import annotations
from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import os

import MetaTrader5 as mt5
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

# --------- Enums / types ----------
OrderSide = Literal["BUY", "SELL"]
OrderKind = Literal[
    "market",
    "buy_limit", "sell_limit",
    "buy_stop", "sell_stop",
    "buy_stop_limit", "sell_stop_limit"
]
FillPolicy = Literal["RETURN", "FOK", "IOC"]
TimePolicy = Literal["GTC", "DAY", "SPECIFIED", "SPECIFIED_DAY"]


# --------- Pydantic request/response models ----------
class OrderRequest(BaseModel):
    symbol: str = Field(..., example="USDJPY")
    side: OrderSide = Field(..., example="BUY")
    volume: float = Field(..., gt=0, example=0.10)
    kind: OrderKind = Field("market", example="market")

    price: Optional[float] = Field(None, example=108.023)        # for pending
    stoplimit: Optional[float] = Field(None, example=108.020)    # *_stop_limit

    deviation: int = Field(20, ge=0, le=1000)
    sl_points: Optional[float] = Field(None, ge=0)
    tp_points: Optional[float] = Field(None, ge=0)
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None

    magic: int = Field(234000, ge=0)
    comment: str = Field("api order", max_length=64)
    do_order_check: bool = True

    type_filling: Optional[FillPolicy] = Field(None, example="RETURN")
    type_time: TimePolicy = Field("GTC")
    expiration: Optional[datetime] = Field(
        None, example="2025-08-23T18:00:00+10:00"
    )

    @validator("price", always=True)
    def _pending_needs_price(cls, v, values):
        if values.get("kind") != "market" and v is None:
            raise ValueError("price is required for pending orders")
        return v

    @validator("stoplimit", always=True)
    def _stop_limit_needs_stoplimit(cls, v, values):
        if values.get("kind") in {"buy_stop_limit", "sell_stop_limit"} and v is None:
            raise ValueError("stoplimit is required for *_stop_limit orders")
        return v


class OrderResponseModel(BaseModel):
    ok: bool
    retcode: int
    retcode_meaning: Optional[str] = None
    comment: str = ""
    result: Optional[dict] = None


# --------- Helpers ----------
def retcode_name(code: int) -> Optional[str]:
    """Map MT5 trade retcode int -> name, e.g., 10009 -> TRADE_RETCODE_DONE."""
    for name in dir(mt5):
        if name.startswith("TRADE_RETCODE_"):
            if getattr(mt5, name) == code:
                return name
    return None


def map_fill(s: Optional[FillPolicy]) -> Optional[int]:
    if s is None:
        return None
    return {
        "RETURN": mt5.ORDER_FILLING_RETURN,
        "FOK": mt5.ORDER_FILLING_FOK,
        "IOC": mt5.ORDER_FILLING_IOC,
    }[s]


def map_time(s: TimePolicy) -> int:
    return {
        "GTC": mt5.ORDER_TIME_GTC,
        "DAY": mt5.ORDER_TIME_DAY,
        "SPECIFIED": mt5.ORDER_TIME_SPECIFIED,
        "SPECIFIED_DAY": mt5.ORDER_TIME_SPECIFIED_DAY,
    }[s]


@dataclass
class _PlaceResult:
    ok: bool
    retcode: int
    comment: str
    result: Optional[mt5.OrderSendResult]


def serialize_mt5_result(res: Optional[mt5.OrderSendResult]) -> Optional[dict]:
    if res is None:
        return None
    d = res._asdict()
    if "request" in d and hasattr(d["request"], "_asdict"):
        d["request"] = d["request"]._asdict()
    return d


# --------- Core place_order logic (from earlier) ----------
def place_order(
    symbol: str,
    side: OrderSide,
    volume: float,
    kind: OrderKind = "market",
    price: Optional[float] = None,
    stoplimit: Optional[float] = None,
    deviation: int = 20,
    sl_points: Optional[float] = None,
    tp_points: Optional[float] = None,
    sl_price: Optional[float] = None,
    tp_price: Optional[float] = None,
    magic: int = 234000,
    comment: str = "python order",
    do_order_check: bool = False,
    type_filling: Optional[int] = None,
    type_time: int = mt5.ORDER_TIME_GTC,
    expiration: Optional[datetime] = None,
) -> _PlaceResult:
    # Ensure symbol visible
    info = mt5.symbol_info(symbol)
    if info is None:
        return _PlaceResult(False, -1, f"Symbol '{symbol}' not found", None)
    if not info.visible:
        if not mt5.symbol_select(symbol, True):
            return _PlaceResult(False, -2, f"symbol_select({symbol}) failed", None)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return _PlaceResult(False, -4, "symbol_info_tick() failed", None)

    # Volume snap to step/min/max
    vol_min = getattr(info, "volume_min", 0.0) or 0.0
    vol_max = getattr(info, "volume_max", volume) or volume
    vol_step = getattr(info, "volume_step", 0.01) or 0.01
    steps = round(volume / vol_step)
    adj_volume = max(vol_min, min(vol_max, steps * vol_step))
    if adj_volume <= 0:
        return _PlaceResult(False, -3, f"Invalid volume after snapping: {adj_volume}", None)



    point = info.point or 0.0
    side = side.upper()
    kind = kind.lower()

    if kind == "market":
        eff_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
        eff_price = tick.ask if side == "BUY" else tick.bid
    else:
        if price is None:
            return _PlaceResult(False, -5, f"price is required for pending '{kind}'", None)
        eff_type = {
            "buy_limit": mt5.ORDER_TYPE_BUY_LIMIT,
            "sell_limit": mt5.ORDER_TYPE_SELL_LIMIT,
            "buy_stop": mt5.ORDER_TYPE_BUY_STOP,
            "sell_stop": mt5.ORDER_TYPE_SELL_STOP,
            "buy_stop_limit": mt5.ORDER_TYPE_BUY_STOP_LIMIT,
            "sell_stop_limit": mt5.ORDER_TYPE_SELL_STOP_LIMIT,
        }[kind]
        eff_price = price

    # SL/TP
    sl = sl_price
    tp = tp_price
    if sl is None and sl_points is not None and point > 0:
        sl = eff_price - sl_points * point if side == "BUY" else eff_price + sl_points * point
    if tp is None and tp_points is not None and point > 0:
        tp = eff_price + tp_points * point if side == "BUY" else eff_price - tp_points * point

    req = {
        "action": mt5.TRADE_ACTION_DEAL if kind == "market" else mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": adj_volume,
        "type": eff_type,
        "price": eff_price,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": type_time,
        "type_filling": type_filling if type_filling is not None else mt5.ORDER_FILLING_RETURN,
    }
    if sl is not None:
        req["sl"] = float(sl)
    if tp is not None:
        req["tp"] = float(tp)
    if "stop_limit" in kind and stoplimit is None:
        return _PlaceResult(False, -7, "stoplimit required for *_stop_limit orders", None)
    if "stop_limit" in kind:
        req["stoplimit"] = float(stoplimit)

    if req["action"] == mt5.TRADE_ACTION_PENDING and type_time == mt5.ORDER_TIME_SPECIFIED and expiration:
        req["expiration"] = expiration

    if do_order_check:
        check = mt5.order_check(req)
        print(check)
        # request the result as a dictionary and display it element by element
        result_dict = check._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field, result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        if check is None:
            return _PlaceResult(False, -8, f"order_check() failed: {mt5.last_error()}", None)
        if check.retcode != mt5.TRADE_RETCODE_DONE:
            return _PlaceResult(False, check.retcode, f"order_check failed: {check.comment}", None)

    print(f"Placing order: {req}")

    res = mt5.order_send(req)

    # fallback for invalid fill policy
    if res is not None and res.retcode == mt5.TRADE_RETCODE_INVALID_FILL and type_filling is None:
        for fp in (mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC):
            req["type_filling"] = fp
            res = mt5.order_send(req)
            if res is not None and res.retcode != mt5.TRADE_RETCODE_INVALID_FILL:
                break

    if res is None:
        return _PlaceResult(False, -9, f"order_send() failed: {mt5.last_error()}", None)

    ok = (res.retcode == mt5.TRADE_RETCODE_DONE)
    return _PlaceResult(ok, res.retcode, getattr(res, "comment", ""), res)

