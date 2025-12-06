"""
Utility functions for EOL enrichment

Helper functions for calculating EOL status and date handling.
"""

from datetime import date, datetime
from typing import Optional


def calculate_eol_status(eol_date_str: Optional[str]) -> str:
    """Calculate EOL status based on date string."""
    if not eol_date_str:
        return "unknown"

    try:
        eol_date = datetime.strptime(eol_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "unknown"

    today = date.today()

    if eol_date < today:
        return "eol_expired"

    months_until_eol = (eol_date.year - today.year) * 12 + (
        eol_date.month - today.month
    )
    if months_until_eol <= 12:
        return "eol_soon"

    return "active"
