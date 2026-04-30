"""LLM usage tracking service with extracted method modules."""

import logging
from typing import Any, Dict

from app.services.llm_usage_tracker_methods import (
    _calculate_costs,
    _get_model_pricing,
    _sanitize_data,
    _save_usage_log,
    get_usage_report,
    initialize_default_pricing,
    log_llm_usage,
    set_request_context,
    track_llm_call,
)
from app.services.llm_usage_tracker_pricing import DEFAULT_PRICING

logger = logging.getLogger(__name__)


class LLMUsageTracker:
    """Service for tracking LLM usage and costs across the application."""

    set_request_context = set_request_context
    track_llm_call = track_llm_call
    log_llm_usage = log_llm_usage
    _calculate_costs = _calculate_costs
    _get_model_pricing = _get_model_pricing
    _save_usage_log = _save_usage_log
    _sanitize_data = _sanitize_data
    get_usage_report = get_usage_report
    initialize_default_pricing = initialize_default_pricing

    def __init__(self):
        self.current_request_context: Dict[str, Any] = {
            "client_account_id": None,
            "engagement_id": None,
            "user_id": None,
            "username": None,
            "flow_id": None,
            "page_context": None,
            "feature_context": None,
            "endpoint": None,
            "ip_address": None,
            "user_agent": None,
            "request_id": None,
        }
        self.pricing_cache: Dict[str, Dict[str, float]] = {}
        self.default_pricing = DEFAULT_PRICING


llm_tracker = LLMUsageTracker()
