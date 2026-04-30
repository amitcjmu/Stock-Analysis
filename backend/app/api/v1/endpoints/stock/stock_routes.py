"""Backward-compatible shim for modular stock routes."""

from app.api.v1.endpoints.stock.stock_routes_modular import router

__all__ = ["router"]
