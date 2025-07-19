"""
Authentication infrastructure for deployment flexibility.
"""

from .interface import AuthenticationBackend
from .implementations import DatabaseAuthBackend, SSOAuthBackend

__all__ = [
    "AuthenticationBackend",
    "DatabaseAuthBackend",
    "SSOAuthBackend"
]