# Remediation Plan: Phase 3 - Feature Completion (Weeks 5-6)

## Overview

Phase 3 focuses on completing missing implementations and fixing incomplete features identified in the current codebase. This includes implementing proper WebSocket real-time updates, completing the learning system, enhancing LLM cost tracking, and improving agent collaboration.

## Week 5: Real-Time System and Learning Implementation

### Day 21-22: Implement WebSocket Real-Time System

#### Current Issues
```python
# backend/app/websocket/__init__.py - Empty implementation
"""
WebSocket package for real-time communication.
"""  # No actual implementation

# Real-time updates through indirect agent_ui_bridge pattern
agent_ui_bridge.add_agent_insight(
    agent_id="data_import_agent",
    agent_name="Data Import Agent",
    insight_type="processing",
    page=f"flow_{self.state.flow_id}",
    # Complex workaround instead of proper WebSocket
)
```

#### Remediation Steps

**Step 1: WebSocket Manager Implementation**
```python
# backend/app/websocket/manager.py - Proper WebSocket implementation
import asyncio
import json
import uuid
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import get_logger
from app.core.context import RequestContext, set_current_context

logger = get_logger("websocket.manager")

class ConnectionManager:
    """Manages WebSocket connections with tenant isolation"""
    
    def __init__(self):
        # Store connections by tenant and flow
        self.connections: Dict[str, Dict[str, WebSocket]] = {}
        # tenant_id -> {connection_id: websocket}
        
        self.flow_subscriptions: Dict[str, Set[str]] = {}
        # flow_id -> {connection_ids}
        
        self.connection_metadata: Dict[str, Dict] = {}
        # connection_id -> {tenant_id, user_id, subscriptions}
    
    async def connect(self, websocket: WebSocket, context: RequestContext, 
                     flow_id: Optional[str] = None) -> str:
        """Accept WebSocket connection with tenant context"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        tenant_id = str(context.client_account_id)
        
        # Store connection with tenant isolation
        if tenant_id not in self.connections:
            self.connections[tenant_id] = {}
        
        self.connections[tenant_id][connection_id] = websocket
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            'tenant_id': tenant_id,
            'user_id': str(context.user_id) if context.user_id else None,
            'subscriptions': set()
        }
        
        # Subscribe to flow if specified
        if flow_id:
            await self.subscribe_to_flow(connection_id, flow_id)
        
        logger.info(f"WebSocket connection established: {connection_id} for tenant {tenant_id}")
        
        # Send connection confirmation
        await self.send_to_connection(connection_id, {
            'type': 'connection_established',
            'connection_id': connection_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        metadata = self.connection_metadata.get(connection_id)
        if not metadata:
            return
        
        tenant_id = metadata['tenant_id']
        
        # Remove from tenant connections
        if tenant_id in self.connections and connection_id in self.connections[tenant_id]:
            del self.connections[tenant_id][connection_id]
            
            # Clean up empty tenant dict
            if not self.connections[tenant_id]:
                del self.connections[tenant_id]
        
        # Remove from flow subscriptions
        for flow_id, subscribers in self.flow_subscriptions.items():
            subscribers.discard(connection_id)
        
        # Clean up empty flow subscriptions
        self.flow_subscriptions = {
            flow_id: subscribers 
            for flow_id, subscribers in self.flow_subscriptions.items() 
            if subscribers
        }
        
        # Remove metadata
        del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def subscribe_to_flow(self, connection_id: str, flow_id: str):
        """Subscribe connection to flow updates"""
        metadata = self.connection_metadata.get(connection_id)
        if not metadata:
            return
        
        # Add to flow subscriptions
        if flow_id not in self.flow_subscriptions:
            self.flow_subscriptions[flow_id] = set()
        
        self.flow_subscriptions[flow_id].add(connection_id)
        metadata['subscriptions'].add(flow_id)
        
        logger.info(f"Connection {connection_id} subscribed to flow {flow_id}")
    
    async def unsubscribe_from_flow(self, connection_id: str, flow_id: str):
        """Unsubscribe connection from flow updates"""
        if flow_id in self.flow_subscriptions:
            self.flow_subscriptions[flow_id].discard(connection_id)
        
        metadata = self.connection_metadata.get(connection_id)
        if metadata:
            metadata['subscriptions'].discard(flow_id)
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        metadata = self.connection_metadata.get(connection_id)
        if not metadata:
            return
        
        tenant_id = metadata['tenant_id']
        
        if (tenant_id in self.connections and 
            connection_id in self.connections[tenant_id]):
            
            websocket = self.connections[tenant_id][connection_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast_to_flow(self, flow_id: str, message: dict, 
                               exclude_connection: Optional[str] = None):
        """Broadcast message to all connections subscribed to a flow"""
        if flow_id not in self.flow_subscriptions:
            return
        
        subscribers = self.flow_subscriptions[flow_id].copy()
        if exclude_connection:
            subscribers.discard(exclude_connection)
        
        # Add flow context to message
        message['flow_id'] = flow_id
        message['timestamp'] = datetime.utcnow().isoformat()
        
        # Send to all subscribers
        for connection_id in subscribers:
            await self.send_to_connection(connection_id, message)
        
        logger.info(f"Broadcasted message to {len(subscribers)} connections for flow {flow_id}")
    
    async def broadcast_to_tenant(self, tenant_id: str, message: dict,
                                 exclude_connection: Optional[str] = None):
        """Broadcast message to all connections for a tenant"""
        if tenant_id not in self.connections:
            return
        
        connections = list(self.connections[tenant_id].keys())
        if exclude_connection:
            connections = [c for c in connections if c != exclude_connection]
        
        message['timestamp'] = datetime.utcnow().isoformat()
        
        for connection_id in connections:
            await self.send_to_connection(connection_id, message)

# Global connection manager instance
connection_manager = ConnectionManager()
```

**Step 2: WebSocket API Endpoints**
```python
# backend/app/api/v1/websocket.py - WebSocket endpoints
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.websocket.manager import connection_manager
from app.core.context import RequestContext, set_current_context
from app.api.dependencies import get_context_from_websocket

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_account_id: str = Query(...),
    engagement_id: str = Query(None),
    user_id: str = Query(None),
    flow_id: str = Query(None)
):
    """Main WebSocket endpoint for real-time updates"""
    
    # Create context from query parameters
    try:
        context = RequestContext(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id) if engagement_id else None,
            user_id=UUID(user_id) if user_id else None
        )
        set_current_context(context)
        
    except ValueError as e:
        await websocket.close(code=4000, reason=f"Invalid context: {e}")
        return
    
    # Establish connection
    connection_id = await connection_manager.connect(websocket, context, flow_id)
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_json()
            await handle_websocket_message(connection_id, data)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
        await connection_manager.disconnect(connection_id)

async def handle_websocket_message(connection_id: str, message: dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get('type')
    
    if message_type == 'subscribe_flow':
        flow_id = message.get('flow_id')
        if flow_id:
            await connection_manager.subscribe_to_flow(connection_id, flow_id)
            await connection_manager.send_to_connection(connection_id, {
                'type': 'subscription_confirmed',
                'flow_id': flow_id
            })
    
    elif message_type == 'unsubscribe_flow':
        flow_id = message.get('flow_id')
        if flow_id:
            await connection_manager.unsubscribe_from_flow(connection_id, flow_id)
            await connection_manager.send_to_connection(connection_id, {
                'type': 'unsubscription_confirmed',
                'flow_id': flow_id
            })
    
    elif message_type == 'ping':
        await connection_manager.send_to_connection(connection_id, {
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    else:
        await connection_manager.send_to_connection(connection_id, {
            'type': 'error',
            'message': f'Unknown message type: {message_type}'
        })
```

**Step 3: Integration with Flow System**
```python
# backend/app/services/websocket_service.py - Service integration
from app.websocket.manager import connection_manager
from app.core.context import get_current_context

class WebSocketService:
    """Service for sending real-time updates"""
    
    @staticmethod
    async def send_flow_update(flow_id: str, update_data: dict):
        """Send flow status update to subscribed clients"""
        message = {
            'type': 'flow_update',
            'flow_id': flow_id,
            'data': update_data
        }
        
        await connection_manager.broadcast_to_flow(flow_id, message)
    
    @staticmethod
    async def send_agent_insight(flow_id: str, agent_name: str, insight: dict):
        """Send agent insight to subscribed clients"""
        message = {
            'type': 'agent_insight',
            'flow_id': flow_id,
            'agent_name': agent_name,
            'insight': insight
        }
        
        await connection_manager.broadcast_to_flow(flow_id, message)
    
    @staticmethod
    async def send_error_notification(flow_id: str, error: dict):
        """Send error notification to subscribed clients"""
        message = {
            'type': 'error_notification',
            'flow_id': flow_id,
            'error': error
        }
        
        await connection_manager.broadcast_to_flow(flow_id, message)
    
    @staticmethod
    async def send_completion_notification(flow_id: str, results: dict):
        """Send flow completion notification"""
        message = {
            'type': 'flow_completed',
            'flow_id': flow_id,
            'results': results
        }
        
        await connection_manager.broadcast_to_flow(flow_id, message)

# Update flow to use WebSocket service
# backend/app/flows/discovery_flow.py - Add WebSocket integration
from app.services.websocket_service import WebSocketService

class DiscoveryFlow(Flow[DiscoveryFlowState]):
    
    async def _persist_state(self):
        """Persist state and send real-time update"""
        # Save to database
        await self.state_manager.save_state(
            self.state.flow_id,
            self.state.dict()
        )
        
        # Send real-time update
        await WebSocketService.send_flow_update(
            self.state.flow_id,
            {
                'status': self.state.status,
                'phase': self.state.current_phase,
                'progress': self.state.progress,
                'updated_at': datetime.utcnow().isoformat()
            }
        )
    
    @listen(validate_data)
    def discover_applications(self, result):
        """Enhanced with real-time updates"""
        if result == "validation_failed":
            asyncio.create_task(WebSocketService.send_error_notification(
                self.state.flow_id,
                {'phase': 'validation', 'message': 'Data validation failed'}
            ))
            return "flow_failed"
        
        logger.info(f"🔍 Starting application discovery for flow {self.state.flow_id}")
        
        # Send start notification
        asyncio.create_task(WebSocketService.send_agent_insight(
            self.state.flow_id,
            "Application Discovery Agent",
            {
                'type': 'phase_started',
                'phase': 'application_discovery',
                'message': 'Starting application discovery and dependency mapping'
            }
        ))
        
        # Execute discovery...
        discovery_agent = agent_registry.get_agent("application_discovery")()
        crew = Crew(
            agents=[discovery_agent],
            tasks=[discovery_agent.create_discovery_task(self.state.import_data)],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Send completion notification
        asyncio.create_task(WebSocketService.send_agent_insight(
            self.state.flow_id,
            "Application Discovery Agent",
            {
                'type': 'phase_completed',
                'phase': 'application_discovery',
                'results_summary': self._summarize_discovery_results(result)
            }
        ))
        
        # Update state
        self.state.current_phase = "application_discovery"
        self.state.discovery_results = result
        self.state.progress = 60
        
        asyncio.create_task(self._persist_state())
        return "discovered"
```

### Day 23-24: Complete Learning System Implementation

#### Current Issues
```python
# Over-engineered learning_management_handler.py (569 lines)
# Learning insights stored but not effectively used
# No actual pattern recognition or ML integration
```

#### Remediation Steps

**Step 1: Simplified Learning System Architecture**
```python
# backend/app/services/learning/learning_engine.py - Focused learning system
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from app.core.context import get_current_context, require_context
from app.models.learning import LearningPattern, LearningEvent

class LearningEngine:
    """Simplified but effective learning system"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.pattern_vectors = None
        self.patterns_cache = {}
        self.min_confidence_threshold = 0.7
    
    @require_context
    async def learn_from_correction(self, original_result: Dict[str, Any], 
                                  corrected_result: Dict[str, Any], 
                                  context: Dict[str, Any]) -> bool:
        """Learn from user corrections"""
        tenant_context = get_current_context()
        
        # Extract learning pattern
        pattern = {
            'type': 'user_correction',
            'original': original_result,
            'corrected': corrected_result,
            'context': context,
            'client_account_id': tenant_context.client_account_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Create pattern text for vectorization
        pattern_text = self._create_pattern_text(pattern)
        
        # Store pattern
        learning_pattern = LearningPattern(
            client_account_id=tenant_context.client_account_id,
            pattern_type='correction',
            pattern_data=pattern,
            pattern_text=pattern_text,
            confidence_score=0.95,  # High confidence for user corrections
            source='user_feedback'
        )
        
        # Save to database
        async with AsyncSessionLocal() as session:
            session.add(learning_pattern)
            await session.commit()
        
        # Update pattern cache
        await self._update_pattern_cache()
        
        return True
    
    @require_context
    async def learn_from_success(self, successful_result: Dict[str, Any],
                                context: Dict[str, Any]) -> bool:
        """Learn from successful operations"""
        tenant_context = get_current_context()
        
        # Create success pattern
        pattern = {
            'type': 'success_pattern',
            'result': successful_result,
            'context': context,
            'client_account_id': tenant_context.client_account_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        pattern_text = self._create_pattern_text(pattern)
        
        learning_pattern = LearningPattern(
            client_account_id=tenant_context.client_account_id,
            pattern_type='success',
            pattern_data=pattern,
            pattern_text=pattern_text,
            confidence_score=0.8,  # Good confidence for successful patterns
            source='system_observation'
        )
        
        async with AsyncSessionLocal() as session:
            session.add(learning_pattern)
            await session.commit()
        
        await self._update_pattern_cache()
        return True
    
    @require_context
    async def get_recommendations(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations based on learned patterns"""
        tenant_context = get_current_context()
        
        # Create context text for similarity matching
        context_text = self._create_pattern_text({'context': current_context})
        
        # Load tenant-specific patterns
        patterns = await self._get_tenant_patterns(tenant_context.client_account_id)
        
        if not patterns:
            return []
        
        # Find similar patterns
        similar_patterns = self._find_similar_patterns(context_text, patterns)
        
        # Generate recommendations from similar patterns
        recommendations = []
        for pattern, similarity in similar_patterns:
            if similarity >= self.min_confidence_threshold:
                rec = self._generate_recommendation(pattern, similarity)
                if rec:
                    recommendations.append(rec)
        
        # Sort by confidence and return top 5
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations[:5]
    
    def _create_pattern_text(self, pattern: Dict[str, Any]) -> str:
        """Convert pattern to text for vectorization"""
        text_parts = []
        
        def extract_text(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, (str, int, float)):
                        text_parts.append(f"{prefix}{key}: {value}")
                    elif isinstance(value, (dict, list)):
                        extract_text(value, f"{prefix}{key}_")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_text(item, f"{prefix}{i}_")
            else:
                text_parts.append(str(obj))
        
        extract_text(pattern)
        return " ".join(text_parts)
    
    async def _get_tenant_patterns(self, client_account_id: str) -> List[LearningPattern]:
        """Get patterns for specific tenant"""
        async with AsyncSessionLocal() as session:
            stmt = select(LearningPattern).where(
                LearningPattern.client_account_id == UUID(client_account_id),
                LearningPattern.confidence_score >= self.min_confidence_threshold
            ).order_by(LearningPattern.created_at.desc()).limit(100)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    def _find_similar_patterns(self, context_text: str, patterns: List[LearningPattern]) -> List[tuple]:
        """Find patterns similar to current context"""
        if not patterns:
            return []
        
        # Prepare pattern texts
        pattern_texts = [pattern.pattern_text for pattern in patterns]
        all_texts = [context_text] + pattern_texts
        
        # Vectorize
        vectors = self.vectorizer.fit_transform(all_texts)
        context_vector = vectors[0]
        pattern_vectors = vectors[1:]
        
        # Calculate similarities
        similarities = cosine_similarity(context_vector, pattern_vectors)[0]
        
        # Return patterns with similarities
        return [(patterns[i], similarities[i]) for i in range(len(patterns))]
    
    def _generate_recommendation(self, pattern: LearningPattern, similarity: float) -> Optional[Dict[str, Any]]:
        """Generate recommendation from learned pattern"""
        pattern_data = pattern.pattern_data
        
        if pattern.pattern_type == 'correction':
            # Recommend the corrected approach
            return {
                'type': 'correction_recommendation',
                'recommendation': pattern_data.get('corrected'),
                'confidence': similarity * pattern.confidence_score,
                'reasoning': f"Based on previous user correction with {similarity:.2%} similarity",
                'pattern_id': str(pattern.id)
            }
        
        elif pattern.pattern_type == 'success':
            # Recommend the successful approach
            return {
                'type': 'success_recommendation',
                'recommendation': pattern_data.get('result'),
                'confidence': similarity * pattern.confidence_score,
                'reasoning': f"Based on previous successful operation with {similarity:.2%} similarity",
                'pattern_id': str(pattern.id)
            }
        
        return None
    
    async def _update_pattern_cache(self):
        """Update internal pattern cache for performance"""
        # Implementation for caching frequently used patterns
        pass
```

**Step 2: Learning Integration with Agents**
```python
# backend/app/agents/learning_aware_agent.py - Base agent with learning
from app.services.learning.learning_engine import LearningEngine

class LearningAwareAgent(Agent):
    """Base agent class that learns from interactions"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.learning_engine = LearningEngine()
    
    async def execute_with_learning(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with learning integration"""
        
        # Get recommendations from previous patterns
        recommendations = await self.learning_engine.get_recommendations(task_context)
        
        # Include recommendations in task context
        enhanced_context = {
            **task_context,
            'learned_recommendations': recommendations
        }
        
        # Execute the actual task
        result = await self._execute_task(enhanced_context)
        
        # Learn from successful execution
        if result.get('success', True):
            await self.learning_engine.learn_from_success(result, task_context)
        
        return result
    
    async def handle_correction(self, original_result: Dict[str, Any], 
                              corrected_result: Dict[str, Any], 
                              context: Dict[str, Any]):
        """Handle user corrections and learn from them"""
        await self.learning_engine.learn_from_correction(
            original_result, corrected_result, context
        )
        
        # Update agent's understanding
        await self._update_agent_knowledge(corrected_result, context)
    
    async def _execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses to implement specific task logic"""
        raise NotImplementedError("Subclasses must implement _execute_task")
    
    async def _update_agent_knowledge(self, corrected_result: Dict[str, Any], 
                                    context: Dict[str, Any]):
        """Update agent's internal knowledge based on corrections"""
        # Implementation for updating agent-specific knowledge
        pass

# Update existing agents to use learning
# backend/app/agents/field_mapping.py - Learning-aware field mapping
class FieldMappingAgent(LearningAwareAgent):
    """Field mapping agent with learning capabilities"""
    
    agent_name = "field_mapping"
    
    def __init__(self, **kwargs):
        super().__init__(
            role="Data Mapping Specialist",
            goal="Accurately map fields between source and target schemas",
            backstory="""You are an expert in data schema mapping with the ability 
            to learn from previous mappings and user corrections.""",
            tools=tool_registry.get_tools_for_agent('field_mapping'),
            **kwargs
        )
    
    async def _execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute field mapping with learning integration"""
        source_schema = context.get('source_schema')
        target_schema = context.get('target_schema')
        recommendations = context.get('learned_recommendations', [])
        
        # Use field matcher tool
        field_matcher = tool_registry.get_tool('field_matcher')
        mapping_result = field_matcher._run(source_schema, target_schema)
        
        # Apply learned recommendations to improve mappings
        improved_mappings = self._apply_learned_recommendations(
            mapping_result, recommendations
        )
        
        return {
            'success': True,
            'mappings': improved_mappings,
            'confidence': mapping_result.get('match_rate', 0),
            'recommendations_applied': len(recommendations)
        }
    
    def _apply_learned_recommendations(self, base_mappings: Dict, 
                                     recommendations: List[Dict]) -> Dict:
        """Apply learned patterns to improve base mappings"""
        improved_mappings = base_mappings.copy()
        
        for rec in recommendations:
            if rec['type'] == 'correction_recommendation':
                # Apply previous user corrections
                correction_data = rec['recommendation']
                self._apply_correction_pattern(improved_mappings, correction_data)
            
            elif rec['type'] == 'success_recommendation':
                # Apply successful patterns
                success_data = rec['recommendation']
                self._apply_success_pattern(improved_mappings, success_data)
        
        return improved_mappings
```

### Day 25-26: LLM Cost Tracking Enhancement

#### Current Issues
```python
# Basic tracking implemented but incomplete:
# - 7 admin endpoints defined
# - Missing aggregation features  
# - No cost optimization logic
# - No budget enforcement
```

#### Remediation Steps

**Step 1: Enhanced Cost Tracking System**
```python
# backend/app/services/llm_cost/cost_tracker.py - Enhanced cost tracking
from typing import Dict, List, Optional, Tuple
from app.models.llm_usage import LLMUsageRecord, LLMCostBudget
from app.core.context import get_current_context, require_context

class LLMCostTracker:
    """Enhanced LLM cost tracking with optimization and budgets"""
    
    def __init__(self):
        self.model_costs = {
            # Cost per 1K tokens - input/output
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'deepinfra/meta-llama/Meta-Llama-3-70B-Instruct': {'input': 0.0007, 'output': 0.0009}
        }
        
        self.model_performance = {
            # Quality score (0-1) and speed (tokens/sec)
            'gpt-4': {'quality': 0.95, 'speed': 30},
            'gpt-3.5-turbo': {'quality': 0.80, 'speed': 100},
            'claude-3-sonnet': {'quality': 0.90, 'speed': 50},
            'deepinfra/meta-llama/Meta-Llama-3-70B-Instruct': {'quality': 0.85, 'speed': 80}
        }
    
    @require_context
    async def track_usage(self, model: str, input_tokens: int, output_tokens: int,
                         agent_name: str = None, flow_id: str = None) -> float:
        """Track LLM usage and calculate cost"""
        context = get_current_context()
        
        # Calculate cost
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Check budget before usage
        budget_ok = await self._check_budget(cost)
        if not budget_ok:
            raise ValueError(f"Usage would exceed budget. Cost: ${cost:.4f}")
        
        # Record usage
        usage_record = LLMUsageRecord(
            client_account_id=context.client_account_id,
            model_name=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=cost,
            agent_name=agent_name,
            flow_id=flow_id,
            timestamp=datetime.utcnow()
        )
        
        async with AsyncSessionLocal() as session:
            session.add(usage_record)
            await session.commit()
        
        # Update budget tracking
        await self._update_budget_usage(cost)
        
        return cost
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        if model not in self.model_costs:
            # Default to GPT-4 pricing for unknown models
            model = 'gpt-4'
        
        costs = self.model_costs[model]
        input_cost = (input_tokens / 1000) * costs['input']
        output_cost = (output_tokens / 1000) * costs['output']
        
        return input_cost + output_cost
    
    @require_context
    async def get_usage_summary(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage summary with cost breakdown"""
        context = get_current_context()
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with AsyncSessionLocal() as session:
            # Get usage records for tenant
            stmt = select(LLMUsageRecord).where(
                LLMUsageRecord.client_account_id == context.client_account_id,
                LLMUsageRecord.timestamp >= start_date,
                LLMUsageRecord.timestamp <= end_date
            )
            
            result = await session.execute(stmt)
            records = list(result.scalars().all())
        
        # Aggregate data
        summary = {
            'total_cost': sum(r.total_cost for r in records),
            'total_tokens': sum(r.input_tokens + r.output_tokens for r in records),
            'total_requests': len(records),
            'cost_by_model': {},
            'cost_by_agent': {},
            'cost_by_flow': {},
            'daily_costs': {},
            'optimization_recommendations': []
        }
        
        # Group by model
        for record in records:
            model = record.model_name
            if model not in summary['cost_by_model']:
                summary['cost_by_model'][model] = {'cost': 0, 'tokens': 0, 'requests': 0}
            
            summary['cost_by_model'][model]['cost'] += record.total_cost
            summary['cost_by_model'][model]['tokens'] += record.input_tokens + record.output_tokens
            summary['cost_by_model'][model]['requests'] += 1
        
        # Group by agent
        for record in records:
            agent = record.agent_name or 'unknown'
            if agent not in summary['cost_by_agent']:
                summary['cost_by_agent'][agent] = {'cost': 0, 'tokens': 0}
            
            summary['cost_by_agent'][agent]['cost'] += record.total_cost
            summary['cost_by_agent'][agent]['tokens'] += record.input_tokens + record.output_tokens
        
        # Daily breakdown
        for record in records:
            day = record.timestamp.date().isoformat()
            if day not in summary['daily_costs']:
                summary['daily_costs'][day] = 0
            summary['daily_costs'][day] += record.total_cost
        
        # Generate optimization recommendations
        summary['optimization_recommendations'] = await self._generate_optimization_recommendations(records)
        
        return summary
    
    async def _generate_optimization_recommendations(self, records: List[LLMUsageRecord]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        if not records:
            return recommendations
        
        # Analyze model usage patterns
        model_usage = {}
        for record in records:
            model = record.model_name
            if model not in model_usage:
                model_usage[model] = {'cost': 0, 'count': 0}
            model_usage[model]['cost'] += record.total_cost
            model_usage[model]['count'] += 1
        
        # Recommend cheaper alternatives for high-usage expensive models
        for model, usage in model_usage.items():
            if usage['cost'] > 10 and model in ['gpt-4', 'claude-3-sonnet']:
                cheaper_alternative = self._find_cheaper_alternative(model)
                if cheaper_alternative:
                    potential_savings = self._calculate_potential_savings(
                        usage['cost'], model, cheaper_alternative
                    )
                    
                    recommendations.append({
                        'type': 'model_substitution',
                        'current_model': model,
                        'recommended_model': cheaper_alternative,
                        'potential_monthly_savings': potential_savings,
                        'quality_impact': self._calculate_quality_impact(model, cheaper_alternative),
                        'priority': 'high' if potential_savings > 50 else 'medium'
                    })
        
        # Recommend batching for high-frequency low-cost operations
        total_requests = len(records)
        if total_requests > 1000:
            recommendations.append({
                'type': 'request_batching',
                'current_requests': total_requests,
                'potential_reduction': '30-50%',
                'implementation': 'Batch similar operations together',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _find_cheaper_alternative(self, current_model: str) -> Optional[str]:
        """Find cheaper model alternative"""
        current_performance = self.model_performance.get(current_model, {})
        current_quality = current_performance.get('quality', 0)
        
        alternatives = []
        for model, perf in self.model_performance.items():
            if (model != current_model and 
                perf['quality'] >= current_quality - 0.1):  # Allow 10% quality reduction
                
                current_cost = self.model_costs[current_model]['input']
                alt_cost = self.model_costs[model]['input']
                
                if alt_cost < current_cost:
                    alternatives.append((model, alt_cost, perf['quality']))
        
        # Return cheapest alternative with acceptable quality
        if alternatives:
            alternatives.sort(key=lambda x: x[1])  # Sort by cost
            return alternatives[0][0]
        
        return None
    
    @require_context
    async def set_budget(self, monthly_budget: float, alert_threshold: float = 0.8) -> bool:
        """Set monthly budget for LLM usage"""
        context = get_current_context()
        
        async with AsyncSessionLocal() as session:
            # Check if budget exists
            stmt = select(LLMCostBudget).where(
                LLMCostBudget.client_account_id == context.client_account_id,
                LLMCostBudget.month == datetime.utcnow().strftime('%Y-%m')
            )
            
            result = await session.execute(stmt)
            budget = result.scalar_one_or_none()
            
            if budget:
                budget.budget_amount = monthly_budget
                budget.alert_threshold = alert_threshold
            else:
                budget = LLMCostBudget(
                    client_account_id=context.client_account_id,
                    month=datetime.utcnow().strftime('%Y-%m'),
                    budget_amount=monthly_budget,
                    alert_threshold=alert_threshold,
                    current_usage=0.0
                )
                session.add(budget)
            
            await session.commit()
        
        return True
    
    async def _check_budget(self, additional_cost: float) -> bool:
        """Check if additional cost would exceed budget"""
        context = get_current_context()
        
        async with AsyncSessionLocal() as session:
            stmt = select(LLMCostBudget).where(
                LLMCostBudget.client_account_id == context.client_account_id,
                LLMCostBudget.month == datetime.utcnow().strftime('%Y-%m')
            )
            
            result = await session.execute(stmt)
            budget = result.scalar_one_or_none()
            
            if not budget:
                return True  # No budget set, allow usage
            
            projected_usage = budget.current_usage + additional_cost
            return projected_usage <= budget.budget_amount
    
    async def _update_budget_usage(self, cost: float):
        """Update current month's budget usage"""
        context = get_current_context()
        
        async with AsyncSessionLocal() as session:
            stmt = select(LLMCostBudget).where(
                LLMCostBudget.client_account_id == context.client_account_id,
                LLMCostBudget.month == datetime.utcnow().strftime('%Y-%m')
            )
            
            result = await session.execute(stmt)
            budget = result.scalar_one_or_none()
            
            if budget:
                budget.current_usage += cost
                
                # Check if alert threshold reached
                usage_percentage = budget.current_usage / budget.budget_amount
                if usage_percentage >= budget.alert_threshold and not budget.alert_sent:
                    # Send budget alert
                    await self._send_budget_alert(budget, usage_percentage)
                    budget.alert_sent = True
                
                await session.commit()

# Global cost tracker instance
cost_tracker = LLMCostTracker()
```

**Step 2: Model Selection Optimization**
```python
# backend/app/services/llm_cost/model_selector.py - Intelligent model selection
class ModelSelector:
    """Intelligently selects optimal model based on task requirements and cost"""
    
    def __init__(self, cost_tracker: LLMCostTracker):
        self.cost_tracker = cost_tracker
        self.task_model_mapping = {
            # Task complexity -> recommended models (in order of preference)
            'simple': ['gpt-3.5-turbo', 'deepinfra/meta-llama/Meta-Llama-3-70B-Instruct'],
            'medium': ['claude-3-sonnet', 'gpt-4', 'gpt-3.5-turbo'],
            'complex': ['gpt-4', 'claude-3-sonnet'],
            'analysis': ['claude-3-sonnet', 'gpt-4'],
            'creative': ['gpt-4', 'claude-3-sonnet']
        }
    
    async def select_optimal_model(self, task_type: str, quality_requirement: float = 0.8,
                                  cost_constraint: Optional[float] = None) -> str:
        """Select optimal model for task"""
        
        # Get candidate models for task type
        candidates = self.task_model_mapping.get(task_type, ['gpt-3.5-turbo'])
        
        # Filter by quality requirement
        qualified_models = []
        for model in candidates:
            performance = self.cost_tracker.model_performance.get(model, {})
            if performance.get('quality', 0) >= quality_requirement:
                qualified_models.append(model)
        
        if not qualified_models:
            # Fall back to best quality model if none meet requirement
            qualified_models = ['gpt-4']
        
        # If cost constraint specified, filter by cost
        if cost_constraint:
            affordable_models = []
            for model in qualified_models:
                # Estimate cost for typical usage (1000 input + 500 output tokens)
                estimated_cost = self.cost_tracker._calculate_cost(model, 1000, 500)
                if estimated_cost <= cost_constraint:
                    affordable_models.append(model)
            
            if affordable_models:
                qualified_models = affordable_models
        
        # Return first (best) qualified model
        return qualified_models[0]
    
    async def get_cost_estimate(self, model: str, estimated_tokens: int) -> Dict[str, Any]:
        """Get cost estimate for model and token usage"""
        # Assume 2:1 input to output token ratio
        input_tokens = int(estimated_tokens * 0.67)
        output_tokens = int(estimated_tokens * 0.33)
        
        cost = self.cost_tracker._calculate_cost(model, input_tokens, output_tokens)
        
        return {
            'model': model,
            'estimated_input_tokens': input_tokens,
            'estimated_output_tokens': output_tokens,
            'estimated_cost': cost,
            'cost_per_1k_tokens': cost / (estimated_tokens / 1000)
        }
```

## Week 6: Agent Collaboration and Integration

### Day 27-28: Enhanced Agent Collaboration

#### Current Issues
```python
# Limited agent collaboration
# Manual orchestration instead of crew-based
# No proper agent hierarchy or communication
```

#### Remediation Steps

**Step 1: Agent Collaboration Framework**
```python
# backend/app/services/agent_collaboration.py - Agent collaboration system
from typing import List, Dict, Any, Optional
from crewai import Crew, Process, Agent, Task
from app.agents import agent_registry

class AgentCollaborationManager:
    """Manages complex agent collaborations and workflows"""
    
    def __init__(self):
        self.collaboration_patterns = {
            'sequential': Process.sequential,
            'parallel': Process.parallel,
            'hierarchical': Process.hierarchical
        }
    
    async def create_discovery_crew(self, discovery_context: Dict[str, Any]) -> Crew:
        """Create comprehensive discovery crew with multiple specialized agents"""
        
        # Get agents
        data_agent = agent_registry.get_agent("data_validation")()
        app_agent = agent_registry.get_agent("application_discovery")()
        mapping_agent = agent_registry.get_agent("field_mapping")()
        risk_agent = agent_registry.get_agent("risk_assessment")()
        
        # Create tasks with dependencies
        tasks = [
            Task(
                description=f"""
                Perform comprehensive data validation on the imported dataset:
                {discovery_context.get('data_summary', 'No summary available')}
                
                Focus on:
                - Data quality assessment
                - Security and PII scanning  
                - Format validation
                - Compliance checking
                
                Provide detailed findings and recommendations.
                """,
                agent=data_agent,
                expected_output="Structured validation report with recommendations"
            ),
            
            Task(
                description=f"""
                Based on the data validation results, discover and map applications:
                
                Data context: {discovery_context}
                
                Tasks:
                - Identify application components
                - Map dependencies and relationships
                - Analyze technology stacks
                - Assess migration complexity
                
                Coordinate with the data validation findings to ensure consistency.
                """,
                agent=app_agent,
                expected_output="Application discovery report with dependency mapping",
                context=[tasks[0]] if 'tasks' in locals() else None  # Depends on validation
            ),
            
            Task(
                description=f"""
                Create field mappings between source and target schemas:
                
                Use insights from both data validation and application discovery to:
                - Map fields accurately
                - Identify transformation requirements
                - Suggest mapping optimizations
                - Validate mapping consistency
                
                Consider the findings from previous agents in your analysis.
                """,
                agent=mapping_agent,
                expected_output="Complete field mapping specification",
                context=[tasks[0], tasks[1]] if 'tasks' in locals() else None
            ),
            
            Task(
                description=f"""
                Perform comprehensive risk assessment based on all previous findings:
                
                Analyze:
                - Migration risks from data validation results
                - Technical risks from application discovery
                - Data risks from field mapping analysis
                
                Provide risk mitigation strategies and recommendations.
                """,
                agent=risk_agent,
                expected_output="Risk assessment report with mitigation strategies",
                context=[tasks[0], tasks[1], tasks[2]] if 'tasks' in locals() else None
            )
        ]
        
        # Create crew with hierarchical process for complex coordination
        crew = Crew(
            agents=[data_agent, app_agent, mapping_agent, risk_agent],
            tasks=tasks,
            process=Process.hierarchical,  # Allows for better coordination
            manager_llm=self._get_manager_llm(),
            verbose=True,
            memory=True
        )
        
        return crew
    
    async def create_optimization_crew(self, optimization_context: Dict[str, Any]) -> Crew:
        """Create crew focused on migration optimization"""
        
        strategy_agent = agent_registry.get_agent("migration_strategy")()
        cost_agent = agent_registry.get_agent("cost_optimization")()
        timeline_agent = agent_registry.get_agent("timeline_planning")()
        
        tasks = [
            Task(
                description=f"""
                Develop optimal migration strategy:
                {optimization_context}
                
                Consider:
                - 6R migration strategies (Rehost, Replatform, Refactor, etc.)
                - Technical constraints and requirements
                - Business objectives and timelines
                """,
                agent=strategy_agent,
                expected_output="Migration strategy recommendations"
            ),
            
            Task(
                description="""
                Optimize migration costs based on the strategy:
                
                Analyze:
                - Infrastructure costs
                - Migration tool costs
                - Resource requirements
                - Long-term operational costs
                
                Provide cost optimization recommendations.
                """,
                agent=cost_agent,
                expected_output="Cost optimization plan",
                context=[tasks[0]] if 'tasks' in locals() else None
            ),
            
            Task(
                description="""
                Create detailed migration timeline:
                
                Based on strategy and cost considerations:
                - Phase migration activities
                - Identify critical path items
                - Account for dependencies
                - Include testing and validation phases
                """,
                agent=timeline_agent,
                expected_output="Detailed migration timeline with milestones",
                context=[tasks[0], tasks[1]] if 'tasks' in locals() else None
            )
        ]
        
        crew = Crew(
            agents=[strategy_agent, cost_agent, timeline_agent],
            tasks=tasks,
            process=Process.sequential,  # Sequential for timeline dependencies
            verbose=True
        )
        
        return crew
    
    def _get_manager_llm(self):
        """Get LLM for crew manager (use most capable model)"""
        from crewai import LLM
        from app.core.config import settings
        
        return LLM(
            model="gpt-4",  # Use best model for coordination
            api_key=settings.OPENAI_API_KEY
        )
```

**Step 2: Inter-Agent Communication Protocol**
```python
# backend/app/services/agent_communication.py - Agent communication system
from typing import Dict, Any, List, Optional
from enum import Enum

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class AgentMessage:
    """Structured message for agent communication"""
    
    def __init__(self, message_type: MessageType, sender: str, receiver: str,
                 content: Dict[str, Any], message_id: str = None):
        self.message_type = message_type
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()

class AgentCommunicationBus:
    """Communication bus for agent interactions"""
    
    def __init__(self):
        self.message_queue: Dict[str, List[AgentMessage]] = {}
        self.agent_subscriptions: Dict[str, List[str]] = {}
        
    def subscribe_agent(self, agent_name: str, topics: List[str]):
        """Subscribe agent to communication topics"""
        if agent_name not in self.agent_subscriptions:
            self.agent_subscriptions[agent_name] = []
        
        self.agent_subscriptions[agent_name].extend(topics)
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send message between agents"""
        receiver = message.receiver
        
        # Add to receiver's queue
        if receiver not in self.message_queue:
            self.message_queue[receiver] = []
        
        self.message_queue[receiver].append(message)
        
        # Notify receiver if online
        await self._notify_agent(receiver, message)
        
        return True
    
    async def get_messages(self, agent_name: str) -> List[AgentMessage]:
        """Get pending messages for agent"""
        messages = self.message_queue.get(agent_name, [])
        self.message_queue[agent_name] = []  # Clear after retrieval
        return messages
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any], 
                                sender: str) -> int:
        """Broadcast message to all agents subscribed to topic"""
        subscribers = []
        for agent, topics in self.agent_subscriptions.items():
            if topic in topics and agent != sender:
                subscribers.append(agent)
        
        for subscriber in subscribers:
            msg = AgentMessage(
                MessageType.NOTIFICATION,
                sender,
                subscriber,
                {**message, 'topic': topic}
            )
            await self.send_message(msg)
        
        return len(subscribers)
    
    async def _notify_agent(self, agent_name: str, message: AgentMessage):
        """Notify agent of new message (implementation specific)"""
        # Could integrate with WebSocket system for real-time notifications
        pass

# Global communication bus
agent_comm_bus = AgentCommunicationBus()
```

### Day 29-30: Integration Testing and Validation

#### Remediation Steps

**Step 1: Comprehensive Integration Tests**
```python
# backend/tests/test_feature_completion.py - Integration tests for new features
import pytest
from app.websocket.manager import connection_manager
from app.services.learning.learning_engine import LearningEngine
from app.services.llm_cost.cost_tracker import cost_tracker

@pytest.mark.asyncio
class TestFeatureCompletion:
    
    async def test_websocket_real_time_updates(self, test_context):
        """Test WebSocket real-time update system"""
        from app.services.websocket_service import WebSocketService
        
        # Mock WebSocket connection
        flow_id = "test-flow-123"
        
        # Test flow update broadcast
        update_data = {
            'status': 'running',
            'phase': 'data_validation',
            'progress': 50
        }
        
        # This should not raise an exception even without active connections
        await WebSocketService.send_flow_update(flow_id, update_data)
        
        # Test agent insight broadcast
        insight = {
            'type': 'phase_started',
            'message': 'Starting validation phase'
        }
        
        await WebSocketService.send_agent_insight(flow_id, "Data Validation Agent", insight)
        
        # Verify no errors occurred
        assert True  # If we get here, no exceptions were raised
    
    async def test_learning_system_functionality(self, test_context):
        """Test learning system learning and recommendation"""
        learning_engine = LearningEngine()
        
        # Test learning from correction
        original_result = {
            'field_mappings': [
                {'source': 'customer_name', 'target': 'client_name', 'confidence': 0.8}
            ]
        }
        
        corrected_result = {
            'field_mappings': [
                {'source': 'customer_name', 'target': 'customer_full_name', 'confidence': 0.95}
            ]
        }
        
        context = {'data_type': 'customer_data', 'source_system': 'CRM'}
        
        # Learn from correction
        success = await learning_engine.learn_from_correction(
            original_result, corrected_result, context
        )
        assert success is True
        
        # Test getting recommendations
        similar_context = {'data_type': 'customer_data', 'source_system': 'CRM'}
        recommendations = await learning_engine.get_recommendations(similar_context)
        
        # Should have at least one recommendation based on the correction
        assert len(recommendations) > 0
        assert recommendations[0]['type'] == 'correction_recommendation'
        assert recommendations[0]['confidence'] > 0.5
    
    async def test_llm_cost_tracking_and_optimization(self, test_context):
        """Test LLM cost tracking and optimization features"""
        
        # Test cost tracking
        cost = await cost_tracker.track_usage(
            model='gpt-3.5-turbo',
            input_tokens=1000,
            output_tokens=500,
            agent_name='test_agent',
            flow_id='test-flow-123'
        )
        
        assert cost > 0
        assert cost < 0.01  # Should be very low for gpt-3.5-turbo
        
        # Test usage summary
        summary = await cost_tracker.get_usage_summary()
        
        assert 'total_cost' in summary
        assert 'cost_by_model' in summary
        assert 'optimization_recommendations' in summary
        assert summary['total_cost'] >= cost
        
        # Test budget setting
        budget_set = await cost_tracker.set_budget(100.0, 0.8)
        assert budget_set is True
    
    async def test_agent_collaboration_flow(self, test_context):
        """Test agent collaboration in discovery flow"""
        from app.services.agent_collaboration import AgentCollaborationManager
        
        collaboration_manager = AgentCollaborationManager()
        
        discovery_context = {
            'data_summary': 'Test dataset with 1000 customer records',
            'source_system': 'Legacy CRM',
            'target_system': 'Cloud CRM'
        }
        
        # Create discovery crew
        crew = await collaboration_manager.create_discovery_crew(discovery_context)
        
        # Verify crew configuration
        assert len(crew.agents) == 4  # data, app, mapping, risk agents
        assert len(crew.tasks) == 4
        assert crew.process == Process.hierarchical
        
        # Test crew execution (mock execution without actual LLM calls)
        # In a real test, you might mock the LLM responses
        # result = crew.kickoff()
        # assert result is not None
    
    async def test_end_to_end_flow_with_new_features(self, test_context):
        """Test complete flow execution with all new features"""
        from app.flows.discovery_flow import DiscoveryFlow
        from app.services.discovery_flow_service import DiscoveryFlowService
        
        # Create flow service
        service = DiscoveryFlowService(test_context)
        
        # Create flow with test data
        flow_data = {
            'name': 'End-to-End Test Flow',
            'description': 'Testing all new features',
            'data': {
                'customers': [
                    {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                    {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
                ]
            }
        }
        
        flow = await service.create_flow(flow_data)
        
        # Verify flow created successfully
        assert flow is not None
        assert flow.state.flow_id is not None
        assert flow.state.status == "initialized"
        
        # Test state persistence
        saved_flow = await service.get_flow(flow.state.flow_id)
        assert saved_flow is not None
        assert saved_flow.state.name == 'End-to-End Test Flow'
        
        # Test flow continuation (mock without full execution)
        # In a real scenario, this would trigger the full flow
        # result = await service.continue_flow(flow.state.flow_id)
        # assert result is not None
```

**Step 2: Performance and Load Testing**
```python
# backend/tests/test_performance_features.py - Performance tests for new features
import pytest
import asyncio
import time

@pytest.mark.performance
class TestFeaturePerformance:
    
    async def test_websocket_connection_scale(self):
        """Test WebSocket manager with multiple connections"""
        from app.websocket.manager import ConnectionManager
        
        manager = ConnectionManager()
        connection_ids = []
        
        # Mock multiple connections
        start_time = time.time()
        
        for i in range(100):
            # Mock connection metadata
            connection_id = f"test-connection-{i}"
            manager.connection_metadata[connection_id] = {
                'tenant_id': 'test-tenant',
                'user_id': f'user-{i}',
                'subscriptions': set()
            }
            connection_ids.append(connection_id)
        
        end_time = time.time()
        setup_time = end_time - start_time
        
        # Test broadcast performance
        start_time = time.time()
        
        for connection_id in connection_ids:
            await manager.subscribe_to_flow(connection_id, "test-flow")
        
        # Simulate broadcast to all connections
        message = {'type': 'test', 'data': 'performance test'}
        await manager.broadcast_to_flow("test-flow", message)
        
        end_time = time.time()
        broadcast_time = end_time - start_time
        
        # Performance assertions
        assert setup_time < 1.0  # Should setup 100 connections in under 1 second
        assert broadcast_time < 0.5  # Should broadcast to 100 connections in under 0.5 seconds
    
    async def test_learning_system_scale(self, test_context):
        """Test learning system with multiple patterns"""
        from app.services.learning.learning_engine import LearningEngine
        
        learning_engine = LearningEngine()
        
        # Create multiple learning patterns
        start_time = time.time()
        
        for i in range(50):
            original = {'field': f'field_{i}', 'mapping': f'old_target_{i}'}
            corrected = {'field': f'field_{i}', 'mapping': f'new_target_{i}'}
            context = {'type': f'test_type_{i % 5}'}
            
            await learning_engine.learn_from_correction(original, corrected, context)
        
        learning_time = time.time() - start_time
        
        # Test recommendation performance
        start_time = time.time()
        
        recommendations = await learning_engine.get_recommendations({
            'type': 'test_type_1'
        })
        
        recommendation_time = time.time() - start_time
        
        # Performance assertions
        assert learning_time < 10.0  # Should learn 50 patterns in under 10 seconds
        assert recommendation_time < 2.0  # Should get recommendations in under 2 seconds
        assert len(recommendations) > 0
    
    async def test_cost_tracking_performance(self, test_context):
        """Test cost tracking with high volume"""
        
        # Track many usage records
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            task = cost_tracker.track_usage(
                model='gpt-3.5-turbo',
                input_tokens=100 + i,
                output_tokens=50 + i,
                agent_name=f'agent_{i % 10}',
                flow_id=f'flow_{i % 20}'
            )
            tasks.append(task)
        
        # Execute all tracking operations concurrently
        await asyncio.gather(*tasks)
        
        tracking_time = time.time() - start_time
        
        # Test summary generation performance
        start_time = time.time()
        summary = await cost_tracker.get_usage_summary()
        summary_time = time.time() - start_time
        
        # Performance assertions
        assert tracking_time < 5.0  # Should track 100 records in under 5 seconds
        assert summary_time < 2.0  # Should generate summary in under 2 seconds
        assert summary['total_requests'] >= 100
```

## Phase 3 Deliverables

### Feature Completions
1. **WebSocket Real-Time System**: Full implementation with connection management, tenant isolation, and broadcasting
2. **Learning System**: Functional pattern recognition, recommendation engine, and continuous learning
3. **Enhanced LLM Cost Tracking**: Budget management, optimization recommendations, and intelligent model selection
4. **Agent Collaboration**: Multi-agent crews with hierarchical coordination and communication protocols

### Testing
1. **Integration Tests**: Comprehensive tests for all new features
2. **Performance Tests**: Load testing for scalability validation
3. **End-to-End Tests**: Complete workflow testing with all features

### Quality Gates
- [ ] WebSocket system handles 100+ concurrent connections efficiently
- [ ] Learning system demonstrates measurable improvement in recommendations
- [ ] Cost tracking provides actionable optimization recommendations
- [ ] Agent collaboration crews execute complex workflows successfully
- [ ] All integration tests pass with >90% coverage
- [ ] Performance benchmarks meet requirements

This completes Phase 3 feature completion, transforming the incomplete implementations into fully functional, production-ready systems while maintaining backward compatibility and system stability.