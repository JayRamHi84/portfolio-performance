# ═══════════════════════════════════════════════════════════════════════════════
#  funds.py  —  T. Rowe Price equity mutual-fund universe (name → symbol)
# ═══════════════════════════════════════════════════════════════════════════════
#  `FUNDS` is an ordered list of (symbol, name, category) tuples consumed by main.py.
# ═══════════════════════════════════════════════════════════════════════════════

FUNDS = [
    # 1. U.S. Large-Cap & Core Equity Funds
    ("PRWAX", "All-Cap Opportunities Fund",                     "US Large-Cap / Core"),
    ("TRBCX", "Blue Chip Growth Fund",                          "US Large-Cap / Core"),
    ("PRDGX", "Dividend Growth Fund",                           "US Large-Cap / Core"),
    ("PRFDX", "Equity Income Fund",                             "US Large-Cap / Core"),
    ("PRGFX", "Growth Stock Fund",                              "US Large-Cap / Core"),
    ("TQMVX", "Integrated U.S. Large-Cap Value Equity Fund",    "US Large-Cap / Core"),
    ("TRGOX", "Large-Cap Growth Fund",                          "US Large-Cap / Core"),
    ("TRLUX", "Large-Cap Value Fund",                           "US Large-Cap / Core"),
    ("PREFX", "Tax-Efficient Equity Fund",                      "US Large-Cap / Core"),
    ("PRCOX", "U.S. Equity Research Fund",                      "US Large-Cap / Core"),
    ("TRVLX", "Value Fund",                                     "US Large-Cap / Core"),

    # 2. U.S. Mid-Cap Equity Funds
    ("PRDMX", "Diversified Mid-Cap Growth Fund",                "US Mid-Cap"),
    ("RPMGX", "Mid-Cap Growth Fund",                            "US Mid-Cap"),
    ("TRMCX", "Mid-Cap Value Fund",                             "US Mid-Cap"),
    ("TQSMX", "Integrated U.S. Small-Mid Cap Core Equity Fund", "US Mid-Cap"),

    # 3. U.S. Small-Cap Equity Funds
    ("PRDSX", "Integrated U.S. Small-Cap Growth Equity Fund",   "US Small-Cap"),
    ("PRNHX", "New Horizons Fund",                              "US Small-Cap"),
    ("OTCFX", "Small-Cap Stock Fund",                           "US Small-Cap"),
    ("PRSVX", "Small-Cap Value Fund",                           "US Small-Cap"),

    # 4. International & Global Equity Funds
    ("TCELX", "China Evolution Equity Fund",                    "International / Global"),
    ("PRIJX", "Emerging Markets Discovery Stock Fund",          "International / Global"),
    ("PRMSX", "Emerging Markets Stock Fund",                    "International / Global"),
    ("PRESX", "European Stock Fund",                            "International / Global"),
    ("RPGEX", "Global Growth Stock Fund",                       "International / Global"),
    ("TGPEX", "Global Impact Equity Fund",                      "International / Global"),
    ("PRGSX", "Global Stock Fund",                              "International / Global"),
    ("TRGVX", "Global Value Equity Fund",                       "International / Global"),
    ("TQGEX", "Integrated Global Equity Fund",                  "International / Global"),
    ("PRIDX", "International Discovery Fund",                    "International / Global"),
    ("PRITX", "International Stock Fund",                        "International / Global"),
    ("TRIGX", "International Value Equity Fund",                "International / Global"),
    ("PRJPX", "Japan Fund",                                     "International / Global"),
    ("PRLAX", "Latin America Fund",                             "International / Global"),
    ("PRASX", "New Asia Fund",                                  "International / Global"),
    ("PSILX", "Spectrum International Equity Fund",             "International / Global"),

    # 5. Sector & Specialty Equity Funds
    ("PRMTX", "Communications & Technology Fund",               "Sector / Specialty"),
    ("PRISX", "Financial Services Fund",                        "Sector / Specialty"),
    ("RPGIX", "Global Industrials Fund",                        "Sector / Specialty"),
    ("TRGRX", "Global Real Estate Fund",                        "Sector / Specialty"),
    ("PRGTX", "Global Technology Fund",                         "Sector / Specialty"),
    ("PRHSX", "Health Sciences Fund",                           "Sector / Specialty"),
    ("PRNEX", "New Era Fund",                                   "Sector / Specialty"),
    ("PRAFX", "Real Assets Fund",                               "Sector / Specialty"),
    ("TRREX", "Real Estate Fund",                               "Sector / Specialty"),
    ("PRSCX", "Science & Technology Fund",                      "Sector / Specialty"),

    # 6. Index (Passively Managed) Stock Funds
    ("PREIX", "Equity Index 500 Fund",                          "Index"),
    ("PEXMX", "Extended Equity Market Index Fund",              "Index"),
    ("PIEQX", "International Equity Index Fund",                "Index"),
    ("POMIX", "Total Equity Market Index Fund",                 "Index"),

    # 7. Hedged, Core-Hybrid & Multi-Asset Funds (Equity-Heavy)
    ("PRWCX", "Capital Appreciation Fund",                      "Hybrid / Multi-Asset"),
    ("PRCFX", "Capital Appreciation and Income Fund",           "Hybrid / Multi-Asset"),
    ("RPBAX", "Balanced Fund",                                  "Hybrid / Multi-Asset"),
    ("PHEFX", "Hedged Equity Fund",                             "Hybrid / Multi-Asset"),
    ("PRSGX", "Spectrum Diversified Equity Fund",               "Hybrid / Multi-Asset"),
]
