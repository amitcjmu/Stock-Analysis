"""
Collection Flow Handlers
ADCS: Handlers for Collection flow lifecycle and phase transitions

Provides handler functions for initialization, finalization, error handling,
and phase-specific operations in the Collection flow.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Flow Lifecycle Handlers
async def collection_initialization(
    flow_id: str,
    flow_type: str,
    configuration: Optional[Dict[str, Any]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Initialize Collection flow configuration - following async flow state pattern"""
    try:
        logger.info(f"🚀 Initializing Collection flow {flow_id}")
        
        # Extract configuration
        config = configuration or {}
        state = initial_state or {}
        
        # Set up collection-specific initialization (no DB operations)
        initialization_result = {
            "initialized": True,
            "flow_id": flow_id,
            "initialization_time": datetime.utcnow().isoformat(),
            "collection_config": {
                "automation_tier": state.get("automation_tier", "tier_2"),
                "parallel_collection": config.get("parallel_collection", True),
                "quality_threshold": config.get("quality_threshold", 0.8),
                "gap_analysis_enabled": config.get("gap_analysis_enabled", True),
                "adaptive_questionnaires": config.get("adaptive_questionnaires", True),
                "max_collection_attempts": config.get("max_collection_attempts", 3)
            },
            "platform_detection": {
                "auto_discovery": config.get("auto_discovery", True),
                "credential_validation": config.get("credential_validation", True),
                "tier_assessment": config.get("tier_assessment", True)
            },
            "adapter_settings": {
                "timeout_seconds": config.get("adapter_timeout", 300),
                "retry_attempts": config.get("retry_attempts", 3),
                "batch_size": config.get("batch_size", 100)
            },
            "monitoring": {
                "metrics_enabled": True,
                "log_level": config.get("log_level", "INFO"),
                "alerts_enabled": config.get("alerts_enabled", True)
            }
        }
        
        # Add initial state data if provided
        if state:
            initialization_result["initial_state"] = state
        
        # Initialize statistics tracking (in-memory only)
        initialization_result["statistics"] = {
            "platforms_detected": 0,
            "data_collected": 0,
            "gaps_identified": 0,
            "questionnaires_generated": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Start CrewAI flow execution in background
        try:
            await _start_crewai_collection_flow_background(flow_id, state, context)
            initialization_result["crewai_execution"] = "started"
            logger.info(f"✅ Collection flow {flow_id} initialized successfully with CrewAI execution started")
        except Exception as crewai_error:
            logger.error(f"⚠️ Collection flow {flow_id} initialized but CrewAI execution failed to start: {crewai_error}")
            initialization_result["crewai_execution"] = "failed"
            initialization_result["crewai_error"] = str(crewai_error)
        
        return initialization_result
        
    except Exception as e:
        logger.error(f"❌ Collection initialization failed: {e}")
        return {
            "initialized": False,
            "flow_id": flow_id,
            "error": str(e),
            "initialization_time": datetime.utcnow().isoformat()
        }


async def collection_finalization(
    db: AsyncSession,
    flow_id: str,
    final_state: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Finalize Collection flow and update records"""
    try:
        logger.info(f"🏁 Finalizing Collection flow {flow_id}")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Calculate final metrics
        crew_results = final_state.get("crew_results", {})
        quality_report = crew_results.get("quality_report", {})
        
        # Update collection flow
        update_query = """
            UPDATE collection_flows
            SET status = :status,
                completed_at = :completed_at,
                collection_quality_score = :quality_score,
                confidence_score = :confidence_score,
                metadata = metadata || :metadata::jsonb,
                updated_at = :updated_at
            WHERE master_flow_id = :master_flow_id
        """
        
        await db.execute(update_query, {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "quality_score": quality_report.get("overall_quality", 0.0),
            "confidence_score": crew_results.get("sixr_readiness_score", 0.0),
            "metadata": {
                "completion_time": datetime.utcnow().isoformat(),
                "total_resources_collected": quality_report.get("total_resources", 0),
                "platforms_collected": len(crew_results.get("final_data", {})),
                "collection_summary": crew_results.get("summary", {})
            },
            "updated_at": datetime.utcnow(),
            "master_flow_id": flow_id
        })
        
        # Update master flow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        master_flow_query = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_id
        )
        result = await db.execute(master_flow_query)
        master_flow = result.scalar_one_or_none()
        
        if master_flow:
            master_flow.collection_quality_score = quality_report.get("overall_quality", 0.0)
            master_flow.data_collection_metadata["completed_at"] = datetime.utcnow().isoformat()
            master_flow.data_collection_metadata["final_metrics"] = {
                "quality_score": quality_report.get("overall_quality", 0.0),
                "sixr_readiness": crew_results.get("sixr_readiness_score", 0.0),
                "total_resources": quality_report.get("total_resources", 0)
            }
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Collection flow finalized successfully",
            "final_metrics": {
                "quality_score": quality_report.get("overall_quality", 0.0),
                "sixr_readiness": crew_results.get("sixr_readiness_score", 0.0),
                "total_resources": quality_report.get("total_resources", 0),
                "completion_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Collection finalization failed: {e}")
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


async def collection_error_handler(
    db: AsyncSession,
    flow_id: str,
    error: Exception,
    error_context: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle errors in Collection flow"""
    try:
        logger.error(f"❌ Collection flow error for {flow_id}: {error}")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            logger.warning(f"Collection flow for master {flow_id} not found")
            return {"success": False, "error": "Collection flow not found"}
        
        # Update collection flow with error
        update_query = """
            UPDATE collection_flows
            SET status = :status,
                error_message = :error_message,
                error_details = :error_details::jsonb,
                updated_at = :updated_at
            WHERE master_flow_id = :master_flow_id
        """
        
        await db.execute(update_query, {
            "status": "failed",
            "error_message": str(error),
            "error_details": {
                "error_type": type(error).__name__,
                "error_context": error_context,
                "failed_at": datetime.utcnow().isoformat(),
                "phase": error_context.get("phase", "unknown"),
                "operation": error_context.get("operation", "unknown")
            },
            "updated_at": datetime.utcnow(),
            "master_flow_id": flow_id
        })
        
        await db.commit()
        
        # Determine if error is recoverable
        recoverable_errors = ["ConnectionError", "TimeoutError", "RateLimitError"]
        is_recoverable = type(error).__name__ in recoverable_errors
        
        return {
            "success": True,
            "error_handled": True,
            "is_recoverable": is_recoverable,
            "recovery_strategy": "retry" if is_recoverable else "manual_intervention",
            "message": f"Error logged: {str(error)}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error handler failed: {e}")
        return {
            "success": False,
            "error": f"Error handler failed: {str(e)}"
        }


async def collection_rollback_handler(
    db: AsyncSession,
    flow_id: str,
    rollback_to_phase: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle rollback for Collection flow"""
    try:
        logger.info(f"⏪ Rolling back Collection flow {flow_id} to phase {rollback_to_phase}")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Define rollback actions by phase
        rollback_actions = {
            "platform_detection": ["clear_all_collected_data", "reset_adapters"],
            "automated_collection": ["clear_collected_data", "retain_platforms"],
            "gap_analysis": ["clear_gaps", "retain_collected_data"],
            "manual_collection": ["clear_responses", "retain_gaps"],
            "synthesis": ["clear_synthesis", "retain_all_raw_data"]
        }
        
        actions = rollback_actions.get(rollback_to_phase, [])
        
        # Execute rollback actions
        for action in actions:
            if action == "clear_all_collected_data":
                await _clear_collected_data(db, collection_flow["id"])
            elif action == "clear_collected_data":
                await _clear_collected_data(db, collection_flow["id"], preserve_platforms=True)
            elif action == "clear_gaps":
                await _clear_gaps(db, collection_flow["id"])
            elif action == "clear_responses":
                await _clear_questionnaire_responses(db, collection_flow["id"])
        
        # Update collection flow state
        update_query = """
            UPDATE collection_flows
            SET current_phase = :current_phase,
                status = :status,
                phase_state = phase_state || :rollback_info::jsonb,
                updated_at = :updated_at
            WHERE master_flow_id = :master_flow_id
        """
        
        await db.execute(update_query, {
            "current_phase": rollback_to_phase,
            "status": "rolled_back",
            "rollback_info": {
                "rollback_at": datetime.utcnow().isoformat(),
                "rollback_from": collection_flow.get("current_phase"),
                "rollback_to": rollback_to_phase,
                "actions_taken": actions
            },
            "updated_at": datetime.utcnow(),
            "master_flow_id": flow_id
        })
        
        await db.commit()
        
        return {
            "success": True,
            "rolled_back_to": rollback_to_phase,
            "actions_taken": actions,
            "message": f"Successfully rolled back to {rollback_to_phase}"
        }
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


async def collection_checkpoint_handler(
    db: AsyncSession,
    flow_id: str,
    checkpoint_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Create checkpoint for Collection flow"""
    try:
        logger.info(f"💾 Creating checkpoint for Collection flow {flow_id}")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Update phase state with checkpoint
        update_query = """
            UPDATE collection_flows
            SET phase_state = phase_state || :checkpoint::jsonb,
                updated_at = :updated_at
            WHERE master_flow_id = :master_flow_id
        """
        
        checkpoint_info = {
            "checkpoints": {
                checkpoint_data.get("phase", "unknown"): {
                    "created_at": datetime.utcnow().isoformat(),
                    "data": checkpoint_data,
                    "phase_progress": checkpoint_data.get("progress", 0),
                    "can_resume": True
                }
            }
        }
        
        await db.execute(update_query, {
            "checkpoint": checkpoint_info,
            "updated_at": datetime.utcnow(),
            "master_flow_id": flow_id
        })
        
        await db.commit()
        
        return {
            "success": True,
            "checkpoint_created": True,
            "phase": checkpoint_data.get("phase"),
            "message": "Checkpoint created successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Checkpoint creation failed: {e}")
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


# Phase-specific Handlers
async def platform_inventory_creation(
    db: AsyncSession,
    flow_id: str,
    phase_results: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Create platform inventory after detection"""
    try:
        crew_results = phase_results.get("crew_results", {})
        detected_platforms = crew_results.get("platforms", [])
        
        logger.info(f"📋 Creating platform inventory for {len(detected_platforms)} platforms")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Store platform inventory in metadata
        update_query = """
            UPDATE collection_flows
            SET metadata = metadata || :platform_data::jsonb,
                updated_at = :updated_at
            WHERE master_flow_id = :master_flow_id
        """
        
        platform_data = {
            "platform_inventory": {
                "detected_at": datetime.utcnow().isoformat(),
                "platforms": detected_platforms,
                "recommended_adapters": crew_results.get("recommended_adapters", {}),
                "platform_metadata": crew_results.get("platform_metadata", {})
            }
        }
        
        await db.execute(update_query, {
            "platform_data": platform_data,
            "updated_at": datetime.utcnow(),
            "master_flow_id": flow_id
        })
        
        await db.commit()
        
        return {
            "success": True,
            "platforms_detected": len(detected_platforms),
            "adapters_recommended": len(crew_results.get("recommended_adapters", {}))
        }
        
    except Exception as e:
        logger.error(f"❌ Platform inventory creation failed: {e}")
        return {"success": False, "error": str(e)}


async def adapter_preparation(
    db: AsyncSession,
    flow_id: str,
    phase_input: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare adapters for automated collection"""
    try:
        logger.info("🔧 Preparing adapters for collection")
        
        # Get available adapters from registry
        adapter_configs = phase_input.get("adapter_configs", {})
        
        # Validate and prepare each adapter
        prepared_adapters = {}
        for platform_id, config in adapter_configs.items():
            # Check adapter availability
            adapter_name = config.get("adapter_name")
            if adapter_name:
                # Verify adapter exists in platform_adapters table
                adapter = await _get_adapter_by_name(db, adapter_name)
                if adapter:
                    prepared_adapters[platform_id] = {
                        "adapter_id": str(adapter["id"]),
                        "adapter_name": adapter_name,
                        "status": "ready",
                        "config": config
                    }
                else:
                    logger.warning(f"Adapter {adapter_name} not found for platform {platform_id}")
        
        return {
            "success": True,
            "prepared_adapters": prepared_adapters,
            "adapter_count": len(prepared_adapters)
        }
        
    except Exception as e:
        logger.error(f"❌ Adapter preparation failed: {e}")
        return {"success": False, "error": str(e)}


async def collection_data_normalization(
    db: AsyncSession,
    flow_id: str,
    phase_results: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Normalize collected data after automated collection"""
    try:
        crew_results = phase_results.get("crew_results", {})
        collected_data = crew_results.get("collected_data", {})
        
        logger.info(f"🔄 Normalizing data from {len(collected_data)} platforms")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Store collected data in inventory
        for platform_id, platform_data in collected_data.items():
            inventory_data = {
                "id": uuid.uuid4(),
                "collection_flow_id": collection_flow["id"],
                "platform": platform_id,
                "collection_method": "automated",
                "raw_data": platform_data,
                "normalized_data": _normalize_platform_data(platform_data),
                "data_type": platform_data.get("data_type", "mixed"),
                "resource_count": len(platform_data.get("resources", [])),
                "quality_score": crew_results.get("quality_scores", {}).get(platform_id, 0.0),
                "validation_status": "validated",
                "metadata": {
                    "collection_timestamp": datetime.utcnow().isoformat(),
                    "adapter_used": platform_data.get("adapter_name")
                },
                "collected_at": datetime.utcnow()
            }
            
            # Insert into collected_data_inventory
            insert_query = """
                INSERT INTO collected_data_inventory
                (id, collection_flow_id, platform, collection_method, raw_data,
                 normalized_data, data_type, resource_count, quality_score,
                 validation_status, metadata, collected_at)
                VALUES
                (:id, :collection_flow_id, :platform, :collection_method, :raw_data::jsonb,
                 :normalized_data::jsonb, :data_type, :resource_count, :quality_score,
                 :validation_status, :metadata::jsonb, :collected_at)
            """
            
            await db.execute(insert_query, inventory_data)
        
        await db.commit()
        
        return {
            "success": True,
            "platforms_normalized": len(collected_data),
            "total_resources": sum(len(d.get("resources", [])) for d in collected_data.values())
        }
        
    except Exception as e:
        logger.error(f"❌ Data normalization failed: {e}")
        await db.rollback()
        return {"success": False, "error": str(e)}


async def gap_analysis_preparation(
    db: AsyncSession,
    flow_id: str,
    phase_input: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare for gap analysis"""
    try:
        logger.info("🔍 Preparing gap analysis")
        
        # Load collected data from inventory
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Query collected data
        query = """
            SELECT platform, normalized_data, quality_score, resource_count
            FROM collected_data_inventory
            WHERE collection_flow_id = :collection_flow_id
        """
        
        result = await db.execute(query, {"collection_flow_id": collection_flow["id"]})
        collected_data = result.fetchall()
        
        # Prepare data for gap analysis
        analysis_data = {
            "platforms": {},
            "total_resources": 0,
            "average_quality": 0.0
        }
        
        quality_scores = []
        for row in collected_data:
            analysis_data["platforms"][row.platform] = {
                "data": row.normalized_data,
                "quality_score": row.quality_score,
                "resource_count": row.resource_count
            }
            analysis_data["total_resources"] += row.resource_count
            quality_scores.append(row.quality_score)
        
        if quality_scores:
            analysis_data["average_quality"] = sum(quality_scores) / len(quality_scores)
        
        return {
            "success": True,
            "analysis_data": analysis_data,
            "platform_count": len(analysis_data["platforms"])
        }
        
    except Exception as e:
        logger.error(f"❌ Gap analysis preparation failed: {e}")
        return {"success": False, "error": str(e)}


async def gap_prioritization(
    db: AsyncSession,
    flow_id: str,
    phase_results: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Prioritize identified gaps"""
    try:
        crew_results = phase_results.get("crew_results", {})
        identified_gaps = crew_results.get("data_gaps", [])
        
        logger.info(f"📊 Prioritizing {len(identified_gaps)} identified gaps")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Store gaps in database
        for gap in identified_gaps:
            gap_data = {
                "id": uuid.uuid4(),
                "collection_flow_id": collection_flow["id"],
                "gap_type": gap.get("type", "missing_data"),
                "gap_category": gap.get("category", "general"),
                "field_name": gap.get("field_name", "unknown"),
                "description": gap.get("description", ""),
                "impact_on_sixr": gap.get("sixr_impact", "medium"),
                "priority": gap.get("priority", 5),
                "suggested_resolution": gap.get("resolution", ""),
                "resolution_status": "pending",
                "metadata": {
                    "platform": gap.get("platform"),
                    "resource_type": gap.get("resource_type"),
                    "detection_method": gap.get("detection_method", "ai_analysis")
                },
                "created_at": datetime.utcnow()
            }
            
            insert_query = """
                INSERT INTO collection_data_gaps
                (id, collection_flow_id, gap_type, gap_category, field_name,
                 description, impact_on_sixr, priority, suggested_resolution,
                 resolution_status, metadata, created_at)
                VALUES
                (:id, :collection_flow_id, :gap_type, :gap_category, :field_name,
                 :description, :impact_on_sixr, :priority, :suggested_resolution,
                 :resolution_status, :metadata::jsonb, :created_at)
            """
            
            await db.execute(insert_query, gap_data)
        
        await db.commit()
        
        # Calculate gap statistics
        high_priority_gaps = len([g for g in identified_gaps if g.get("priority", 0) >= 8])
        critical_sixr_gaps = len([g for g in identified_gaps if g.get("sixr_impact") == "high"])
        
        return {
            "success": True,
            "total_gaps": len(identified_gaps),
            "high_priority_gaps": high_priority_gaps,
            "critical_sixr_gaps": critical_sixr_gaps
        }
        
    except Exception as e:
        logger.error(f"❌ Gap prioritization failed: {e}")
        await db.rollback()
        return {"success": False, "error": str(e)}


async def questionnaire_generation(
    db: AsyncSession,
    flow_id: str,
    phase_input: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate questionnaires for manual collection"""
    try:
        logger.info("📝 Generating questionnaires for manual collection")
        
        # Get collection flow and gaps
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Query gaps that need manual collection
        gaps_query = """
            SELECT id, gap_type, field_name, description, priority, suggested_resolution
            FROM collection_data_gaps
            WHERE collection_flow_id = :collection_flow_id
            AND resolution_status = 'pending'
            ORDER BY priority DESC
        """
        
        result = await db.execute(gaps_query, {"collection_flow_id": collection_flow["id"]})
        gaps = result.fetchall()
        
        # Generate questions based on gaps
        questions_generated = 0
        for gap in gaps:
            # Create questionnaire based on gap type
            question_template = _get_question_template(gap.gap_type)
            
            question_data = {
                "id": uuid.uuid4(),
                "collection_flow_id": collection_flow["id"],
                "gap_id": gap.id,
                "questionnaire_type": "gap_resolution",
                "question_category": gap.gap_type,
                "question_id": f"gap_{gap.id}",
                "question_text": question_template.format(
                    field_name=gap.field_name,
                    description=gap.description
                ),
                "response_type": "structured",
                "metadata": {
                    "priority": gap.priority,
                    "suggested_resolution": gap.suggested_resolution
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            insert_query = """
                INSERT INTO collection_questionnaire_responses
                (id, collection_flow_id, gap_id, questionnaire_type, question_category,
                 question_id, question_text, response_type, metadata, created_at, updated_at)
                VALUES
                (:id, :collection_flow_id, :gap_id, :questionnaire_type, :question_category,
                 :question_id, :question_text, :response_type, :metadata::jsonb, :created_at, :updated_at)
            """
            
            await db.execute(insert_query, question_data)
            questions_generated += 1
        
        await db.commit()
        
        return {
            "success": True,
            "questions_generated": questions_generated,
            "gaps_addressed": len(gaps)
        }
        
    except Exception as e:
        logger.error(f"❌ Questionnaire generation failed: {e}")
        await db.rollback()
        return {"success": False, "error": str(e)}


async def response_processing(
    db: AsyncSession,
    flow_id: str,
    phase_results: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Process questionnaire responses"""
    try:
        crew_results = phase_results.get("crew_results", {})
        responses = crew_results.get("responses", {})
        
        logger.info(f"✅ Processing {len(responses)} questionnaire responses")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Update questionnaire responses
        for gap_id, response in responses.items():
            update_query = """
                UPDATE collection_questionnaire_responses
                SET response_value = :response_value::jsonb,
                    confidence_score = :confidence_score,
                    validation_status = :validation_status,
                    responded_by = :responded_by,
                    responded_at = :responded_at,
                    updated_at = :updated_at
                WHERE collection_flow_id = :collection_flow_id
                AND gap_id = :gap_id
            """
            
            await db.execute(update_query, {
                "response_value": response.get("value", {}),
                "confidence_score": response.get("confidence", 0.0),
                "validation_status": "validated" if response.get("is_valid", False) else "pending",
                "responded_by": context["user_id"],
                "responded_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "collection_flow_id": collection_flow["id"],
                "gap_id": gap_id
            })
            
            # Update gap resolution status
            if response.get("is_valid", False):
                gap_update_query = """
                    UPDATE collection_data_gaps
                    SET resolution_status = 'resolved',
                        resolved_at = :resolved_at,
                        resolved_by = 'manual_collection'
                    WHERE id = :gap_id
                """
                
                await db.execute(gap_update_query, {
                    "resolved_at": datetime.utcnow(),
                    "gap_id": gap_id
                })
        
        await db.commit()
        
        return {
            "success": True,
            "responses_processed": len(responses),
            "gaps_resolved": len([r for r in responses.values() if r.get("is_valid", False)])
        }
        
    except Exception as e:
        logger.error(f"❌ Response processing failed: {e}")
        await db.rollback()
        return {"success": False, "error": str(e)}


async def synthesis_preparation(
    db: AsyncSession,
    flow_id: str,
    phase_input: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for synthesis"""
    try:
        logger.info("🔄 Preparing data synthesis")
        
        # Get collection flow
        collection_flow = await _get_collection_flow_by_master_id(db, flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow for master {flow_id} not found")
        
        # Load all collected data
        collected_query = """
            SELECT platform, collection_method, normalized_data, quality_score
            FROM collected_data_inventory
            WHERE collection_flow_id = :collection_flow_id
        """
        
        result = await db.execute(collected_query, {"collection_flow_id": collection_flow["id"]})
        collected_data = result.fetchall()
        
        # Load resolved gaps
        gaps_query = """
            SELECT g.field_name, g.platform, r.response_value, r.confidence_score
            FROM collection_data_gaps g
            JOIN collection_questionnaire_responses r ON g.id = r.gap_id
            WHERE g.collection_flow_id = :collection_flow_id
            AND g.resolution_status = 'resolved'
        """
        
        result = await db.execute(gaps_query, {"collection_flow_id": collection_flow["id"]})
        resolved_gaps = result.fetchall()
        
        # Prepare synthesis input
        synthesis_data = {
            "automated_data": {},
            "manual_data": {},
            "platform_summary": {}
        }
        
        # Process automated collection data
        for row in collected_data:
            if row.collection_method == "automated":
                synthesis_data["automated_data"][row.platform] = {
                    "data": row.normalized_data,
                    "quality_score": row.quality_score
                }
        
        # Process manual collection data
        for gap in resolved_gaps:
            platform = gap.platform or "general"
            if platform not in synthesis_data["manual_data"]:
                synthesis_data["manual_data"][platform] = {}
            
            synthesis_data["manual_data"][platform][gap.field_name] = {
                "value": gap.response_value,
                "confidence": gap.confidence_score
            }
        
        return {
            "success": True,
            "synthesis_data": synthesis_data,
            "automated_platforms": len(synthesis_data["automated_data"]),
            "manual_fields": sum(len(fields) for fields in synthesis_data["manual_data"].values())
        }
        
    except Exception as e:
        logger.error(f"❌ Synthesis preparation failed: {e}")
        return {"success": False, "error": str(e)}


# Helper functions
async def _get_collection_flow_by_master_id(db: AsyncSession, master_flow_id: str) -> Optional[Dict[str, Any]]:
    """Get collection flow by master flow ID"""
    query = """
        SELECT id, flow_id, status, current_phase, automation_tier
        FROM collection_flows
        WHERE master_flow_id = :master_flow_id
    """
    
    result = await db.execute(query, {"master_flow_id": master_flow_id})
    row = result.fetchone()
    
    if row:
        return {
            "id": row.id,
            "flow_id": row.flow_id,
            "status": row.status,
            "current_phase": row.current_phase,
            "automation_tier": row.automation_tier
        }
    return None


async def _initialize_adapter_registry(db: AsyncSession) -> List[Dict[str, Any]]:
    """Initialize and return available adapters"""
    query = """
        SELECT id, adapter_name, adapter_type, capabilities, supported_platforms
        FROM platform_adapters
        WHERE status = 'active'
    """
    
    result = await db.execute(query)
    adapters = []
    
    for row in result:
        adapters.append({
            "id": str(row.id),
            "name": row.adapter_name,
            "type": row.adapter_type,
            "capabilities": row.capabilities,
            "platforms": row.supported_platforms
        })
    
    return adapters


async def _get_adapter_by_name(db: AsyncSession, adapter_name: str) -> Optional[Dict[str, Any]]:
    """Get adapter by name"""
    query = """
        SELECT id, adapter_name, status, capabilities
        FROM platform_adapters
        WHERE adapter_name = :adapter_name
        AND status = 'active'
    """
    
    result = await db.execute(query, {"adapter_name": adapter_name})
    row = result.fetchone()
    
    if row:
        return {
            "id": row.id,
            "adapter_name": row.adapter_name,
            "status": row.status,
            "capabilities": row.capabilities
        }
    return None


def _normalize_platform_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize platform-specific data to common schema"""
    normalized = {
        "resources": [],
        "metadata": {},
        "platform_specific": {}
    }
    
    # Extract resources
    if "resources" in raw_data:
        normalized["resources"] = raw_data["resources"]
    elif "assets" in raw_data:
        normalized["resources"] = raw_data["assets"]
    elif "items" in raw_data:
        normalized["resources"] = raw_data["items"]
    
    # Extract metadata
    for key in ["platform", "region", "account", "environment"]:
        if key in raw_data:
            normalized["metadata"][key] = raw_data[key]
    
    # Keep platform-specific data
    normalized["platform_specific"] = {
        k: v for k, v in raw_data.items()
        if k not in ["resources", "assets", "items"] and not k.startswith("_")
    }
    
    return normalized


async def _clear_collected_data(db: AsyncSession, collection_flow_id: uuid.UUID, preserve_platforms: bool = False):
    """Clear collected data for rollback"""
    if not preserve_platforms:
        await db.execute(
            "DELETE FROM collected_data_inventory WHERE collection_flow_id = :flow_id",
            {"flow_id": collection_flow_id}
        )
    else:
        # Only clear automated collection data
        await db.execute(
            "DELETE FROM collected_data_inventory WHERE collection_flow_id = :flow_id AND collection_method = 'automated'",
            {"flow_id": collection_flow_id}
        )


async def _clear_gaps(db: AsyncSession, collection_flow_id: uuid.UUID):
    """Clear identified gaps"""
    await db.execute(
        "DELETE FROM collection_data_gaps WHERE collection_flow_id = :flow_id",
        {"flow_id": collection_flow_id}
    )


async def _clear_questionnaire_responses(db: AsyncSession, collection_flow_id: uuid.UUID):
    """Clear questionnaire responses"""
    await db.execute(
        "DELETE FROM collection_questionnaire_responses WHERE collection_flow_id = :flow_id",
        {"flow_id": collection_flow_id}
    )


def _get_question_template(gap_type: str) -> str:
    """Get question template based on gap type"""
    templates = {
        "missing_data": "Please provide the missing {field_name} information. {description}",
        "incomplete_data": "The {field_name} field is incomplete. {description}. Please provide the complete information.",
        "quality_issues": "There are quality issues with {field_name}. {description}. Please provide corrected information.",
        "validation_errors": "The {field_name} failed validation. {description}. Please provide valid information."
    }
    
    return templates.get(gap_type, "Please provide information for {field_name}. {description}")


async def _start_crewai_collection_flow_background(
    flow_id: str,
    initial_state: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Start CrewAI collection flow execution in background"""
    
    async def run_collection_flow():
        try:
            logger.info(f"🚀 Starting CrewAI collection flow execution: {flow_id}")
            
            # Import required modules
            from app.core.context import RequestContext
            from app.services.crewai_flow_service import CrewAIFlowService
            from app.services.crewai_flows.unified_collection_flow import create_unified_collection_flow
            
            # Extract context information
            if context and hasattr(context, 'client_account_id'):
                # If context is a RequestContext object
                request_context = context
            else:
                # Create RequestContext from context dict or use defaults
                context_dict = context or {}
                request_context = RequestContext(
                    client_account_id=context_dict.get('client_account_id'),
                    engagement_id=context_dict.get('engagement_id'),
                    user_id=context_dict.get('user_id', 'system'),
                    flow_id=flow_id
                )
            
            # Create CrewAI service (it will handle its own database connections)
            crewai_service = CrewAIFlowService()
            
            # Prepare initial state data
            automation_tier = initial_state.get("automation_tier", "tier_2")
            collection_config = initial_state.get("collection_config", {})
            flow_metadata = initial_state.copy()
            flow_metadata['master_flow_id'] = flow_id
            
            # Create the UnifiedCollectionFlow instance
            collection_flow = create_unified_collection_flow(
                flow_id=flow_id,
                client_account_id=request_context.client_account_id,
                engagement_id=request_context.engagement_id,
                user_id=request_context.user_id or "system",
                automation_tier=automation_tier,
                collection_config=collection_config,
                metadata=flow_metadata,
                crewai_service=crewai_service,
                context=request_context
            )
            
            # Execute the flow (this will run the CrewAI flow)
            await collection_flow.kickoff()
            
            logger.info(f"✅ CrewAI collection flow completed: {flow_id}")
            
        except Exception as e:
            logger.error(f"❌ CrewAI collection flow execution failed for {flow_id}: {e}")
            # Note: We don't re-raise here as this is a background task
    
    # Start in background - don't await
    asyncio.create_task(run_collection_flow())
    logger.info(f"🔄 CrewAI collection flow {flow_id} started in background")


# Export all handlers
__all__ = [
    # Lifecycle handlers
    "collection_initialization",
    "collection_finalization",
    "collection_error_handler",
    "collection_rollback_handler",
    "collection_checkpoint_handler",
    
    # Phase-specific handlers
    "platform_inventory_creation",
    "adapter_preparation",
    "collection_data_normalization",
    "gap_analysis_preparation",
    "gap_prioritization",
    "questionnaire_generation",
    "response_processing",
    "synthesis_preparation"
]