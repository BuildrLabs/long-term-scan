#!/usr/bin/env python3
"""Quarterly SMA regime + setup detector.

Resamples price bars to calendar-quarter candles, computes the quarterly SMA
(default 50), identifies the REGIME first, then looks for the matching setup.

Input (--input FILE or stdin), either:
  * JSON: {"AAPL": [{"date": "2012-01-03", "open":..,"high":..,"low":..,"close":..}, ...], "MSFT": [...]}
          or a bare list of bars (use --ticker to label it)
  * CSV with header: date,open,high,low,close   (use --ticker to label it)
Bars may be daily, weekly, monthly or quarterly. Close is required; open/high/low
are optional but pullback and bottom detection need highs and lows.

Regime (from the SMA slope over the last 4 completed quarters and where price closed):
  bullish     SMA rising AND price closed above it in at least one of the last 2 completed quarters
  bearish     SMA falling AND price closed below it in at least one of the last 2 completed quarters
  transition  anything else (breaking_down / recovering / flat)

RSI (Wilder, on completed quarterly closes, default 14) is reported as context:
  oversold <= 30, overbought >= 70. It never changes the regime or setup by itself.

Setups:
  bullish:  pullback_cross_below price just closed BELOW the rising SMA after being above it
                                 (early "buy the dip" entry; a 2nd close below flips the regime)
            pullback_reclaim     low pierced (or came within tolerance of) the SMA in the last 2
                                 completed quarters after a run above it, and the last close is back above
            pullback_in_progress current unfinished quarter is doing the same (watch only)
            pullback_approaching close is within 5% above the SMA and falling (watch only)
            extended_wait        close is 25%+ above the SMA; wait for a pullback
            trend_intact         above the SMA, no pullback yet
  bearish:  bottom_confirmed     higher low vs prior 6 quarters + close above prior quarter's high
                                 + close above the 4-quarter (1-year) SMA
            bottom_watch         higher low only (no new low), not yet confirmed
            bearish_wait         still making lows; do nothing
  transition: none
"""
import argparse
import csv
import io
import json
import sys
from datetime import date, timedelta

SLOPE_LOOKBACK = 4        # quarters over which SMA slope is measured
EXTENDED_PCT = 25.0       # % above SMA considered extended
RUN_PCT = 10.0            # must have been this far above SMA recently for a dip to count as a pullback
RUN_WINDOW = 10           # quarters to look back for that run
APPROACH_PCT = 5.0        # "approaching" band above the SMA
BOTTOM_LOOKBACK = 6       # quarters compared for the higher-low test
FAST_PERIOD = 4           # quarterly SMA (1-year average) used to confirm a bottom
MIN_SHORT_QUARTERS = 12   # below this we refuse to compute anything


def parse_date(s):
    return date.fromisoformat(str(s)[:10])


def quarter_key(d):
    return (d.year, (d.month - 1) // 3 + 1)


def quarter_end(key):
    y, q = key
    if q == 4:
        return date(y, 12, 31)
    return date(y, q * 3 + 1, 1) - timedelta(days=1)


def to_quarters(bars):
    bars = sorted(bars, key=lambda b: b["date"])
    quarters = {}
    for b in bars:
        k = quarter_key(b["date"])
        c = b["close"]
        o = b.get("open", c)
        h = b.get("high", c)
        l = b.get("low", c)
        if k not in quarters:
            quarters[k] = {"key": k, "open": o, "high": h, "low": l, "close": c}
        else:
            q = quarters[k]
            q["high"] = max(q["high"], h)
            q["low"] = min(q["low"], l)
            q["close"] = c
    return [quarters[k] for k in sorted(quarters)]


def sma_series(closes, period):
    out = [None] * len(closes)
    if period <= 0 or len(closes) < period:
        return out
    window = sum(closes[:period])
    out[period - 1] = window / period
    for i in range(period, len(closes)):
        window += closes[i] - closes[i - period]
        out[i] = window / period
    return out


def rsi_last(closes, period=14):
    """Wilder RSI of the last close. None if there is not enough data."""
    if len(closes) < period + 1:
        return None
    gains = losses = 0.0
    for k in range(1, period + 1):
        d = closes[k] - closes[k - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    avg_g, avg_l = gains / period, losses / period
    for k in range(period + 1, len(closes)):
        d = closes[k] - closes[k - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0.0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0.0)) / period
    if avg_l == 0:
        return 100.0
    return 100.0 - 100.0 / (1 + avg_g / avg_l)


def pct(a, b):
    return (a / b - 1) * 100 if b else None


def r(x, n=2):
    return None if x is None else round(x, n)


def analyze(ticker, bars, period=50, tolerance=3.0, strict=False, rsi_period=14):
    quarters = to_quarters(bars)
    if not quarters:
        return {"ticker": ticker, "regime": "unknown", "setup": "none", "reason": "no bars"}

    has_hl = any("high" in b and "low" in b for b in bars)
    last_date = max(b["date"] for b in bars)
    in_progress = last_date < quarter_end(quarter_key(last_date)) - timedelta(days=4)
    completed = quarters[:-1] if in_progress else quarters
    current = quarters[-1] if in_progress else None
    n = len(completed)

    needed_reliable = period + SLOPE_LOOKBACK
    reliable = n >= needed_reliable
    if strict and not reliable:
        return {"ticker": ticker, "regime": "unknown", "setup": "none", "reliable": False,
                "quarters_completed": n, "reason": "history shorter than %d quarters (strict)" % needed_reliable}

    # With short history, shrink the period so the SMA and its slope exist, and flag it.
    period_used = period if reliable else n - SLOPE_LOOKBACK
    if period_used < MIN_SHORT_QUARTERS - SLOPE_LOOKBACK:
        return {"ticker": ticker, "regime": "unknown", "setup": "none", "reliable": False,
                "quarters_completed": n, "reason": "not enough history"}

    closes = [q["close"] for q in completed]
    highs = [q["high"] for q in completed]
    lows = [q["low"] for q in completed]
    sma = sma_series(closes, period_used)
    fast = sma_series(closes, FAST_PERIOD)
    i = n - 1

    s_now, s_then = sma[i], sma[i - SLOPE_LOOKBACK]
    slope = pct(s_now, s_then) if (s_now and s_then) else None
    above_last = closes[i] > s_now
    above_prev = sma[i - 1] is not None and closes[i - 1] > sma[i - 1]

    if slope is None:
        regime = "unknown"
    elif slope > 0 and (above_last or above_prev):
        regime = "bullish"
    elif slope < 0 and (not above_last or not above_prev):
        regime = "bearish"
    elif slope > 0:
        regime = "transition_breaking_down"
    elif slope < 0:
        regime = "transition_recovering"
    else:
        regime = "transition_flat"

    setup, detail = "none", {}
    pct_vs = pct(closes[i], s_now)

    if regime == "bullish":
        touched = [j for j in (i, i - 1) if j >= 0 and sma[j] and lows[j] <= sma[j] * (1 + tolerance / 100)]
        ran = any(sma[j] and closes[j] >= sma[j] * (1 + RUN_PCT / 100)
                  for j in range(max(0, i - RUN_WINDOW), i + 1))
        # a quarter that touched the SMA may itself be the one that closed back above it,
        # so also look for a prior run above the SMA before the touch
        ran_before = any(sma[j] and closes[j] >= sma[j] * (1 + RUN_PCT / 100)
                         for j in range(max(0, i - RUN_WINDOW - 2), i + 1))
        if has_hl and touched and above_last and (ran or ran_before):
            setup = "pullback_reclaim"
            detail = {"quarters_since_touch": i - max(touched),
                      "pullback_low": r(min(lows[j] for j in touched)),
                      "pullback_low_vs_sma_pct": r(pct(min(lows[j] for j in touched), s_now))}
        elif (not above_last) and above_prev and (ran or ran_before):
            setup = "pullback_cross_below"
            detail = {"pct_vs_sma_at_close": r(pct_vs, 1)}
        elif (has_hl and current is not None and current["low"] <= s_now * (1 + tolerance / 100)
              and current["close"] > s_now and ran):
            setup = "pullback_in_progress"
            detail = {"current_low": r(current["low"]), "current_close_so_far": r(current["close"])}
        elif above_last and pct_vs <= APPROACH_PCT and closes[i] < closes[i - 1]:
            setup = "pullback_approaching"
        elif pct_vs >= EXTENDED_PCT:
            setup = "extended_wait"
        else:
            setup = "trend_intact"

    elif regime == "bearish":
        if not has_hl:
            setup = "bearish_wait"
            detail = {"note": "no high/low data; bottom detection skipped"}
        else:
            prior_lows = lows[max(0, i - BOTTOM_LOOKBACK):i]
            higher_low = bool(prior_lows) and lows[i] > min(prior_lows)
            reversal = i >= 1 and closes[i] > highs[i - 1]
            above_fast = fast[i] is not None and closes[i] > fast[i]
            if higher_low and reversal and above_fast:
                setup = "bottom_confirmed"
            elif higher_low:
                setup = "bottom_watch"
            else:
                setup = "bearish_wait"
            detail = {"higher_low": higher_low, "closed_above_prior_high": reversal,
                      "above_4q_sma": above_fast,
                      "lowest_low_last_%dq" % BOTTOM_LOOKBACK: r(min(prior_lows)) if prior_lows else None}

    result = {
        "ticker": ticker,
        "regime": regime,
        "setup": setup,
        "reliable": reliable,
        "sma_period_used": period_used,
        "quarters_completed": n,
        "last_completed_quarter": "%d-Q%d" % completed[-1]["key"],
        "last_close": r(closes[i]),
        "sma": r(s_now),
        "pct_vs_sma": r(pct_vs, 1),
        "sma_slope_pct_%dq" % SLOPE_LOOKBACK: r(slope, 1),
        "data_through": last_date.isoformat(),
    }
    result.update(detail)
    rsi = rsi_last(closes, rsi_period)
    if rsi is not None:
        result["rsi_%dq" % rsi_period] = r(rsi, 1)
        result["rsi_state"] = "oversold" if rsi <= 30 else "overbought" if rsi >= 70 else "neutral"
    if current is not None:
        result["in_progress_quarter"] = {
            "quarter": "%d-Q%d" % current["key"],
            "close_so_far": r(current["close"]),
            "above_last_sma": current["close"] > s_now,
        }
    if not has_hl:
        result["warning"] = "No high/low data: pullback and bottom detection are limited."
    if not reliable:
        result["note"] = ("Only %d completed quarters; used a %d-quarter SMA instead of %d. "
                          "Treat as low confidence." % (n, period_used, period))
    return result


def norm(bars):
    out = []
    for b in bars:
        b = {str(k).lower(): v for k, v in b.items()}
        try:
            close = float(b.get("close") or b.get("adj close") or b.get("adj_close"))
        except (TypeError, ValueError):
            continue
        d = b.get("date") or b.get("begins_at") or b.get("timestamp")
        item = {"date": parse_date(d), "close": close}
        for k in ("open", "high", "low"):
            if b.get(k) not in (None, ""):
                item[k] = float(b[k])
        out.append(item)
    return out


def load(text, ticker):
    text = text.strip()
    if text.startswith("{") or text.startswith("["):
        raw = json.loads(text)
        if isinstance(raw, list):
            raw = {ticker or "TICKER": raw}
        return {sym: norm(bars) for sym, bars in raw.items()}
    rows = list(csv.DictReader(io.StringIO(text)))
    return {ticker or "TICKER": norm(rows)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", help="JSON or CSV file (default: stdin)")
    p.add_argument("--ticker", help="Label for a bare list or CSV")
    p.add_argument("--period", type=int, default=50, help="SMA length in quarters (default 50)")
    p.add_argument("--tolerance", type=float, default=3.0,
                   help="%% above the SMA that still counts as a touch (default 3)")
    p.add_argument("--rsi-period", type=int, default=14, help="RSI length in quarters (default 14)")
    p.add_argument("--strict", action="store_true",
                   help="Skip tickers without period+4 completed quarters instead of flagging them")
    args = p.parse_args()

    text = open(args.input).read() if args.input else sys.stdin.read()
    data = load(text, args.ticker)
    results = [analyze(s, b, args.period, args.tolerance, args.strict, args.rsi_period) for s, b in data.items()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
