"""Method implementations extracted from LLMUsageTracker."""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.models.llm_usage import LLMModelPricing, LLMUsageLog

logger = logging.getLogger(__name__)


def set_request_context(
    self,
    request: Optional[Request] = None,
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    flow_id: Optional[str] = None,
    page_context: Optional[str] = None,
    feature_context: Optional[str] = None,
    endpoint: Optional[str] = None,
):
    self.current_request_context = {
        "client_account_id": client_account_id,
        "engagement_id": engagement_id,
        "user_id": user_id,
        "username": username,
        "flow_id": flow_id,
        "page_context": page_context,
        "feature_context": feature_context,
        "endpoint": endpoint,
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None,
        "request_id": str(uuid.uuid4()),
    }


@asynccontextmanager
async def track_llm_call(
    self,
    provider: str,
    model: str,
    model_version: Optional[str] = None,
    feature_context: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    start_time = time.time()
    usage_log = LLMUsageLog(
        **self.current_request_context,
        llm_provider=provider,
        model_name=model,
        model_version=model_version,
        feature_context=feature_context
        or self.current_request_context.get("feature_context"),
        additional_metadata=metadata or {},
    )
    try:
        yield usage_log
        usage_log.success = True
    except Exception as e:
        usage_log.success = False
        usage_log.error_type = type(e).__name__
        usage_log.error_message = str(e)
        logger.error(f"LLM call failed: {provider}/{model} - {e}")
        raise
    finally:
        usage_log.response_time_ms = int((time.time() - start_time) * 1000)
        if usage_log.input_tokens or usage_log.output_tokens:
            await self._calculate_costs(usage_log)
        asyncio.create_task(self._save_usage_log(usage_log))


async def log_llm_usage(
    self,
    provider: str,
    model: str,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    success: bool = True,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    model_version: Optional[str] = None,
    feature_context: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    usage_log = LLMUsageLog(
        **self.current_request_context,
        llm_provider=provider,
        model_name=model,
        model_version=model_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=(input_tokens or 0) + (output_tokens or 0),
        response_time_ms=response_time_ms,
        success=success,
        error_type=error_type,
        error_message=error_message,
        request_data=self._sanitize_data(request_data),
        response_data=self._sanitize_data(response_data),
        feature_context=feature_context
        or self.current_request_context.get("feature_context"),
        additional_metadata=metadata or {},
    )
    await self._calculate_costs(usage_log)
    await self._save_usage_log(usage_log)
    return str(usage_log.id)


async def _calculate_costs(self, usage_log: LLMUsageLog):
    if not usage_log.input_tokens and not usage_log.output_tokens:
        return
    pricing = await self._get_model_pricing(
        usage_log.llm_provider, usage_log.model_name
    )
    if pricing:
        input_cost = ((usage_log.input_tokens or 0) / 1000) * pricing.get("input", 0)
        output_cost = ((usage_log.output_tokens or 0) / 1000) * pricing.get("output", 0)
        usage_log.input_cost = Decimal(str(input_cost))
        usage_log.output_cost = Decimal(str(output_cost))
        usage_log.total_cost = Decimal(str(input_cost + output_cost))


async def _get_model_pricing(
    self, provider: str, model: str
) -> Optional[Dict[str, float]]:
    cache_key = f"{provider}:{model}"
    if cache_key in self.pricing_cache:
        return self.pricing_cache[cache_key]
    try:
        async with AsyncSessionLocal() as session:
            query = text(
                """
                SELECT input_cost_per_1k_tokens, output_cost_per_1k_tokens
                FROM llm_model_pricing
                WHERE provider = :provider
                AND model_name = :model
                AND is_active = true
                AND effective_from <= NOW()
                AND (effective_to IS NULL OR effective_to > NOW())
                ORDER BY effective_from DESC
                LIMIT 1
            """
            )
            row = (
                await session.execute(query, {"provider": provider, "model": model})
            ).fetchone()
            if row:
                pricing = {"input": float(row[0]), "output": float(row[1])}
                self.pricing_cache[cache_key] = pricing
                return pricing
    except Exception as e:
        logger.warning(f"Failed to get model pricing from database: {e}")

    default = self.default_pricing.get(provider, {}).get(model)
    if default:
        self.pricing_cache[cache_key] = default
        return default
    logger.warning(f"No pricing found for {provider}/{model}")
    return None


async def _save_usage_log(self, usage_log: LLMUsageLog):
    try:
        async with AsyncSessionLocal() as session:
            session.add(usage_log)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save LLM usage log: {e}")


def _sanitize_data(
    self, data: Optional[Dict[str, Any]], max_length: int = 5000
) -> Optional[Dict[str, Any]]:
    if not data:
        return None
    try:
        sanitized = {
            k: v
            for k, v in data.items()
            if k.lower()
            not in ["api_key", "token", "password", "secret", "authorization"]
        }
        data_str = json.dumps(sanitized)
        if len(data_str) > max_length:
            return {
                "truncated": True,
                "original_length": len(data_str),
                "sample": data_str[: max_length // 2]
                + "..."
                + data_str[-max_length // 2 :],
            }
        return sanitized
    except Exception:
        return {"error": "failed_to_sanitize"}


async def get_usage_report(
    self,
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    page_context: Optional[str] = None,
    feature_context: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        async with AsyncSessionLocal() as session:
            conditions = ["1=1"]
            params: Dict[str, Any] = {}
            for key, value in {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "page_context": page_context,
                "feature_context": feature_context,
            }.items():
                if value is not None:
                    column = (
                        "llm_provider"
                        if key == "provider"
                        else "model_name" if key == "model" else key
                    )
                    conditions.append(f"{column} = :{key}")
                    params[key] = value
            if start_date:
                conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
            if end_date:
                conditions.append("created_at <= :end_date")
                params["end_date"] = end_date

            where_sql = " AND ".join(f"({condition})" for condition in conditions)
            summary_query = text(
                """
                SELECT COUNT(*), COUNT(*) FILTER (WHERE success = true),
                       COUNT(*) FILTER (WHERE success = false),
                       COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0),
                       COALESCE(SUM(total_tokens), 0), COALESCE(SUM(total_cost), 0),
                       COALESCE(AVG(response_time_ms), 0), MIN(created_at), MAX(created_at)
                FROM llm_usage_logs WHERE """
                + where_sql
            )
            summary = (await session.execute(summary_query, params)).fetchone()
            breakdown_query = text(
                """
                SELECT llm_provider, model_name, COUNT(*) as requests,
                       COALESCE(SUM(total_tokens), 0) as tokens,
                       COALESCE(SUM(total_cost), 0) as cost
                FROM llm_usage_logs WHERE """
                + where_sql
                + " GROUP BY llm_provider, model_name ORDER BY cost DESC"
            )
            breakdown = [
                dict(row._mapping)
                for row in await session.execute(breakdown_query, params)
            ]
            return {
                "summary": {
                    "total_requests": summary[0],
                    "successful_requests": summary[1],
                    "failed_requests": summary[2],
                    "success_rate": (
                        (summary[1] / summary[0] * 100) if summary[0] > 0 else 0
                    ),
                    "total_input_tokens": summary[3],
                    "total_output_tokens": summary[4],
                    "total_tokens": summary[5],
                    "total_cost": float(summary[6]),
                    "avg_response_time_ms": float(summary[7]),
                    "period": {
                        "start": summary[8].isoformat() if summary[8] else None,
                        "end": summary[9].isoformat() if summary[9] else None,
                    },
                },
                "breakdown_by_model": breakdown,
            }
    except Exception as e:
        logger.error(f"Failed to generate usage report: {e}")
        raise


async def initialize_default_pricing(self):
    try:
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            for provider, models in self.default_pricing.items():
                for model_name, pricing in models.items():
                    existing = await session.execute(
                        text(
                            """
                            SELECT id FROM llm_model_pricing
                            WHERE provider = :provider AND model_name = :model_name AND is_active = true
                        """
                        ),
                        {"provider": provider, "model_name": model_name},
                    )
                    if not existing.fetchone():
                        session.add(
                            LLMModelPricing(
                                provider=provider,
                                model_name=model_name,
                                input_cost_per_1k_tokens=Decimal(str(pricing["input"])),
                                output_cost_per_1k_tokens=Decimal(
                                    str(pricing["output"])
                                ),
                                effective_from=now,
                                is_active=True,
                                source="default_initialization",
                                notes="Default pricing from service initialization",
                            )
                        )
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to initialize default pricing: {e}")
