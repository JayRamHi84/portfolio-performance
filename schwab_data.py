# ═══════════════════════════════════════════════════════════════════════════════
#  schwab_data.py  —  Schwab client + daily price-history fetch
# ═══════════════════════════════════════════════════════════════════════════════
import threading
import time
from collections import deque
from datetime import datetime

import httpx
import pandas as pd
from schwab import auth

import config


# ── Global API rate limiter (sliding-window token bucket) ──────────────────────
class _RateLimiter:
    def __init__(self, max_calls: int, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                cutoff = now - self.period
                while self._calls and self._calls[0] <= cutoff:
                    self._calls.popleft()
                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return
                sleep_for = self._calls[0] + self.period - now + 0.01
            time.sleep(max(0.01, min(sleep_for, self.period)))


_LIMITER = _RateLimiter(config.MAX_REQUESTS_PER_MIN)


def get_client():
    client = auth.easy_client(
        api_key=config.CLIENT_ID,
        app_secret=config.CLIENT_SECRET,
        callback_url=config.REDIRECT_URI,
        token_path=config.TOKEN_PATH,
    )
    client.session.timeout = httpx.Timeout(60.0)
    return client


def fetch_daily_history(client, symbol: str, retries: int = 3) -> pd.DataFrame | None:
    """Fetch the maximum available daily OHLC history for a symbol.

    Returns a DataFrame indexed by date with columns
    [open, high, low, close, volume], or None on failure / no data.
    Retries transient network / empty-body errors a few times.
    """
    payload = None
    for attempt in range(retries):
        try:
            _LIMITER.acquire()
            resp = client.get_price_history_every_day(
                symbol,
                need_extended_hours_data=False,
                need_previous_close=False,
            )
        except Exception:
            time.sleep(1.0 + attempt)
            continue

        if resp.status_code != 200:
            # 429 = rate limited; back off and retry. Others: retry once too.
            time.sleep(1.5 + attempt)
            continue

        try:
            payload = resp.json()
            break
        except Exception:
            # Empty / non-JSON body (transient). Back off and retry.
            time.sleep(1.0 + attempt)
            continue

    if payload is None:
        return None

    if payload.get("empty", False):
        return None

    candles = payload.get("candles", [])
    if not candles:
        return None

    rows = []
    for c in candles:
        ts = c.get("datetime")
        if ts is None:
            continue
        dt = datetime.fromtimestamp(ts / 1000.0).date()
        rows.append({
            "date":   dt,
            "open":   c.get("open"),
            "high":   c.get("high"),
            "low":    c.get("low"),
            "close":  c.get("close"),
            "volume": c.get("volume"),
        })

    if not rows:
        return None

    df = pd.DataFrame(rows).drop_duplicates(subset="date")
    df = df.set_index("date").sort_index()
    df = df[df["close"] > 0]
    return df if not df.empty else None
