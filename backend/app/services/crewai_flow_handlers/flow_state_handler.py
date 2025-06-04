"""
Flow State Handler for CrewAI Flow Service
Manages flow states, progress tracking, lifecycle management, and memory cleanup.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FlowStateHandler:
    """Handler for managing flow states and lifecycle operations."""
    
    def __init__(self, config):
        self.config = config
        self.active_flows = {}
        self.completed_flows = {}
        self.flow_metrics = {}
    
    def create_flow(self, flow_id: str, flow_state: Any) -> str:
        """Create and register a new flow."""
        try:
            self.active_flows[flow_id] = flow_state
            self.flow_metrics[flow_id] = {
                "created_at": datetime.now().isoformat(),
                "phase_transitions": [],
                "duration_by_phase": {},
                "status": "active"
            }
            
            logger.info(f"Flow {flow_id} created successfully")
            return flow_id
            
        except Exception as e:
            logger.error(f"Failed to create flow {flow_id}: {e}")
            raise
    
    def update_flow_progress(self, flow_id: str, phase: str, progress: float, **kwargs) -> bool:
        """Update flow progress and phase information."""
        if flow_id not in self.active_flows:
            logger.warning(f"Flow {flow_id} not found for progress update")
            return False
        
        try:
            flow_state = self.active_flows[flow_id]
            
            # Update progress
            flow_state.current_phase = phase
            flow_state.progress_percentage = progress
            
            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(flow_state, key):
                    setattr(flow_state, key, value)
            
            # Record phase transition
            self._record_phase_transition(flow_id, phase, progress)
            
            logger.debug(f"Flow {flow_id} progress updated: {phase} ({progress}%)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update flow {flow_id} progress: {e}")
            return False
    
    def complete_flow(self, flow_id: str, final_results: Dict[str, Any]) -> bool:
        """Mark flow as completed and archive it."""
        if flow_id not in self.active_flows:
            logger.warning(f"Flow {flow_id} not found for completion")
            return False
        
        try:
            flow_state = self.active_flows[flow_id]
            flow_state.completed_at = datetime.now()
            flow_state.current_phase = "completed"
            flow_state.progress_percentage = 100.0
            
            # Archive completed flow
            self.completed_flows[flow_id] = {
                "flow_state": flow_state,
                "final_results": final_results,
                "completed_at": datetime.now().isoformat()
            }
            
            # Update metrics
            if flow_id in self.flow_metrics:
                self.flow_metrics[flow_id]["status"] = "completed"
                self.flow_metrics[flow_id]["completed_at"] = datetime.now().isoformat()
                if flow_state.started_at:
                    duration = (flow_state.completed_at - flow_state.started_at).total_seconds()
                    self.flow_metrics[flow_id]["total_duration_seconds"] = duration
            
            # Remove from active flows
            del self.active_flows[flow_id]
            
            logger.info(f"Flow {flow_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete flow {flow_id}: {e}")
            return False
    
    def fail_flow(self, flow_id: str, error_info: Dict[str, Any]) -> bool:
        """Mark flow as failed and archive with error information."""
        if flow_id not in self.active_flows:
            logger.warning(f"Flow {flow_id} not found for failure")
            return False
        
        try:
            flow_state = self.active_flows[flow_id]
            flow_state.current_phase = "failed"
            
            # Archive failed flow
            self.completed_flows[flow_id] = {
                "flow_state": flow_state,
                "error_info": error_info,
                "failed_at": datetime.now().isoformat()
            }
            
            # Update metrics
            if flow_id in self.flow_metrics:
                self.flow_metrics[flow_id]["status"] = "failed"
                self.flow_metrics[flow_id]["failed_at"] = datetime.now().isoformat()
                self.flow_metrics[flow_id]["error_info"] = error_info
            
            # Remove from active flows
            del self.active_flows[flow_id]
            
            logger.warning(f"Flow {flow_id} marked as failed: {error_info}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark flow {flow_id} as failed: {e}")
            return False
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get comprehensive status of a specific flow."""
        # Check active flows
        if flow_id in self.active_flows:
            flow_state = self.active_flows[flow_id]
            metrics = self.flow_metrics.get(flow_id, {})
            
            return {
                "flow_id": flow_id,
                "status": "active",
                "current_phase": flow_state.current_phase,
                "progress_percentage": flow_state.progress_percentage,
                "started_at": flow_state.started_at.isoformat() if flow_state.started_at else None,
                "duration_seconds": (datetime.now() - flow_state.started_at).total_seconds() if flow_state.started_at else None,
                "components_completed": {
                    "data_validation": flow_state.data_validation_complete,
                    "field_mapping": flow_state.field_mapping_complete,
                    "asset_classification": flow_state.asset_classification_complete,
                    "readiness_assessment": flow_state.readiness_assessment_complete
                },
                "phase_transitions": metrics.get("phase_transitions", []),
                "metrics": metrics
            }
        
        # Check completed flows
        if flow_id in self.completed_flows:
            completed_flow = self.completed_flows[flow_id]
            flow_state = completed_flow["flow_state"]
            metrics = self.flow_metrics.get(flow_id, {})
            
            return {
                "flow_id": flow_id,
                "status": "completed" if "completed_at" in completed_flow else "failed",
                "current_phase": flow_state.current_phase,
                "progress_percentage": flow_state.progress_percentage,
                "started_at": flow_state.started_at.isoformat() if flow_state.started_at else None,
                "completed_at": completed_flow.get("completed_at") or completed_flow.get("failed_at"),
                "total_duration_seconds": metrics.get("total_duration_seconds"),
                "final_results": completed_flow.get("final_results"),
                "error_info": completed_flow.get("error_info"),
                "metrics": metrics
            }
        
        return {"flow_id": flow_id, "status": "not_found"}
    
    def get_active_flows_summary(self) -> Dict[str, Any]:
        """Get summary of all active flows."""
        summary = {
            "total_active_flows": len(self.active_flows),
            "flows_by_phase": {},
            "flows": []
        }
        
        for flow_id, flow_state in self.active_flows.items():
            phase = flow_state.current_phase
            
            # Count by phase
            summary["flows_by_phase"][phase] = summary["flows_by_phase"].get(phase, 0) + 1
            
            # Add flow summary
            flow_summary = {
                "flow_id": flow_id,
                "current_phase": phase,
                "progress_percentage": flow_state.progress_percentage,
                "started_at": flow_state.started_at.isoformat() if flow_state.started_at else None,
                "duration_seconds": (datetime.now() - flow_state.started_at).total_seconds() if flow_state.started_at else None
            }
            summary["flows"].append(flow_summary)
        
        return summary
    
    def cleanup_expired_flows(self) -> int:
        """Clean up expired flows based on TTL configuration."""
        current_time = datetime.now()
        ttl_hours = self.config.flow_ttl_hours
        cutoff_time = current_time - timedelta(hours=ttl_hours)
        
        # Find expired active flows
        expired_flow_ids = []
        for flow_id, flow_state in self.active_flows.items():
            if flow_state.started_at and flow_state.started_at < cutoff_time:
                expired_flow_ids.append(flow_id)
        
        # Move expired flows to completed with timeout status
        for flow_id in expired_flow_ids:
            try:
                flow_state = self.active_flows[flow_id]
                
                # Archive expired flow
                self.completed_flows[flow_id] = {
                    "flow_state": flow_state,
                    "error_info": {"reason": "expired", "ttl_hours": ttl_hours},
                    "expired_at": current_time.isoformat()
                }
                
                # Update metrics
                if flow_id in self.flow_metrics:
                    self.flow_metrics[flow_id]["status"] = "expired"
                    self.flow_metrics[flow_id]["expired_at"] = current_time.isoformat()
                
                # Remove from active flows
                del self.active_flows[flow_id]
                
            except Exception as e:
                logger.error(f"Failed to expire flow {flow_id}: {e}")
        
        # Clean up old completed flows (keep for 24 hours)
        completed_cutoff = current_time - timedelta(hours=24)
        old_completed_ids = []
        
        for flow_id, completed_flow in self.completed_flows.items():
            completed_at_str = completed_flow.get("completed_at") or completed_flow.get("failed_at") or completed_flow.get("expired_at")
            if completed_at_str:
                try:
                    completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                    if completed_at < completed_cutoff:
                        old_completed_ids.append(flow_id)
                except ValueError:
                    pass  # Skip invalid timestamps
        
        # Remove old completed flows
        for flow_id in old_completed_ids:
            del self.completed_flows[flow_id]
            if flow_id in self.flow_metrics:
                del self.flow_metrics[flow_id]
        
        total_cleaned = len(expired_flow_ids) + len(old_completed_ids)
        
        if total_cleaned > 0:
            logger.info(f"Cleaned up {total_cleaned} flows ({len(expired_flow_ids)} expired, {len(old_completed_ids)} old)")
        
        return total_cleaned
    
    def _record_phase_transition(self, flow_id: str, phase: str, progress: float):
        """Record phase transition for metrics and monitoring."""
        if flow_id not in self.flow_metrics:
            return
        
        transition = {
            "phase": phase,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
        self.flow_metrics[flow_id]["phase_transitions"].append(transition)
        
        # Calculate phase duration if previous phase exists
        transitions = self.flow_metrics[flow_id]["phase_transitions"]
        if len(transitions) > 1:
            prev_transition = transitions[-2]
            try:
                prev_time = datetime.fromisoformat(prev_transition["timestamp"])
                curr_time = datetime.fromisoformat(transition["timestamp"])
                duration = (curr_time - prev_time).total_seconds()
                
                self.flow_metrics[flow_id]["duration_by_phase"][prev_transition["phase"]] = duration
                
            except ValueError:
                pass  # Skip if timestamp parsing fails
    
    def calculate_readiness_scores(self, flow_state: Any) -> Dict[str, float]:
        """Calculate comprehensive readiness scores for a flow."""
        scores = {
            "data_quality": 0.0,
            "field_mapping": 0.0,
            "asset_coverage": 0.0,
            "overall_readiness": 0.0
        }
        
        try:
            # Data quality score from validation
            if flow_state.data_validation_complete:
                validation_score = flow_state.validated_structure.get("data_quality_score", 0)
                scores["data_quality"] = min(10.0, max(0.0, validation_score))
            
            # Field mapping score
            if flow_state.field_mapping_complete:
                total_fields = len(flow_state.headers)
                mapped_fields = len(flow_state.suggested_field_mappings)
                mapping_ratio = mapped_fields / max(total_fields, 1)
                scores["field_mapping"] = mapping_ratio * 10.0
            
            # Asset coverage score
            if flow_state.asset_classification_complete:
                total_assets = len(flow_state.sample_data)
                classified_assets = len(flow_state.asset_classifications)
                coverage_ratio = classified_assets / max(total_assets, 1)
                
                # Calculate average confidence
                total_confidence = sum(
                    asset.get("confidence_score", 0.7) 
                    for asset in flow_state.asset_classifications
                )
                avg_confidence = total_confidence / max(len(flow_state.asset_classifications), 1)
                
                scores["asset_coverage"] = coverage_ratio * avg_confidence * 10.0
            
            # Overall readiness (weighted average)
            if all([
                flow_state.data_validation_complete, 
                flow_state.field_mapping_complete, 
                flow_state.asset_classification_complete
            ]):
                scores["overall_readiness"] = (
                    scores["data_quality"] * 0.4 +
                    scores["field_mapping"] * 0.3 + 
                    scores["asset_coverage"] * 0.3
                )
            
        except Exception as e:
            logger.error(f"Failed to calculate readiness scores: {e}")
        
        return scores
    
    def format_flow_results(self, flow_state: Any) -> Dict[str, Any]:
        """Format comprehensive flow results for API response."""
        duration = None
        if flow_state.started_at and flow_state.completed_at:
            duration = (flow_state.completed_at - flow_state.started_at).total_seconds()
        
        readiness_scores = self.calculate_readiness_scores(flow_state)
        
        return {
            "status": "completed",
            "flow_type": "discovery",
            "progress": flow_state.progress_percentage,
            "duration_seconds": duration,
            "performance_metrics": {
                "parallel_execution": True,
                "retry_enabled": True,
                "enhanced_parsing": True,
                "input_validation": True
            },
            "results": {
                "data_validation": {
                    "completed": flow_state.data_validation_complete,
                    "structure": flow_state.validated_structure
                },
                "field_mapping": {
                    "completed": flow_state.field_mapping_complete,
                    "mappings": flow_state.suggested_field_mappings,
                    "mapping_coverage": len(flow_state.suggested_field_mappings) / max(len(flow_state.headers), 1)
                },
                "asset_classification": {
                    "completed": flow_state.asset_classification_complete,
                    "classifications": flow_state.asset_classifications,
                    "classification_coverage": len(flow_state.asset_classifications) / max(len(flow_state.sample_data), 1)
                },
                "readiness_assessment": {
                    "completed": flow_state.readiness_assessment_complete,
                    "scores": readiness_scores
                }
            },
            "recommendations": flow_state.recommendations,
            "ready_for_assessment": readiness_scores.get("overall_readiness", 0) >= 7.0
        }
    
    def get_flow_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive flow metrics and performance statistics."""
        total_flows = len(self.flow_metrics)
        
        if total_flows == 0:
            return {
                "total_flows": 0,
                "active_flows": 0,
                "completed_flows": 0,
                "failed_flows": 0
            }
        
        # Count by status
        status_counts = {}
        durations = []
        
        for metrics in self.flow_metrics.values():
            status = metrics.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if "total_duration_seconds" in metrics:
                durations.append(metrics["total_duration_seconds"])
        
        # Calculate performance metrics
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_flows": total_flows,
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.completed_flows),
            "status_distribution": status_counts,
            "performance": {
                "total_completed_flows": len(durations),
                "average_duration_seconds": avg_duration,
                "min_duration_seconds": min(durations) if durations else 0,
                "max_duration_seconds": max(durations) if durations else 0
            }
        }
    
    def get_handler_summary(self) -> Dict[str, Any]:
        """Get flow state handler summary."""
        return {
            "handler": "flow_state_handler",
            "version": "1.0.0",
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.completed_flows),
            "total_flows_processed": len(self.flow_metrics),
            "features": [
                "flow_lifecycle_management",
                "progress_tracking",
                "state_persistence",
                "metrics_collection",
                "automatic_cleanup"
            ],
            "configuration": {
                "flow_ttl_hours": self.config.flow_ttl_hours
            }
        } 