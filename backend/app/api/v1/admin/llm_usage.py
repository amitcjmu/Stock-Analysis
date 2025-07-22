"""LLM Usage Tracking API Endpoints

Endpoints for monitoring LLM usage, costs, and generating reports.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.llm_usage import LLMModelPricing, LLMUsageLog, LLMUsageSummary
from app.services.llm_usage_tracker import llm_tracker

router = APIRouter()


class UsageReportRequest(BaseModel):
    """Request model for usage reports."""
    client_account_id: Optional[int] = None
    engagement_id: Optional[int] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    page_context: Optional[str] = None
    feature_context: Optional[str] = None


class ModelPricingCreate(BaseModel):
    """Model for creating/updating pricing."""
    provider: str = Field(..., description="LLM provider name")
    model_name: str = Field(..., description="Model name")
    model_version: Optional[str] = None
    input_cost_per_1k_tokens: float = Field(..., gt=0, description="Cost per 1K input tokens")
    output_cost_per_1k_tokens: float = Field(..., gt=0, description="Cost per 1K output tokens")
    currency: str = Field(default="USD", description="Currency code")
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    source: Optional[str] = None
    notes: Optional[str] = None


@router.get("/usage/report")
async def get_usage_report(
    client_account_id: Optional[int] = Query(None, description="Filter by client account"),
    engagement_id: Optional[int] = Query(None, description="Filter by engagement"),
    user_id: Optional[int] = Query(None, description="Filter by user"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    provider: Optional[str] = Query(None, description="Filter by LLM provider"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    page_context: Optional[str] = Query(None, description="Filter by page context"),
    feature_context: Optional[str] = Query(None, description="Filter by feature context"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive LLM usage report with filtering options.
    
    Returns detailed statistics including:
    - Total requests, tokens, and costs
    - Success rates and performance metrics
    - Breakdown by model and provider
    - Daily usage trends
    """
    try:
        # Default to last 30 days if no date range specified
        if not start_date and not end_date:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        
        report = await llm_tracker.get_usage_report(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            model=model,
            page_context=page_context,
            feature_context=feature_context
        )
        
        return {
            "success": True,
            "data": report,
            "message": "Usage report generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate usage report: {str(e)}")


@router.get("/usage/summary/daily")
async def get_daily_usage_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    client_account_id: Optional[int] = Query(None, description="Filter by client account"),
    engagement_id: Optional[int] = Query(None, description="Filter by engagement"),
    db: AsyncSession = Depends(get_db)
):
    """Get daily usage summary for the specified number of days."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = await llm_tracker.get_usage_report(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": {
                "daily_usage": report["daily_usage"],
                "summary": report["summary"],
                "period_days": days
            },
            "message": f"Daily usage summary for last {days} days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily summary: {str(e)}")


@router.get("/usage/costs/breakdown")
async def get_cost_breakdown(
    client_account_id: Optional[int] = Query(None, description="Filter by client account"),
    engagement_id: Optional[int] = Query(None, description="Filter by engagement"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed cost breakdown by provider, model, and feature."""
    try:
        # Default to current month if no dates specified
        if not start_date:
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        report = await llm_tracker.get_usage_report(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": {
                "breakdown_by_model": report["breakdown_by_model"],
                "total_cost": report["summary"]["total_cost"],
                "total_tokens": report["summary"]["total_tokens"],
                "period": report["summary"]["period"]
            },
            "message": "Cost breakdown generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost breakdown: {str(e)}")


@router.get("/pricing/models")
async def get_model_pricing(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    active_only: bool = Query(True, description="Only return active pricing"),
    db: AsyncSession = Depends(get_db)
):
    """Get current pricing for all LLM models."""
    try:
        from sqlalchemy import and_, or_, select
        
        query = select(LLMModelPricing)
        
        conditions = []
        if provider:
            conditions.append(LLMModelPricing.provider == provider)
        if active_only:
            conditions.append(LLMModelPricing.is_active == True)
            conditions.append(LLMModelPricing.effective_from <= datetime.utcnow())
            conditions.append(
                or_(
                    LLMModelPricing.effective_to.is_(None),
                    LLMModelPricing.effective_to > datetime.utcnow()
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(LLMModelPricing.provider, LLMModelPricing.model_name)
        
        result = await db.execute(query)
        pricing_records = result.scalars().all()
        
        # Convert to dict for response
        pricing_data = []
        for record in pricing_records:
            pricing_data.append({
                "id": str(record.id),
                "provider": record.provider,
                "model_name": record.model_name,
                "model_version": record.model_version,
                "input_cost_per_1k_tokens": float(record.input_cost_per_1k_tokens),
                "output_cost_per_1k_tokens": float(record.output_cost_per_1k_tokens),
                "currency": record.currency,
                "effective_from": record.effective_from.isoformat(),
                "effective_to": record.effective_to.isoformat() if record.effective_to else None,
                "is_active": record.is_active,
                "source": record.source,
                "notes": record.notes
            })
        
        return {
            "success": True,
            "data": pricing_data,
            "message": f"Found {len(pricing_data)} pricing records"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model pricing: {str(e)}")


@router.post("/pricing/models")
async def create_model_pricing(
    pricing: ModelPricingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create or update pricing for an LLM model."""
    try:
        from decimal import Decimal
        
        # Set default effective_from if not provided
        if not pricing.effective_from:
            pricing.effective_from = datetime.utcnow()
        
        # Create new pricing record
        new_pricing = LLMModelPricing(
            provider=pricing.provider,
            model_name=pricing.model_name,
            model_version=pricing.model_version,
            input_cost_per_1k_tokens=Decimal(str(pricing.input_cost_per_1k_tokens)),
            output_cost_per_1k_tokens=Decimal(str(pricing.output_cost_per_1k_tokens)),
            currency=pricing.currency,
            effective_from=pricing.effective_from,
            effective_to=pricing.effective_to,
            is_active=True,
            source=pricing.source or "api_manual_entry",
            notes=pricing.notes
        )
        
        db.add(new_pricing)
        await db.commit()
        await db.refresh(new_pricing)
        
        # Clear pricing cache
        llm_tracker.pricing_cache.clear()
        
        return {
            "success": True,
            "data": {
                "id": str(new_pricing.id),
                "provider": new_pricing.provider,
                "model_name": new_pricing.model_name,
                "created_at": new_pricing.created_at.isoformat()
            },
            "message": "Model pricing created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create model pricing: {str(e)}")


@router.get("/usage/real-time")
async def get_real_time_usage(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    client_account_id: Optional[int] = Query(None, description="Filter by client account"),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time usage statistics for monitoring."""
    try:
        from sqlalchemy import and_, func, select
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query for recent usage
        query = select(
            func.count(LLMUsageLog.id).label('total_requests'),
            func.count(LLMUsageLog.id).filter(LLMUsageLog.success == True).label('successful_requests'),
            func.count(LLMUsageLog.id).filter(LLMUsageLog.success == False).label('failed_requests'),
            func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label('total_tokens'),
            func.coalesce(func.sum(LLMUsageLog.total_cost), 0).label('total_cost'),
            func.coalesce(func.avg(LLMUsageLog.response_time_ms), 0).label('avg_response_time')
        ).where(LLMUsageLog.created_at >= cutoff_time)
        
        if client_account_id:
            query = query.where(LLMUsageLog.client_account_id == client_account_id)
        
        result = await db.execute(query)
        stats = result.fetchone()
        
        # Get usage by hour for trend
        hourly_query = select(
            func.date_trunc('hour', LLMUsageLog.created_at).label('hour'),
            func.count(LLMUsageLog.id).label('requests'),
            func.coalesce(func.sum(LLMUsageLog.total_cost), 0).label('cost')
        ).where(LLMUsageLog.created_at >= cutoff_time)
        
        if client_account_id:
            hourly_query = hourly_query.where(LLMUsageLog.client_account_id == client_account_id)
        
        hourly_query = hourly_query.group_by(func.date_trunc('hour', LLMUsageLog.created_at))
        hourly_query = hourly_query.order_by(func.date_trunc('hour', LLMUsageLog.created_at))
        
        hourly_result = await db.execute(hourly_query)
        hourly_data = [
            {
                "hour": row.hour.isoformat(),
                "requests": row.requests,
                "cost": float(row.cost)
            }
            for row in hourly_result
        ]
        
        return {
            "success": True,
            "data": {
                "period_hours": hours,
                "cutoff_time": cutoff_time.isoformat(),
                "summary": {
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "success_rate": (stats.successful_requests / stats.total_requests * 100) if stats.total_requests > 0 else 0,
                    "total_tokens": stats.total_tokens,
                    "total_cost": float(stats.total_cost),
                    "avg_response_time_ms": float(stats.avg_response_time)
                },
                "hourly_trend": hourly_data
            },
            "message": f"Real-time usage for last {hours} hours"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time usage: {str(e)}")


@router.post("/pricing/initialize")
async def initialize_pricing(db: AsyncSession = Depends(get_db)):
    """Initialize default pricing for common LLM models."""
    try:
        await llm_tracker.initialize_default_pricing()
        
        return {
            "success": True,
            "message": "Default pricing initialized successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize pricing: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for LLM usage tracking."""
    return {
        "success": True,
        "service": "llm_usage_tracking",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "pricing_cache_size": len(llm_tracker.pricing_cache)
    } 