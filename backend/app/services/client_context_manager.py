"""
Client Context Manager - Enterprise-grade client-specific context management

Manages user preferences, organizational patterns, and engagement-scoped agent behavior
while maintaining strict data isolation between client accounts for enterprise deployment.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from collections import defaultdict, deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from backend.app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Types of client context data"""
    USER_PREFERENCES = "user_preferences"
    ORGANIZATIONAL_PATTERNS = "organizational_patterns"
    CLARIFICATION_HISTORY = "clarification_history"
    AGENT_BEHAVIOR = "agent_behavior"
    FIELD_MAPPINGS = "field_mappings"
    DATA_QUALITY_RULES = "data_quality_rules"
    BUSINESS_CONTEXT = "business_context"

class PreferenceCategory(Enum):
    """Categories of user preferences"""
    WORKFLOW = "workflow"
    COMMUNICATION = "communication"
    ANALYSIS_DEPTH = "analysis_depth"
    RISK_TOLERANCE = "risk_tolerance"
    AUTOMATION_LEVEL = "automation_level"
    REPORTING = "reporting"

@dataclass
class ClientContext:
    """Client-specific context data"""
    client_account_id: int
    engagement_id: str
    context_type: ContextType
    context_key: str
    context_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str
    version: int = 1
    active: bool = True

@dataclass
class UserPreference:
    """User preference within a client context"""
    preference_id: str
    user_id: str
    client_account_id: int
    engagement_id: str
    category: PreferenceCategory
    preference_key: str
    preference_value: Any
    confidence: float
    learned_from: str  # user_input, agent_observation, pattern_analysis
    created_at: datetime
    last_reinforced: datetime

@dataclass
class OrganizationalPattern:
    """Organizational pattern specific to a client"""
    pattern_id: str
    client_account_id: int
    engagement_id: str
    pattern_type: str
    pattern_category: str
    pattern_data: Dict[str, Any]
    confidence: float
    evidence_count: int
    business_impact: str
    created_at: datetime
    last_observed: datetime

@dataclass
class ClarificationSession:
    """Session tracking for agent clarifications"""
    session_id: str
    client_account_id: int
    engagement_id: str
    agent_name: str
    page_context: str
    questions_asked: List[Dict[str, Any]]
    user_responses: List[Dict[str, Any]]
    resolution_status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class ClientContextManager:
    """
    Enterprise-grade client context management system for maintaining
    client-specific agent behavior, preferences, and organizational patterns.
    """
    
    def __init__(self):
        self.context_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.preference_cache: Dict[str, Dict[str, UserPreference]] = defaultdict(dict)
        self.pattern_cache: Dict[str, List[OrganizationalPattern]] = defaultdict(list)
        self.clarification_sessions: Dict[str, ClarificationSession] = {}
        self.cache_ttl = timedelta(hours=1)
        self.last_cache_refresh = datetime.now()
    
    async def initialize_client_context(
        self,
        client_account_id: int,
        engagement_id: str,
        user_id: str,
        initial_preferences: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Initialize context for a new client engagement"""
        try:
            context_key = f"{client_account_id}_{engagement_id}"
            
            # Initialize default preferences
            default_preferences = {
                "workflow_automation_level": 0.7,
                "risk_tolerance": "medium",
                "communication_frequency": "normal",
                "analysis_depth": "standard",
                "reporting_detail": "summary"
            }
            
            if initial_preferences:
                default_preferences.update(initial_preferences)
            
            # Store initial context
            await self._store_client_context(
                client_account_id,
                engagement_id,
                ContextType.USER_PREFERENCES,
                "initial_setup",
                default_preferences,
                user_id
            )
            
            # Initialize organizational pattern detection
            await self._initialize_pattern_detection(client_account_id, engagement_id)
            
            logger.info(f"Initialized client context for {context_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing client context: {str(e)}")
            return False
    
    async def get_user_preferences(
        self,
        client_account_id: int,
        engagement_id: str,
        user_id: str,
        category: Optional[PreferenceCategory] = None
    ) -> Dict[str, Any]:
        """Get user preferences for specific client context"""
        try:
            context_key = f"{client_account_id}_{engagement_id}_{user_id}"
            
            # Check cache first
            if context_key in self.preference_cache and self._is_cache_valid():
                cached_prefs = self.preference_cache[context_key]
                if category:
                    return {k: v.preference_value for k, v in cached_prefs.items() 
                           if v.category == category}
                else:
                    return {k: v.preference_value for k, v in cached_prefs.items()}
            
            # Load from persistent storage (simulated)
            preferences = await self._load_user_preferences(
                client_account_id, engagement_id, user_id, category
            )
            
            # Update cache
            self.preference_cache[context_key] = preferences
            
            if category:
                return {k: v.preference_value for k, v in preferences.items() 
                       if v.category == category}
            else:
                return {k: v.preference_value for k, v in preferences.items()}
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}
    
    async def update_user_preference(
        self,
        client_account_id: int,
        engagement_id: str,
        user_id: str,
        category: PreferenceCategory,
        preference_key: str,
        preference_value: Any,
        learned_from: str = "user_input",
        confidence: float = 1.0
    ) -> bool:
        """Update or create user preference"""
        try:
            preference_id = self._generate_preference_id(
                client_account_id, engagement_id, user_id, preference_key
            )
            
            preference = UserPreference(
                preference_id=preference_id,
                user_id=user_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                category=category,
                preference_key=preference_key,
                preference_value=preference_value,
                confidence=confidence,
                learned_from=learned_from,
                created_at=datetime.now(),
                last_reinforced=datetime.now()
            )
            
            # Update cache
            context_key = f"{client_account_id}_{engagement_id}_{user_id}"
            self.preference_cache[context_key][preference_key] = preference
            
            # Store in persistent storage
            await self._store_user_preference(preference)
            
            logger.info(f"Updated preference {preference_key} for {context_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preference: {str(e)}")
            return False
    
    async def learn_organizational_pattern(
        self,
        client_account_id: int,
        engagement_id: str,
        pattern_type: str,
        pattern_category: str,
        pattern_data: Dict[str, Any],
        business_impact: str,
        confidence: float = 0.8
    ) -> str:
        """Learn and store organizational pattern"""
        try:
            pattern_id = self._generate_pattern_id(
                client_account_id, pattern_type, pattern_data
            )
            
            pattern = OrganizationalPattern(
                pattern_id=pattern_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type=pattern_type,
                pattern_category=pattern_category,
                pattern_data=pattern_data,
                confidence=confidence,
                evidence_count=1,
                business_impact=business_impact,
                created_at=datetime.now(),
                last_observed=datetime.now()
            )
            
            # Update cache
            context_key = f"{client_account_id}_{engagement_id}"
            self.pattern_cache[context_key].append(pattern)
            
            # Store in persistent storage
            await self._store_organizational_pattern(pattern)
            
            logger.info(f"Learned organizational pattern {pattern_id} for client {client_account_id}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Error learning organizational pattern: {str(e)}")
            return ""
    
    async def get_organizational_patterns(
        self,
        client_account_id: int,
        engagement_id: str,
        pattern_type: Optional[str] = None,
        pattern_category: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[OrganizationalPattern]:
        """Get organizational patterns for client"""
        try:
            context_key = f"{client_account_id}_{engagement_id}"
            
            # Check cache first
            if context_key in self.pattern_cache and self._is_cache_valid():
                patterns = self.pattern_cache[context_key]
            else:
                # Load from persistent storage
                patterns = await self._load_organizational_patterns(
                    client_account_id, engagement_id
                )
                self.pattern_cache[context_key] = patterns
            
            # Filter patterns
            filtered_patterns = []
            for pattern in patterns:
                if pattern.confidence < min_confidence:
                    continue
                    
                if pattern_type and pattern.pattern_type != pattern_type:
                    continue
                    
                if pattern_category and pattern.pattern_category != pattern_category:
                    continue
                
                filtered_patterns.append(pattern)
            
            # Sort by confidence and recency
            filtered_patterns.sort(key=lambda p: (p.confidence, p.last_observed), reverse=True)
            
            return filtered_patterns
            
        except Exception as e:
            logger.error(f"Error getting organizational patterns: {str(e)}")
            return []
    
    async def start_clarification_session(
        self,
        client_account_id: int,
        engagement_id: str,
        agent_name: str,
        page_context: str,
        initial_questions: List[Dict[str, Any]]
    ) -> str:
        """Start a new clarification session"""
        try:
            session_id = self._generate_session_id(
                client_account_id, engagement_id, agent_name, page_context
            )
            
            session = ClarificationSession(
                session_id=session_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                agent_name=agent_name,
                page_context=page_context,
                questions_asked=initial_questions,
                user_responses=[],
                resolution_status="active",
                created_at=datetime.now()
            )
            
            self.clarification_sessions[session_id] = session
            
            logger.info(f"Started clarification session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting clarification session: {str(e)}")
            return ""
    
    async def add_clarification_response(
        self,
        session_id: str,
        question_id: str,
        user_response: Dict[str, Any]
    ) -> bool:
        """Add user response to clarification session"""
        try:
            if session_id not in self.clarification_sessions:
                logger.error(f"Clarification session {session_id} not found")
                return False
            
            session = self.clarification_sessions[session_id]
            
            response_data = {
                "question_id": question_id,
                "response": user_response,
                "timestamp": datetime.now().isoformat(),
                "page_context": session.page_context
            }
            
            session.user_responses.append(response_data)
            
            # Learn from response
            await self._learn_from_clarification_response(session, response_data)
            
            logger.info(f"Added response to clarification session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding clarification response: {str(e)}")
            return False
    
    async def complete_clarification_session(
        self,
        session_id: str,
        resolution_status: str = "completed"
    ) -> bool:
        """Complete a clarification session"""
        try:
            if session_id not in self.clarification_sessions:
                logger.error(f"Clarification session {session_id} not found")
                return False
            
            session = self.clarification_sessions[session_id]
            session.resolution_status = resolution_status
            session.completed_at = datetime.now()
            
            # Extract learning patterns from session
            await self._extract_session_patterns(session)
            
            # Store session history
            await self._store_clarification_session(session)
            
            logger.info(f"Completed clarification session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing clarification session: {str(e)}")
            return False
    
    async def get_agent_behavior_config(
        self,
        client_account_id: int,
        engagement_id: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """Get agent behavior configuration for client context"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(
                client_account_id, engagement_id, "default"
            )
            
            # Get organizational patterns
            patterns = await self.get_organizational_patterns(
                client_account_id, engagement_id
            )
            
            # Build agent behavior config
            config = {
                "communication_style": preferences.get("communication_frequency", "normal"),
                "analysis_depth": preferences.get("analysis_depth", "standard"),
                "automation_level": preferences.get("workflow_automation_level", 0.7),
                "risk_tolerance": preferences.get("risk_tolerance", "medium"),
                "organizational_patterns": [
                    {
                        "pattern_type": p.pattern_type,
                        "pattern_data": p.pattern_data,
                        "confidence": p.confidence
                    } for p in patterns[:10]  # Top 10 patterns
                ]
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting agent behavior config: {str(e)}")
            return {}
    
    async def invalidate_cache(
        self,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[str] = None
    ) -> None:
        """Invalidate cache for specific client or all clients"""
        try:
            if client_account_id and engagement_id:
                # Invalidate specific client cache
                context_key = f"{client_account_id}_{engagement_id}"
                self.context_cache.pop(context_key, None)
                
                # Clear related preference and pattern caches
                keys_to_remove = [k for k in self.preference_cache.keys() 
                                 if k.startswith(context_key)]
                for key in keys_to_remove:
                    self.preference_cache.pop(key, None)
                
                self.pattern_cache.pop(context_key, None)
                
            else:
                # Clear all caches
                self.context_cache.clear()
                self.preference_cache.clear()
                self.pattern_cache.clear()
            
            self.last_cache_refresh = datetime.now()
            logger.info("Invalidated client context cache")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
    
    # Private helper methods
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return datetime.now() - self.last_cache_refresh < self.cache_ttl
    
    def _generate_preference_id(
        self,
        client_account_id: int,
        engagement_id: str,
        user_id: str,
        preference_key: str
    ) -> str:
        """Generate unique preference ID"""
        content = f"{client_account_id}_{engagement_id}_{user_id}_{preference_key}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_pattern_id(
        self,
        client_account_id: int,
        pattern_type: str,
        pattern_data: Dict[str, Any]
    ) -> str:
        """Generate unique pattern ID"""
        content = f"{client_account_id}_{pattern_type}_{str(pattern_data)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_session_id(
        self,
        client_account_id: int,
        engagement_id: str,
        agent_name: str,
        page_context: str
    ) -> str:
        """Generate unique session ID"""
        content = f"{client_account_id}_{engagement_id}_{agent_name}_{page_context}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _store_client_context(
        self,
        client_account_id: int,
        engagement_id: str,
        context_type: ContextType,
        context_key: str,
        context_data: Dict[str, Any],
        created_by: str
    ) -> None:
        """Store client context in persistent storage"""
        # Simulated storage - in real implementation, would use database
        cache_key = f"{client_account_id}_{engagement_id}"
        self.context_cache[cache_key][context_key] = context_data
        logger.info(f"Stored client context {context_key} for {cache_key}")
    
    async def _load_user_preferences(
        self,
        client_account_id: int,
        engagement_id: str,
        user_id: str,
        category: Optional[PreferenceCategory] = None
    ) -> Dict[str, UserPreference]:
        """Load user preferences from persistent storage"""
        # Simulated loading - in real implementation, would query database
        preferences = {}
        
        # Default preferences for demo
        default_prefs = [
            ("workflow_automation_level", PreferenceCategory.AUTOMATION_LEVEL, 0.7),
            ("risk_tolerance", PreferenceCategory.RISK_TOLERANCE, "medium"),
            ("communication_frequency", PreferenceCategory.COMMUNICATION, "normal"),
            ("analysis_depth", PreferenceCategory.ANALYSIS_DEPTH, "standard"),
            ("reporting_detail", PreferenceCategory.REPORTING, "summary")
        ]
        
        for pref_key, pref_category, pref_value in default_prefs:
            if category is None or pref_category == category:
                preference_id = self._generate_preference_id(
                    client_account_id, engagement_id, user_id, pref_key
                )
                
                preferences[pref_key] = UserPreference(
                    preference_id=preference_id,
                    user_id=user_id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    category=pref_category,
                    preference_key=pref_key,
                    preference_value=pref_value,
                    confidence=1.0,
                    learned_from="default",
                    created_at=datetime.now(),
                    last_reinforced=datetime.now()
                )
        
        return preferences
    
    async def _store_user_preference(self, preference: UserPreference) -> None:
        """Store user preference in persistent storage"""
        # Simulated storage - in real implementation, would use database
        logger.info(f"Stored user preference {preference.preference_key}")
    
    async def _load_organizational_patterns(
        self,
        client_account_id: int,
        engagement_id: str
    ) -> List[OrganizationalPattern]:
        """Load organizational patterns from persistent storage"""
        # Simulated loading - in real implementation, would query database
        patterns = []
        
        # Sample patterns for demo
        sample_patterns = [
            {
                "pattern_type": "naming_convention",
                "pattern_category": "infrastructure",
                "pattern_data": {"prefix_pattern": "srv-", "environment_suffix": True},
                "business_impact": "Standardized server naming improves asset tracking",
                "confidence": 0.9
            },
            {
                "pattern_type": "application_grouping",
                "pattern_category": "business",
                "pattern_data": {"department_based": True, "function_based": False},
                "business_impact": "Applications organized by department ownership",
                "confidence": 0.8
            }
        ]
        
        for i, pattern_data in enumerate(sample_patterns):
            pattern_id = self._generate_pattern_id(
                client_account_id, pattern_data["pattern_type"], pattern_data["pattern_data"]
            )
            
            pattern = OrganizationalPattern(
                pattern_id=pattern_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pattern_type=pattern_data["pattern_type"],
                pattern_category=pattern_data["pattern_category"],
                pattern_data=pattern_data["pattern_data"],
                confidence=pattern_data["confidence"],
                evidence_count=5 + i,
                business_impact=pattern_data["business_impact"],
                created_at=datetime.now() - timedelta(days=i),
                last_observed=datetime.now()
            )
            
            patterns.append(pattern)
        
        return patterns
    
    async def _store_organizational_pattern(self, pattern: OrganizationalPattern) -> None:
        """Store organizational pattern in persistent storage"""
        # Simulated storage - in real implementation, would use database
        logger.info(f"Stored organizational pattern {pattern.pattern_id}")
    
    async def _initialize_pattern_detection(
        self,
        client_account_id: int,
        engagement_id: str
    ) -> None:
        """Initialize pattern detection for new client"""
        # Set up pattern detection algorithms
        logger.info(f"Initialized pattern detection for client {client_account_id}")
    
    async def _learn_from_clarification_response(
        self,
        session: ClarificationSession,
        response_data: Dict[str, Any]
    ) -> None:
        """Learn from user clarification response"""
        try:
            # Extract learning signals from response
            response = response_data["response"]
            
            # Update user preferences based on response patterns
            if "preference" in response:
                await self.update_user_preference(
                    session.client_account_id,
                    session.engagement_id,
                    "default",  # Use default user for session-level preferences
                    PreferenceCategory.COMMUNICATION,
                    "clarification_style",
                    response.get("style", "detailed"),
                    "agent_observation",
                    0.8
                )
            
            logger.info(f"Learned from clarification response in session {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error learning from clarification response: {str(e)}")
    
    async def _extract_session_patterns(self, session: ClarificationSession) -> None:
        """Extract patterns from completed clarification session"""
        try:
            # Analyze session for organizational patterns
            if len(session.user_responses) >= 3:
                # Pattern: User response style
                response_style = self._analyze_response_style(session.user_responses)
                
                await self.learn_organizational_pattern(
                    session.client_account_id,
                    session.engagement_id,
                    "communication_pattern",
                    "user_interaction",
                    {"response_style": response_style, "page_context": session.page_context},
                    "Improved agent communication effectiveness",
                    0.7
                )
            
            logger.info(f"Extracted patterns from session {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error extracting session patterns: {str(e)}")
    
    def _analyze_response_style(self, responses: List[Dict[str, Any]]) -> str:
        """Analyze user response style from session"""
        # Simple analysis - can be enhanced with NLP
        avg_length = sum(len(str(r.get("response", ""))) for r in responses) / len(responses)
        
        if avg_length > 100:
            return "detailed"
        elif avg_length > 50:
            return "moderate"
        else:
            return "concise"
    
    async def _store_clarification_session(self, session: ClarificationSession) -> None:
        """Store clarification session in persistent storage"""
        # Simulated storage - in real implementation, would use database
        logger.info(f"Stored clarification session {session.session_id}")

# Global instance for client context management
client_context_manager = ClientContextManager() 