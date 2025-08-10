"""
Environment flag helpers for consistent truthy parsing.

Treats 1/true/yes/on/y/t (any case, with surrounding whitespace) as truthy.
Anything else is falsy.
"""

import os
from typing import Optional


TRUTHY_VALUES = {"1", "true", "yes", "on", "y", "t"}


def is_truthy_env(var_name: str, default: Optional[bool] = False) -> bool:
    """Return True if the environment variable is set to a recognized truthy value.

    Args:
        var_name: Environment variable name.
        default: Default boolean when variable is not set.

    Returns:
        bool: Parsed truthy value.
    """
    raw = os.getenv(var_name)
    if raw is None:
        return bool(default)
    return raw.strip().lower() in TRUTHY_VALUES
