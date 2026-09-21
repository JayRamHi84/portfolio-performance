# ═══════════════════════════════════════════════════════════════════════════════
#  main.py  —  Portfolio_Performance
# ═══════════════════════════════════════════════════════════════════════════════
#  Pulls maximum-available daily history for every T. Rowe Price equity fund via
#  the Schwab API, computes a full performance / risk metric set for each, ranks
#  them (best return + lowest risk on top), and writes a spreadsheet-ready CSV
#  plus a console table.
# ═══════════════════════════════════════════════════════════════════════════════
import sys

import pandas as pd

import analytics
import config
import schwab_data
import top3_relationship
from funds import FUNDS

# Metrics used to build the composite ranking.  Higher-better metrics rank so a
# larger value is better; drawdown / VaR / CVaR are negative returns where a
# less-negative (larger) value is better, so they also count as higher-better.
_HIGHER_BETTER = [
    "sharpe", "martin", "treynor", "sortino", "omega", "calmar", "alpha",
    "ann_return", "max_drawdown", "cvar_95", "var_95",
]
_LOWER_BETTER = ["ulcer_index", "vol_close"]

# Column order for the exported CSV (spreadsheet-friendly).
_CSV_COLUMNS = [
    "Rank", "Score", "Symbol", "Fund", "Category", "N Days", "Start", "End",
    "Ann Return %",
    # PERFORMANCE
    "Sharpe", "Martin", "Treynor", "Sortino", "Omega", "Calmar", "Summers",
    "Alpha %",
    # RISK
    "Max Drawdown %", "CVaR 95% %", "Ulcer Index", "VaR 95% %",
    "Vol Close-to-Close %", "Vol Parkinson %", "Vol Garman-Klass %",
    "Vol Rogers-Satchell %", "Vol Yang-Zhang %", "Beta",
]


def _fmt_pct(x):
    return round(x * 100.0, 2) if pd.notna(x) else None


def _fmt_num(x, nd=3):
    return round(x, nd) if pd.notna(x) else None


def window_cutoff(reference_end) -> "pd.Timestamp | None":
    """Trailing-window start date (reference_end - LOOKBACK_YEARS), or None."""
    if config.LOOKBACK_YEARS is None:
        return None
    return (pd.Timestamp(reference_end)
            - pd.DateOffset(years=config.LOOKBACK_YEARS)).date()


def slice_window(close: pd.Series, cutoff) -> pd.Series:
    """Restrict a close/NAV series to dates on/after the cutoff."""
    if cutoff is None:
        return close
    return close[close.index >= cutoff]


def build_row(symbol, name, category, m):
    return {
        "Symbol": symbol,
        "Fund": name,
        "Category": category,
        "N Days": m["n_days"],
        "Start": m["start"],
        "End": m["end"],
        "Ann Return %": _fmt_pct(m["ann_return"]),
        "Sharpe": _fmt_num(m["sharpe"]),
        "Martin": _fmt_num(m["martin"]),
        "Treynor": _fmt_num(m["treynor"]),
        "Sortino": _fmt_num(m["sortino"]),
        "Omega": _fmt_num(m["omega"]),
        "Calmar": _fmt_num(m["calmar"]),
        "Summers": "N/A",
        "Alpha %": _fmt_pct(m["alpha"]),
        "Max Drawdown %": _fmt_pct(m["max_drawdown"]),
        "CVaR 95% %": _fmt_pct(m["cvar_95"]),
        "Ulcer Index": _fmt_num(m["ulcer_index"], 2),
        "VaR 95% %": _fmt_pct(m["var_95"]),
        "Vol Close-to-Close %": _fmt_pct(m["vol_close"]),
        "Vol Parkinson %": "N/A",
        "Vol Garman-Klass %": "N/A",
        "Vol Rogers-Satchell %": "N/A",
        "Vol Yang-Zhang %": "N/A",
        "Beta": _fmt_num(m["beta"]),
        # raw values retained for ranking
        **{f"_{k}": m[k] for k in _HIGHER_BETTER + _LOWER_BETTER},
    }


def rank_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a composite Score (0-100) and Rank; sort best → worst."""
    score = pd.Series(0.0, index=df.index)
    count = 0
    for col in _HIGHER_BETTER:
        s = df[f"_{col}"]
        if s.notna().sum() >= 2:
            score = score.add(s.rank(pct=True), fill_value=0.0)
            count += 1
    for col in _LOWER_BETTER:
        s = df[f"_{col}"]
        if s.notna().sum() >= 2:
            score = score.add((1.0 - s.rank(pct=True)), fill_value=0.0)
            count += 1

    df = df.copy()
    df["Score"] = (score / max(count, 1) * 100.0).round(2)
    df = df.sort_values("Score", ascending=False, kind="mergesort").reset_index(drop=True)
    df["Rank"] = df.index + 1
    return df


def main() -> int:
    print("Connecting to Schwab API…")
    try:
        client = schwab_data.get_client()
    except Exception as exc:
        print(f"  ✗ Could not create Schwab client: {exc}")
        return 1

    # ── Benchmark ────────────────────────────────────────────────────────────
    print(f"Fetching benchmark {config.BENCHMARK_SYMBOL} …")
    bench_df = schwab_data.fetch_daily_history(client, config.BENCHMARK_SYMBOL)
    if bench_df is None or bench_df.empty:
        print("  ✗ Failed to fetch benchmark history; Alpha/Beta/Treynor unavailable.")
        bench_returns = pd.Series(dtype=float)
        cutoff = window_cutoff(pd.Timestamp.today().date())
    else:
        cutoff = window_cutoff(bench_df.index.max())
        bench_close = slice_window(bench_df["close"], cutoff)
        bench_returns = analytics.daily_returns(bench_close)
        print(f"  ✓ {len(bench_returns)} benchmark days "
              f"({bench_returns.index.min()} → {bench_returns.index.max()})")

    if cutoff is not None:
        print(f"Common window: trailing {config.LOOKBACK_YEARS}y "
              f"(from {cutoff})")

    # ── Funds ────────────────────────────────────────────────────────────────
    rows, failed, partial = [], [], []
    total = len(FUNDS)
    for i, (symbol, name, category) in enumerate(FUNDS, 1):
        print(f"[{i:>2}/{total}] {symbol:<6} {name[:42]:<42}", end="", flush=True)
        df = schwab_data.fetch_daily_history(client, symbol)
        if df is None or df.empty:
            print("  ✗ no data")
            failed.append((symbol, name))
            continue
        # Flag funds whose history starts after the window (insufficient coverage).
        if cutoff is not None and df.index.min() > cutoff:
            partial.append((symbol, name, df.index.min()))
        close = slice_window(df["close"], cutoff)
        if len(close) < 30:
            print("  ✗ insufficient data in window")
            failed.append((symbol, name))
            continue
        metrics = analytics.compute_all(close, bench_returns)
        rows.append(build_row(symbol, name, category, metrics))
        flag = "  ⚠ partial" if (cutoff is not None and df.index.min() > cutoff) else ""
        print(f"  ✓ {metrics['n_days']} days{flag}")

    if not rows:
        print("\nNo fund data retrieved — aborting.")
        return 1

    df = pd.DataFrame(rows)
    df = rank_frame(df)

    # ── CSV export ─────────────────────────────────────────────────────────────
    out = df[_CSV_COLUMNS]
    out.to_csv(config.OUTPUT_CSV, index=False)
    print(f"\n✓ Wrote {len(out)} funds → {config.OUTPUT_CSV}")

    # ── Console table (key columns) ─────────────────────────────────────────────
    view = df[[
        "Rank", "Symbol", "Score", "Ann Return %", "Sharpe", "Sortino",
        "Calmar", "Max Drawdown %", "Ulcer Index", "Vol Close-to-Close %", "Beta",
    ]]
    with pd.option_context("display.max_rows", None, "display.width", 200,
                           "display.colheader_justify", "right"):
        print("\n" + view.to_string(index=False))

    if failed:
        print(f"\n⚠ {len(failed)} fund(s) had no Schwab data:")
        for sym, nm in failed:
            print(f"    {sym:<6} {nm}")

    if partial:
        print(f"\n⚠ {len(partial)} fund(s) do NOT cover the full "
              f"{config.LOOKBACK_YEARS}y window (history starts later):")
        for sym, nm, start in partial:
            print(f"    {sym:<6} starts {start}  {nm}")

    # ── Graphical relationship figure for the top-3 funds ───────────────────────
    try:
        png = top3_relationship.build_figure()
        print(f"\n✓ Wrote relationship figure → {png}")
    except Exception as exc:
        print(f"\n⚠ Could not build relationship figure: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
