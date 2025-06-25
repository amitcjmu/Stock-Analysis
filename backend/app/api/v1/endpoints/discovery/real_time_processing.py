"""
Real-Time Processing API Endpoints
Provides live updates during discovery flow execution including validation, progress, and agent insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime, timedelta
import asyncio

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.agent_ui_bridge import agent_ui_bridge
from app.schemas.discovery_schemas import (
    ProcessingStatusResponse, 
    ValidationStatusResponse,
    ProcessingUpdate,
    ValidationStatus,
    AgentStatus,
    SecurityScan,
    FormatValidation,
    DataQuality
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flow", tags=["real-time-processing"])

@router.get("/{flow_id}/processing-status")
async def get_processing_status(
    flow_id: str,
    phase: Optional[str] = Query(None, description="Optional phase filter"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> ProcessingStatusResponse:
    """
    Get real-time processing status for a discovery flow
    """
    try:
        logger.info(f"🔍 Getting processing status for flow {flow_id}")
        
        # Get flow from database
        flow_repo = DiscoveryFlowRepository(db, context.client)
        flow = await flow_repo.get_discovery_flow_by_id(flow_id)
        
        if not flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Get agent status from agent-UI bridge
        agent_status = {}
        try:
            # Get agent insights for this flow
            insights = agent_ui_bridge.get_insights_for_page(f"flow_{flow_id}")
            
            # Get agent questions/clarifications
            questions = agent_ui_bridge.get_questions_for_page(f"flow_{flow_id}")
            
            # Build agent status from available data
            unique_agents = set()
            for insight in insights:
                if insight.get('agent_name'):
                    unique_agents.add(insight['agent_name'])
            
            for question in questions:
                if question.get('agent_name'):
                    unique_agents.add(question['agent_name'])
            
            # Add default agents if none found
            if not unique_agents:
                unique_agents = {'Data Import Agent', 'Validation Agent', 'Asset Intelligence Agent'}
            
            # Create status for each agent
            for agent_name in unique_agents:
                agent_insights = [i for i in insights if i.get('agent_name') == agent_name]
                agent_questions = [q for q in questions if q.get('agent_name') == agent_name and not q.get('is_resolved', False)]
                
                # Determine agent status based on flow phase and recent activity
                if flow.status == 'active' and flow.current_phase != 'completed':
                    agent_status_val = 'processing'
                elif flow.status == 'completed':
                    agent_status_val = 'completed'
                else:
                    agent_status_val = 'idle'
                
                # Calculate confidence from recent insights
                recent_insights = [i for i in agent_insights if i.get('confidence')]
                avg_confidence = 0.8  # Default
                if recent_insights:
                    confidence_values = []
                    for insight in recent_insights:
                        conf_str = insight.get('confidence', 'medium')
                        if conf_str == 'high':
                            confidence_values.append(0.9)
                        elif conf_str == 'medium':
                            confidence_values.append(0.7)
                        else:
                            confidence_values.append(0.5)
                    if confidence_values:
                        avg_confidence = sum(confidence_values) / len(confidence_values)
                
                agent_status[agent_name] = AgentStatus(
                    status=agent_status_val,
                    confidence=avg_confidence,
                    insights_generated=len(agent_insights),
                    clarifications_pending=len(agent_questions)
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Could not get agent status: {e}")
            # Fallback agent status
            agent_status = {
                'Data Import Agent': AgentStatus(
                    status='idle' if flow.status == 'completed' else 'processing',
                    confidence=0.8,
                    insights_generated=0,
                    clarifications_pending=0
                )
            }
        
        # Calculate validation status
        validation_status = ValidationStatus(
            format_valid=True,  # Default - would be enhanced with actual validation
            security_scan_passed=True,
            data_quality_score=0.85,
            issues_found=[]
        )
        
        # Generate recent updates based on flow state
        recent_updates = []
        try:
            # Create synthetic updates based on flow progress
            if flow.progress_percentage > 0:
                recent_updates.append(ProcessingUpdate(
                    id=str(uuid.uuid4()),
                    timestamp=(datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    phase=flow.current_phase,
                    agent_name='Data Import Agent',
                    update_type='progress',
                    message=f'Processing {flow.current_phase} phase - {flow.progress_percentage:.1f}% complete',
                    details={
                        'records_processed': int(flow.progress_percentage * 10),  # Mock calculation
                        'records_total': 1000,  # Mock total
                        'confidence_score': 0.8
                    }
                ))
            
            # Add insights as updates
            for insight in insights[-3:]:  # Last 3 insights
                recent_updates.append(ProcessingUpdate(
                    id=str(uuid.uuid4()),
                    timestamp=insight.get('created_at', datetime.utcnow().isoformat()),
                    phase=flow.current_phase,
                    agent_name=insight.get('agent_name', 'Unknown Agent'),
                    update_type='insight',
                    message=insight.get('title', 'New insight generated'),
                    details={
                        'confidence_score': 0.8 if insight.get('confidence') == 'high' else 0.6
                    }
                ))
                
        except Exception as e:
            logger.warning(f"⚠️ Could not generate recent updates: {e}")
        
        # Estimate completion time
        estimated_completion = None
        if flow.status == 'active' and flow.progress_percentage > 0:
            # Simple estimation based on current progress
            remaining_percentage = 100 - flow.progress_percentage
            if remaining_percentage > 0:
                # Assume 1% per minute (mock calculation)
                estimated_minutes = remaining_percentage
                estimated_completion = (datetime.utcnow() + timedelta(minutes=estimated_minutes)).isoformat()
        
        response = ProcessingStatusResponse(
            flow_id=flow_id,
            phase=flow.current_phase,
            status=flow.status,
            progress_percentage=flow.progress_percentage,
            records_processed=int(flow.progress_percentage * 10) if flow.progress_percentage else 0,
            records_total=1000,  # Mock - would come from actual data
            records_failed=0,  # Mock - would come from actual validation
            validation_status=validation_status,
            agent_status=agent_status,
            recent_updates=recent_updates,
            estimated_completion=estimated_completion,
            last_update=flow.updated_at.isoformat() if flow.updated_at else datetime.utcnow().isoformat()
        )
        
        logger.info(f"✅ Processing status retrieved for flow {flow_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting processing status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")

@router.get("/{flow_id}/validation-status")
async def get_validation_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> ValidationStatusResponse:
    """
    Get real-time validation status for a discovery flow
    """
    try:
        logger.info(f"🔍 Getting validation status for flow {flow_id}")
        
        # Get flow from database
        flow_repo = DiscoveryFlowRepository(db, context.client)
        flow = await flow_repo.get_discovery_flow_by_id(flow_id)
        
        if not flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Mock validation data - in real implementation, this would come from actual validation services
        security_scan = SecurityScan(
            status='passed',
            issues=[],
            scan_time=datetime.utcnow().isoformat(),
            threat_level='low'
        )
        
        format_validation = FormatValidation(
            status='passed',
            errors=[],
            warnings=[],
            validation_time=datetime.utcnow().isoformat()
        )
        
        data_quality = DataQuality(
            score=0.85,
            metrics={
                'completeness': 0.9,
                'accuracy': 0.8,
                'consistency': 0.85,
                'validity': 0.9
            },
            issues=[],
            assessment_time=datetime.utcnow().isoformat()
        )
        
        # Check for any validation issues in agent insights
        insights = agent_ui_bridge.get_insights_for_page(f"flow_{flow_id}")
        validation_insights = [i for i in insights if 'validation' in i.get('insight_type', '').lower()]
        
        if validation_insights:
            # If there are validation insights, there might be issues
            for insight in validation_insights:
                if 'error' in insight.get('title', '').lower() or 'issue' in insight.get('title', '').lower():
                    if 'security' in insight.get('description', '').lower():
                        security_scan.issues.append(insight.get('description', 'Security issue detected'))
                    elif 'format' in insight.get('description', '').lower():
                        format_validation.errors.append(insight.get('description', 'Format error detected'))
                    else:
                        data_quality.issues.append(insight.get('description', 'Data quality issue detected'))
        
        response = ValidationStatusResponse(
            flow_id=flow_id,
            overall_status='passed' if not any([
                security_scan.issues,
                format_validation.errors,
                data_quality.score < 0.7
            ]) else 'failed',
            security_scan=security_scan,
            format_validation=format_validation,
            data_quality=data_quality,
            last_validation=datetime.utcnow().isoformat()
        )
        
        logger.info(f"✅ Validation status retrieved for flow {flow_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting validation status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get validation status: {str(e)}")

@router.post("/{flow_id}/validate")
async def trigger_validation(
    flow_id: str,
    validation_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> Dict[str, Any]:
    """
    Trigger manual validation for a discovery flow
    """
    try:
        validation_type = validation_request.get('validation_type', 'all')
        logger.info(f"🔍 Triggering {validation_type} validation for flow {flow_id}")
        
        # Get flow from database
        flow_repo = DiscoveryFlowRepository(db, context.client)
        flow = await flow_repo.get_discovery_flow_by_id(flow_id)
        
        if not flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Mock validation trigger - in real implementation, this would trigger actual validation services
        validation_results = {
            'validation_id': str(uuid.uuid4()),
            'flow_id': flow_id,
            'validation_type': validation_type,
            'status': 'initiated',
            'message': f'{validation_type.title()} validation started',
            'estimated_completion': (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        }
        
        # Add insight about validation trigger
        agent_ui_bridge.add_agent_insight(
            agent_id="validation_agent",
            agent_name="Validation Agent",
            insight_type="validation",
            page=f"flow_{flow_id}",
            title=f"{validation_type.title()} Validation Triggered",
            description=f"Manual {validation_type} validation initiated by user",
            content={
                'validation_type': validation_type,
                'trigger_time': datetime.utcnow().isoformat(),
                'expected_duration': '2-3 minutes'
            },
            confidence="high",
            priority="medium"
        )
        
        logger.info(f"✅ {validation_type} validation triggered for flow {flow_id}")
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error triggering validation for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger validation: {str(e)}")

@router.get("/{flow_id}/agent-insights")
async def get_agent_insights(
    flow_id: str,
    page_context: Optional[str] = Query(None, description="Page context filter"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> Dict[str, Any]:
    """
    Get real-time agent insights for a discovery flow
    """
    try:
        logger.info(f"🔍 Getting agent insights for flow {flow_id}")
        
        # Get insights from agent-UI bridge
        page_key = page_context if page_context else f"flow_{flow_id}"
        insights = agent_ui_bridge.get_insights_for_page(page_key)
        
        # Enhance insights with flow-specific data
        enhanced_insights = []
        for insight in insights:
            enhanced_insight = insight.copy()
            enhanced_insight['flow_id'] = flow_id
            enhanced_insight['page_context'] = page_context
            
            # Add timestamps if missing
            if 'created_at' not in enhanced_insight:
                enhanced_insight['created_at'] = datetime.utcnow().isoformat()
            
            enhanced_insights.append(enhanced_insight)
        
        response = {
            'success': True,
            'flow_id': flow_id,
            'page_context': page_context,
            'insights': enhanced_insights,
            'total_insights': len(enhanced_insights),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Retrieved {len(enhanced_insights)} insights for flow {flow_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting agent insights for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent insights: {str(e)}") 