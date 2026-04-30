"""Stock Financials Agent - Specialized AI agent for financial analysis."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import (
    ModelType,
    TaskComplexity,
    multi_model_service,
)
from app.services.stock_data_api import StockDataAPIService
from app.services.stock_financials_helpers import (
    _build_investment_scorecard,
    _compute_price_band,
    _create_financials_prompt,
    _parse_llm_response,
    _safe_float,
    _score_higher_better,
    _score_lower_better,
    _to_ratio,
)
from app.services.stock_llm_fallback import (
    analysis_when_anthropic_insufficient_credits,
    analysis_when_anthropic_unconfigured,
)
from app.services.stock_service import StockService
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)


class StockFinancialsAgent:
    """Specialized agent for generating financial analysis using Anthropic."""

    _safe_float = _safe_float
    _to_ratio = _to_ratio
    _score_higher_better = _score_higher_better
    _score_lower_better = _score_lower_better
    _compute_price_band = _compute_price_band
    _build_investment_scorecard = _build_investment_scorecard
    _create_financials_prompt = _create_financials_prompt
    _parse_llm_response = _parse_llm_response

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)
        self.stock_data_api = StockDataAPIService()

    async def analyze_financials(
        self, stock_symbol: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info("💰 [FINANCIALS AGENT] Starting analysis for %s", stock_symbol)
        stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
        if not stock_data:
            raise ValueError(f"Stock {stock_symbol} not found")

        detailed_data = await self.stock_data_api.get_stock_data(stock_symbol)
        if detailed_data:
            stock_data.update(detailed_data)

        stock = await self.stock_service.save_stock(stock_data)
        prompt = self._create_financials_prompt(stock_data)
        response_data = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="analysis",
            complexity=TaskComplexity.AGENTIC,
            model_type=ModelType.CLAUDE_OPUS_4_6,
        )

        if response_data.get("status") == "placeholder":
            analysis_data = analysis_when_anthropic_unconfigured(
                "financials", stock_data
            )
        elif (
            response_data.get("status") == "error"
            and response_data.get("anthropic_error_kind") == "insufficient_credits"
        ):
            analysis_data = analysis_when_anthropic_insufficient_credits(
                "financials", stock_data
            )
        elif response_data.get("status") == "error":
            error_msg = response_data.get("error", "Unknown error")
            raise ValueError(f"LLM error for {stock_symbol}: {error_msg}")
        else:
            response_text = response_data.get("response") or response_data.get(
                "content", ""
            )
            if not response_text:
                raise ValueError(f"Empty response from LLM for {stock_symbol}")
            analysis_data = self._parse_llm_response(
                response_text,
                stock_data,
                model_used=response_data.get("model_used", "auto"),
            )

        analysis = await self.stock_service.save_stock_analysis(
            UUID(str(stock.id)),
            sanitize_for_json(analysis_data),
        )
        stock_dict = stock.to_dict() if hasattr(stock, "to_dict") else stock
        analysis_dict = analysis.to_dict() if hasattr(analysis, "to_dict") else analysis
        return {
            "stock": sanitize_for_json(stock_dict),
            "analysis": sanitize_for_json(analysis_dict),
        }
