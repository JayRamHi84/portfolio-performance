# ═══════════════════════════════════════════════════════════════════════════════
#  analytics.py  —  portfolio performance & risk metrics
# ═══════════════════════════════════════════════════════════════════════════════
#  All metrics are computed from daily total-price (NAV) series.  Metrics that
#  require intraday Open/High/Low (Parkinson, Garman-Klass, Rogers-Satchell,
#  Yang-Zhang) are NOT computable from mutual-fund NAV closes and are reported
#  as None (N/A), per the analysis scope.
# ═══════════════════════════════════════════════════════════════════════════════
import numpy as np
import pandas as pd

import config

_TD = config.TRADING_DAYS
_RF_ANNUAL = config.RISK_FREE_RATE
_RF_DAILY = _RF_ANNUAL / _TD


def daily_returns(close: pd.Series) -> pd.Series:
    """Simple daily returns from a close/NAV series."""
    return close.pct_change().dropna()


def annualized_return(returns: pd.Series) -> float:
    """Geometric (CAGR-equivalent) annualized return from daily returns."""
    n = len(returns)
    if n == 0:
        return np.nan
    growth = float((1.0 + returns).prod())
    if growth <= 0:
        return np.nan
    return growth ** (_TD / n) - 1.0


def annualized_vol(returns: pd.Series) -> float:
    """Close-to-close annualized volatility (std of daily returns)."""
    if len(returns) < 2:
        return np.nan
    return float(returns.std(ddof=1) * np.sqrt(_TD))


def _drawdown_series(returns: pd.Series) -> pd.Series:
    cum = (1.0 + returns).cumprod()
    peak = cum.cummax()
    return cum / peak - 1.0


def max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return np.nan
    return float(_drawdown_series(returns).min())


def ulcer_index(returns: pd.Series) -> float:
    """RMS of percentage drawdowns (in percent points)."""
    if returns.empty:
        return np.nan
    dd_pct = _drawdown_series(returns) * 100.0
    return float(np.sqrt(np.mean(np.square(dd_pct))))


def sharpe_ratio(returns: pd.Series) -> float:
    if len(returns) < 2:
        return np.nan
    excess = returns - _RF_DAILY
    sd = excess.std(ddof=1)
    if sd == 0:
        return np.nan
    return float(excess.mean() / sd * np.sqrt(_TD))


def sortino_ratio(returns: pd.Series) -> float:
    if len(returns) < 2:
        return np.nan
    excess = returns - _RF_DAILY
    downside = np.minimum(excess, 0.0)
    dd = np.sqrt(np.mean(np.square(downside)))
    if dd == 0:
        return np.nan
    return float(excess.mean() / dd * np.sqrt(_TD))


def calmar_ratio(returns: pd.Series) -> float:
    ann = annualized_return(returns)
    mdd = max_drawdown(returns)
    if mdd is None or np.isnan(mdd) or mdd == 0:
        return np.nan
    return float(ann / abs(mdd))


def martin_ratio(returns: pd.Series) -> float:
    """Ulcer Performance Index: excess annual return / Ulcer Index (fraction)."""
    ann = annualized_return(returns)
    ui = ulcer_index(returns) / 100.0  # back to fraction
    if ui is None or np.isnan(ui) or ui == 0:
        return np.nan
    return float((ann - _RF_ANNUAL) / ui)


def omega_ratio(returns: pd.Series, threshold_daily: float = _RF_DAILY) -> float:
    """Omega ratio at a daily return threshold."""
    if returns.empty:
        return np.nan
    diff = returns - threshold_daily
    gains = diff[diff > 0].sum()
    losses = -diff[diff < 0].sum()
    if losses == 0:
        return np.nan
    return float(gains / losses)


def beta(returns: pd.Series, bench: pd.Series) -> float:
    """Beta vs benchmark on the overlapping date range."""
    aligned = pd.concat([returns, bench], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return np.nan
    var_b = aligned.iloc[:, 1].var(ddof=1)
    if var_b == 0:
        return np.nan
    cov = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
    return float(cov / var_b)


def treynor_ratio(returns: pd.Series, b: float) -> float:
    if b is None or np.isnan(b) or b == 0:
        return np.nan
    ann = annualized_return(returns)
    return float((ann - _RF_ANNUAL) / b)


def jensens_alpha(returns: pd.Series, bench: pd.Series, b: float) -> float:
    """Annualized Jensen's alpha vs benchmark (CAPM)."""
    if b is None or np.isnan(b):
        return np.nan
    aligned = pd.concat([returns, bench], axis=1, join="inner").dropna()
    if aligned.empty:
        return np.nan
    r_fund = annualized_return(aligned.iloc[:, 0])
    r_bench = annualized_return(aligned.iloc[:, 1])
    return float(r_fund - (_RF_ANNUAL + b * (r_bench - _RF_ANNUAL)))


def value_at_risk(returns: pd.Series, conf: float = config.VAR_CONFIDENCE) -> float:
    """Historical daily VaR (as a negative return at the (1-conf) quantile)."""
    if returns.empty:
        return np.nan
    return float(np.percentile(returns, (1.0 - conf) * 100.0))


def expected_shortfall(returns: pd.Series,
                       conf: float = config.VAR_CONFIDENCE) -> float:
    """Historical daily CVaR: mean of returns at/below the VaR threshold."""
    if returns.empty:
        return np.nan
    var = value_at_risk(returns, conf)
    tail = returns[returns <= var]
    if tail.empty:
        return float(var)
    return float(tail.mean())


def compute_all(close: pd.Series, bench_returns: pd.Series) -> dict:
    """Compute the full metric set for one fund's close/NAV series."""
    r = daily_returns(close)
    b = beta(r, bench_returns)

    return {
        "n_days":        int(len(r)),
        "start":         r.index.min().isoformat() if not r.empty else "",
        "end":           r.index.max().isoformat() if not r.empty else "",
        "ann_return":    annualized_return(r),
        # PERFORMANCE
        "sharpe":        sharpe_ratio(r),
        "martin":        martin_ratio(r),
        "treynor":       treynor_ratio(r, b),
        "sortino":       sortino_ratio(r),
        "omega":         omega_ratio(r),
        "calmar":        calmar_ratio(r),
        "summers":       None,               # non-standard metric — skipped (N/A)
        "alpha":         jensens_alpha(r, bench_returns, b),
        # RISK
        "max_drawdown":  max_drawdown(r),
        "cvar_95":       expected_shortfall(r),
        "ulcer_index":   ulcer_index(r),
        "var_95":        value_at_risk(r),
        "vol_close":     annualized_vol(r),
        "vol_parkinson": None,               # needs intraday High/Low — N/A for NAV
        "vol_garman_klass": None,            # needs OHLC — N/A for NAV
        "vol_rogers_satchell": None,         # needs OHLC — N/A for NAV
        "vol_yang_zhang": None,              # needs OHLC — N/A for NAV
        "beta":          b,
    }
