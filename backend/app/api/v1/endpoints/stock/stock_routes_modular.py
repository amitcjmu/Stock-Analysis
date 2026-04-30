"""Stock API routes entrypoint (modularized)."""

from fastapi import APIRouter

from app.api.v1.endpoints.stock.routes.analysis_all import router as analysis_all_router
from app.api.v1.endpoints.stock.routes.analysis_single import (
    router as analysis_single_router,
)
from app.api.v1.endpoints.stock.routes.data_and_sector import (
    router as data_and_sector_router,
)
from app.api.v1.endpoints.stock.routes.search_and_watchlist import (
    router as search_and_watchlist_router,
)

router = APIRouter(prefix="")
router.include_router(search_and_watchlist_router)
router.include_router(data_and_sector_router)
router.include_router(analysis_single_router)
router.include_router(analysis_all_router)
