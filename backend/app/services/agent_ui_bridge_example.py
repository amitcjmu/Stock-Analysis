"""
Example usage of the Agent-UI Bridge for broadcasting agent decisions in real-time.

This demonstrates how agents can broadcast their decisions through the bridge
to be streamed via SSE to the frontend.
"""

from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.models.agent_communication import ConfidenceLevel


# Example 1: Field Mapping Agent Broadcasting a Decision
def example_field_mapping_decision(flow_id: str):
    """Example of a field mapping agent broadcasting its decision."""
    
    # Agent analyzes source and target fields
    decision_id = agent_ui_bridge.broadcast_agent_decision(
        flow_id=flow_id,
        agent_id="field_mapping_agent_001",
        agent_name="Field Mapping Specialist",
        decision_type="field_mapping",
        decision="Map 'customer_name' to 'client_full_name'",
        reasoning="Both fields contain customer names. The target field 'client_full_name' appears to be the standardized naming convention in the target system. Semantic similarity score: 0.92",
        confidence=ConfidenceLevel.HIGH,
        affected_items=["customer_name", "client_full_name"],
        metadata={
            "similarity_score": 0.92,
            "field_type": "string",
            "mapping_strategy": "direct",
            "data_sample": "John Doe"
        }
    )
    
    print(f"Broadcast field mapping decision: {decision_id}")
    return decision_id


# Example 2: Data Quality Agent Making Assessment
def example_data_quality_decision(flow_id: str):
    """Example of a data quality agent broadcasting its assessment."""
    
    decision_id = agent_ui_bridge.broadcast_agent_decision(
        flow_id=flow_id,
        agent_id="data_quality_agent_002",
        agent_name="Data Quality Analyst",
        decision_type="data_quality",
        decision="Flag 'email' field for validation - 15% invalid format",
        reasoning="Analysis of 10,000 records shows 1,500 email addresses (15%) do not match standard email format. Common issues: missing @ symbol (800), invalid domains (500), multiple @ symbols (200).",
        confidence=ConfidenceLevel.HIGH,
        affected_items=["email_field", "customer_contact_table"],
        metadata={
            "total_records": 10000,
            "invalid_count": 1500,
            "invalid_percentage": 15,
            "issues": {
                "missing_at": 800,
                "invalid_domain": 500,
                "multiple_at": 200
            },
            "recommendation": "Implement email validation before migration"
        }
    )
    
    print(f"Broadcast data quality decision: {decision_id}")
    return decision_id


# Example 3: Migration Strategy Agent Decision
def example_migration_strategy_decision(flow_id: str):
    """Example of a migration strategy agent making a recommendation."""
    
    decision_id = agent_ui_bridge.broadcast_agent_decision(
        flow_id=flow_id,
        agent_id="strategy_agent_003",
        agent_name="Migration Strategy Advisor",
        decision_type="migration_strategy",
        decision="Recommend phased migration approach for customer database",
        reasoning="Database size (500GB) and business criticality require careful approach. Phase 1: Migrate historical data (>2 years old, 300GB). Phase 2: Migrate recent transactional data with minimal downtime window. Phase 3: Real-time sync and cutover.",
        confidence=ConfidenceLevel.HIGH,
        affected_items=["customer_database", "transaction_tables", "history_tables"],
        metadata={
            "database_size_gb": 500,
            "phases": [
                {
                    "phase": 1,
                    "name": "Historical Data",
                    "size_gb": 300,
                    "downtime": "None",
                    "duration": "2 weeks"
                },
                {
                    "phase": 2,
                    "name": "Recent Transactions",
                    "size_gb": 180,
                    "downtime": "2 hours",
                    "duration": "1 weekend"
                },
                {
                    "phase": 3,
                    "name": "Cutover",
                    "size_gb": 20,
                    "downtime": "30 minutes",
                    "duration": "1 day"
                }
            ],
            "risk_level": "medium",
            "rollback_plan": "Available for each phase"
        }
    )
    
    print(f"Broadcast migration strategy decision: {decision_id}")
    return decision_id


# Example 4: Dependency Analysis Agent Decision
def example_dependency_decision(flow_id: str):
    """Example of a dependency analysis agent identifying critical dependencies."""
    
    decision_id = agent_ui_bridge.broadcast_agent_decision(
        flow_id=flow_id,
        agent_id="dependency_agent_004",
        agent_name="Dependency Analyzer",
        decision_type="dependency_analysis",
        decision="Critical dependency identified: Payment Gateway API integration",
        reasoning="The customer database has real-time integration with PaymentGatewayAPI v2.3. This dependency must be updated to v3.0 in the target environment before migration. Current API calls: 50,000/day average.",
        confidence=ConfidenceLevel.MEDIUM,
        affected_items=["payment_gateway_integration", "customer_payment_table", "transaction_processor"],
        metadata={
            "dependency_type": "external_api",
            "current_version": "2.3",
            "required_version": "3.0",
            "api_calls_per_day": 50000,
            "criticality": "high",
            "migration_impact": "API endpoints must be updated",
            "testing_required": True,
            "estimated_effort_hours": 40
        }
    )
    
    print(f"Broadcast dependency analysis decision: {decision_id}")
    return decision_id


# Example 5: How to integrate with CrewAI agents
def example_crewai_agent_integration():
    """
    Example showing how a CrewAI agent would use the broadcast functionality
    within a flow execution.
    """
    
    from crewai import Agent, Task
    
    class FieldMappingAgent:
        def __init__(self, flow_id: str):
            self.flow_id = flow_id
            self.agent = Agent(
                role="Field Mapping Specialist",
                goal="Map source fields to target fields accurately",
                backstory="Expert in data schema analysis and field mapping"
            )
        
        def analyze_and_broadcast(self, source_field: str, target_candidates: list):
            """Analyze field mapping and broadcast decision."""
            
            # Agent performs analysis (simplified)
            best_match = target_candidates[0]  # In reality, would use AI analysis
            confidence = ConfidenceLevel.HIGH
            
            # Broadcast the decision through agent-ui-bridge
            decision_id = agent_ui_bridge.broadcast_agent_decision(
                flow_id=self.flow_id,
                agent_id=f"crewai_field_mapper_{self.agent.role}",
                agent_name=self.agent.role,
                decision_type="field_mapping",
                decision=f"Map '{source_field}' to '{best_match}'",
                reasoning=f"AI analysis indicates {best_match} is the best semantic match for {source_field}",
                confidence=confidence,
                affected_items=[source_field, best_match],
                metadata={
                    "agent_framework": "crewai",
                    "analysis_method": "semantic_similarity",
                    "alternatives_considered": target_candidates
                }
            )
            
            return decision_id
    
    # Usage in a flow
    flow_id = "discovery_flow_123"
    mapper = FieldMappingAgent(flow_id)
    
    # Agent makes and broadcasts a decision
    decision_id = mapper.analyze_and_broadcast(
        source_field="cust_id",
        target_candidates=["customer_id", "client_id", "user_id"]
    )
    
    print(f"CrewAI agent broadcast decision: {decision_id}")


# Example 6: Listening for decisions in another service
async def example_decision_listener(flow_id: str):
    """Example of how another service can listen for agent decisions."""
    
    import asyncio
    
    # Create a queue to receive decisions
    decision_queue = asyncio.Queue(maxsize=100)
    
    # Register as a listener
    agent_ui_bridge.register_decision_listener(flow_id, decision_queue)
    
    try:
        # Listen for decisions
        while True:
            decision = await asyncio.wait_for(decision_queue.get(), timeout=30.0)
            
            print(f"Received agent decision: {decision['decision']}")
            print(f"  Agent: {decision['agent_name']}")
            print(f"  Type: {decision['decision_type']}")
            print(f"  Confidence: {decision['confidence']}")
            print(f"  Reasoning: {decision['reasoning']}")
            
            # Process the decision as needed
            # e.g., update UI, trigger workflows, log to analytics
            
    except asyncio.TimeoutError:
        print("No decisions received in 30 seconds")
    finally:
        # Unregister when done
        agent_ui_bridge.unregister_decision_listener(flow_id, decision_queue)


if __name__ == "__main__":
    # Test flow ID
    test_flow_id = "test_discovery_flow_001"
    
    # Run examples
    print("=== Agent Decision Broadcasting Examples ===\n")
    
    # Example 1: Field Mapping
    example_field_mapping_decision(test_flow_id)
    print()
    
    # Example 2: Data Quality
    example_data_quality_decision(test_flow_id)
    print()
    
    # Example 3: Migration Strategy
    example_migration_strategy_decision(test_flow_id)
    print()
    
    # Example 4: Dependency Analysis
    example_dependency_decision(test_flow_id)
    print()
    
    # Example 5: CrewAI Integration
    example_crewai_agent_integration()
    print()
    
    # Get insights for the flow (as SSE endpoint would)
    insights = agent_ui_bridge.get_flow_insights(test_flow_id)
    print(f"\n=== Flow Insights (Total: {len(insights)}) ===")
    for insight in insights[:5]:  # Show first 5
        print(f"- [{insight['type']}] {insight['title']}")
        print(f"  Agent: {insight['agent_name']} | Confidence: {insight['confidence']}")