import pandas as pd
import numpy as np
from typing import List, Dict, Optional

def find_body_ranges(
    df: pd.DataFrame,
    lookback: int,
    range_size: float,
    step: Optional[int] = None  # None => sliding (1). Use lookback for non-overlapping.
) -> pd.DataFrame:
    """
    Find windows of length `lookback` where the range of *candle bodies only*
    stays within `range_size`.

    Per-candle:
      body_top    = max(open, close)
      body_bottom = min(open, close)

    For each window:
      window_top    = max(body_top in window)
      window_bottom = min(body_bottom in window)
      body_range    = window_top - window_bottom

    A window qualifies if body_range <= range_size.

    Returns one record per qualifying window:
      {
        'start_idx','end_idx','start_ts','end_ts',
        'top','bottom','mid','range_value','duration_bars'
      }
    """
    out: List[Dict] = []
    if df is None or df.empty or not {"open", "close"}.issubset(df.columns):
        return out

    o = df["open"].astype(float).values
    c = df["close"].astype(float).values
    idx = df.index
    n = len(df)
    if n < lookback:
        return out

    hop = 1 if step is None else max(1, int(step))

    for start in range(0, n - lookback + 1, hop):
        end = start + lookback - 1

        # Slice window data
        win_o = o[start:end + 1]
        win_c = c[start:end + 1]

        # Compute body tops/bottoms *inside* the window
        win_body_top = np.maximum(win_o, win_c)
        win_body_bot = np.minimum(win_o, win_c)

        window_top = float(win_body_top.max())
        window_bot = float(win_body_bot.min())
        body_range = window_top - window_bot

        if body_range <= range_size:
            out.append({
                "symbol": df.iloc[start]["symbol"] if "symbol" in df.columns else None,
                "time": idx[start],
                "end_time": idx[end],
                "top": window_top,
                "bottom": window_bot,
                "mid": round((window_top + window_bot) / 2.0, 2),
                "range_value": round(body_range, 2),
                "duration_bars": lookback
            })
            # out.append({
            #     "start_idx": start,
            #     "end_idx": end,
            #     "start_ts": idx[start],
            #     "end_ts": idx[end],
            #     "top": window_top,
            #     "bottom": window_bot,
            #     "mid": (window_top + window_bot) / 2.0,
            #     "range_value": body_range,
            #     "duration_bars": lookback
            # })

    # if out:
    #     print(out[0])
    #     print(out[-1])
    return_df  = pd.DataFrame(out)
    return_df.to_csv(f"data/{df['symbol'].iloc[0]}_body_ranges.csv", index=False, mode='w')

    return return_df