"""
Shared request/response schemas and helper utilities for stock routes.
"""

import json
import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StockSearchResponse(BaseModel):
    """Response model for stock search."""

    success: bool
    stocks: List[dict]
    count: int
    query: str


class StockDetailResponse(BaseModel):
    """Response model for stock details."""

    success: bool
    stock: dict


class StockAnalysisRequest(BaseModel):
    """Request model for stock analysis."""

    symbol: str = Field(..., description="Stock symbol to analyze")
    model: Optional[str] = Field(
        default=None,
        description="Ignored. Stock analysis always uses Anthropic Claude (ANTHROPIC_API_KEY).",
    )


class StockAnalysisResponse(BaseModel):
    """Response model for stock analysis."""

    success: bool
    stock: dict
    analysis: dict
    message: str


def clean_json_response(response_text: str) -> str:
    """Extract and clean JSON from LLM response text."""
    response_clean = response_text.strip()

    if "```json" in response_clean:
        json_match = re.search(r"```json\s*(.*?)\s*```", response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(1).strip()
    elif "```" in response_clean:
        json_match = re.search(r"```\s*(.*?)\s*```", response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(1).strip()

    json_match = re.search(r"\[.*\]", response_clean, re.DOTALL)
    if json_match:
        response_clean = json_match.group(0)

    return response_clean


def format_llm_insight(insight: dict, symbol: str, index: int) -> dict:
    """Format a single LLM insight to match Yahoo Finance format."""
    return {
        "title": insight.get("title", "AI News Insight"),
        "publisher": insight.get("source", "AI Analysis"),
        "link": "",
        "published_date": int(datetime.now().timestamp()),
        "uuid": f"llm-{symbol}-{index}",
        "summary": insight.get("summary", ""),
        "category": insight.get("category", "market_update"),
        "impact": insight.get("impact", "neutral"),
        "is_llm_generated": True,
    }


def parse_llm_news_response(
    response_text: str, response_clean: str, symbol: str
) -> List[dict]:
    """Parse LLM news response and return formatted insights."""
    llm_news_insights: List[dict] = []

    try:
        llm_news_data = json.loads(response_clean)
        if isinstance(llm_news_data, list) and llm_news_data:
            for idx, insight in enumerate(llm_news_data[:5]):
                if isinstance(insight, dict) and insight.get("title"):
                    llm_news_insights.append(format_llm_insight(insight, symbol, idx))
        elif isinstance(llm_news_data, dict) and llm_news_data.get("title"):
            llm_news_insights.append(format_llm_insight(llm_news_data, symbol, 0))
    except json.JSONDecodeError:
        if response_text and len(response_text) > 20:
            llm_news_insights.append(
                {
                    "title": f"Market Analysis for {symbol}",
                    "publisher": "AI Analysis",
                    "link": "",
                    "published_date": int(datetime.now().timestamp()),
                    "uuid": f"llm-{symbol}-fallback",
                    "summary": (
                        response_text[:300] + "..."
                        if len(response_text) > 300
                        else response_text
                    ),
                    "category": "market_update",
                    "impact": "neutral",
                    "is_llm_generated": True,
                }
            )

    return llm_news_insights
