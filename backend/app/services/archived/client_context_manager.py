"""
Client Context Manager
Manages client and engagement-specific context data for multi-tenant learning.
Implements Task 5.1: Context-Scoped Agent Learning
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ClientContext:
    """Client-specific context data."""
    client_account_id: int
    client_name: str
    industry: Optional[str] = None
    organization_size: Optional[str] = None
    technology_stack: List[str] = None
    business_priorities: List[str] = None
    compliance_requirements: List[str] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.technology_stack is None:
            self.technology_stack = []
        if self.business_priorities is None:
            self.business_priorities = []
        if self.compliance_requirements is None:
            self.compliance_requirements = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class EngagementContext:
    """Engagement-specific context data."""
    engagement_id: str
    client_account_id: int
    engagement_name: str
    engagement_type: Optional[str] = None
    migration_goals: List[str] = None
    timeline: Optional[Dict[str, Any]] = None
    stakeholders: List[Dict[str, str]] = None
    technical_constraints: List[str] = None
    business_constraints: List[str] = None
    success_criteria: List[str] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.migration_goals is None:
            self.migration_goals = []
        if self.stakeholders is None:
            self.stakeholders = []
        if self.technical_constraints is None:
            self.technical_constraints = []
        if self.business_constraints is None:
            self.business_constraints = []
        if self.success_criteria is None:
            self.success_criteria = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class OrganizationalPattern:
    """Organizational pattern learned for a client."""
    pattern_id: str
    client_account_id: int
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float
    usage_count: int
    created_at: datetime
    last_used: datetime


@dataclass
class ClarificationResponse:
    """Clarification response from stakeholders."""
    response_id: str
    engagement_id: str
    question_type: str
    question: str
    response: str
    stakeholder: str
    timestamp: datetime
    context: Dict[str, Any]


class ClientContextManager:
    """Manages client and engagement-specific context data."""
    
    def __init__(self, data_dir: str = "data/client_context"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Context storage
        self.client_contexts: Dict[int, ClientContext] = {}
        self.engagement_contexts: Dict[str, EngagementContext] = {}
        self.organizational_patterns: Dict[int, List[OrganizationalPattern]] = {}
        self.clarification_responses: Dict[str, List[ClarificationResponse]] = {}
        
        # Load existing data
        self._load_contexts()
    
    async def create_client_context(self, client_account_id: int, client_data: Dict[str, Any]):
        """Create or update client-specific context."""
        context = ClientContext(
            client_account_id=client_account_id,
            client_name=client_data.get("client_name", f"Client {client_account_id}"),
            industry=client_data.get("industry"),
            organization_size=client_data.get("organization_size"),
            technology_stack=client_data.get("technology_stack", []),
            business_priorities=client_data.get("business_priorities", []),
            compliance_requirements=client_data.get("compliance_requirements", []),
            last_updated=datetime.utcnow()
        )
        
        self.client_contexts[client_account_id] = context
        self._save_contexts()
        
        logger.info(f"Created/updated client context for {client_account_id}: {context.client_name}")
    
    async def create_engagement_context(
        self, 
        engagement_id: str, 
        client_account_id: int, 
        engagement_data: Dict[str, Any]
    ):
        """Create or update engagement-specific context."""
        context = EngagementContext(
            engagement_id=engagement_id,
            client_account_id=client_account_id,
            engagement_name=engagement_data.get("engagement_name", f"Engagement {engagement_id}"),
            engagement_type=engagement_data.get("engagement_type"),
            migration_goals=engagement_data.get("migration_goals", []),
            timeline=engagement_data.get("timeline"),
            stakeholders=engagement_data.get("stakeholders", []),
            technical_constraints=engagement_data.get("technical_constraints", []),
            business_constraints=engagement_data.get("business_constraints", []),
            success_criteria=engagement_data.get("success_criteria", []),
            last_updated=datetime.utcnow()
        )
        
        self.engagement_contexts[engagement_id] = context
        self._save_contexts()
        
        logger.info(f"Created/updated engagement context for {engagement_id}: {context.engagement_name}")
    
    async def learn_organizational_pattern(self, client_account_id: int, pattern_data: Dict[str, Any]):
        """Learn organizational patterns specific to the client."""
        pattern = OrganizationalPattern(
            pattern_id=f"org_pattern_{datetime.utcnow().timestamp()}",
            client_account_id=client_account_id,
            pattern_type=pattern_data.get("pattern_type", "general"),
            pattern_data=pattern_data.get("pattern_data", {}),
            confidence=pattern_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        if client_account_id not in self.organizational_patterns:
            self.organizational_patterns[client_account_id] = []
        
        self.organizational_patterns[client_account_id].append(pattern)
        self._save_contexts()
        
        logger.info(f"Learned organizational pattern for client {client_account_id}: {pattern.pattern_type}")
    
    async def get_organizational_patterns(self, client_account_id: int) -> List[Dict[str, Any]]:
        """Get organizational patterns for a client."""
        patterns = self.organizational_patterns.get(client_account_id, [])
        
        # Convert to serializable format
        return [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "pattern_data": p.pattern_data,
                "confidence": p.confidence,
                "usage_count": p.usage_count,
                "created_at": p.created_at.isoformat(),
                "last_used": p.last_used.isoformat()
            }
            for p in patterns
        ]
    
    async def store_clarification_response(self, engagement_id: str, clarification_data: Dict[str, Any]):
        """Store clarification response from stakeholders."""
        response = ClarificationResponse(
            response_id=f"clarification_{datetime.utcnow().timestamp()}",
            engagement_id=engagement_id,
            question_type=clarification_data.get("question_type", "general"),
            question=clarification_data.get("question", ""),
            response=clarification_data.get("response", ""),
            stakeholder=clarification_data.get("stakeholder", "unknown"),
            timestamp=datetime.utcnow(),
            context=clarification_data.get("context", {})
        )
        
        if engagement_id not in self.clarification_responses:
            self.clarification_responses[engagement_id] = []
        
        self.clarification_responses[engagement_id].append(response)
        self._save_contexts()
        
        logger.info(f"Stored clarification response for engagement {engagement_id}: {response.question_type}")
    
    async def get_clarification_history(
        self, 
        engagement_id: str, 
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get clarification history for an engagement."""
        responses = self.clarification_responses.get(engagement_id, [])
        
        if question_type:
            responses = [r for r in responses if r.question_type == question_type]
        
        # Convert to serializable format
        return [
            {
                "response_id": r.response_id,
                "question_type": r.question_type,
                "question": r.question,
                "response": r.response,
                "stakeholder": r.stakeholder,
                "timestamp": r.timestamp.isoformat(),
                "context": r.context
            }
            for r in responses
        ]
    
    async def get_client_context(self, client_account_id: int) -> Optional[Dict[str, Any]]:
        """Get client context data."""
        context = self.client_contexts.get(client_account_id)
        
        if not context:
            return None
        
        return {
            "client_account_id": context.client_account_id,
            "client_name": context.client_name,
            "industry": context.industry,
            "organization_size": context.organization_size,
            "technology_stack": context.technology_stack,
            "business_priorities": context.business_priorities,
            "compliance_requirements": context.compliance_requirements,
            "created_at": context.created_at.isoformat(),
            "last_updated": context.last_updated.isoformat()
        }
    
    async def get_engagement_context(self, engagement_id: str) -> Optional[Dict[str, Any]]:
        """Get engagement context data."""
        context = self.engagement_contexts.get(engagement_id)
        
        if not context:
            return None
        
        return {
            "engagement_id": context.engagement_id,
            "client_account_id": context.client_account_id,
            "engagement_name": context.engagement_name,
            "engagement_type": context.engagement_type,
            "migration_goals": context.migration_goals,
            "timeline": context.timeline,
            "stakeholders": context.stakeholders,
            "technical_constraints": context.technical_constraints,
            "business_constraints": context.business_constraints,
            "success_criteria": context.success_criteria,
            "created_at": context.created_at.isoformat(),
            "last_updated": context.last_updated.isoformat()
        }
    
    async def get_combined_context(self, engagement_id: str) -> Dict[str, Any]:
        """Get combined client and engagement context."""
        engagement_context = await self.get_engagement_context(engagement_id)
        
        if not engagement_context:
            return {}
        
        client_context = await self.get_client_context(engagement_context["client_account_id"])
        
        return {
            "client_context": client_context,
            "engagement_context": engagement_context,
            "organizational_patterns": await self.get_organizational_patterns(engagement_context["client_account_id"]),
            "clarification_history": await self.get_clarification_history(engagement_id)
        }
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """Get context management statistics."""
        total_patterns = sum(len(patterns) for patterns in self.organizational_patterns.values())
        total_clarifications = sum(len(responses) for responses in self.clarification_responses.values())
        
        return {
            "total_clients": len(self.client_contexts),
            "total_engagements": len(self.engagement_contexts),
            "total_organizational_patterns": total_patterns,
            "total_clarification_responses": total_clarifications,
            "clients_with_patterns": len([c for c in self.organizational_patterns.keys() if self.organizational_patterns[c]]),
            "engagements_with_clarifications": len([e for e in self.clarification_responses.keys() if self.clarification_responses[e]])
        }
    
    def _save_contexts(self):
        """Save all context data to disk."""
        try:
            # Save client contexts
            client_file = self.data_dir / "client_contexts.json"
            client_data = {}
            for client_id, context in self.client_contexts.items():
                context_dict = asdict(context)
                context_dict["created_at"] = context.created_at.isoformat()
                context_dict["last_updated"] = context.last_updated.isoformat()
                client_data[str(client_id)] = context_dict
            
            with open(client_file, 'w') as f:
                json.dump(client_data, f, indent=2)
            
            # Save engagement contexts
            engagement_file = self.data_dir / "engagement_contexts.json"
            engagement_data = {}
            for engagement_id, context in self.engagement_contexts.items():
                context_dict = asdict(context)
                context_dict["created_at"] = context.created_at.isoformat()
                context_dict["last_updated"] = context.last_updated.isoformat()
                engagement_data[engagement_id] = context_dict
            
            with open(engagement_file, 'w') as f:
                json.dump(engagement_data, f, indent=2)
            
            # Save organizational patterns
            patterns_file = self.data_dir / "organizational_patterns.json"
            patterns_data = {}
            for client_id, patterns in self.organizational_patterns.items():
                patterns_data[str(client_id)] = []
                for pattern in patterns:
                    pattern_dict = asdict(pattern)
                    pattern_dict["created_at"] = pattern.created_at.isoformat()
                    pattern_dict["last_used"] = pattern.last_used.isoformat()
                    patterns_data[str(client_id)].append(pattern_dict)
            
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save clarification responses
            clarifications_file = self.data_dir / "clarification_responses.json"
            clarifications_data = {}
            for engagement_id, responses in self.clarification_responses.items():
                clarifications_data[engagement_id] = []
                for response in responses:
                    response_dict = asdict(response)
                    response_dict["timestamp"] = response.timestamp.isoformat()
                    clarifications_data[engagement_id].append(response_dict)
            
            with open(clarifications_file, 'w') as f:
                json.dump(clarifications_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save context data: {e}")
    
    def _load_contexts(self):
        """Load all context data from disk."""
        try:
            # Load client contexts
            client_file = self.data_dir / "client_contexts.json"
            if client_file.exists():
                with open(client_file, 'r') as f:
                    client_data = json.load(f)
                
                for client_id_str, context_dict in client_data.items():
                    context_dict["created_at"] = datetime.fromisoformat(context_dict["created_at"])
                    context_dict["last_updated"] = datetime.fromisoformat(context_dict["last_updated"])
                    context = ClientContext(**context_dict)
                    self.client_contexts[int(client_id_str)] = context
            
            # Load engagement contexts
            engagement_file = self.data_dir / "engagement_contexts.json"
            if engagement_file.exists():
                with open(engagement_file, 'r') as f:
                    engagement_data = json.load(f)
                
                for engagement_id, context_dict in engagement_data.items():
                    context_dict["created_at"] = datetime.fromisoformat(context_dict["created_at"])
                    context_dict["last_updated"] = datetime.fromisoformat(context_dict["last_updated"])
                    context = EngagementContext(**context_dict)
                    self.engagement_contexts[engagement_id] = context
            
            # Load organizational patterns
            patterns_file = self.data_dir / "organizational_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                
                for client_id_str, patterns_list in patterns_data.items():
                    client_id = int(client_id_str)
                    self.organizational_patterns[client_id] = []
                    for pattern_dict in patterns_list:
                        pattern_dict["created_at"] = datetime.fromisoformat(pattern_dict["created_at"])
                        pattern_dict["last_used"] = datetime.fromisoformat(pattern_dict["last_used"])
                        pattern = OrganizationalPattern(**pattern_dict)
                        self.organizational_patterns[client_id].append(pattern)
            
            # Load clarification responses
            clarifications_file = self.data_dir / "clarification_responses.json"
            if clarifications_file.exists():
                with open(clarifications_file, 'r') as f:
                    clarifications_data = json.load(f)
                
                for engagement_id, responses_list in clarifications_data.items():
                    self.clarification_responses[engagement_id] = []
                    for response_dict in responses_list:
                        response_dict["timestamp"] = datetime.fromisoformat(response_dict["timestamp"])
                        response = ClarificationResponse(**response_dict)
                        self.clarification_responses[engagement_id].append(response)
            
            logger.info(f"Loaded context data: {len(self.client_contexts)} clients, {len(self.engagement_contexts)} engagements")
            
        except Exception as e:
            logger.error(f"Failed to load context data: {e}")


# Global instance
client_context_manager = ClientContextManager() 