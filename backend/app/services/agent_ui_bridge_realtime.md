# Agent-UI Bridge Real-Time Broadcasting

## Overview

The Agent-UI Bridge has been enhanced with real-time broadcasting capabilities to stream agent decisions and insights through Server-Sent Events (SSE). This enables the frontend to receive live updates as agents analyze data and make decisions during flow execution.

## Key Features

### 1. Agent Decision Broadcasting

The `broadcast_agent_decision()` method allows agents to broadcast their decisions in real-time:

```python
decision_id = agent_ui_bridge.broadcast_agent_decision(
    flow_id="discovery_flow_123",
    agent_id="field_mapper_001",
    agent_name="Field Mapping Specialist",
    decision_type="field_mapping",
    decision="Map 'customer_id' to 'client_id'",
    reasoning="Semantic analysis shows 95% similarity...",
    confidence=ConfidenceLevel.HIGH,
    affected_items=["customer_id", "client_id"],
    metadata={"similarity_score": 0.95}
)
```

### 2. Flow-Specific Insights

The `get_flow_insights()` method aggregates all insights and decisions for a specific flow:

```python
insights = agent_ui_bridge.get_flow_insights(flow_id)
# Returns list of insights and decisions for SSE streaming
```

### 3. Pending Messages

The `get_pending_messages()` method retrieves messages since a specific version:

```python
messages = agent_ui_bridge.get_pending_messages(flow_id, since_version=10)
# Returns new messages with version > 10
```

### 4. Subscription Management

Create and manage subscriptions for flow events:

```python
# Create subscription
subscription_id = agent_ui_bridge.create_subscription(
    flow_id=flow_id,
    client_id=user_id,
    client_account_id=account_id
)

# Remove subscription
success = agent_ui_bridge.remove_subscription(subscription_id)
```

## Integration with SSE Endpoint

The agent_events.py SSE endpoint uses these methods to stream updates:

```python
# In SSE event generator
insights = agent_ui_bridge.get_flow_insights(flow_id)
messages = agent_ui_bridge.get_pending_messages(flow_id, since_version=last_version)
```

## Decision Types

Common decision types agents can broadcast:

- `field_mapping` - Field mapping decisions
- `data_quality` - Data quality assessments
- `migration_strategy` - Migration approach recommendations
- `dependency_analysis` - Dependency identification
- `risk_assessment` - Risk evaluations
- `performance_optimization` - Performance recommendations

## Real-Time Event Flow

1. **Agent makes decision** → Calls `broadcast_agent_decision()`
2. **Decision stored** → In memory with version tracking
3. **Listeners notified** → Async queues receive updates
4. **SSE streams** → Frontend receives via EventSource
5. **UI updates** → Real-time decision display

## Best Practices

### For Agent Developers

1. **Always broadcast significant decisions** - Not every analysis needs broadcasting
2. **Include clear reasoning** - Explain why the decision was made
3. **Set appropriate confidence** - Use HIGH, MEDIUM, LOW accurately
4. **Provide metadata** - Include supporting data for transparency
5. **List affected items** - Identify what the decision impacts

### For SSE Consumers

1. **Handle reconnection** - SSE will auto-reconnect on disconnect
2. **Track versions** - Use version numbers to avoid duplicates
3. **Process decision types** - Different UI handling per type
4. **Show confidence levels** - Visual indicators for confidence
5. **Enable user feedback** - Allow users to validate/override

## Example: CrewAI Integration

```python
from crewai import Agent
from app.services.agent_ui_bridge import agent_ui_bridge

class DataQualityAgent:
    def __init__(self, flow_id: str):
        self.flow_id = flow_id
        self.agent = Agent(
            role="Data Quality Analyst",
            goal="Assess data quality issues"
        )
    
    def analyze_field(self, field_name: str, data_sample: list):
        # Perform analysis
        issues = self._analyze_data_quality(data_sample)
        
        # Broadcast decision
        agent_ui_bridge.broadcast_agent_decision(
            flow_id=self.flow_id,
            agent_id=self.agent.id,
            agent_name=self.agent.role,
            decision_type="data_quality",
            decision=f"Field '{field_name}' requires validation",
            reasoning=f"Found {len(issues)} data quality issues",
            confidence=ConfidenceLevel.HIGH,
            affected_items=[field_name],
            metadata={"issues": issues}
        )
```

## Frontend Integration

Frontend can consume SSE events:

```typescript
const eventSource = new EventSource(`/api/v1/flows/${flowId}/events`);

eventSource.addEventListener('flow_update', (event) => {
  const data = JSON.parse(event.data);
  
  // Check for agent decisions
  if (data.agent_decision) {
    displayAgentDecision(data.agent_decision);
  }
  
  // Display insights
  data.agent_insights.forEach(insight => {
    if (insight.type === 'decision') {
      showDecisionCard(insight);
    }
  });
});
```

## Performance Considerations

- **Decision limit**: Last 100 decisions per flow kept in memory
- **Message versioning**: Prevents duplicate processing
- **Async notifications**: Non-blocking decision broadcasting
- **Insight persistence**: Decisions also saved as insights for history
- **Resource cleanup**: Subscriptions should be removed when not needed

## Error Handling

The system handles errors gracefully:

- **Queue full**: Logged but doesn't block broadcasting
- **Missing flow**: 404 error in SSE endpoint
- **Access denied**: 403 for wrong tenant
- **Stream errors**: Auto-retry with backoff

## Future Enhancements

Potential improvements:

1. **Decision categories**: Group related decisions
2. **Decision chains**: Link dependent decisions
3. **Confidence trends**: Track confidence over time
4. **Decision replay**: Replay decision history
5. **ML feedback loop**: Learn from user validations