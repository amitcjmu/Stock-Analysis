"""Shared static universe used by in-app stock sector endpoints."""

from typing import Any, Dict

TRENDING_SECTOR_UNIVERSE: Dict[str, Dict[str, Any]] = {
    "railways": {
        "name": "Railways",
        "one_day_change_percent": 3.77,
        "gainers": 1,
        "losers": 0,
        "symbols": ["IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "TITAGARH.NS"],
    },
    "shipbuilding": {
        "name": "Shipbuilding",
        "one_day_change_percent": 3.64,
        "gainers": 2,
        "losers": 2,
        "symbols": ["MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS"],
    },
    "non_ferrous_metals": {
        "name": "Non-Ferrous Metals",
        "one_day_change_percent": 2.09,
        "gainers": 24,
        "losers": 16,
        "symbols": ["HINDALCO.NS", "NALCO.NS", "VEDL.NS", "HINDCOPPER.NS"],
    },
    "glass_products": {
        "name": "Glass Products",
        "one_day_change_percent": 1.81,
        "gainers": 5,
        "losers": 5,
        "symbols": ["BORORENEW.NS", "ASAHIINDIA.NS", "LAOPALA.NS"],
    },
    "jewellery": {
        "name": "Jewellery",
        "one_day_change_percent": 1.37,
        "gainers": 34,
        "losers": 32,
        "symbols": ["TITAN.NS", "KALYANKJIL.NS", "SENCO.NS", "THANGAMAYL.NS"],
    },
    "media": {
        "name": "Media",
        "one_day_change_percent": 0.81,
        "gainers": 14,
        "losers": 4,
        "symbols": ["ZEEL.NS", "SUNTV.NS", "PVRINOX.NS", "TV18BRDCST.NS"],
    },
    "mining": {
        "name": "Mining",
        "one_day_change_percent": 0.80,
        "gainers": 20,
        "losers": 6,
        "symbols": ["COALINDIA.NS", "NMDC.NS", "MOIL.NS", "HINDZINC.NS"],
    },
    "infra_developers_operators": {
        "name": "Infra Developers & Operators",
        "one_day_change_percent": 0.62,
        "gainers": 58,
        "losers": 88,
        "symbols": ["LT.NS", "NBCC.NS", "IRB.NS", "GMRINFRA.NS"],
    },
    "it_education": {
        "name": "IT Education",
        "one_day_change_percent": 0.58,
        "gainers": 4,
        "losers": 7,
        "symbols": ["NIITLTD.NS", "APTECHT.NS", "NIITMTS.NS"],
    },
    "infra_investment_trusts": {
        "name": "Infra Investment Trusts",
        "one_day_change_percent": 0.57,
        "gainers": 8,
        "losers": 1,
        "symbols": ["IRBInvIT.NS", "INDIGRID.NS", "POWERGRID.NS"],
    },
    "miscellaneous": {
        "name": "Miscellaneous",
        "one_day_change_percent": 0.54,
        "gainers": 78,
        "losers": 84,
        "symbols": ["RELIANCE.NS", "ITC.NS", "ADANIENT.NS", "LTIM.NS"],
    },
}
