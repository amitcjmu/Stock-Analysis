"""
Seed discovery flows in various states.
Agent 2 Task 2.3 - Discovery flows seeding
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from seeding.constants import BASE_TIMESTAMP, DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, FLOW_IDS, FLOWS, USER_IDS


async def create_discovery_flows(db: AsyncSession) -> list[DiscoveryFlow]:
    """Create discovery flows in various states."""
    print("Creating discovery flows...")
    
    created_flows = []
    
    for i, flow_data in enumerate(FLOWS):
        # Calculate timestamps based on flow state
        created_at = BASE_TIMESTAMP + timedelta(days=i * 7)
        updated_at = created_at + timedelta(hours=flow_data["progress"])
        
        # Create DiscoveryFlow with proper model fields
        flow = DiscoveryFlow(
            id=flow_data["id"],
            flow_id=flow_data["id"],  # Using same ID for both
            master_flow_id=None,  # No master flow for these demos
            
            # Multi-tenant isolation
            client_account_id=DEMO_CLIENT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            user_id=str(flow_data["created_by"]),
            
            # Flow metadata
            flow_name=flow_data["name"],
            status=flow_data["state"],
            progress_percentage=flow_data["progress"] / 100.0,
            
            # Phase completion tracking
            data_import_completed=flow_data["progress"] >= 20,
            field_mapping_completed=flow_data["progress"] >= 45,
            data_cleansing_completed=flow_data["progress"] >= 60,
            asset_inventory_completed=flow_data["progress"] >= 75,
            dependency_analysis_completed=flow_data["progress"] >= 90,
            tech_debt_assessment_completed=flow_data["progress"] >= 100,
            
            # Agent learning configuration
            learning_scope="engagement",
            memory_isolation_level="strict",
            assessment_ready=flow_data.get("assessment_ready", False),
            
            # State management
            phase_state={
                "current_phase": flow_data["current_phase"],
                "phase_progress": flow_data["progress"],
                "phase_metadata": {
                    "source": "demo_seeding",
                    "version": "1.0"
                }
            },
            agent_state={
                "active_agents": get_active_agents(flow_data["current_phase"]),
                "agent_confidence": 0.85,
                "learning_enabled": True
            },
            
            # Optional fields for V3
            flow_type="unified_discovery",
            current_phase=flow_data["current_phase"],
            phases_completed=get_completed_phases(flow_data["progress"]),
            flow_state={
                "initialized": True,
                "configuration": {
                    "auto_advance": True,
                    "notification_enabled": True
                }
            },
            
            # CrewAI integration
            crewai_state_data={
                "flow_status": flow_data["state"],
                "crews_executed": get_crews_executed(flow_data["progress"]),
                "agent_insights": get_agent_insights(flow_data)
            },
            
            # Error handling for failed flow
            error_message=flow_data.get("error_message"),
            error_phase="data_import_phase" if flow_data.get("error_message") else None,
            error_details={"reason": flow_data.get("error_message"), "timestamp": updated_at.isoformat()} if flow_data.get("error_message") else None,
            
            # Timestamps
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Set completion time for completed flow
        if flow_data["state"] == "complete":
            flow.completed_at = updated_at
        
        # Create CrewAI Flow State Extensions
        crew_state = CrewAIFlowStateExtensions(
            flow_id=flow_data["id"],
            client_account_id=DEMO_CLIENT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            user_id=str(flow_data["created_by"]),
            
            # Flow metadata
            flow_type="discovery",
            flow_name=flow_data["name"],
            flow_status=flow_data["state"],
            flow_configuration={
                "auto_advance": True,
                "notification_enabled": True,
                "current_phase": flow_data["current_phase"]
            },
            
            # CrewAI Flow persistence data
            flow_persistence_data={
                "current_task": get_current_task(flow_data["current_phase"]),
                "completed_tasks": get_completed_tasks(flow_data["progress"]),
                "pending_tasks": get_pending_tasks(flow_data["progress"]),
                "crew_outputs": get_crew_outputs(flow_data),
                "intermediate_results": get_intermediate_results(flow_data)
            },
            
            # Agent collaboration log
            agent_collaboration_log=get_agent_interactions(flow_data["progress"]),
            
            # Memory usage metrics
            memory_usage_metrics={
                "total_memories": flow_data["progress"] * 10,
                "active_memories": flow_data["progress"] * 5,
                "memory_utilization": 0.75
            },
            
            # Knowledge base analytics
            knowledge_base_analytics={
                "patterns_identified": flow_data["progress"] // 10,
                "rules_created": flow_data["progress"] // 15,
                "confidence_improvements": flow_data["progress"] / 200
            },
            
            # Flow performance metrics
            phase_execution_times=get_task_durations(flow_data["progress"]),
            agent_performance_metrics={
                "total_execution_time": flow_data["progress"] * 10,  # minutes
                "llm_calls": flow_data["progress"] * 5,
                "success_rate": 0.95 if flow_data["state"] != "failed" else 0.0,
                "confidence_scores": {
                    "data_import": 0.9,
                    "field_mapping": 0.85,
                    "asset_intelligence": 0.88
                }
            },
            crew_coordination_analytics={
                "crews_executed": get_crews_executed(flow_data["progress"]),
                "coordination_efficiency": 0.9,
                "handoff_success_rate": 0.95
            },
            
            # Learning and adaptation data
            learning_patterns=[
                {
                    "timestamp": (created_at + timedelta(hours=i)).isoformat(),
                    "type": "field_mapping",
                    "data": {"confidence": 0.8 + (i * 0.02)}
                }
                for i in range(min(flow_data["progress"] // 20, 5))
            ],
            user_feedback_history=[],
            adaptation_metrics={
                "learning_rate": 0.05,
                "adaptation_success": 0.85
            },
            
            # Metadata
            created_at=created_at,
            updated_at=updated_at
        )
        
        db.add(flow)
        db.add(crew_state)
        created_flows.append(flow)
        
        print(f"✓ Created flow: {flow_data['name']} (state: {flow_data['state']}, progress: {flow_data['progress']}%)")
    
    await db.commit()
    return created_flows


def get_active_agents(phase: str) -> list[str]:
    """Get active agents based on phase."""
    agents_by_phase = {
        "initialization_phase": ["flow_initialization_agent"],
        "data_import_phase": ["data_import_agent", "validation_agent"],
        "field_mapping_phase": ["field_mapping_agent", "schema_analysis_agent"],
        "asset_intelligence_phase": ["asset_discovery_agent", "dependency_agent"],
        "completion_phase": ["summary_agent", "report_generation_agent"]
    }
    return agents_by_phase.get(phase, [])


def get_completed_phases(progress: int) -> list[str]:
    """Get completed phases based on progress."""
    phases = []
    if progress >= 20:
        phases.append("data_import_phase")
    if progress >= 45:
        phases.append("field_mapping_phase")
    if progress >= 60:
        phases.append("data_cleansing_phase")
    if progress >= 75:
        phases.append("asset_intelligence_phase")
    if progress >= 90:
        phases.append("dependency_analysis_phase")
    if progress >= 100:
        phases.append("completion_phase")
    return phases


def get_crews_executed(progress: int) -> list[str]:
    """Get crews executed based on progress."""
    crews = []
    if progress >= 20:
        crews.append("data_import_validation_crew")
    if progress >= 45:
        crews.append("field_mapping_crew")
    if progress >= 60:
        crews.append("data_cleansing_crew")
    if progress >= 75:
        crews.append("asset_intelligence_crew")
    if progress >= 90:
        crews.append("dependency_analysis_crew")
    return crews


def get_agent_insights(flow_data: dict) -> list[dict]:
    """Generate agent insights based on flow state."""
    insights = []
    
    if flow_data["progress"] >= 20:
        insights.append({
            "agent": "data_import_agent",
            "insight": "Successfully imported and validated data with 98% quality score",
            "confidence": 0.92,
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=2)).isoformat()
        })
    
    if flow_data["progress"] >= 45:
        insights.append({
            "agent": "field_mapping_agent",
            "insight": "Identified 45 critical fields with 87% confidence in mapping accuracy",
            "confidence": 0.87,
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=5)).isoformat()
        })
    
    if flow_data["progress"] >= 75:
        insights.append({
            "agent": "asset_discovery_agent",
            "insight": "Discovered 75 assets across 3 categories with dependency relationships",
            "confidence": 0.89,
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=8)).isoformat()
        })
    
    return insights


def get_current_task(phase: str) -> str:
    """Get current task based on phase."""
    task_map = {
        "initialization_phase": "initialize_flow",
        "data_import_phase": "validate_imported_data",
        "field_mapping_phase": "map_source_fields",
        "asset_intelligence_phase": "analyze_assets",
        "completion_phase": "generate_final_report"
    }
    return task_map.get(phase, "unknown_task")


def get_completed_tasks(progress: int) -> list[str]:
    """Get completed tasks based on progress."""
    all_tasks = [
        "initialize_flow",
        "setup_environment",
        "validate_credentials",
        "import_data",
        "validate_data_quality",
        "identify_fields",
        "map_fields",
        "validate_mappings",
        "discover_assets",
        "analyze_dependencies"
    ]
    
    completed_count = int(len(all_tasks) * (progress / 100))
    return all_tasks[:completed_count]


def get_pending_tasks(progress: int) -> list[str]:
    """Get pending tasks based on progress."""
    all_tasks = [
        "initialize_flow",
        "setup_environment",
        "validate_credentials",
        "import_data",
        "validate_data_quality",
        "identify_fields",
        "map_fields",
        "validate_mappings",
        "discover_assets",
        "analyze_dependencies",
        "generate_reports",
        "finalize_assessment"
    ]
    
    completed_count = int(len(all_tasks) * (progress / 100))
    return all_tasks[completed_count:]


def get_crew_outputs(flow_data: dict) -> dict:
    """Generate crew outputs based on flow state."""
    if flow_data["state"] == "failed":
        return {"error": flow_data.get("error_message", "Data validation failed")}
    
    outputs = {}
    
    if flow_data["progress"] >= 20:
        outputs["data_import"] = {
            "imported_records": 150,
            "validation_status": "passed",
            "data_quality_score": 0.92
        }
    
    if flow_data["progress"] >= 45:
        outputs["field_mapping"] = {
            "mapped_fields": 45,
            "confidence_score": 0.87,
            "unmapped_fields": 5
        }
    
    if flow_data["progress"] >= 65:
        outputs["asset_discovery"] = {
            "discovered_assets": 75,
            "asset_types": ["servers", "applications", "databases"],
            "dependency_count": 120
        }
    
    if flow_data["progress"] >= 100:
        outputs["final_assessment"] = {
            "total_assets": 75,
            "migration_ready": 65,
            "requires_remediation": 10,
            "estimated_effort": "6 months"
        }
    
    return outputs


def get_intermediate_results(flow_data: dict) -> dict:
    """Generate intermediate results based on flow progress."""
    results = {
        "phase_results": {},
        "validation_results": {},
        "analysis_results": {}
    }
    
    if flow_data["progress"] >= 15:
        results["phase_results"]["initialization"] = {
            "status": "complete",
            "duration_minutes": 5,
            "environment_ready": True
        }
    
    if flow_data["progress"] >= 30:
        results["validation_results"]["data_quality"] = {
            "total_records": 150,
            "valid_records": 148,
            "issues_found": 2,
            "quality_score": 0.987
        }
    
    if flow_data["progress"] >= 60:
        results["analysis_results"]["dependencies"] = {
            "direct_dependencies": 45,
            "transitive_dependencies": 75,
            "circular_dependencies": 0,
            "missing_dependencies": 3
        }
    
    return results


def get_task_durations(progress: int) -> dict:
    """Generate task durations based on progress."""
    durations = {}
    
    base_tasks = [
        ("initialize_flow", 2),
        ("setup_environment", 3),
        ("import_data", 15),
        ("validate_data", 10),
        ("map_fields", 20),
        ("discover_assets", 25),
        ("analyze_dependencies", 30)
    ]
    
    for task, base_duration in base_tasks:
        if progress > len(durations) * (100 / len(base_tasks)):
            durations[task] = base_duration + (progress // 20)  # Add some variation
    
    return durations


def get_agent_interactions(progress: int) -> list[dict]:
    """Generate agent interactions based on progress."""
    interactions = []
    
    if progress >= 20:
        interactions.append({
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=2)).isoformat(),
            "from_agent": "data_import_agent",
            "to_agent": "validation_agent",
            "message_type": "data_ready",
            "payload": {"record_count": 150}
        })
    
    if progress >= 45:
        interactions.append({
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=5)).isoformat(),
            "from_agent": "field_mapping_agent",
            "to_agent": "asset_intelligence_agent",
            "message_type": "mapping_complete",
            "payload": {"mapped_fields": 45}
        })
    
    if progress >= 65:
        interactions.append({
            "timestamp": (BASE_TIMESTAMP + timedelta(hours=8)).isoformat(),
            "from_agent": "asset_intelligence_agent",
            "to_agent": "dependency_agent",
            "message_type": "assets_discovered",
            "payload": {"asset_count": 75}
        })
    
    return interactions


async def main():
    """Main seeding function."""
    print("\n=== Seeding Discovery Flows ===\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            existing_flow = await db.get(DiscoveryFlow, FLOW_IDS["complete"])
            if existing_flow:
                print("⚠️  Discovery flows already seeded. Skipping...")
                return
            
            # Create flows
            flows = await create_discovery_flows(db)
            
            print(f"\n✅ Successfully seeded {len(flows)} discovery flows:")
            for flow in flows:
                print(f"   - {flow.flow_name} ({flow.status}, {flow.progress_percentage * 100:.0f}%)")
            
            # Export flow IDs for reference
            flow_ids_for_export = {
                "flows": [
                    {
                        "id": str(flow.id),
                        "flow_id": str(flow.flow_id),
                        "name": flow.flow_name,
                        "state": flow.status,
                        "progress": int(flow.progress_percentage * 100)
                    }
                    for flow in flows
                ]
            }
            
            with open(Path(__file__).parent / "FLOW_IDS.json", "w") as f:
                json.dump(flow_ids_for_export, f, indent=2)
            
            print("\n✅ Exported flow IDs to FLOW_IDS.json")
            
        except Exception as e:
            print(f"\n❌ Error seeding discovery flows: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())