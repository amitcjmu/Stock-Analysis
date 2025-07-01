# Implementation Plan: Part 5 - Remaining Phases (Weeks 5-10)

## Phase 3: Agent Intelligence System (Weeks 5-6)

### Week 5: Learning and Memory Systems

#### Day 21-22: Learning Infrastructure

```python
# backend/app/services/learning/pattern_store.py
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.learned_pattern import LearnedPattern
from app.services.embedding_service import EmbeddingService

class PatternStore:
    """Stores and retrieves learned patterns with vector similarity"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def store_pattern(self, pattern_type: str, pattern_data: Dict, 
                          confidence: float, context: Dict = None) -> str:
        """Store a learned pattern with vector embedding"""
        
        # Generate embedding for the pattern
        pattern_text = self._pattern_to_text(pattern_data)
        embedding = await self.embedding_service.get_embedding(pattern_text)
        
        # Create pattern record
        pattern = LearnedPattern(
            pattern_type=pattern_type,
            pattern_data=pattern_data,
            embedding=embedding,
            confidence=confidence,
            context=context or {},
            tenant_id=get_current_tenant().tenant_id
        )
        
        self.db.add(pattern)
        await self.db.commit()
        return str(pattern.id)
    
    async def find_similar_patterns(self, query_data: Dict, 
                                  pattern_type: str = None, 
                                  threshold: float = 0.8) -> List[LearnedPattern]:
        """Find patterns similar to query using vector similarity"""
        
        # Generate embedding for query
        query_text = self._pattern_to_text(query_data)
        query_embedding = await self.embedding_service.get_embedding(query_text)
        
        # Build similarity query
        query = """
        SELECT *, (embedding <-> %s) as distance
        FROM learned_patterns
        WHERE tenant_id = %s
        AND (embedding <-> %s) < %s
        """
        
        params = [query_embedding, get_current_tenant().tenant_id, 
                 query_embedding, 1.0 - threshold]
        
        if pattern_type:
            query += " AND pattern_type = %s"
            params.append(pattern_type)
        
        query += " ORDER BY distance LIMIT 10"
        
        result = await self.db.execute(query, params)
        return result.fetchall()

# backend/app/services/learning/learning_system.py
class LearningSystem:
    """Main learning system coordinator"""
    
    def __init__(self):
        self.pattern_store = None
        self.confidence_tracker = ConfidenceTracker()
        self.feedback_processor = FeedbackProcessor()
    
    async def learn_from_correction(self, agent_id: str, original_result: Dict, 
                                  corrected_result: Dict, context: Dict):
        """Learn from user corrections"""
        
        # Extract learning pattern
        pattern = self._extract_correction_pattern(
            original_result, corrected_result, agent_id
        )
        
        # Store with high confidence (user correction)
        async with AsyncSessionLocal() as db:
            pattern_store = PatternStore(db)
            await pattern_store.store_pattern(
                pattern_type=f"{agent_id}_correction",
                pattern_data=pattern,
                confidence=0.95,
                context=context
            )
        
        # Update agent confidence
        await self.confidence_tracker.adjust_confidence(
            agent_id, -0.1  # Reduce confidence due to correction
        )
    
    async def apply_learned_patterns(self, agent_id: str, input_data: Dict) -> Dict:
        """Apply learned patterns to enhance agent performance"""
        
        async with AsyncSessionLocal() as db:
            pattern_store = PatternStore(db)
            
            # Find relevant patterns
            patterns = await pattern_store.find_similar_patterns(
                query_data=input_data,
                pattern_type=f"{agent_id}_pattern"
            )
            
            # Apply patterns to enhance input
            enhanced_data = input_data.copy()
            
            for pattern in patterns:
                enhancement = self._apply_pattern(enhanced_data, pattern.pattern_data)
                enhanced_data.update(enhancement)
            
            return enhanced_data
```

#### Day 23-24: Agent Tools Implementation

```python
# backend/app/tools/database_query_tool.py
from crewai.tools import BaseTool
from typing import Dict, Any, List
from app.core.database import AsyncSessionLocal
from app.core.context import get_current_tenant

class DatabaseQueryTool(BaseTool):
    name: str = "database_query"
    description: str = "Query database for historical data and patterns"
    
    def _run(self, query_type: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute database queries for agents"""
        
        async def _execute_query():
            async with AsyncSessionLocal() as db:
                tenant = get_current_tenant()
                
                if query_type == "historical_mappings":
                    # Query for historical field mappings
                    query = """
                    SELECT source_field, target_field, confidence, count(*) as usage_count
                    FROM field_mappings 
                    WHERE tenant_id = %s
                    GROUP BY source_field, target_field, confidence
                    ORDER BY usage_count DESC, confidence DESC
                    LIMIT 50
                    """
                    result = await db.execute(query, [tenant.tenant_id])
                    return [dict(row) for row in result.fetchall()]
                
                elif query_type == "asset_patterns":
                    # Query for asset classification patterns
                    query = """
                    SELECT asset_type, characteristics, classification_confidence
                    FROM asset_classifications
                    WHERE tenant_id = %s AND classification_confidence > 0.8
                    ORDER BY classification_confidence DESC
                    LIMIT 30
                    """
                    result = await db.execute(query, [tenant.tenant_id])
                    return [dict(row) for row in result.fetchall()]
                
                return []
        
        import asyncio
        return asyncio.run(_execute_query())

# backend/app/tools/pattern_matcher_tool.py
class PatternMatcherTool(BaseTool):
    name: str = "pattern_matcher"
    description: str = "Find patterns in data using machine learning"
    
    def _run(self, data: List[Dict], pattern_type: str) -> Dict[str, Any]:
        """Find patterns in provided data"""
        
        if pattern_type == "field_names":
            return self._find_field_name_patterns(data)
        elif pattern_type == "value_formats":
            return self._find_value_format_patterns(data)
        elif pattern_type == "relationships":
            return self._find_relationship_patterns(data)
        
        return {"patterns": [], "confidence": 0.0}
    
    def _find_field_name_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Find patterns in field names"""
        
        field_names = []
        for record in data:
            field_names.extend(record.keys())
        
        # Analyze naming patterns
        patterns = {}
        
        # Common prefixes/suffixes
        prefixes = {}
        suffixes = {}
        
        for field in field_names:
            # Count prefixes (first 3 chars)
            if len(field) > 3:
                prefix = field[:3].lower()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            # Count suffixes (last 3 chars)
            if len(field) > 3:
                suffix = field[-3:].lower()
                suffixes[suffix] = suffixes.get(suffix, 0) + 1
        
        # Identify significant patterns (>10% usage)
        total_fields = len(field_names)
        threshold = total_fields * 0.1
        
        significant_prefixes = {k: v for k, v in prefixes.items() if v > threshold}
        significant_suffixes = {k: v for k, v in suffixes.items() if v > threshold}
        
        return {
            "patterns": {
                "prefixes": significant_prefixes,
                "suffixes": significant_suffixes
            },
            "confidence": 0.8 if significant_prefixes or significant_suffixes else 0.3,
            "total_fields_analyzed": total_fields
        }
```

### Week 6: Advanced Agent Capabilities

#### Day 25-26: Multi-Agent Collaboration

```python
# backend/app/services/collaboration/agent_coordinator.py
class AgentCoordinator:
    """Coordinates collaboration between agents"""
    
    def __init__(self):
        self.active_collaborations = {}
        self.shared_context = {}
    
    async def initiate_collaboration(self, initiator_agent: str, 
                                   target_agents: List[str],
                                   collaboration_type: str,
                                   context: Dict) -> str:
        """Start a collaboration session between agents"""
        
        collaboration_id = str(uuid4())
        
        collaboration = {
            'id': collaboration_id,
            'initiator': initiator_agent,
            'participants': target_agents,
            'type': collaboration_type,
            'context': context,
            'shared_insights': {},
            'status': 'active',
            'created_at': datetime.utcnow()
        }
        
        self.active_collaborations[collaboration_id] = collaboration
        
        # Notify target agents
        for agent_id in target_agents:
            await self._notify_agent_collaboration(agent_id, collaboration)
        
        return collaboration_id
    
    async def share_insight(self, collaboration_id: str, agent_id: str, 
                          insight: Dict) -> bool:
        """Share insight within collaboration session"""
        
        if collaboration_id not in self.active_collaborations:
            return False
        
        collaboration = self.active_collaborations[collaboration_id]
        
        if agent_id not in collaboration['participants']:
            return False
        
        # Store insight
        if agent_id not in collaboration['shared_insights']:
            collaboration['shared_insights'][agent_id] = []
        
        collaboration['shared_insights'][agent_id].append({
            'insight': insight,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Notify other participants
        for participant in collaboration['participants']:
            if participant != agent_id:
                await self._notify_agent_insight(participant, insight, agent_id)
        
        return True

# Enhanced agent base class with collaboration
class CollaborativeAgent(BaseAgent):
    """Base agent with collaboration capabilities"""
    
    def __init__(self):
        super().__init__()
        self.coordinator = AgentCoordinator()
        self.collaboration_sessions = {}
    
    async def request_collaboration(self, target_agents: List[str], 
                                  purpose: str, context: Dict) -> str:
        """Request collaboration with other agents"""
        
        return await self.coordinator.initiate_collaboration(
            initiator_agent=self.get_agent_id(),
            target_agents=target_agents,
            collaboration_type=purpose,
            context=context
        )
    
    async def respond_to_collaboration(self, collaboration_id: str, 
                                     response: str) -> bool:
        """Respond to collaboration request"""
        
        # Implementation depends on collaboration type
        if response == "accept":
            self.collaboration_sessions[collaboration_id] = "active"
            return True
        
        return False
```

#### Day 27-28: Performance Optimization

```python
# backend/app/services/performance/agent_optimizer.py
class AgentOptimizer:
    """Optimizes agent performance and resource usage"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.optimization_strategies = {}
    
    async def optimize_agent_execution(self, agent_id: str, 
                                     task_context: Dict) -> Dict[str, Any]:
        """Optimize agent execution based on context and history"""
        
        # Get historical performance
        metrics = await self._get_agent_metrics(agent_id)
        
        # Determine optimization strategy
        strategy = self._select_optimization_strategy(metrics, task_context)
        
        # Apply optimizations
        optimizations = {
            'model_selection': await self._optimize_model_selection(agent_id, strategy),
            'tool_selection': await self._optimize_tool_selection(agent_id, task_context),
            'parallel_execution': await self._determine_parallelization(agent_id, task_context),
            'caching_strategy': await self._optimize_caching(agent_id, task_context)
        }
        
        return optimizations
    
    async def _optimize_model_selection(self, agent_id: str, strategy: str) -> Dict:
        """Select optimal LLM model for task"""
        
        # Performance vs cost optimization
        if strategy == "fast_execution":
            return {
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.1
            }
        elif strategy == "high_accuracy":
            return {
                'model': 'gpt-4',
                'max_tokens': 2000,
                'temperature': 0.3
            }
        elif strategy == "cost_optimized":
            return {
                'model': 'claude-instant',
                'max_tokens': 800,
                'temperature': 0.2
            }
        
        return {'model': 'gpt-3.5-turbo', 'max_tokens': 1000, 'temperature': 0.2}

# backend/app/services/performance/metrics_collector.py
class MetricsCollector:
    """Collects and analyzes agent performance metrics"""
    
    def __init__(self):
        self.metrics_store = MetricsStore()
    
    async def record_agent_execution(self, agent_id: str, execution_data: Dict):
        """Record agent execution metrics"""
        
        metrics = {
            'agent_id': agent_id,
            'execution_time': execution_data.get('duration', 0),
            'tokens_used': execution_data.get('tokens', 0),
            'cost': execution_data.get('cost', 0),
            'success': execution_data.get('success', False),
            'confidence': execution_data.get('confidence', 0),
            'task_type': execution_data.get('task_type'),
            'timestamp': datetime.utcnow()
        }
        
        await self.metrics_store.store_metrics(metrics)
    
    async def analyze_performance_trends(self, agent_id: str, 
                                       timeframe_days: int = 30) -> Dict:
        """Analyze performance trends for an agent"""
        
        metrics = await self.metrics_store.get_metrics(
            agent_id=agent_id,
            timeframe_days=timeframe_days
        )
        
        if not metrics:
            return {'trend': 'no_data'}
        
        # Calculate trends
        avg_execution_time = sum(m['execution_time'] for m in metrics) / len(metrics)
        avg_confidence = sum(m['confidence'] for m in metrics) / len(metrics)
        success_rate = sum(1 for m in metrics if m['success']) / len(metrics)
        
        # Detect trends (improving/declining)
        recent_metrics = [m for m in metrics if 
                         (datetime.utcnow() - m['timestamp']).days <= 7]
        
        if recent_metrics:
            recent_success_rate = sum(1 for m in recent_metrics if m['success']) / len(recent_metrics)
            trend = 'improving' if recent_success_rate > success_rate else 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'avg_execution_time': avg_execution_time,
            'avg_confidence': avg_confidence,
            'success_rate': success_rate,
            'total_executions': len(metrics)
        }
```

## Phase 4: API and Integration Layer (Weeks 7-8)

### Week 7: RESTful API Implementation

#### Day 29-30: Core API Endpoints

```python
# backend/app/api/v1/flows.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.context import get_current_tenant, TenantContext
from app.schemas.flow import FlowCreateRequest, FlowResponse, FlowListResponse
from app.services.flow_service import FlowService
from app.flows.discovery import DiscoveryFlow

router = APIRouter()

@router.post("/", response_model=FlowResponse)
async def create_flow(
    request: FlowCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Create and start a new discovery flow"""
    
    try:
        service = FlowService(db, tenant)
        
        # Create flow record
        flow = await service.create_flow(
            flow_type=request.flow_type,
            name=request.name,
            description=request.description,
            configuration=request.configuration
        )
        
        # Start flow execution in background
        background_tasks.add_task(
            execute_discovery_flow,
            flow.id,
            request.raw_data,
            request.metadata
        )
        
        return FlowResponse.from_orm(flow)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Get flow details and current status"""
    
    service = FlowService(db, tenant)
    flow = await service.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return FlowResponse.from_orm(flow)

@router.get("/", response_model=FlowListResponse)
async def list_flows(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """List flows with filtering and pagination"""
    
    service = FlowService(db, tenant)
    flows, total = await service.list_flows(
        skip=skip,
        limit=limit,
        status_filter=status
    )
    
    return FlowListResponse(
        flows=[FlowResponse.from_orm(flow) for flow in flows],
        total=total,
        skip=skip,
        limit=limit
    )

@router.post("/{flow_id}/pause")
async def pause_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Pause a running flow"""
    
    service = FlowService(db, tenant)
    result = await service.pause_flow(flow_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Flow not found or not pausable")
    
    return {"message": "Flow paused successfully"}

@router.post("/{flow_id}/resume")
async def resume_flow(
    flow_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Resume a paused flow"""
    
    service = FlowService(db, tenant)
    flow = await service.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    if flow.status != "paused":
        raise HTTPException(status_code=400, detail="Flow is not paused")
    
    # Resume flow execution
    background_tasks.add_task(resume_flow_execution, flow_id)
    
    return {"message": "Flow resumed successfully"}

async def execute_discovery_flow(flow_id: UUID, raw_data: List[Dict], metadata: Dict):
    """Background task to execute discovery flow"""
    
    try:
        # Create and execute flow
        flow = DiscoveryFlow(raw_data=raw_data, metadata=metadata)
        result = await flow.execute_flow()
        
        # Update flow status in database
        async with AsyncSessionLocal() as db:
            service = FlowService(db, None)  # No tenant context in background
            await service.update_flow_status(flow_id, result)
            
    except Exception as e:
        logger.error(f"Flow execution failed for {flow_id}: {e}")
        # Update flow status to failed
        async with AsyncSessionLocal() as db:
            service = FlowService(db, None)
            await service.update_flow_status(flow_id, "failed", error=str(e))
```

#### Day 31-32: WebSocket Implementation

```python
# backend/app/api/websocket/flow_updates.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from uuid import UUID

from app.core.context import get_current_tenant_from_ws
from app.services.websocket_manager import WebSocketManager
from app.services.event_bus import EventBus

class FlowWebSocketManager:
    """Manages WebSocket connections for flow updates"""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
        self.user_flows: Dict[str, List[str]] = {}
        self.event_bus = EventBus()
        
        # Subscribe to flow events
        self.event_bus.subscribe("state_changed", self._handle_state_change)
        self.event_bus.subscribe("phase_started", self._handle_phase_started)
        self.event_bus.subscribe("phase_completed", self._handle_phase_completed)
        self.event_bus.subscribe("error_occurred", self._handle_error)
    
    async def connect(self, websocket: WebSocket, flow_id: str, user_id: str):
        """Connect user to flow updates"""
        
        await websocket.accept()
        
        # Add connection
        if flow_id not in self.connections:
            self.connections[flow_id] = []
        self.connections[flow_id].append(websocket)
        
        # Track user flows
        if user_id not in self.user_flows:
            self.user_flows[user_id] = []
        if flow_id not in self.user_flows[user_id]:
            self.user_flows[user_id].append(flow_id)
        
        try:
            # Send initial flow state
            initial_state = await self._get_flow_state(flow_id)
            await websocket.send_json({
                "type": "initial_state",
                "data": initial_state
            })
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)  # Heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
        except WebSocketDisconnect:
            await self.disconnect(websocket, flow_id, user_id)
    
    async def disconnect(self, websocket: WebSocket, flow_id: str, user_id: str):
        """Disconnect user from flow updates"""
        
        if flow_id in self.connections:
            if websocket in self.connections[flow_id]:
                self.connections[flow_id].remove(websocket)
            
            if not self.connections[flow_id]:
                del self.connections[flow_id]
        
        if user_id in self.user_flows and flow_id in self.user_flows[user_id]:
            self.user_flows[user_id].remove(flow_id)
    
    async def _handle_state_change(self, event):
        """Handle flow state change events"""
        
        flow_id = str(event.flow_id)
        
        if flow_id in self.connections:
            message = {
                "type": "state_change",
                "flow_id": flow_id,
                "data": event.data
            }
            
            await self._broadcast_to_flow(flow_id, message)
    
    async def _handle_phase_started(self, event):
        """Handle phase started events"""
        
        flow_id = str(event.flow_id)
        
        if flow_id in self.connections:
            message = {
                "type": "phase_started",
                "flow_id": flow_id,
                "phase": event.data["phase"]
            }
            
            await self._broadcast_to_flow(flow_id, message)
    
    async def _broadcast_to_flow(self, flow_id: str, message: Dict):
        """Broadcast message to all connections for a flow"""
        
        if flow_id not in self.connections:
            return
        
        disconnected = []
        
        for websocket in self.connections[flow_id]:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            self.connections[flow_id].remove(ws)

# WebSocket endpoint
@router.websocket("/ws/flows/{flow_id}")
async def websocket_flow_updates(
    websocket: WebSocket,
    flow_id: UUID,
    user_id: str = Query(...),  # Get from query params
):
    """WebSocket endpoint for real-time flow updates"""
    
    manager = FlowWebSocketManager()
    await manager.connect(websocket, str(flow_id), user_id)
```

### Week 8: Frontend Integration

#### Day 33-34: React Hooks and State Management

```typescript
// frontend/src/hooks/useDiscoveryFlow.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { FlowResponse, CreateFlowRequest } from '@/types/flow'
import { flowApi } from '@/services/flowApi'
import { useWebSocket } from '@/hooks/useWebSocket'

export interface UseDiscoveryFlowOptions {
  flowId?: string
  enableRealTime?: boolean
  pollInterval?: number
}

export function useDiscoveryFlow(options: UseDiscoveryFlowOptions = {}) {
  const { flowId, enableRealTime = true, pollInterval = 5000 } = options
  const queryClient = useQueryClient()
  
  // Flow query
  const flowQuery = useQuery({
    queryKey: ['flow', flowId],
    queryFn: () => flowApi.getFlow(flowId!),
    enabled: !!flowId,
    refetchInterval: enableRealTime ? undefined : pollInterval,
  })
  
  // WebSocket for real-time updates
  const { lastMessage, connectionStatus } = useWebSocket(
    flowId && enableRealTime ? `/ws/flows/${flowId}` : null,
    {
      onMessage: (event) => {
        const message = JSON.parse(event.data)
        
        if (message.type === 'state_change') {
          // Update query cache with new state
          queryClient.setQueryData(['flow', flowId], (old: FlowResponse | undefined) => {
            if (!old) return old
            
            return {
              ...old,
              ...message.data,
              updated_at: new Date().toISOString()
            }
          })
        }
        
        if (message.type === 'phase_started') {
          // Show notification or update UI
          console.log(`Phase started: ${message.phase}`)
        }
      }
    }
  )
  
  // Create flow mutation
  const createFlowMutation = useMutation({
    mutationFn: (data: CreateFlowRequest) => flowApi.createFlow(data),
    onSuccess: (data) => {
      queryClient.setQueryData(['flow', data.id], data)
      // Navigate to flow detail page
    },
    onError: (error) => {
      console.error('Failed to create flow:', error)
    }
  })
  
  // Pause flow mutation
  const pauseFlowMutation = useMutation({
    mutationFn: (flowId: string) => flowApi.pauseFlow(flowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow', flowId] })
    }
  })
  
  // Resume flow mutation
  const resumeFlowMutation = useMutation({
    mutationFn: (flowId: string) => flowApi.resumeFlow(flowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow', flowId] })
    }
  })
  
  return {
    // Data
    flow: flowQuery.data,
    isLoading: flowQuery.isLoading,
    isError: flowQuery.isError,
    error: flowQuery.error,
    
    // Real-time status
    isConnected: connectionStatus === 'Connected',
    lastUpdate: lastMessage?.timestamp,
    
    // Actions
    createFlow: createFlowMutation.mutate,
    pauseFlow: pauseFlowMutation.mutate,
    resumeFlow: resumeFlowMutation.mutate,
    
    // States
    isCreating: createFlowMutation.isPending,
    isPausing: pauseFlowMutation.isPending,
    isResuming: resumeFlowMutation.isPending,
    
    // Utilities
    refetch: flowQuery.refetch,
  }
}

// Custom WebSocket hook
function useWebSocket(url: string | null, options: {
  onMessage?: (event: MessageEvent) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}) {
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Connected' | 'Disconnected'>('Disconnected')
  const [lastMessage, setLastMessage] = useState<{data: any, timestamp: Date} | null>(null)
  const ws = useRef<WebSocket | null>(null)
  
  useEffect(() => {
    if (!url) return
    
    const connect = () => {
      setConnectionStatus('Connecting')
      ws.current = new WebSocket(`${WS_BASE_URL}${url}?user_id=${getCurrentUserId()}`)
      
      ws.current.onopen = () => {
        setConnectionStatus('Connected')
        options.onOpen?.()
      }
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setLastMessage({ data, timestamp: new Date() })
        options.onMessage?.(event)
      }
      
      ws.current.onclose = () => {
        setConnectionStatus('Disconnected')
        options.onClose?.()
        
        // Reconnect after delay
        setTimeout(connect, 3000)
      }
      
      ws.current.onerror = (error) => {
        options.onError?.(error)
      }
    }
    
    connect()
    
    return () => {
      ws.current?.close()
    }
  }, [url])
  
  return { connectionStatus, lastMessage }
}
```

#### Day 35-36: UI Components

```typescript
// frontend/src/components/flows/FlowProgressTracker.tsx
import React from 'react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react'
import { FlowResponse, PhaseStatus } from '@/types/flow'

interface FlowProgressTrackerProps {
  flow: FlowResponse
  showDetails?: boolean
}

const PHASES = [
  { key: 'validation', label: 'Data Validation', icon: CheckCircle },
  { key: 'mapping', label: 'Field Mapping', icon: CheckCircle },
  { key: 'cleansing', label: 'Data Cleansing', icon: CheckCircle },
  { key: 'inventory', label: 'Asset Inventory', icon: CheckCircle },
  { key: 'dependencies', label: 'Dependencies', icon: CheckCircle },
  { key: 'analysis', label: 'Analysis', icon: CheckCircle },
]

export function FlowProgressTracker({ flow, showDetails = true }: FlowProgressTrackerProps) {
  const getPhaseStatus = (phaseKey: string): PhaseStatus => {
    return flow.phases[phaseKey] || 'pending'
  }
  
  const getPhaseIcon = (status: PhaseStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }
  
  const getStatusBadge = (status: PhaseStatus) => {
    const variants = {
      completed: 'success',
      running: 'default',
      failed: 'destructive',
      pending: 'secondary',
      skipped: 'outline'
    } as const
    
    return (
      <Badge variant={variants[status] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Flow Progress</h3>
          <span className="text-sm text-gray-600">
            {Math.round(flow.progress_percentage)}%
          </span>
        </div>
        <Progress value={flow.progress_percentage} className="h-2" />
      </div>
      
      {/* Phase Details */}
      {showDetails && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Phases</h4>
          <div className="grid gap-3">
            {PHASES.map((phase, index) => {
              const status = getPhaseStatus(phase.key)
              const isActive = flow.current_phase === phase.key
              
              return (
                <div
                  key={phase.key}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    {getPhaseIcon(status)}
                    <div>
                      <span className="font-medium">{phase.label}</span>
                      {isActive && (
                        <span className="ml-2 text-sm text-blue-600">(Current)</span>
                      )}
                    </div>
                  </div>
                  {getStatusBadge(status)}
                </div>
              )
            })}
          </div>
        </div>
      )}
      
      {/* Flow Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {flow.results?.total_assets || 0}
          </div>
          <div className="text-sm text-gray-600">Assets Discovered</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {flow.results?.total_dependencies || 0}
          </div>
          <div className="text-sm text-gray-600">Dependencies</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {flow.errors?.length || 0}
          </div>
          <div className="text-sm text-gray-600">Issues</div>
        </div>
      </div>
    </div>
  )
}

// Real-time flow dashboard
export function FlowDashboard({ flowId }: { flowId: string }) {
  const { flow, isLoading, isConnected } = useDiscoveryFlow({ 
    flowId, 
    enableRealTime: true 
  })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }
  
  if (!flow) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Flow not found</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{flow.name}</h1>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      {/* Progress Tracker */}
      <FlowProgressTracker flow={flow} />
      
      {/* Recent Activity */}
      <FlowActivityFeed flowId={flowId} />
      
      {/* Actions */}
      <FlowActions flow={flow} />
    </div>
  )
}
```

## Phase 5: Advanced Features (Weeks 9-10)

### Week 9: Real-Time Processing & Monitoring

#### Day 37-38: Monitoring and Observability

```python
# backend/app/services/monitoring/metrics_service.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps

# Metrics definitions
FLOW_EXECUTIONS = Counter('flow_executions_total', 'Total flow executions', ['flow_type', 'status'])
FLOW_DURATION = Histogram('flow_duration_seconds', 'Flow execution duration', ['flow_type'])
AGENT_EXECUTIONS = Counter('agent_executions_total', 'Total agent executions', ['agent_id', 'status'])
AGENT_DURATION = Histogram('agent_duration_seconds', 'Agent execution duration', ['agent_id'])
ACTIVE_FLOWS = Gauge('active_flows', 'Number of active flows')
LLM_COSTS = Counter('llm_costs_total', 'Total LLM costs', ['provider', 'model'])

class MetricsService:
    """Service for collecting and exposing metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
    
    def record_flow_execution(self, flow_type: str, status: str, duration: float):
        """Record flow execution metrics"""
        FLOW_EXECUTIONS.labels(flow_type=flow_type, status=status).inc()
        FLOW_DURATION.labels(flow_type=flow_type).observe(duration)
    
    def record_agent_execution(self, agent_id: str, status: str, duration: float):
        """Record agent execution metrics"""
        AGENT_EXECUTIONS.labels(agent_id=agent_id, status=status).inc()
        AGENT_DURATION.labels(agent_id=agent_id).observe(duration)
    
    def record_llm_cost(self, provider: str, model: str, cost: float):
        """Record LLM cost metrics"""
        LLM_COSTS.labels(provider=provider, model=model).inc(cost)
    
    def update_active_flows(self, count: int):
        """Update active flows gauge"""
        ACTIVE_FLOWS.set(count)

def monitor_execution(metric_name: str = None):
    """Decorator to monitor function execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_name == "flow":
                    flow_type = kwargs.get('flow_type', 'unknown')
                    FLOW_EXECUTIONS.labels(flow_type=flow_type, status=status).inc()
                    FLOW_DURATION.labels(flow_type=flow_type).observe(duration)
                elif metric_name == "agent":
                    agent_id = kwargs.get('agent_id', getattr(args[0], 'get_agent_id', lambda: 'unknown')())
                    AGENT_EXECUTIONS.labels(agent_id=agent_id, status=status).inc()
                    AGENT_DURATION.labels(agent_id=agent_id).observe(duration)
        
        return wrapper
    return decorator

# backend/app/services/monitoring/health_service.py
class HealthService:
    """Service for health checks and system status"""
    
    def __init__(self):
        self.checks = {}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            async with AsyncSessionLocal() as db:
                await db.execute("SELECT 1")
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            # Implement Redis health check
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_llm_services_health(self) -> Dict[str, Any]:
        """Check LLM service availability"""
        services_health = {}
        
        for provider in ["openai", "anthropic", "deepinfra"]:
            try:
                # Implement provider-specific health checks
                services_health[provider] = {"status": "healthy"}
            except Exception as e:
                services_health[provider] = {"status": "unhealthy", "error": str(e)}
        
        return services_health
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        checks = await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_llm_services_health(),
            return_exceptions=True
        )
        
        db_health, redis_health, llm_health = checks
        
        # Determine overall status
        all_healthy = (
            db_health.get("status") == "healthy" and
            redis_health.get("status") == "healthy" and
            all(service.get("status") == "healthy" for service in llm_health.values())
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_health,
                "redis": redis_health,
                "llm_services": llm_health
            }
        }
```

#### Day 39-40: Cost Optimization and Analytics

```python
# backend/app/services/optimization/cost_optimizer.py
class CostOptimizer:
    """Optimizes LLM usage and costs"""
    
    def __init__(self):
        self.model_costs = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-instant': {'input': 0.001, 'output': 0.003}
        }
        self.usage_tracker = LLMUsageTracker()
    
    async def select_optimal_model(self, task_complexity: str, 
                                 accuracy_requirement: float,
                                 budget_limit: float = None) -> str:
        """Select the most cost-effective model for the task"""
        
        # Model performance vs cost matrix
        model_profiles = {
            'gpt-4': {'accuracy': 0.95, 'cost_per_1k': 0.045, 'speed': 0.7},
            'gpt-3.5-turbo': {'accuracy': 0.85, 'cost_per_1k': 0.0015, 'speed': 0.9},
            'claude-3-opus': {'accuracy': 0.93, 'cost_per_1k': 0.045, 'speed': 0.8},
            'claude-instant': {'accuracy': 0.82, 'cost_per_1k': 0.002, 'speed': 0.95}
        }
        
        # Filter models that meet accuracy requirement
        suitable_models = {
            model: profile for model, profile in model_profiles.items()
            if profile['accuracy'] >= accuracy_requirement
        }
        
        if not suitable_models:
            # Fall back to highest accuracy model
            return max(model_profiles.keys(), 
                      key=lambda m: model_profiles[m]['accuracy'])
        
        # Select most cost-effective suitable model
        if task_complexity == "low":
            # Prioritize speed and cost
            return min(suitable_models.keys(), 
                      key=lambda m: suitable_models[m]['cost_per_1k'])
        elif task_complexity == "high":
            # Prioritize accuracy
            return max(suitable_models.keys(), 
                      key=lambda m: suitable_models[m]['accuracy'])
        else:
            # Balance cost and accuracy
            return min(suitable_models.keys(), 
                      key=lambda m: suitable_models[m]['cost_per_1k'] / suitable_models[m]['accuracy'])
    
    async def predict_flow_cost(self, flow_config: Dict) -> Dict[str, float]:
        """Predict the cost of running a flow"""
        
        # Historical data for similar flows
        historical_usage = await self.usage_tracker.get_historical_usage(
            flow_type=flow_config.get('type'),
            data_size=flow_config.get('data_size', 1000)
        )
        
        if not historical_usage:
            # Default estimates
            estimated_tokens = flow_config.get('data_size', 1000) * 100  # 100 tokens per record
        else:
            # Use historical average
            estimated_tokens = historical_usage['avg_tokens_per_record'] * flow_config.get('data_size', 1000)
        
        # Calculate cost for different models
        cost_estimates = {}
        for model, costs in self.model_costs.items():
            # Assume 70% input, 30% output token distribution
            input_tokens = estimated_tokens * 0.7
            output_tokens = estimated_tokens * 0.3
            
            total_cost = (
                (input_tokens / 1000) * costs['input'] +
                (output_tokens / 1000) * costs['output']
            )
            
            cost_estimates[model] = total_cost
        
        return {
            'estimated_tokens': estimated_tokens,
            'cost_by_model': cost_estimates,
            'recommended_model': min(cost_estimates.keys(), key=lambda m: cost_estimates[m])
        }

# Performance analytics dashboard
class PerformanceAnalytics:
    """Analytics service for performance insights"""
    
    def __init__(self):
        self.metrics_store = MetricsStore()
    
    async def generate_performance_report(self, timeframe_days: int = 30) -> Dict:
        """Generate comprehensive performance report"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Gather metrics
        flow_metrics = await self.metrics_store.get_flow_metrics(start_date, end_date)
        agent_metrics = await self.metrics_store.get_agent_metrics(start_date, end_date)
        cost_metrics = await self.metrics_store.get_cost_metrics(start_date, end_date)
        
        # Calculate KPIs
        total_flows = len(flow_metrics)
        successful_flows = len([f for f in flow_metrics if f['status'] == 'success'])
        success_rate = (successful_flows / total_flows) * 100 if total_flows > 0 else 0
        
        avg_flow_duration = sum(f['duration'] for f in flow_metrics) / total_flows if total_flows > 0 else 0
        
        total_cost = sum(cost_metrics.values())
        cost_per_flow = total_cost / total_flows if total_flows > 0 else 0
        
        # Identify top performing agents
        agent_performance = {}
        for agent_id, metrics in agent_metrics.items():
            agent_performance[agent_id] = {
                'avg_duration': sum(m['duration'] for m in metrics) / len(metrics),
                'success_rate': len([m for m in metrics if m['status'] == 'success']) / len(metrics) * 100,
                'executions': len(metrics)
            }
        
        # Identify optimization opportunities
        optimizations = []
        
        if avg_flow_duration > 60:  # More than 1 minute
            optimizations.append({
                'type': 'performance',
                'description': 'Flow duration is above target (60s)',
                'recommendation': 'Consider parallel agent execution or model optimization'
            })
        
        if cost_per_flow > 1.0:  # More than $1 per flow
            optimizations.append({
                'type': 'cost',
                'description': 'Cost per flow is above target ($1.00)',
                'recommendation': 'Consider using more cost-effective models for routine tasks'
            })
        
        return {
            'timeframe': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'kpis': {
                'total_flows': total_flows,
                'success_rate': success_rate,
                'avg_flow_duration': avg_flow_duration,
                'total_cost': total_cost,
                'cost_per_flow': cost_per_flow
            },
            'agent_performance': agent_performance,
            'optimizations': optimizations,
            'generated_at': datetime.utcnow().isoformat()
        }
```

### Week 10: Production Readiness

#### Day 41-42: Security and Compliance

```python
# backend/app/services/security/compliance_service.py
class ComplianceService:
    """Handles compliance requirements (GDPR, SOC2, etc.)"""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.data_classifier = DataClassifier()
    
    async def classify_data_sensitivity(self, data: List[Dict]) -> Dict[str, Any]:
        """Classify data based on sensitivity levels"""
        
        classification = {
            'public': [],
            'internal': [],
            'confidential': [],
            'restricted': []
        }
        
        for record in data:
            sensitivity = await self.data_classifier.classify_record(record)
            classification[sensitivity].append(record)
        
        return {
            'classification': classification,
            'summary': {level: len(records) for level, records in classification.items()},
            'compliance_requirements': self._get_compliance_requirements(classification)
        }
    
    def _get_compliance_requirements(self, classification: Dict) -> List[str]:
        """Determine compliance requirements based on data classification"""
        
        requirements = []
        
        if classification['restricted']:
            requirements.extend([
                'SOC2_TYPE_II',
                'ENCRYPTION_AT_REST',
                'ACCESS_LOGGING',
                'DATA_RETENTION_POLICY'
            ])
        
        if classification['confidential']:
            requirements.extend([
                'GDPR_COMPLIANCE',
                'DATA_MASKING',
                'RIGHT_TO_DELETION'
            ])
        
        return list(set(requirements))
    
    async def audit_data_access(self, user_id: str, resource_id: str, 
                              action: str, context: Dict):
        """Audit all data access for compliance"""
        
        audit_entry = {
            'user_id': user_id,
            'resource_id': resource_id,
            'action': action,
            'timestamp': datetime.utcnow(),
            'context': context,
            'ip_address': context.get('ip_address'),
            'user_agent': context.get('user_agent')
        }
        
        await self.audit_logger.log_access(audit_entry)

# Data encryption service
class EncryptionService:
    """Handles data encryption and decryption"""
    
    def __init__(self):
        self.key_manager = KeyManager()
    
    async def encrypt_sensitive_fields(self, data: Dict, 
                                     sensitivity_level: str) -> Dict:
        """Encrypt sensitive fields based on classification"""
        
        if sensitivity_level in ['confidential', 'restricted']:
            # Get encryption key for tenant
            tenant = get_current_tenant()
            key = await self.key_manager.get_key(tenant.tenant_id)
            
            # Encrypt PII fields
            pii_fields = ['ssn', 'email', 'phone', 'credit_card']
            
            encrypted_data = data.copy()
            for field in pii_fields:
                if field in encrypted_data:
                    encrypted_data[field] = await self._encrypt_field(
                        encrypted_data[field], key
                    )
            
            return encrypted_data
        
        return data
    
    async def _encrypt_field(self, value: str, key: bytes) -> str:
        """Encrypt a single field value"""
        # Implementation would use proper encryption library
        # This is a placeholder
        import base64
        return base64.b64encode(value.encode()).decode()
```

#### Day 43-44: Deployment and DevOps

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-migration-backend
  labels:
    app: ai-migration-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-migration-backend
  template:
    metadata:
      labels:
        app: ai-migration-backend
    spec:
      containers:
      - name: backend
        image: ai-migration-platform/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ai-migration-backend-service
spec:
  selector:
    app: ai-migration-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

# CI/CD Pipeline
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements/dev.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and push backend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: ai-migration-backend
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    
    - name: Deploy to EKS
      run: |
        aws eks update-kubeconfig --region us-west-2 --name ai-migration-cluster
        
        # Update deployment with new image
        kubectl set image deployment/ai-migration-backend \
          backend=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        
        # Wait for rollout to complete
        kubectl rollout status deployment/ai-migration-backend
```

#### Day 45: Final Integration and Testing

```python
# backend/tests/integration/test_end_to_end.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
@pytest.mark.integration
class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    async def test_complete_discovery_flow(self):
        """Test complete discovery flow execution"""
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Create flow
            flow_data = {
                "name": "Test Discovery Flow",
                "flow_type": "discovery",
                "raw_data": [
                    {"hostname": "server1", "ip": "10.0.0.1", "os": "Linux"},
                    {"hostname": "server2", "ip": "10.0.0.2", "os": "Windows"}
                ],
                "metadata": {"source": "test"}
            }
            
            response = await client.post("/api/v1/flows/", json=flow_data)
            assert response.status_code == 201
            
            flow = response.json()
            flow_id = flow["id"]
            
            # 2. Wait for flow completion (with timeout)
            timeout = 60  # 1 minute
            while timeout > 0:
                response = await client.get(f"/api/v1/flows/{flow_id}")
                flow_status = response.json()
                
                if flow_status["status"] in ["completed", "failed"]:
                    break
                
                await asyncio.sleep(1)
                timeout -= 1
            
            # 3. Verify flow completed successfully
            assert flow_status["status"] == "completed"
            assert flow_status["progress_percentage"] == 100.0
            
            # 4. Verify all phases completed
            assert all(status == "completed" for status in flow_status["phases"].values())
            
            # 5. Verify results
            assert "results" in flow_status
            assert flow_status["results"]["total_assets"] >= 2
    
    async def test_flow_error_handling(self):
        """Test flow error handling with invalid data"""
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create flow with invalid data
            flow_data = {
                "name": "Error Test Flow",
                "flow_type": "discovery",
                "raw_data": [],  # Empty data should cause error
                "metadata": {}
            }
            
            response = await client.post("/api/v1/flows/", json=flow_data)
            assert response.status_code == 400
    
    async def test_real_time_updates(self):
        """Test WebSocket real-time updates"""
        
        # This would require WebSocket testing setup
        # Implementation depends on chosen WebSocket testing library
        pass

# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    async def test_flow_execution_performance(self, benchmark):
        """Benchmark flow execution performance"""
        
        def create_test_data(size: int):
            return [
                {
                    "hostname": f"server{i}",
                    "ip": f"10.0.{i//256}.{i%256}",
                    "os": "Linux" if i % 2 == 0 else "Windows"
                }
                for i in range(size)
            ]
        
        # Test with different data sizes
        for size in [100, 1000, 10000]:
            test_data = create_test_data(size)
            
            # Benchmark flow execution
            result = await benchmark(execute_discovery_flow_benchmark, test_data)
            
            # Verify performance targets
            assert result["duration"] < 45  # Under 45 seconds
            assert result["success_rate"] > 0.95  # 95% success rate
```

## Deliverables Summary for All Phases

### Phase 1 Deliverables (Foundation)
- ✅ Complete development environment with Docker
- ✅ FastAPI application with proper middleware
- ✅ Multi-tenant database architecture
- ✅ Repository pattern with context injection
- ✅ Testing framework and CI/CD pipeline

### Phase 2 Deliverables (CrewAI)
- ✅ CrewAI flow framework with proper decorators
- ✅ Agent registry and auto-discovery system
- ✅ Crew factory for dynamic composition
- ✅ Tool system with extensible architecture
- ✅ State management with event bus

### Phase 3 Deliverables (Intelligence)
- ✅ Learning system with pattern storage
- ✅ Vector similarity for pattern matching
- ✅ Agent collaboration framework
- ✅ Performance optimization system
- ✅ Advanced agent tools and capabilities

### Phase 4 Deliverables (API/Frontend)
- ✅ Complete RESTful API with OpenAPI docs
- ✅ WebSocket real-time updates
- ✅ React hooks for state management
- ✅ Real-time UI components
- ✅ Comprehensive error handling

### Phase 5 Deliverables (Production)
- ✅ Monitoring and observability
- ✅ Cost optimization and analytics
- ✅ Security and compliance features
- ✅ Kubernetes deployment configuration
- ✅ End-to-end testing and benchmarks

### Final Success Metrics
- **Performance**: <45s for 10,000 assets, <200ms API response times
- **Reliability**: 99.9% uptime, comprehensive error handling
- **Accuracy**: 95%+ field mapping accuracy through AI learning
- **Security**: SOC2 compliance, data encryption, audit logging
- **Scalability**: Kubernetes deployment, auto-scaling capabilities