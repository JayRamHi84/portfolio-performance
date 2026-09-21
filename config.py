# ═══════════════════════════════════════════════════════════════════════════════
#  config.py  —  Portfolio_Performance central configuration
# ═══════════════════════════════════════════════════════════════════════════════
#  Self-contained configuration. Secrets (Schwab API key/secret and the OAuth
#  token file) read from local .env file and a local schwab_token.json
# ═══════════════════════════════════════════════════════════════════════════════
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Minimal .env loader (reads a local .env if present) ────────────────────────
def _load_env() -> None:
    candidate = os.path.join(_THIS_DIR, ".env")
    if os.path.exists(candidate):
        with open(candidate, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(),
                                      val.strip().strip('"').strip("'"))


_load_env()

# ── API credentials (pulled from environment / .env) ───────────────────────────
CLIENT_ID      = os.environ.get("SCHWAB_CLIENT_ID", "xxx")
CLIENT_SECRET  = os.environ.get("SCHWAB_CLIENT_SECRET", "xxx")
REDIRECT_URI   = os.environ.get("SCHWAB_REDIRECT_URI", "https://127.0.0.1:8182")

# OAuth token cache. Honor an explicit env override, otherwise use the local
# token file created on first authentication.
TOKEN_PATH = (os.environ.get("SCHWAB_TOKEN_PATH")
              or os.path.join(_THIS_DIR, "schwab_token.json"))

# ── Analysis parameters ─────────────────────────────────────────────────────────
# Annual risk-free rate used across Sharpe / Sortino / Treynor / etc.
RISK_FREE_RATE = float(os.environ.get("RISK_FREE_RATE", "0.05"))

# Trading days per year for annualization.
TRADING_DAYS = 252

# Common trailing window (years) applied to EVERY fund + benchmark so all funds
# are compared over the identical period. Set to None to use each fund's full
# available history instead.
LOOKBACK_YEARS = 5

# Benchmark used for Alpha / Beta / Treynor (S&P 500 cash index per user choice).
BENCHMARK_SYMBOL = "$SPX"

# Confidence level for Value-at-Risk / CVaR (95% → 5% tail).
VAR_CONFIDENCE = 0.95

# Schwab API throttle (Schwab enforces ~120 req/min; stay under with margin).
MAX_REQUESTS_PER_MIN = int(os.environ.get("MAX_REQUESTS_PER_MIN", "110"))

# Output locations.
OUTPUT_CSV = os.path.join(_THIS_DIR, "portfolio_performance.csv")
