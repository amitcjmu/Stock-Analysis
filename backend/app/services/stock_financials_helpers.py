"""Helper methods for StockFinancialsAgent."""

import math
from typing import Any, Dict

from app.utils.json_sanitization import safe_parse_llm_json


def _safe_float(self, value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "N/A", "nan"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_ratio(self, value: float) -> float:
    if value > 1:
        return value / 100.0
    return value


def _score_higher_better(self, value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 100.0
    return ((value - low) / (high - low)) * 100.0


def _score_lower_better(self, value: float, low: float, high: float) -> float:
    if value <= low:
        return 100.0
    if value >= high:
        return 0.0
    return ((high - value) / (high - low)) * 100.0


def _compute_price_band(self, stock_data: Dict[str, Any], current_price: float) -> str:
    currency = str(stock_data.get("currency", "")).upper()
    is_inr = currency in {"INR", "NSE", "BSE"} or str(
        stock_data.get("symbol", "")
    ).endswith(".NS")
    if is_inr:
        if current_price < 200:
            return "low_price"
        if current_price <= 2000:
            return "mid_price"
        return "high_price"
    if current_price < 20:
        return "low_price"
    if current_price <= 200:
        return "mid_price"
    return "high_price"


def _build_investment_scorecard(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
    pe_ratio = self._safe_float(
        stock_data.get("trailingPE") or stock_data.get("pe_ratio"), 0.0
    )
    pb_ratio = self._safe_float(
        stock_data.get("priceToBook") or stock_data.get("price_to_book"), 0.0
    )
    ps_ratio = self._safe_float(stock_data.get("priceToSalesTrailing12Months"), 0.0)
    roe = self._to_ratio(
        self._safe_float(stock_data.get("returnOnEquity") or stock_data.get("roe"), 0.0)
    )
    net_margin = self._to_ratio(
        self._safe_float(
            stock_data.get("profitMargins") or stock_data.get("profit_margin"), 0.0
        )
    )
    current_ratio = self._safe_float(
        stock_data.get("currentRatio") or stock_data.get("current_ratio"), 0.0
    )
    rev_growth = self._to_ratio(self._safe_float(stock_data.get("revenueGrowth"), 0.0))
    earn_growth = self._to_ratio(
        self._safe_float(stock_data.get("earningsGrowth"), 0.0)
    )
    debt_to_equity = self._safe_float(
        stock_data.get("debtToEquity") or stock_data.get("debt_to_equity"), 0.0
    )
    debt_to_assets = self._to_ratio(
        self._safe_float(stock_data.get("debtToAssets"), 0.0)
    )
    current_price = self._safe_float(stock_data.get("current_price"), 0.0)
    week52_change = self._to_ratio(
        self._safe_float(stock_data.get("52WeekChange"), 0.0)
    )
    sma_50 = self._safe_float(stock_data.get("fiftyDayAverage"), 0.0)
    sma_200 = self._safe_float(stock_data.get("twoHundredDayAverage"), 0.0)

    valuation_score = (
        self._score_lower_better(pe_ratio, 10, 40)
        + self._score_lower_better(pb_ratio, 1, 8)
        + self._score_lower_better(ps_ratio, 1, 15)
    ) / 3.0
    quality_score = (
        self._score_higher_better(roe, 0.08, 0.25)
        + self._score_higher_better(net_margin, 0.05, 0.2)
        + self._score_higher_better(current_ratio, 1.0, 2.5)
    ) / 3.0
    growth_score = (
        self._score_higher_better(rev_growth, 0.03, 0.2)
        + self._score_higher_better(earn_growth, 0.03, 0.25)
    ) / 2.0
    risk_score = (
        self._score_lower_better(debt_to_equity, 0.3, 2.5)
        + self._score_lower_better(debt_to_assets, 0.2, 0.7)
    ) / 2.0
    momentum_parts = [self._score_higher_better(week52_change, -0.1, 0.4)]
    if sma_50 > 0 and sma_200 > 0 and current_price > 0:
        above_50 = 100.0 if current_price > sma_50 else 35.0
        above_200 = 100.0 if current_price > sma_200 else 20.0
        momentum_parts.extend([above_50, above_200])
    momentum_score = sum(momentum_parts) / len(momentum_parts)

    overall = (
        valuation_score * 0.25
        + quality_score * 0.25
        + growth_score * 0.2
        + risk_score * 0.2
        + momentum_score * 0.1
    )
    overall = max(0.0, min(100.0, overall))

    if overall >= 75:
        rating = "strong"
    elif overall >= 60:
        rating = "moderate"
    elif overall >= 45:
        rating = "speculative"
    else:
        rating = "weak"

    sector_text = " ".join(
        [
            str(stock_data.get("sector", "")),
            str(stock_data.get("industry", "")),
            str(stock_data.get("company_name", "")),
        ]
    ).lower()
    defence_related = any(
        term in sector_text
        for term in ["defence", "defense", "aerospace", "missile", "shipbuilding"]
    )

    order_book = self._safe_float(stock_data.get("order_book_value"), 0.0)
    market_cap = self._safe_float(stock_data.get("market_cap"), 0.0)
    order_book_to_market_cap = (
        order_book / market_cap if order_book > 0 and market_cap > 0 else None
    )

    return {
        "overall_score": round(overall, 2),
        "rating": rating,
        "valuation_score": round(valuation_score, 2),
        "quality_score": round(quality_score, 2),
        "growth_score": round(growth_score, 2),
        "financial_risk_score": round(risk_score, 2),
        "momentum_score": round(momentum_score, 2),
        "price_position": {
            "current_price": current_price,
            "price_band": self._compute_price_band(stock_data, current_price),
        },
        "sector_context": {
            "defence_related": defence_related,
            "order_book_to_market_cap": order_book_to_market_cap,
        },
    }


def _create_financials_prompt(self, stock_data: Dict[str, Any]) -> str:
    company_name = stock_data.get("company_name", "Unknown Company")
    symbol = stock_data.get("symbol", "N/A")
    current_price = stock_data.get("current_price", "N/A")
    market_cap = stock_data.get("market_cap", "N/A")
    pe_ratio = stock_data.get("trailingPE") or stock_data.get("pe_ratio", "N/A")
    pb_ratio = stock_data.get("priceToBook") or stock_data.get("price_to_book", "N/A")
    roe = stock_data.get("returnOnEquity") or stock_data.get("roe", "N/A")
    debt_to_equity = stock_data.get("debtToEquity") or stock_data.get(
        "debt_to_equity", "N/A"
    )
    return f"""
You are a senior equity research analyst. Analyze the financial profile for:
Company: {company_name}
Symbol: {symbol}
Current Price: {current_price}
Market Cap: {market_cap}
P/E: {pe_ratio}
P/B: {pb_ratio}
ROE: {roe}
Debt/Equity: {debt_to_equity}

Return JSON only with keys:
summary, key_insights, valuation_analysis, financial_health, growth_analysis,
risk_factors, recommendation, confidence_score.
"""


def _parse_llm_response(
    self, response_text: str, stock_data: Dict[str, Any], model_used: str = "auto"
) -> Dict[str, Any]:
    parsed = safe_parse_llm_json(response_text)
    scorecard = self._build_investment_scorecard(stock_data)

    summary = "Financial analysis generated."
    key_insights = []
    valuation_analysis = {}
    financial_health = {}
    growth_analysis = {}
    risk_factors = []
    recommendation = {}
    confidence_score = 0.65

    if isinstance(parsed, dict):
        summary = str(parsed.get("summary") or summary)
        key_insights = parsed.get("key_insights") or []
        valuation_analysis = parsed.get("valuation_analysis") or {}
        financial_health = parsed.get("financial_health") or {}
        growth_analysis = parsed.get("growth_analysis") or {}
        risk_factors = parsed.get("risk_factors") or []
        recommendation = parsed.get("recommendation") or {}
        confidence_score = float(parsed.get("confidence_score") or confidence_score)

    if not key_insights and response_text:
        key_insights = [response_text[:220]]
    if not summary and response_text:
        summary = response_text[:320]

    return {
        "analysis_type": "financials",
        "llm_model": model_used,
        "summary": summary,
        "key_insights": (
            key_insights if isinstance(key_insights, list) else [str(key_insights)]
        ),
        "fundamental_analysis": {
            "valuation_analysis": (
                valuation_analysis if isinstance(valuation_analysis, dict) else {}
            ),
            "financial_health": (
                financial_health if isinstance(financial_health, dict) else {}
            ),
            "growth_analysis": (
                growth_analysis if isinstance(growth_analysis, dict) else {}
            ),
            "investment_scorecard": scorecard,
        },
        "risk_assessment": {
            "risk_factors": (
                risk_factors if isinstance(risk_factors, list) else [str(risk_factors)]
            )
        },
        "recommendations": (
            recommendation
            if isinstance(recommendation, dict)
            else {"action": str(recommendation)}
        ),
        "confidence_score": max(
            0.0,
            min(1.0, confidence_score if not math.isnan(confidence_score) else 0.65),
        ),
        "raw_response": response_text[:3000],
    }
