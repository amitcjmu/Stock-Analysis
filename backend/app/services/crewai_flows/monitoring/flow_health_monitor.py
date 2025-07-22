"""
Flow Health Monitoring
Monitors flow execution health, detects hanging flows, and provides auto-recovery
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Set

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class FlowHealthStatus(Enum):
    """Health status for flows"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    HANGING = "hanging"
    FAILED = "failed"


class FlowHealthMonitor:
    """
    Monitors flow health and provides recovery mechanisms
    """
    
    def __init__(self):
        self.monitored_flows: Set[str] = set()
        self.health_metrics: Dict[str, Dict[str, Any]] = {}
        self.phase_timeouts = {
            "data_import_validation": timedelta(minutes=15),
            "field_mapping": timedelta(minutes=30),
            "data_cleansing": timedelta(minutes=20),
            "asset_inventory": timedelta(minutes=25),
            "dependency_analysis": timedelta(minutes=30),
            "tech_debt_assessment": timedelta(minutes=20)
        }
        self.monitoring_interval = 60  # seconds
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Health monitoring already running")
            return
        
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🏥 Flow health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring loop"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("🛑 Flow health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_all_flows()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_all_flows(self):
        """Check health of all active flows"""
        async with AsyncSessionLocal() as db:
            # Get all active flows
            active_statuses = ["initialized", "processing", "waiting_for_approval"]
            
            # Check discovery flows
            discovery_query = select(DiscoveryFlow).where(
                DiscoveryFlow.status.in_(active_statuses)
            )
            discovery_result = await db.execute(discovery_query)
            discovery_flows = discovery_result.scalars().all()
            
            # Check master flows
            master_query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_status.in_(active_statuses)
            )
            master_result = await db.execute(master_query)
            master_flows = master_result.scalars().all()
            
            # Monitor each flow
            for flow in discovery_flows:
                await self._monitor_flow(flow, "discovery", db)
            
            for flow in master_flows:
                await self._monitor_flow(flow, "master", db)
    
    async def _monitor_flow(self, flow: Any, flow_type: str, db):
        """Monitor individual flow health"""
        flow_id = flow.flow_id
        
        try:
            # Calculate health metrics
            health_status = await self._calculate_health_status(flow, flow_type)
            
            # Store metrics
            self.health_metrics[flow_id] = {
                "flow_type": flow_type,
                "status": health_status,
                "last_check": datetime.utcnow(),
                "phase": flow.current_phase if hasattr(flow, 'current_phase') else None,
                "duration": self._calculate_duration(flow),
                "progress": flow.progress_percentage if hasattr(flow, 'progress_percentage') else 0
            }
            
            # Take action based on health status
            if health_status == FlowHealthStatus.HANGING:
                await self._handle_hanging_flow(flow, flow_type, db)
            elif health_status == FlowHealthStatus.CRITICAL:
                await self._handle_critical_flow(flow, flow_type, db)
            elif health_status == FlowHealthStatus.FAILED:
                await self._handle_failed_flow(flow, flow_type, db)
                
        except Exception as e:
            logger.error(f"Error monitoring flow {flow_id}: {e}")
    
    def _get_flow_status(self, flow: Any, flow_type: str) -> str:
        """Get the correct status field based on flow type"""
        if flow_type == "discovery":
            return flow.status
        elif flow_type == "master":
            return flow.flow_status
        else:
            return getattr(flow, 'status', getattr(flow, 'flow_status', 'unknown'))
    
    def _set_flow_status(self, flow: Any, flow_type: str, status: str):
        """Set the correct status field based on flow type"""
        if flow_type == "discovery":
            flow.status = status
        elif flow_type == "master":
            flow.flow_status = status
        else:
            # Try both fields
            if hasattr(flow, 'status'):
                flow.status = status
            elif hasattr(flow, 'flow_status'):
                flow.flow_status = status

    async def _calculate_health_status(self, flow: Any, flow_type: str) -> FlowHealthStatus:
        """Calculate health status for a flow"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Check if flow is failed
        current_status = self._get_flow_status(flow, flow_type)
        if current_status in ["failed", "error", "cancelled"]:
            return FlowHealthStatus.FAILED
        
        # Check last update time
        last_update = flow.updated_at if hasattr(flow, 'updated_at') else flow.created_at
        # Handle timezone-aware/naive datetime comparison
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        time_since_update = now - last_update
        
        # Check phase timeout
        current_phase = flow.current_phase if hasattr(flow, 'current_phase') else None
        if current_phase and current_phase in self.phase_timeouts:
            phase_timeout = self.phase_timeouts[current_phase]
            if time_since_update > phase_timeout:
                return FlowHealthStatus.HANGING
        
        # Check overall timeout
        created_at = flow.created_at
        # Handle timezone-aware/naive datetime comparison
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        total_duration = now - created_at
        
        if total_duration > timedelta(hours=2):
            return FlowHealthStatus.CRITICAL
        elif total_duration > timedelta(hours=1):
            return FlowHealthStatus.WARNING
        
        # Check progress stagnation
        if hasattr(flow, 'progress_percentage'):
            # Would need to track progress history for this
            # For now, just check if progress is very low after long time
            if flow.progress_percentage < 20 and total_duration > timedelta(minutes=30):
                return FlowHealthStatus.WARNING
        
        return FlowHealthStatus.HEALTHY
    
    async def _handle_hanging_flow(self, flow: Any, flow_type: str, db):
        """Handle a hanging flow"""
        flow_id = flow.flow_id
        logger.warning(f"🚨 Detected hanging flow: {flow_id}")
        
        try:
            # Add to hanging flows tracking
            if flow_id not in self.monitored_flows:
                self.monitored_flows.add(flow_id)
                
                # Log the issue
                await self._log_health_event(
                    flow_id,
                    "hanging_detected",
                    {
                        "phase": flow.current_phase if hasattr(flow, 'current_phase') else None,
                        "duration": str(self._calculate_duration(flow)),
                        "last_update": str(flow.updated_at if hasattr(flow, 'updated_at') else flow.created_at)
                    }
                )
                
                # Attempt auto-recovery
                if await self._should_auto_recover(flow, flow_type):
                    await self._attempt_auto_recovery(flow, flow_type, db)
                
        except Exception as e:
            logger.error(f"Error handling hanging flow {flow_id}: {e}")
    
    async def _handle_critical_flow(self, flow: Any, flow_type: str, db):
        """Handle a flow in critical state"""
        flow_id = flow.flow_id
        logger.warning(f"⚠️ Flow in critical state: {flow_id}")
        
        await self._log_health_event(
            flow_id,
            "critical_state",
            {
                "duration": str(self._calculate_duration(flow)),
                "progress": flow.progress_percentage if hasattr(flow, 'progress_percentage') else 0
            }
        )
    
    async def _handle_failed_flow(self, flow: Any, flow_type: str, db):
        """Handle a failed flow"""
        flow_id = flow.flow_id
        logger.error(f"❌ Failed flow detected: {flow_id}")
        
        await self._log_health_event(
            flow_id,
            "flow_failed",
            {
                "status": self._get_flow_status(flow, flow_type),
                "phase": flow.current_phase if hasattr(flow, 'current_phase') else None,
                "errors": flow.error_details if hasattr(flow, 'error_details') else None
            }
        )
    
    async def _should_auto_recover(self, flow: Any, flow_type: str) -> bool:
        """Determine if flow should be auto-recovered"""
        # Don't auto-recover if waiting for user approval
        current_status = self._get_flow_status(flow, flow_type)
        if current_status == "waiting_for_approval":
            return False
        
        # Don't auto-recover if already attempted recently
        flow_id = flow.flow_id
        if flow_id in self.health_metrics:
            last_recovery = self.health_metrics[flow_id].get("last_recovery_attempt")
            if last_recovery and (datetime.utcnow() - last_recovery) < timedelta(minutes=30):
                return False
        
        return True
    
    async def _attempt_auto_recovery(self, flow: Any, flow_type: str, db):
        """Attempt to auto-recover a hanging flow"""
        flow_id = flow.flow_id
        logger.info(f"🔧 Attempting auto-recovery for flow: {flow_id}")
        
        try:
            # Update last recovery attempt
            if flow_id not in self.health_metrics:
                self.health_metrics[flow_id] = {}
            self.health_metrics[flow_id]["last_recovery_attempt"] = datetime.utcnow()
            
            # Recovery strategy based on phase
            current_phase = flow.current_phase if hasattr(flow, 'current_phase') else None
            current_status = self._get_flow_status(flow, flow_type)
            
            if current_phase == "field_mapping" and current_status == "processing":
                # Common issue: field mapping hanging on LLM call
                # Force transition to waiting_for_approval
                self._set_flow_status(flow, flow_type, "waiting_for_approval")
                if hasattr(flow, 'awaiting_user_approval'):
                    flow.awaiting_user_approval = True
                await db.commit()
                
                logger.info(f"✅ Auto-recovered flow {flow_id} by forcing field mapping approval state")
                
            elif current_phase in ["dependency_analysis", "tech_debt_assessment"]:
                # These phases can be skipped if hanging
                self._set_flow_status(flow, flow_type, "completed")
                if hasattr(flow, 'progress_percentage'):
                    flow.progress_percentage = 100
                await db.commit()
                
                logger.info(f"✅ Auto-recovered flow {flow_id} by completing with partial results")
                
            else:
                # General recovery: mark as failed with recovery flag
                self._set_flow_status(flow, flow_type, "failed")
                if hasattr(flow, 'error_details'):
                    flow.error_details = {"auto_recovery": "Flow was hanging and auto-recovery failed"}
                await db.commit()
                
                logger.warning(f"⚠️ Auto-recovery failed for flow {flow_id}, marked as failed")
                
        except Exception as e:
            logger.error(f"Error during auto-recovery for flow {flow_id}: {e}")
    
    def _calculate_duration(self, flow: Any) -> timedelta:
        """Calculate flow duration"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        created_at = flow.created_at
        # Handle timezone-aware/naive datetime comparison
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return now - created_at
    
    async def _log_health_event(self, flow_id: str, event_type: str, details: Dict[str, Any]):
        """Log health monitoring event"""
        logger.info(f"📊 Health Event - Flow: {flow_id}, Type: {event_type}, Details: {json.dumps(details)}")
        
        # Could store in database for historical tracking
        # For now, just log
    
    def get_flow_health(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get health metrics for a specific flow"""
        return self.health_metrics.get(flow_id)
    
    def get_all_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for all monitored flows"""
        return {
            "monitored_flows": len(self.health_metrics),
            "hanging_flows": len([
                f for f in self.health_metrics.values()
                if f.get("status") == FlowHealthStatus.HANGING
            ]),
            "critical_flows": len([
                f for f in self.health_metrics.values()
                if f.get("status") == FlowHealthStatus.CRITICAL
            ]),
            "failed_flows": len([
                f for f in self.health_metrics.values()
                if f.get("status") == FlowHealthStatus.FAILED
            ]),
            "flows": self.health_metrics
        }
    
    async def force_recover_flow(self, flow_id: str, recovery_action: str = "restart") -> Dict[str, Any]:
        """Force recovery action on a flow"""
        async with AsyncSessionLocal() as db:
            # Try to find the flow
            discovery_flow = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            )
            flow = discovery_flow.scalar_one_or_none()
            
            if not flow:
                master_flow = await db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id == flow_id
                    )
                )
                flow = master_flow.scalar_one_or_none()
            
            if not flow:
                return {"success": False, "error": "Flow not found"}
            
            # Determine flow type
            flow_type = "discovery" if hasattr(flow, 'status') else "master"
            
            if recovery_action == "restart":
                # Reset flow to last checkpoint
                self._set_flow_status(flow, flow_type, "processing")
                if hasattr(flow, 'updated_at'):
                    flow.updated_at = datetime.utcnow()
                await db.commit()
                return {"success": True, "action": "restart", "new_status": "processing"}
                
            elif recovery_action == "complete":
                # Force complete the flow
                self._set_flow_status(flow, flow_type, "completed")
                if hasattr(flow, 'progress_percentage'):
                    flow.progress_percentage = 100
                if hasattr(flow, 'updated_at'):
                    flow.updated_at = datetime.utcnow()
                await db.commit()
                return {"success": True, "action": "complete", "new_status": "completed"}
                
            elif recovery_action == "fail":
                # Mark flow as failed
                self._set_flow_status(flow, flow_type, "failed")
                if hasattr(flow, 'error_details'):
                    flow.error_details = {"reason": "Manual intervention - marked as failed"}
                if hasattr(flow, 'updated_at'):
                    flow.updated_at = datetime.utcnow()
                await db.commit()
                return {"success": True, "action": "fail", "new_status": "failed"}
                
            else:
                return {"success": False, "error": f"Unknown recovery action: {recovery_action}"}


# Global instance
flow_health_monitor = FlowHealthMonitor()