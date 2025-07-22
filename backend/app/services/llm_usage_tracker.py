"""LLM Usage Tracking Service

Automatically tracks all LLM API calls for cost analysis and monitoring.
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.llm_usage import LLMModelPricing, LLMUsageLog, LLMUsageSummary

logger = logging.getLogger(__name__)


class LLMUsageTracker:
    """Service to track LLM usage, costs, and performance metrics."""
    
    def __init__(self):
        self.current_request_context: Dict[str, Any] = {}
        
        # Model pricing cache (updated periodically)
        self.pricing_cache: Dict[str, Dict[str, Any]] = {}
        self._last_pricing_update = None
        
        # Default pricing for common models (fallback when DB pricing not available)
        self.default_pricing = {
            'openai': {
                'gpt-4': {'input': 0.03, 'output': 0.06},  # per 1K tokens
                'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
                'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            },
            'deepinfra': {
                'meta-llama/Llama-2-70b-chat-hf': {'input': 0.0007, 'output': 0.0009},
                'meta-llama/Llama-2-13b-chat-hf': {'input': 0.0002, 'output': 0.0002},
                'mistralai/Mixtral-8x7B-Instruct-v0.1': {'input': 0.0005, 'output': 0.0005},
            },
            'anthropic': {
                'claude-3-opus': {'input': 0.015, 'output': 0.075},
                'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
                'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
            }
        }
    
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
        endpoint: Optional[str] = None
    ):
        """Set context for current request to be included in all LLM logs."""
        self.current_request_context = {
            'client_account_id': client_account_id,
            'engagement_id': engagement_id,
            'user_id': user_id,
            'username': username,
            'flow_id': flow_id,
            'page_context': page_context,
            'feature_context': feature_context,
            'endpoint': endpoint,
            'ip_address': request.client.host if request else None,
            'user_agent': request.headers.get('user-agent') if request else None,
            'request_id': str(uuid.uuid4())
        }
    
    @asynccontextmanager
    async def track_llm_call(
        self,
        provider: str,
        model: str,
        model_version: Optional[str] = None,
        feature_context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager to automatically track LLM API calls."""
        
        start_time = time.time()
        usage_log = LLMUsageLog(
            **self.current_request_context,
            llm_provider=provider,
            model_name=model,
            model_version=model_version,
            feature_context=feature_context or self.current_request_context.get('feature_context'),
            additional_metadata=metadata or {}
        )
        
        try:
            # Yield control to the LLM call
            yield usage_log
            
            # Mark as successful if we get here
            usage_log.success = True
            
        except Exception as e:
            # Log the error
            usage_log.success = False
            usage_log.error_type = type(e).__name__
            usage_log.error_message = str(e)
            logger.error(f"LLM call failed: {provider}/{model} - {e}")
            raise
            
        finally:
            # Calculate response time
            end_time = time.time()
            usage_log.response_time_ms = int((end_time - start_time) * 1000)
            
            # Calculate costs if token usage is set
            if usage_log.input_tokens or usage_log.output_tokens:
                await self._calculate_costs(usage_log)
            
            # Save to database (async, non-blocking)
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Manually log LLM usage (for when context manager can't be used)."""
        
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
            feature_context=feature_context or self.current_request_context.get('feature_context'),
            additional_metadata=metadata or {}
        )
        
        # Calculate costs
        await self._calculate_costs(usage_log)
        
        # Save to database
        await self._save_usage_log(usage_log)
        
        return str(usage_log.id)
    
    async def _calculate_costs(self, usage_log: LLMUsageLog):
        """Calculate costs for the LLM usage."""
        if not usage_log.input_tokens and not usage_log.output_tokens:
            return
        
        # Get pricing for the model
        pricing = await self._get_model_pricing(usage_log.llm_provider, usage_log.model_name)
        
        if pricing:
            input_cost = 0
            output_cost = 0
            
            if usage_log.input_tokens and pricing.get('input'):
                input_cost = (usage_log.input_tokens / 1000) * pricing['input']
            
            if usage_log.output_tokens and pricing.get('output'):
                output_cost = (usage_log.output_tokens / 1000) * pricing['output']
            
            usage_log.input_cost = Decimal(str(input_cost))
            usage_log.output_cost = Decimal(str(output_cost))
            usage_log.total_cost = Decimal(str(input_cost + output_cost))
    
    async def _get_model_pricing(self, provider: str, model: str) -> Optional[Dict[str, float]]:
        """Get pricing for a specific model."""
        
        # Check cache first
        cache_key = f"{provider}:{model}"
        if cache_key in self.pricing_cache:
            return self.pricing_cache[cache_key]
        
        # Query database for pricing
        try:
            async with AsyncSessionLocal() as session:
                query = text("""
                    SELECT input_cost_per_1k_tokens, output_cost_per_1k_tokens
                    FROM llm_model_pricing
                    WHERE provider = :provider 
                    AND model_name = :model
                    AND is_active = true
                    AND effective_from <= NOW()
                    AND (effective_to IS NULL OR effective_to > NOW())
                    ORDER BY effective_from DESC
                    LIMIT 1
                """)
                
                result = await session.execute(query, {
                    'provider': provider,
                    'model': model
                })
                
                row = result.fetchone()
                if row:
                    pricing = {
                        'input': float(row[0]),
                        'output': float(row[1])
                    }
                    self.pricing_cache[cache_key] = pricing
                    return pricing
        
        except Exception as e:
            logger.warning(f"Failed to get model pricing from database: {e}")
        
        # Fall back to default pricing
        default = self.default_pricing.get(provider, {}).get(model)
        if default:
            self.pricing_cache[cache_key] = default
            return default
        
        logger.warning(f"No pricing found for {provider}/{model}")
        return None
    
    async def _save_usage_log(self, usage_log: LLMUsageLog):
        """Save usage log to database."""
        try:
            async with AsyncSessionLocal() as session:
                session.add(usage_log)
                await session.commit()
                logger.debug(f"Saved LLM usage log: {usage_log.id}")
                
        except Exception as e:
            logger.error(f"Failed to save LLM usage log: {e}")
    
    def _sanitize_data(self, data: Optional[Dict[str, Any]], max_length: int = 5000) -> Optional[Dict[str, Any]]:
        """Sanitize and truncate request/response data for storage."""
        if not data:
            return None
        
        try:
            # Remove sensitive fields
            sanitized = {k: v for k, v in data.items() if k.lower() not in [
                'api_key', 'token', 'password', 'secret', 'authorization'
            ]}
            
            # Truncate if too long
            data_str = json.dumps(sanitized)
            if len(data_str) > max_length:
                # Keep the structure but truncate content
                return {
                    'truncated': True,
                    'original_length': len(data_str),
                    'sample': data_str[:max_length//2] + '...' + data_str[-max_length//2:]
                }
            
            return sanitized
            
        except Exception as e:
            logger.warning(f"Failed to sanitize data: {e}")
            return {'error': 'failed_to_sanitize'}
    
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
        feature_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate usage report with filters."""
        
        try:
            async with AsyncSessionLocal() as session:
                # Build dynamic query
                conditions = ["1=1"]
                params = {}
                
                if client_account_id:
                    conditions.append("client_account_id = :client_account_id")
                    params['client_account_id'] = client_account_id
                
                if engagement_id:
                    conditions.append("engagement_id = :engagement_id")
                    params['engagement_id'] = engagement_id
                
                if user_id:
                    conditions.append("user_id = :user_id")
                    params['user_id'] = user_id
                
                if start_date:
                    conditions.append("created_at >= :start_date")
                    params['start_date'] = start_date
                
                if end_date:
                    conditions.append("created_at <= :end_date")
                    params['end_date'] = end_date
                
                if provider:
                    conditions.append("llm_provider = :provider")
                    params['provider'] = provider
                
                if model:
                    conditions.append("model_name = :model")
                    params['model'] = model
                
                if page_context:
                    conditions.append("page_context = :page_context")
                    params['page_context'] = page_context
                
                if feature_context:
                    conditions.append("feature_context = :feature_context")
                    params['feature_context'] = feature_context
                
                where_clause = " AND ".join(conditions)
                
                # Summary query
                summary_query = text(f"""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(*) FILTER (WHERE success = true) as successful_requests,
                        COUNT(*) FILTER (WHERE success = false) as failed_requests,
                        COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                        COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                        COALESCE(SUM(total_tokens), 0) as total_tokens,
                        COALESCE(SUM(total_cost), 0) as total_cost,
                        COALESCE(AVG(response_time_ms), 0) as avg_response_time_ms,
                        MIN(created_at) as first_request,
                        MAX(created_at) as last_request
                    FROM llm_usage_logs
                    WHERE {where_clause}
                """)
                
                summary_result = await session.execute(summary_query, params)
                summary = summary_result.fetchone()
                
                # Breakdown by provider/model
                breakdown_query = text(f"""
                    SELECT 
                        llm_provider,
                        model_name,
                        COUNT(*) as requests,
                        COALESCE(SUM(total_tokens), 0) as tokens,
                        COALESCE(SUM(total_cost), 0) as cost
                    FROM llm_usage_logs
                    WHERE {where_clause}
                    GROUP BY llm_provider, model_name
                    ORDER BY cost DESC
                """)
                
                breakdown_result = await session.execute(breakdown_query, params)
                breakdown = [dict(row) for row in breakdown_result]
                
                # Daily usage trend
                daily_query = text(f"""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as requests,
                        COALESCE(SUM(total_tokens), 0) as tokens,
                        COALESCE(SUM(total_cost), 0) as cost
                    FROM llm_usage_logs
                    WHERE {where_clause}
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 30
                """)
                
                daily_result = await session.execute(daily_query, params)
                daily_usage = [dict(row) for row in daily_result]
                
                return {
                    'summary': {
                        'total_requests': summary[0],
                        'successful_requests': summary[1],
                        'failed_requests': summary[2],
                        'success_rate': (summary[1] / summary[0] * 100) if summary[0] > 0 else 0,
                        'total_input_tokens': summary[3],
                        'total_output_tokens': summary[4],
                        'total_tokens': summary[5],
                        'total_cost': float(summary[6]),
                        'avg_response_time_ms': float(summary[7]),
                        'period': {
                            'start': summary[8].isoformat() if summary[8] else None,
                            'end': summary[9].isoformat() if summary[9] else None
                        }
                    },
                    'breakdown_by_model': breakdown,
                    'daily_usage': daily_usage,
                    'filters_applied': {
                        'client_account_id': client_account_id,
                        'engagement_id': engagement_id,
                        'user_id': user_id,
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None,
                        'provider': provider,
                        'model': model,
                        'page_context': page_context,
                        'feature_context': feature_context
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate usage report: {e}")
            raise
    
    async def initialize_default_pricing(self):
        """Initialize default pricing in the database."""
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                
                for provider, models in self.default_pricing.items():
                    for model_name, pricing in models.items():
                        # Check if pricing already exists
                        existing = await session.execute(
                            text("""
                                SELECT id FROM llm_model_pricing 
                                WHERE provider = :provider AND model_name = :model_name AND is_active = true
                            """),
                            {'provider': provider, 'model_name': model_name}
                        )
                        
                        if not existing.fetchone():
                            pricing_record = LLMModelPricing(
                                provider=provider,
                                model_name=model_name,
                                input_cost_per_1k_tokens=Decimal(str(pricing['input'])),
                                output_cost_per_1k_tokens=Decimal(str(pricing['output'])),
                                effective_from=now,
                                is_active=True,
                                source='default_initialization',
                                notes='Default pricing from service initialization'
                            )
                            session.add(pricing_record)
                
                await session.commit()
                logger.info("Initialized default LLM pricing")
                
        except Exception as e:
            logger.error(f"Failed to initialize default pricing: {e}")


# Global tracker instance
llm_tracker = LLMUsageTracker() 