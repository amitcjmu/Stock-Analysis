"""
Structured stock analysis payloads when Claude (Anthropic) is not configured.

Avoids surfacing internal prompts or multi_model_service placeholder strings in the UI.
"""

from typing import Any, Dict


def analysis_when_anthropic_unconfigured(
    analysis_type: str,
    stock_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return analysis fields compatible with ``StockService.save_stock_analysis``.

    Used when ``multi_model_service`` returns ``status == "placeholder"`` so the
    UI shows a clear configuration message instead of raw prompt text.
    """
    symbol = stock_data.get("symbol") or "this symbol"
    summary = (
        f"AI-generated commentary for {symbol} is not available: Anthropic Claude is "
        "not configured on the server. Price and market data on other tabs may still "
        "load from data providers. To enable AI analysis, set ANTHROPIC_API_KEY and "
        "restart the backend (see https://console.anthropic.com/)."
    )
    key_insights = [
        "Add ANTHROPIC_API_KEY to your environment (Docker Compose, Railway secrets, or .env).",
        "Optional: CLAUDE_OPUS_MODEL (defaults to claude-opus-4-6).",
        "Restart the API process after changing environment variables.",
    ]
    return {
        "analysis_type": analysis_type,
        "summary": summary,
        "key_insights": key_insights,
        "technical_analysis": {},
        "fundamental_analysis": {},
        "risk_assessment": {
            "overall_risk": "unknown",
            "key_risks": [
                "Structured risk narrative was not generated because the LLM is not configured."
            ],
        },
        "recommendations": {
            "action": "hold",
            "confidence": 0.0,
            "reasoning": "No automated recommendation without Anthropic API access.",
        },
        "price_targets": {},
        "llm_model": "unconfigured",
        "llm_prompt": None,
        "llm_response": {"reason": "anthropic_api_not_configured"},
        "confidence_score": 0.0,
    }


def analysis_when_anthropic_insufficient_credits(
    analysis_type: str,
    stock_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Same shape as ``analysis_when_anthropic_unconfigured`` for Anthropic HTTP 400
    when the workspace credit balance is too low (Plans & Billing).
    """
    symbol = stock_data.get("symbol") or "this symbol"
    summary = (
        f"AI-generated commentary for {symbol} is not available: your Anthropic "
        "workspace has insufficient API credits (or billing blocks usage). "
        "Price and market data on other tabs may still load from data providers."
    )
    key_insights = [
        "Open https://console.anthropic.com/settings/plans — add credits or upgrade the plan.",
        "Confirm the API key belongs to the workspace that has an active balance.",
        (
            "After billing is fixed, run analysis again; no code or env key "
            "change is required if the key was already valid."
        ),
    ]
    return {
        "analysis_type": analysis_type,
        "summary": summary,
        "key_insights": key_insights,
        "technical_analysis": {},
        "fundamental_analysis": {},
        "risk_assessment": {
            "overall_risk": "unknown",
            "key_risks": [
                (
                    "Structured risk narrative was not generated because Anthropic "
                    "rejected the request for billing reasons."
                )
            ],
        },
        "recommendations": {
            "action": "hold",
            "confidence": 0.0,
            "reasoning": "No automated recommendation while Anthropic returns a billing/credit error.",
        },
        "price_targets": {},
        "llm_model": "anthropic_billing_blocked",
        "llm_prompt": None,
        "llm_response": {"reason": "anthropic_insufficient_credits"},
        "confidence_score": 0.0,
    }
