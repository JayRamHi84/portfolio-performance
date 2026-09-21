# ═══════════════════════════════════════════════════════════════════════════════
#  similarity.py  —  peer-similarity explorer for chosen target funds
# ═══════════════════════════════════════════════════════════════════════════════
#  Finds the funds that behave most like a set of target funds over the current
#  window. Similarity = Euclidean distance in z-scored space across the
#  dimensions that matter most: return, volatility, drawdown, beta, Sharpe.
#  Prints the closest peers to the console and renders a horizontal-bar figure
#  (one panel per target) saved next to the CSV as similarity.png.
# ═══════════════════════════════════════════════════════════════════════════════
import os

import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless / file-only backend
import matplotlib.pyplot as plt

import config

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(_THIS_DIR, "similarity.png")

# Behavioural dimensions used to measure similarity.
DIMS = ["Ann Return %", "Vol Close-to-Close %", "Max Drawdown %", "Beta", "Sharpe"]

# Target funds whose closest peers we want to find.
TARGETS = ["PRGTX", "PRSCX"]

# Number of closest peers to display per target.
TOP_N = 6

# Panel colour per target (matches the project palette).
PANEL_COLORS = ["#1f77b4", "#2ca02c"]


def _zscored(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    for c in DIMS:
        z[c] = (df[c] - df[c].mean()) / df[c].std(ddof=0)
    return z


def _closest(df: pd.DataFrame, z: pd.DataFrame, target: str) -> pd.DataFrame:
    """Return every non-target fund ranked by distance to `target` (ascending)."""
    tv = z.loc[z["Symbol"] == target, DIMS].iloc[0]
    dist = ((z[DIMS] - tv) ** 2).sum(axis=1) ** 0.5
    out = df.assign(Distance=dist.round(3))
    out = out[out["Symbol"] != target].sort_values("Distance")
    return out


def print_report() -> None:
    """Console summary: closest peers per target + the targets side by side."""
    df = pd.read_csv(config.OUTPUT_CSV)
    z = _zscored(df)

    for t in TARGETS:
        out = _closest(df, z, t)
        print(f"\n=== Closest to {t} "
              f"({df.loc[df.Symbol == t, 'Fund'].iloc[0]}) ===")
        cols = ["Distance", "Symbol", "Fund", "Ann Return %", "Sharpe",
                "Max Drawdown %", "Vol Close-to-Close %", "Beta"]
        print(out[cols].head(TOP_N).to_string(index=False))

    print("\n=== The target funds ===")
    cols = ["Symbol", "Fund", "Ann Return %", "Sharpe", "Sortino", "Calmar",
            "Max Drawdown %", "Ulcer Index", "Vol Close-to-Close %", "Beta"]
    print(df[df.Symbol.isin(TARGETS)][cols].to_string(index=False))


def build_figure() -> str:
    """Render one horizontal-bar panel per target and save to similarity.png."""
    df = pd.read_csv(config.OUTPUT_CSV)
    z = _zscored(df)

    fig, axes = plt.subplots(1, len(TARGETS), figsize=(15, 6.5))
    if len(TARGETS) == 1:
        axes = [axes]
    fig.suptitle("Fund Similarity — Closest Behavioural Peers",
                 fontsize=17, fontweight="bold", y=0.98)

    for ax, target, color in zip(axes, TARGETS, PANEL_COLORS):
        out = _closest(df, z, target).head(TOP_N).iloc[::-1]  # nearest on top
        labels = [f"{s}\n{n[:24]}" for s, n in zip(out["Symbol"], out["Fund"])]
        dist = out["Distance"].to_numpy()

        bars = ax.barh(range(len(out)), dist, color=color, alpha=0.85)
        ax.set_yticks(range(len(out)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Distance  (smaller = more similar)", fontsize=9)
        tgt_name = df.loc[df.Symbol == target, "Fund"].iloc[0]
        ax.set_title(f"Closest to {target} — {tgt_name}",
                     fontsize=11, color=color, fontweight="bold", pad=10)
        ax.grid(axis="x", linestyle=":", alpha=0.4)
        ax.invert_xaxis()          # shortest (most similar) bar reaches furthest right
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")

        for rect, d in zip(bars, dist):
            ax.text(rect.get_width(), rect.get_y() + rect.get_height() / 2,
                    f" {d:.2f} ", va="center",
                    ha="right", fontsize=8, color="#333")

    fig.text(0.5, 0.02,
             "Similarity measured as Euclidean distance in z-scored space across "
             "Return, Volatility, Max Drawdown, Beta and Sharpe.",
             ha="center", fontsize=8, color="#555")

    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    fig.savefig(OUTPUT_PNG, dpi=150)
    plt.close(fig)
    return OUTPUT_PNG


if __name__ == "__main__":
    print_report()
    path = build_figure()
    print(f"\n✓ Wrote similarity figure → {path}")
