"""
Intelligent Flow Processing Agent
Single agent with comprehensive knowledge and tools for flow analysis and routing.
Replaces the complex multi-agent system with a streamlined, efficient approach.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FlowIntelligenceResult:
    """Result from intelligent flow analysis"""
    flow_id: str
    flow_type: str
    current_phase: str
    phase_status: str
    specific_issues: List[str]
    user_actions: List[str]
    system_actions: List[str]
    routing_decision: str
    confidence: float
    reasoning: str
    estimated_completion_time: int
    success: bool = True
    error_message: Optional[str] = None

class IntelligentFlowAgent:
    """Single intelligent agent for flow processing with comprehensive knowledge"""
    
    def __init__(self):
        """Initialize the intelligent flow agent"""
        pass
    
    async def process_flow_intelligence(self, flow_id: str, user_context: Dict[str, Any] = None) -> FlowIntelligenceResult:
        """Process flow with intelligent analysis and routing"""
        try:
            logger.info(f"🧠 INTELLIGENT FLOW AGENT: Starting analysis for flow {flow_id}")
            
            # Get proper context
            context_info = await self._extract_context(flow_id)
            
            # Perform comprehensive analysis
            analysis_result = await self._analyze_flow_comprehensive(flow_id, context_info)
            
            # Make intelligent routing decision
            routing_result = await self._make_intelligent_routing(analysis_result)
            
            logger.info(f"🧠 INTELLIGENT ANALYSIS COMPLETE: {flow_id} -> {routing_result.routing_decision}")
            return routing_result
            
        except Exception as e:
            logger.error(f"❌ INTELLIGENT AGENT ERROR: {flow_id} - {str(e)}")
            return FlowIntelligenceResult(
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="unknown",
                phase_status="error",
                specific_issues=[f"Analysis failed: {str(e)}"],
                user_actions=["Contact support for assistance"],
                system_actions=["Log error and retry analysis"],
                routing_decision="/discovery/enhanced-dashboard",
                confidence=0.1,
                reasoning=f"Analysis error: {str(e)}",
                estimated_completion_time=0,
                success=False,
                error_message=str(e)
            )
    
    async def _extract_context(self, flow_id: str) -> Dict[str, Any]:
        """Extract proper context for flow operations"""
        try:
            from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            
            # Create basic context
            context = RequestContext(
                client_account_id="dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                engagement_id="ce27e7b1-2ac6-4b74-8dd5-b52d542a1669",
                user_id=None,
                session_id=None
            )
            
            async with AsyncSessionLocal() as session:
                handler = FlowManagementHandler(session, context)
                flow_status = await handler.get_flow_status(flow_id)
                
                return {
                    "client_account_id": flow_status.get("client_account_id", context.client_account_id),
                    "engagement_id": flow_status.get("engagement_id", context.engagement_id),
                    "flow_status": flow_status
                }
                
        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_flow_comprehensive(self, flow_id: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive flow analysis using real services"""
        try:
            from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            
            # Create context from extracted info
            context = RequestContext(
                client_account_id=context_info.get("client_account_id", "dfea7406-1575-4348-a0b2-2770cbe2d9f9"),
                engagement_id=context_info.get("engagement_id", "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"),
                user_id=None,
                session_id=None
            )
            
            async with AsyncSessionLocal() as session:
                # Get flow status
                handler = FlowManagementHandler(session, context)
                flow_status = await handler.get_flow_status(flow_id)
                
                # Analyze data import status specifically
                current_phase = "data_import"
                raw_records = flow_status.get("raw_data", {}).get("record_count", 0) if flow_status.get("raw_data") else 0
                
                # Determine specific issues and actions
                if raw_records == 0:
                    return {
                        "flow_type": "discovery",
                        "current_phase": current_phase,
                        "phase_status": "INCOMPLETE",
                        "raw_records": raw_records,
                        "specific_issue": "No data records found",
                        "user_action": "Upload data file with asset information",
                        "system_action": "Process uploaded data and create records",
                        "navigation": "/discovery/data-import",
                        "confidence": 0.95
                    }
                elif raw_records < 5:
                    return {
                        "flow_type": "discovery",
                        "current_phase": current_phase,
                        "phase_status": "INCOMPLETE",
                        "raw_records": raw_records,
                        "specific_issue": f"Insufficient data ({raw_records} records, need 5+)",
                        "user_action": "Upload larger data file with more records",
                        "system_action": "Guide user through data upload process",
                        "navigation": "/discovery/data-import",
                        "confidence": 0.90
                    }
                else:
                    return {
                        "flow_type": "discovery",
                        "current_phase": current_phase,
                        "phase_status": "PROCESSING",
                        "raw_records": raw_records,
                        "specific_issue": f"Data uploaded ({raw_records} records) but processing incomplete",
                        "user_action": "No user action required",
                        "system_action": "Trigger background data processing",
                        "navigation": f"/discovery/enhanced-dashboard?flow_id={flow_id}&action=processing",
                        "confidence": 0.85
                    }
                
        except Exception as e:
            logger.error(f"Flow analysis failed: {e}")
            return {"error": str(e)}
    
    async def _make_intelligent_routing(self, analysis_result: Dict[str, Any]) -> FlowIntelligenceResult:
        """Make intelligent routing decision based on analysis"""
        try:
            if "error" in analysis_result:
                return FlowIntelligenceResult(
                    flow_id=analysis_result.get("flow_id", "unknown"),
                    flow_type="discovery",
                    current_phase="unknown",
                    phase_status="error",
                    specific_issues=[f"Analysis error: {analysis_result['error']}"],
                    user_actions=["Retry analysis"],
                    system_actions=["Fix analysis system"],
                    routing_decision="/discovery/enhanced-dashboard",
                    confidence=0.1,
                    reasoning=f"Analysis failed: {analysis_result['error']}",
                    estimated_completion_time=0,
                    success=False,
                    error_message=analysis_result["error"]
                )
            
            # Extract analysis results
            flow_type = analysis_result.get("flow_type", "discovery")
            current_phase = analysis_result.get("current_phase", "data_import")
            phase_status = analysis_result.get("phase_status", "INCOMPLETE")
            specific_issue = analysis_result.get("specific_issue", "Unknown issue")
            user_action = analysis_result.get("user_action", "No action specified")
            system_action = analysis_result.get("system_action", "No action specified")
            navigation = analysis_result.get("navigation", "/discovery/enhanced-dashboard")
            confidence = analysis_result.get("confidence", 0.8)
            raw_records = analysis_result.get("raw_records", 0)
            
            # Build comprehensive routing result
            return FlowIntelligenceResult(
                flow_id=analysis_result.get("flow_id", "unknown"),
                flow_type=flow_type,
                current_phase=current_phase,
                phase_status=phase_status,
                specific_issues=[specific_issue],
                user_actions=[user_action],
                system_actions=[system_action],
                routing_decision=navigation,
                confidence=confidence,
                reasoning=f"Analyzed {current_phase} phase: {specific_issue} (Records: {raw_records})",
                estimated_completion_time=5,  # Fast single-agent analysis
                success=True
            )
            
        except Exception as e:
            logger.error(f"Routing decision failed: {e}")
            return FlowIntelligenceResult(
                flow_id="unknown",
                flow_type="discovery",
                current_phase="unknown",
                phase_status="routing_error",
                specific_issues=[f"Routing failed: {str(e)}"],
                user_actions=["Retry routing"],
                system_actions=["Fix routing system"],
                routing_decision="/discovery/enhanced-dashboard",
                confidence=0.1,
                reasoning=f"Routing error: {str(e)}",
                estimated_completion_time=0,
                success=False,
                error_message=str(e)
            ) 