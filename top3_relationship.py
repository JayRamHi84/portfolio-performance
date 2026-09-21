# ═══════════════════════════════════════════════════════════════════════════════
#  top3_relationship.py  —  graphical relationship table for the top-3 funds
# ═══════════════════════════════════════════════════════════════════════════════
#  Reads the ranked portfolio_performance.csv, selects the three best-ranked
#  funds, and renders a single figure with two panels:
#    • left  — a normalized radar (spider) chart comparing the three funds across
#              the core performance/risk dimensions (each axis is a 0-100 rank
#              relative to the full fund universe, higher = better);
#    • right — a colour-graded relationship table of the underlying raw metric
#              values for the same three funds.
# ═══════════════════════════════════════════════════════════════════════════════
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless / file-only backend
import matplotlib.pyplot as plt

import config

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(_THIS_DIR, "top3_relationship.png")

# Dimensions shown on the radar. Value = column name; higher_better flags whether
# a larger raw value is better (risk columns are inverted so "further out" always
# means "better" on the chart).
RADAR_DIMS = [
    ("Ann Return %",         True),
    ("Sharpe",               True),
    ("Sortino",              True),
    ("Calmar",               True),
    ("Alpha %",              True),
    ("Max Drawdown %",       True),   # negative → less-negative is better
    ("Ulcer Index",          False),  # smaller is better
    ("Vol Close-to-Close %", False),  # smaller is better
]

# Raw metrics listed in the relationship table (label, column).
TABLE_ROWS = [
    ("Score",            "Score"),
    ("Ann Return %",     "Ann Return %"),
    ("Sharpe",           "Sharpe"),
    ("Sortino",          "Sortino"),
    ("Calmar",           "Calmar"),
    ("Martin",           "Martin"),
    ("Omega",            "Omega"),
    ("Alpha %",          "Alpha %"),
    ("Max Drawdown %",   "Max Drawdown %"),
    ("CVaR 95% %",       "CVaR 95% %"),
    ("Ulcer Index",      "Ulcer Index"),
    ("VaR 95% %",        "VaR 95% %"),
    ("Vol C2C %",        "Vol Close-to-Close %"),
    ("Beta",             "Beta"),
]

# Distinct colour per fund (colour-blind friendly).
FUND_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c"]


def _percentile_rank(series: pd.Series, higher_better: bool) -> pd.Series:
    """0-100 percentile rank across the universe; inverted when lower is better."""
    r = series.rank(pct=True)
    if not higher_better:
        r = 1.0 - r
    return r * 100.0


def build_figure() -> str:
    df = pd.read_csv(config.OUTPUT_CSV)
    df = df.sort_values("Rank").reset_index(drop=True)
    top3 = df.head(3).copy()

    # Percentile ranks (relative to ALL funds) for every radar dimension.
    ranks = {}
    for col, higher in RADAR_DIMS:
        ranks[col] = _percentile_rank(df[col], higher)
    ranks = pd.DataFrame(ranks, index=df.index)

    labels = [d[0] for d in RADAR_DIMS]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    fig = plt.figure(figsize=(15, 7.5))
    fig.suptitle("Top 3 T. Rowe Price Funds — Relationship Overview",
                 fontsize=17, fontweight="bold", y=0.98)

    # ── Left panel: radar chart ─────────────────────────────────────────────────
    ax = fig.add_subplot(1, 2, 1, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color="#888")
    ax.set_title("Percentile rank vs. full fund universe\n(further out = better)",
                 fontsize=10, pad=18)

    for i, idx in enumerate(top3.index):
        vals = [ranks.loc[idx, col] for col, _ in RADAR_DIMS]
        vals += vals[:1]
        color = FUND_COLORS[i]
        label = f"{top3.loc[idx, 'Symbol']} — {top3.loc[idx, 'Fund']}"
        ax.plot(angles, vals, color=color, linewidth=2, label=label)
        ax.fill(angles, vals, color=color, alpha=0.12)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08),
              fontsize=8, frameon=False)

    # ── Right panel: colour-graded relationship table ───────────────────────────
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.axis("off")
    ax2.set_title("Key metrics (raw values)", fontsize=10, pad=12)

    symbols = list(top3["Symbol"])
    cell_text, cell_colors = [], []
    for label, col in TABLE_ROWS:
        # Colour each row by within-row rank among the 3 funds (green = best).
        raw = top3[col].astype(float)
        higher_better = col not in ("Ulcer Index", "Vol Close-to-Close %",
                                    "Beta")
        order = raw.rank(ascending=not higher_better)  # 1 = best
        row_txt, row_col = [], []
        for sym in symbols:
            v = top3.loc[top3["Symbol"] == sym, col].iloc[0]
            row_txt.append(f"{v:.2f}" if pd.notna(v) else "N/A")
            rank_pos = order.loc[top3["Symbol"] == sym].iloc[0]
            shade = {1: "#c8e6c9", 2: "#fff9c4", 3: "#ffcdd2"}.get(int(rank_pos),
                                                                   "#ffffff")
            row_col.append(shade)
        cell_text.append(row_txt)
        cell_colors.append(row_col)

    col_labels = [f"{s}" for s in symbols]
    row_labels = [r[0] for r in TABLE_ROWS]
    table = ax2.table(cellText=cell_text, cellColours=cell_colors,
                      rowLabels=row_labels, colLabels=col_labels,
                      cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.35)

    # Bold header row + colour the header cells to match the radar legend.
    for j, sym in enumerate(symbols):
        header = table[0, j]
        header.set_text_props(fontweight="bold", color="white")
        header.set_facecolor(FUND_COLORS[j])

    fig.text(0.985, 0.02,
             "Green = best of the three · Yellow = middle · Red = worst",
             ha="right", fontsize=8, color="#555")

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    fig.savefig(OUTPUT_PNG, dpi=150)
    plt.close(fig)
    return OUTPUT_PNG


if __name__ == "__main__":
    path = build_figure()
    print(f"✓ Wrote relationship figure → {path}")
