"""
Authentication infrastructure for deployment flexibility.
"""

from .implementations import DatabaseAuthBackend, SSOAuthBackend
from .interface import AuthenticationBackend

__all__ = ["AuthenticationBackend", "DatabaseAuthBackend", "SSOAuthBackend"]
