"""
Context Handler for Agent-UI Communication
Manages cross-page context and agent coordination.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class ContextHandler:
    """Handles cross-page context and agent coordination."""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.cross_page_context: Dict[str, Any] = {}
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.learning_experiences: List[Dict[str, Any]] = []
    
    def set_cross_page_context(self, key: str, value: Any, page_source: str) -> None:
        """Set cross-page context information."""
        self.cross_page_context[key] = {
            "value": value,
            "page_source": page_source,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.storage_manager.save_context({
            "cross_page_context": self.cross_page_context,
            "agent_states": self.agent_states
        })
        
        logger.info(f"Set cross-page context '{key}' from page '{page_source}'")
    
    def get_cross_page_context(self, key: str = None) -> Any:
        """Get cross-page context information."""
        if key is None:
            return {k: v["value"] for k, v in self.cross_page_context.items()}
        
        if key in self.cross_page_context:
            return self.cross_page_context[key]["value"]
        
        return None
    
    def get_context_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a context item."""
        return self.cross_page_context.get(key)
    
    def clear_cross_page_context(self, key: str = None) -> None:
        """Clear cross-page context."""
        if key is None:
            self.cross_page_context.clear()
            logger.info("Cleared all cross-page context")
        else:
            if key in self.cross_page_context:
                del self.cross_page_context[key]
                logger.info(f"Cleared cross-page context '{key}'")
        
        self.storage_manager.save_context({
            "cross_page_context": self.cross_page_context,
            "agent_states": self.agent_states
        })
    
    def update_agent_state(self, agent_id: str, state_data: Dict[str, Any], 
                          page: str) -> None:
        """Update agent state for cross-page coordination."""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = {}
        
        self.agent_states[agent_id].update({
            **state_data,
            "last_active_page": page,
            "last_updated": datetime.utcnow().isoformat()
        })
        
        self.storage_manager.save_context({
            "cross_page_context": self.cross_page_context,
            "agent_states": self.agent_states
        })
        
        logger.info(f"Updated state for agent {agent_id} on page {page}")
    
    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state for coordination."""
        return self.agent_states.get(agent_id)
    
    def get_all_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent states."""
        return self.agent_states.copy()
    
    def store_learning_experience(self, learning_context: Dict[str, Any]) -> None:
        """Store learning experience for agent improvement."""
        experience = {
            **learning_context,
            "stored_at": datetime.utcnow().isoformat()
        }
        
        self.learning_experiences.append(experience)
        
        # Keep only recent experiences (last 1000)
        if len(self.learning_experiences) > 1000:
            self.learning_experiences = self.learning_experiences[-1000:]
        
        logger.info(f"Stored learning experience: {learning_context.get('question_type', 'unknown')}")
    
    def get_recent_learning_experiences(self, limit: int = 50, 
                                      agent_id: str = None,
                                      experience_type: str = None) -> List[Dict[str, Any]]:
        """Get recent learning experiences."""
        experiences = self.learning_experiences.copy()
        
        # Filter by agent if specified
        if agent_id:
            experiences = [exp for exp in experiences if exp.get("agent_id") == agent_id]
        
        # Filter by type if specified
        if experience_type:
            experiences = [exp for exp in experiences 
                         if exp.get("question_type") == experience_type or 
                         exp.get("update_type") == experience_type]
        
        # Sort by timestamp (most recent first) and limit
        experiences.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
        return experiences[:limit]
    
    def get_agent_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of agent coordination across pages."""
        active_agents = len(self.agent_states)
        total_context_items = len(self.cross_page_context)
        total_experiences = len(self.learning_experiences)
        
        # Analyze agent activity by page
        page_activity = {}
        for agent_id, state in self.agent_states.items():
            page = state.get("last_active_page", "unknown")
            if page not in page_activity:
                page_activity[page] = {"agents": 0, "last_activity": None}
            
            page_activity[page]["agents"] += 1
            
            # Track most recent activity
            last_updated = state.get("last_updated")
            if last_updated and (not page_activity[page]["last_activity"] or 
                               last_updated > page_activity[page]["last_activity"]):
                page_activity[page]["last_activity"] = last_updated
        
        # Analyze learning by type
        learning_by_type = {}
        for exp in self.learning_experiences[-100:]:  # Recent 100
            exp_type = exp.get("question_type") or exp.get("update_type", "unknown")
            learning_by_type[exp_type] = learning_by_type.get(exp_type, 0) + 1
        
        return {
            "active_agents": active_agents,
            "total_context_items": total_context_items,
            "total_learning_experiences": total_experiences,
            "page_activity": page_activity,
            "recent_learning_by_type": learning_by_type,
            "coordination_health": {
                "context_sharing": total_context_items > 0,
                "agent_activity": active_agents > 0,
                "learning_active": total_experiences > 0
            }
        }
    
    def get_context_dependencies(self) -> Dict[str, List[str]]:
        """Get context dependencies between pages."""
        dependencies = {}
        
        for key, context_data in self.cross_page_context.items():
            source_page = context_data.get("page_source", "unknown")
            if source_page not in dependencies:
                dependencies[source_page] = []
            dependencies[source_page].append(key)
        
        return dependencies
    
    def clear_stale_context(self, max_age_hours: int = 24) -> int:
        """Clear stale context items."""
        current_time = datetime.utcnow()
        cleared_count = 0
        
        stale_keys = []
        for key, context_data in self.cross_page_context.items():
            try:
                context_time = datetime.fromisoformat(context_data.get("timestamp", ""))
                age_hours = (current_time - context_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    stale_keys.append(key)
            except:
                # Invalid timestamp, consider stale
                stale_keys.append(key)
        
        for key in stale_keys:
            del self.cross_page_context[key]
            cleared_count += 1
        
        if cleared_count > 0:
            self.storage_manager.save_context({
                "cross_page_context": self.cross_page_context,
                "agent_states": self.agent_states
            })
            logger.info(f"Cleared {cleared_count} stale context items")
        
        return cleared_count
    
    def load_context_data(self, context_data: Dict[str, Any]) -> None:
        """Load context data from storage."""
        self.cross_page_context = context_data.get("cross_page_context", {})
        self.agent_states = context_data.get("agent_states", {})
        self.learning_experiences = context_data.get("learning_experiences", [])
        
        logger.info(f"Loaded context: {len(self.cross_page_context)} items, "
                   f"{len(self.agent_states)} agent states, "
                   f"{len(self.learning_experiences)} learning experiences") 