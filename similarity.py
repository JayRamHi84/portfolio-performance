# Find funds most similar to PRGTX / PRSCX over the current (5y) window.
# Similarity = Euclidean distance in z-scored space across the dimensions the
# user cares about: return, volatility, drawdown, beta, Sharpe.
import pandas as pd

import config

df = pd.read_csv(config.OUTPUT_CSV)

DIMS = ["Ann Return %", "Vol Close-to-Close %", "Max Drawdown %", "Beta", "Sharpe"]
z = df.copy()
for c in DIMS:
    z[c] = (df[c] - df[c].mean()) / df[c].std(ddof=0)

targets = ["PRGTX", "PRSCX"]
for t in targets:
    tv = z.loc[z["Symbol"] == t, DIMS].iloc[0]
    dist = ((z[DIMS] - tv) ** 2).sum(axis=1) ** 0.5
    out = df.assign(Distance=dist.round(3))
    out = out[out["Symbol"] != t].sort_values("Distance")
    print(f"\n=== Closest to {t} "
          f"({df.loc[df.Symbol==t,'Fund'].iloc[0]}) ===")
    cols = ["Distance", "Symbol", "Fund", "Ann Return %", "Sharpe",
            "Max Drawdown %", "Vol Close-to-Close %", "Beta"]
    print(out[cols].head(6).to_string(index=False))

# Also show the two targets side by side.
print("\n=== The two target funds ===")
cols = ["Symbol", "Fund", "Ann Return %", "Sharpe", "Sortino", "Calmar",
        "Max Drawdown %", "Ulcer Index", "Vol Close-to-Close %", "Beta"]
print(df[df.Symbol.isin(targets)][cols].to_string(index=False))
