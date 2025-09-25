# Collection Flow Technical Implementation Guide

## Recent Updates

**Phase Consolidation**: The Collection Flow has been optimized from 8 phases to 7 phases:
- **Removed**: `platform_detection` and `automated_collection` phases
- **Added**: `asset_selection` phase (consolidates functionality of both removed phases)
- **Impact**: Updated handlers, progress calculation, and state management

## Core Implementation Files

### Backend Structure

```
backend/app/
├── api/v1/endpoints/
│   ├── collection.py                      # Main API router
│   ├── collection_crud_queries.py         # Read operations
│   ├── collection_crud_create_commands.py # Create operations
│   ├── collection_crud_update_commands.py # Update operations
│   ├── collection_crud_questionnaires.py  # Questionnaire management
│   └── collection_serializers.py          # Response serialization
├── models/
│   ├── collection_flow.py                 # SQLAlchemy models
│   ├── collection_questionnaire.py        # Questionnaire models
│   └── collection_questionnaire_response.py # Response models
├── schemas/
│   └── collection_flow.py                 # Pydantic schemas
└── services/crewai_flows/
    ├── unified_collection_flow.py         # Main CrewAI flow
    └── unified_collection_flow_modules/   # Flow phase handlers
```

### Frontend Structure

```
src/
├── pages/collection/
│   ├── Index.tsx                          # Collection landing page
│   ├── ApplicationSelection.tsx           # Application selector
│   ├── AdaptiveForms.tsx                 # Adaptive form renderer
│   └── Progress.tsx                       # Progress monitor
├── hooks/collection/
│   ├── useAdaptiveFormFlow.ts            # Form flow management
│   ├── useProgressMonitoring.ts          # Progress tracking
│   └── useCollectionFlowManagement.ts    # Flow operations
├── components/collection/
│   ├── forms/                            # Form components
│   ├── layout/                           # Layout components
│   └── progress/                         # Progress components
└── services/api/
    └── collection-flow.ts                # API client
```

## Key Implementation Details

### Flow State Management

The Collection Flow uses a sophisticated state management system:

```python
# Backend state structure (Pydantic model)
class CollectionFlowState(BaseModel):
    flow_id: str
    client_account_id: str
    engagement_id: str
    user_id: Optional[str]
    current_phase: CollectionPhase
    status: CollectionStatus
    automation_tier: AutomationTier
    phase_results: Dict[str, Any]
    user_inputs: Dict[str, Any]
    errors: List[Dict[str, Any]]
```

### CrewAI Flow Implementation

```python
class UnifiedCollectionFlow(Flow[CollectionFlowState]):
    """Main collection flow orchestrator with optimized 7-phase structure"""

    @start()
    async def initialize_collection(self):
        """Phase 1: Initialize flow"""
        return await self.initialization_handler.initialize_collection(
            self.state, config
        )

    @listen("initialization")
    async def asset_selection(self, initialization_result):
        """Phase 2: Asset selection (consolidates platform detection and automated collection)"""
        return await self.asset_selection_handler.process_asset_selection(
            self.state, config, initialization_result
        )

    @listen("asset_selection")
    async def gap_analysis(self, asset_result):
        """Phase 3: Gap analysis"""
        return await self.gap_analysis_handler.analyze_gaps(
            self.state, config, asset_result
        )

    @listen("gap_analysis")
    async def questionnaire_generation(self, gap_result):
        """Phase 4: Questionnaire generation"""
        return await self.questionnaire_handler.generate_questionnaires(
            self.state, config, gap_result
        )

    @listen("questionnaire_generation")
    async def manual_collection(self, questionnaire_result):
        """Phase 5: Manual collection"""
        return await self.manual_collection_handler.collect_manual_data(
            self.state, config, questionnaire_result
        )

    @listen("manual_collection")
    async def data_validation(self, collection_result):
        """Phase 6: Data validation"""
        return await self.validation_handler.validate_data(
            self.state, config, collection_result
        )

    @listen("data_validation")
    async def finalization(self, validation_result):
        """Phase 7: Finalization"""
        return await self.finalization_handler.finalize_collection(
            self.state, config, validation_result
        )
```

### Adaptive Questionnaire Generation

The questionnaire generation uses CrewAI agents to analyze gaps:

```python
async def generate_adaptive_questionnaire(
    gap_analysis: List[CollectionGap],
    context: RequestContext
) -> CollectionQuestionnaire:
    """Generate questionnaire based on identified gaps"""
    
    # CrewAI agent analyzes gaps
    agent_response = await crewai_service.analyze_gaps(gap_analysis)
    
    # Generate questions targeting specific gaps
    questions = []
    for gap in gap_analysis:
        if gap.priority == "critical":
            question = create_targeted_question(gap)
            questions.append(question)
    
    # Build questionnaire with validation rules
    return CollectionQuestionnaire(
        title=f"Adaptive Questionnaire - {context.engagement_id}",
        questions=questions,
        validation_rules=generate_validation_rules(questions)
    )
```

### Frontend Adaptive Form Flow

```typescript
// Hook for managing adaptive form flow
export const useAdaptiveFormFlow = (options: UseAdaptiveFormFlowOptions) => {
  const [state, setState] = useState<AdaptiveFormFlowState>({
    formData: null,
    formValues: {},
    validation: null,
    flowId: null,
    questionnaires: [],
    isLoading: false,
    isSaving: false,
    isCompleted: false,
    error: null
  });

  const handleSubmit = async (data: CollectionFormData) => {
    // Submit to backend
    const response = await collectionFlowApi.submitQuestionnaireResponse(
      state.flowId,
      questionnaireId,
      data
    );
    
    // Use correct flow_id from response for redirect
    const actualFlowId = response.flow_id;
    
    // Check for next questionnaire or complete
    if (hasMoreQuestionnaires) {
      loadNextQuestionnaire();
    } else {
      // Use navigate() for React Router navigation (better UX)
      navigate(`/collection/progress/${actualFlowId}`);
    }
  };
};
```

### Progress Monitoring Implementation

```typescript
// Real-time progress monitoring
export const useProgressMonitoring = (options: UseProgressMonitoringOptions) => {
  const loadData = useCallback(async () => {
    if (flowId) {
      // Fetch specific flow details
      const flowDetails = await collectionFlowApi.getFlowDetails(flowId);
      
      // Transform to monitoring format
      const flow: CollectionFlow = {
        id: flowDetails.flow_id,  // Use flow_id UUID, not database id
        name: `Collection Flow - ${flowDetails.automation_tier}`,
        type: mapAutomationTierToType(flowDetails.automation_tier),
        status: mapFlowStatus(flowDetails.status),
        progress: flowDetails.progress_percentage || 0,
        // ... additional fields
      };
      
      setState({ flows: [flow], metrics, selectedFlow: flow.id });
    }
  }, [flowId]);
  
  // Auto-refresh with error handling
  useEffect(() => {
    if (autoRefresh && !state.error) {
      const interval = setInterval(loadData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, state.error]);
};
```

## Database Schema

### collection_flows Table

```sql
CREATE TABLE collection_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,  -- Note: flow_id is unique constraint, not PK
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    discovery_flow_id UUID REFERENCES discovery_flows(flow_id),
    status VARCHAR(50) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    automation_tier VARCHAR(20) NOT NULL,
    progress_percentage INTEGER DEFAULT 0,
    collection_config JSONB DEFAULT '{}',
    collection_quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT fk_engagement FOREIGN KEY (engagement_id) 
        REFERENCES engagements(id) ON DELETE CASCADE
);

-- Important indexes for single-tenant queries
CREATE INDEX idx_collection_flows_flow_id ON collection_flows(flow_id);
CREATE INDEX idx_collection_flows_engagement ON collection_flows(engagement_id);
CREATE INDEX idx_collection_flows_status ON collection_flows(status);

-- Composite indexes for multi-tenant queries (CRITICAL for performance)
CREATE INDEX idx_collection_flows_tenant_flow ON collection_flows(client_account_id, engagement_id, flow_id);
CREATE INDEX idx_collection_flows_tenant_status ON collection_flows(client_account_id, engagement_id, status);
CREATE INDEX idx_collection_flows_tenant_phase ON collection_flows(client_account_id, engagement_id, current_phase);
```

### collection_questionnaires Table

```sql
CREATE TABLE collection_questionnaires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_flow_id UUID NOT NULL REFERENCES collection_flows(id),
    questionnaire_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_gaps JSONB DEFAULT '[]',
    questions JSONB NOT NULL,
    validation_rules JSONB DEFAULT '[]',
    completion_status VARCHAR(50) DEFAULT 'pending',
    responses_collected JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### collection_questionnaire_responses Table

```sql
CREATE TABLE collection_questionnaire_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_flow_id UUID NOT NULL REFERENCES collection_flows(id),
    asset_id UUID REFERENCES assets(id),
    questionnaire_type VARCHAR(50),
    question_category VARCHAR(100),
    question_id VARCHAR(255) NOT NULL,
    question_text TEXT,
    response_type VARCHAR(50),
    response_value JSONB,
    confidence_score FLOAT,
    validation_status VARCHAR(50),
    responded_by UUID REFERENCES users(id),
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_metadata JSONB DEFAULT '{}'
);
```

## API Request/Response Examples

### Create Collection Flow

**Request:**
```http
POST /api/v1/collection/flows
Content-Type: application/json
X-Client-Account-ID: 12345678-1234-1234-1234-123456789012
X-Engagement-ID: 87654321-4321-4321-4321-210987654321

{
  "automation_tier": "tier_2",
  "collection_strategy": {
    "focus_areas": ["applications", "infrastructure"],
    "priority": "high"
  },
  "selected_application_ids": ["app-1", "app-2"]
}
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initialized",
  "current_phase": "initialization",
  "automation_tier": "tier_2",
  "progress": 0,
  "created_at": "2025-09-03T10:00:00Z"
}
```

### Submit Questionnaire Response

**Request:**
```http
POST /api/v1/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/submit
Content-Type: application/json
X-Client-Account-ID: 12345678-1234-1234-1234-123456789012
X-Engagement-ID: 87654321-4321-4321-4321-210987654321

{
  "responses": {
    "app_name": "Customer Portal",
    "criticality": "high",
    "monthly_users": 10000
  },
  "form_metadata": {
    "completion_percentage": 75,
    "confidence_score": 0.85
  },
  "validation_results": {
    "isValid": true,
    "errors": []
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully saved 3 responses",
  "questionnaire_id": "quest-123",
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": 75,
  "responses_saved": 3
}
```

## Development Environment Setup

### Docker-First Development (MANDATORY)

**IMPORTANT**: All Collection Flow development MUST be done using Docker containers.

```bash
# Start development environment
docker-compose up -d

# Access application at:
# Frontend: http://localhost:8081 (NOT port 3000)
# Backend API: http://localhost:8000

# Never run 'npm run dev' locally - use Docker only
```

### CrewAI Configuration Source and Injection

CrewAI flows receive configuration through dependency injection:

```python
# Configuration comes from multiple sources (in priority order):
# 1. Environment variables (CREWAI_*)
# 2. Database configuration (client_account_configs)
# 3. Default configuration (crewai_default_config.yaml)

class UnifiedCollectionFlow(Flow[CollectionFlowState]):
    def __init__(self, config: CrewAIFlowConfig):
        super().__init__()
        self.config = config  # Injected by FlowConfigService
        
    @start()
    async def initialize_collection(self):
        # Config is available throughout the flow
        agent_config = self.config.get_agent_config("gap_analysis")
        return await self.initialization_handler.initialize_collection(
            self.state, self.config
        )
```

### JSON Safety for NaN/Infinity Values

**CRITICAL**: Always handle NaN/Infinity values in JSON serialization:

```python
import math
import json
from decimal import Decimal
from typing import Any

def sanitize_for_json(obj: Any):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, Decimal):
        if obj.is_nan() or obj.is_infinite():
            return None
        return float(obj)
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    return obj

def safe_json_dumps(data: Any) -> str:
    sanitized = sanitize_for_json(data)
    return json.dumps(sanitized, allow_nan=False)

# In API responses, always check numeric fields:
def serialize_collection_metrics(metrics):
    return {
        "confidence_score": None if math.isnan(metrics.confidence_score) else metrics.confidence_score,
        "quality_score": None if math.isnan(metrics.quality_score) else metrics.quality_score,
        "progress_percentage": max(0, min(100, metrics.progress_percentage or 0))
    }
```

## Common Patterns and Best Practices

### 1. Flow ID Management
Always use `flow_id` (UUID) for API calls, not the database `id`:

```python
# Correct - always include multi-tenant context
flow = await db.execute(
    select(CollectionFlow)
    .where(CollectionFlow.flow_id == UUID(flow_id))
    .where(CollectionFlow.client_account_id == context.client_account_id)
    .where(CollectionFlow.engagement_id == context.engagement_id)
)

# Incorrect - will cause 404 errors or security issues
flow = await db.execute(
    select(CollectionFlow).where(CollectionFlow.id == flow_id)  # Wrong field
)
```

### 2. Multi-Tenant Queries
Always include tenant context in queries:

```python
result = await db.execute(
    select(CollectionFlow)
    .where(CollectionFlow.flow_id == flow_id)
    .where(CollectionFlow.engagement_id == context.engagement_id)
    .where(CollectionFlow.client_account_id == context.client_account_id)
)
```

### 3. Atomic Transactions
Wrap multi-step operations in transactions:

```python
# Use explicit async session with proper scoping
from app.db.sessions import AsyncSessionLocal

try:
    async with AsyncSessionLocal() as session:
        session.add(questionnaire)
        session.add_all(responses)
        await session.commit()  # Commit changes
except Exception as e:
    # Session automatically rolled back on exception
    logger.error(f"Database operation failed: {e}")
    raise
```

### 4. Progress Calculation
Calculate progress based on multiple factors:

```python
def calculate_progress(flow: CollectionFlow) -> int:
    weights = {
        'asset_selection': 0.4,  # Consolidated from platform_detection (0.1) + automated_collection (0.3)
        'gap_analysis': 0.1,
        'manual_collection': 0.4,
        'validation': 0.1
    }
    
    progress = 0
    for phase, weight in weights.items():
        # Note: completed_phases should be stored in collection_config JSONB field
        if flow.collection_config.get('completed_phases', {}).get(phase):
            progress += weight * 100
    
    return min(int(progress), 100)
```

### 5. Error Recovery
Implement graceful error recovery:

```typescript
const handleFlowAction = async (flowId: string, action: string) => {
  try {
    await collectionFlowApi.updateFlow(flowId, { action });
    await refreshData();
  } catch (error) {
    if (error.status === 404) {
      // Flow not found - stop auto-refresh
      setAutoRefresh(false);
    } else {
      // Retry with exponential backoff
      retryWithBackoff(() => handleFlowAction(flowId, action));
    }
  }
};
```

## Testing Strategies

### Unit Tests
- Test individual phase handlers
- Mock CrewAI agent responses
- Validate state transitions

### Integration Tests
- Test complete flow execution
- Verify database state consistency
- Test pause/resume functionality

### End-to-End Tests
- Complete flow from UI to database
- Multi-user concurrent flows
- Error recovery scenarios

## Performance Considerations

1. **Batch Operations** - Process multiple questionnaire responses in batches
2. **Lazy Loading** - Load questionnaires on demand, not all at once
3. **Caching** - Cache platform configurations and validation rules
4. **Async Processing** - Use async/await for ALL I/O operations
5. **Connection Pooling** - Properly configure database connection pools
6. **JSON Safety** - Always check for NaN/Infinity before JSON serialization
7. **Docker Development** - Use Docker containers only, never local npm dev server

## Security Considerations

1. **Input Validation** - Validate all user inputs against schemas
2. **SQL Injection** - Use parameterized queries exclusively
3. **XSS Prevention** - Sanitize all rendered content
4. **CSRF Protection** - Use CSRF tokens for state-changing operations
5. **Rate Limiting** - Implement rate limits on API endpoints