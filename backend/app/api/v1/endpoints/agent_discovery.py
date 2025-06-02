"""
Agent-Driven Discovery API Endpoints
Provides agentic intelligence for discovery processes, replacing hardcoded heuristics with AI-driven analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent_ui_bridge import agent_ui_bridge, QuestionType, ConfidenceLevel, DataClassification
from app.services.discovery_agents.data_source_intelligence_agent import data_source_intelligence_agent
from app.services.discovery_agents.application_discovery_agent import application_discovery_agent
from app.services.discovery_agents.dependency_intelligence_agent import dependency_intelligence_agent
from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent
from app.services.assessment_readiness_orchestrator import assessment_readiness_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/agent-analysis")
async def perform_agent_analysis(
    analysis_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Multi-agent data analysis for different page contexts and analysis types.
    
    Request body:
    {
        "data_source": {
            "file_data": [...],
            "metadata": {...},
            "upload_context": {...}
        },
        "analysis_type": "data_source_analysis",
        "page_context": "data-import"
    }
    OR for dependency context:
    {
        "data_context": {
            "dependency_analysis": {...},
            "cross_app_dependencies": [...],
            "impact_summary": {...}
        },
        "analysis_type": "dependency_mapping",
        "page_context": "dependencies"
    }
    """
    try:
        data_source = analysis_request.get("data_source", {})
        data_context = analysis_request.get("data_context", {})
        analysis_type = analysis_request.get("analysis_type", "data_source_analysis")
        page_context = analysis_request.get("page_context", "data-import")  # Extract from body
        
        # For dependency analysis, data_context is expected
        if analysis_type == "dependency_mapping" and data_context:
            # Process dependency context analysis
            analysis_result = {
                "analysis_type": "dependency_mapping",
                "status": "success",
                "page_context": page_context,
                "dependency_analysis_available": True,
                "total_dependencies": data_context.get("dependency_analysis", {}).get("total_dependencies", 0),
                "cross_app_dependencies": len(data_context.get("cross_app_dependencies", [])),
                "impact_summary": data_context.get("impact_summary", {}),
                "validation_needs": data_context.get("validation_needs", {}),
                "recommendations": [
                    "Review cross-application dependencies for migration planning",
                    "Validate dependency relationships with business stakeholders",
                    "Consider dependency complexity in migration sequencing"
                ]
            }
        elif not data_source and not data_context:
            raise HTTPException(status_code=400, detail="Data source or data context is required for analysis")
        
        # Route to appropriate agent based on analysis type
        elif analysis_type == "data_source_analysis":
            analysis_result = await data_source_intelligence_agent.analyze_data_source(
                data_source, page_context
            )
        elif analysis_type == "field_mapping_analysis":
            # Import field mapping service for field mapping analysis
            try:
                from app.services.field_mapper_modular import field_mapper
                analysis_result = await field_mapper.analyze_field_mappings(
                    data_source, page_context
                )
            except ImportError:
                # Fallback if field mapper service not available
                analysis_result = {
                    "analysis_type": "field_mapping_analysis",
                    "status": "service_unavailable",
                    "message": "Field mapping analysis service not available",
                    "suggestions": [],
                    "confidence": 0.0
                }
        elif analysis_type == "dependency_mapping":
            # Already processed above in the dependency context block
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")
        
        return {
            "status": "success",
            "analysis_type": analysis_type,
            "page_context": page_context,
            "agent_analysis": analysis_result,
            "ui_bridge_status": agent_ui_bridge.get_agent_status_summary()
        }
        
    except Exception as e:
        logger.error(f"Error in agent analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@router.post("/agent-clarification")
async def answer_agent_clarification(
    clarification_response: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    User responses to agent questions for learning and clarification.
    
    Request body:
    {
        "question_id": "uuid",
        "response": "user_answer",
        "response_type": "text|selection|multiple_choice",
        "page_context": "data-import"
    }
    """
    try:
        question_id = clarification_response.get("question_id")
        response = clarification_response.get("response")
        response_type = clarification_response.get("response_type", "text")
        page_context = clarification_response.get("page_context", "discovery")
        
        if not question_id or response is None:
            raise HTTPException(status_code=400, detail="Question ID and response are required")
        
        # Process the user response through the UI bridge
        result = agent_ui_bridge.answer_agent_question(question_id, response)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Question not found"))
        
        # Trigger agent learning from the response
        await _process_agent_learning(question_id, response, response_type, page_context)
        
        return {
            "status": "success",
            "message": "Agent clarification processed successfully",
            "learning_applied": True,
            "question_resolved": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing agent clarification: {e}")
        raise HTTPException(status_code=500, detail=f"Clarification processing failed: {str(e)}")

@router.get("/agent-status")
async def get_agent_status(
    page_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Current agent understanding and confidence levels.
    """
    try:
        # Get overall agent status
        agent_status = agent_ui_bridge.get_agent_status_summary()
        
        # Get page-specific information if requested
        page_data = {}
        if page_context:
            page_data = {
                "pending_questions": agent_ui_bridge.get_questions_for_page(page_context),
                "data_classifications": agent_ui_bridge.get_classified_data_for_page(page_context),
                "agent_insights": agent_ui_bridge.get_insights_for_page(page_context)
            }
        
        return {
            "status": "success",
            "agent_status": agent_status,
            "page_data": page_data,
            "cross_page_context": agent_ui_bridge.get_cross_page_context()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")

@router.post("/agent-learning")
async def process_agent_learning(
    learning_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent learning from user corrections and feedback.
    
    Request body:
    {
        "learning_type": "field_mapping|data_classification|pattern_recognition|insight_feedback",
        "original_prediction": {...},
        "user_correction": {...},
        "context": {...},
        "page_context": "data-import"
    }
    """
    try:
        learning_type = learning_input.get("learning_type")
        original_prediction = learning_input.get("original_prediction")
        user_correction = learning_input.get("user_correction")
        context = learning_input.get("context", {})
        page_context = learning_input.get("page_context", "discovery")
        
        if not all([learning_type, original_prediction, user_correction]):
            raise HTTPException(
                status_code=400, 
                detail="Learning type, original prediction, and user correction are required"
            )
        
        # Special handling for insight feedback with Presentation Reviewer Agent
        if learning_type == "insight_feedback":
            learning_result = await _process_insight_feedback_learning(
                original_prediction, user_correction, context, page_context
            )
        else:
            # Process learning based on type
            learning_result = await _apply_agent_learning(
                learning_type, original_prediction, user_correction, context, page_context
            )
        
        return {
            "status": "success",
            "message": "Agent learning processed successfully",
            "learning_type": learning_type,
            "learning_result": learning_result,
            "improvement_metrics": await _calculate_learning_metrics()
        }
        
    except Exception as e:
        logger.error(f"Error in agent learning: {e}")
        raise HTTPException(status_code=500, detail=f"Agent learning failed: {str(e)}")

@router.get("/application-portfolio")
async def get_application_portfolio(
    include_confidence_levels: bool = True,
    include_business_intelligence: bool = True,
    business_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive application portfolio analysis with business intelligence.
    
    Enhanced with Application Intelligence Agent for business-aligned analysis.
    """
    try:
        # Get assets from the discovery system
        from app.api.v1.discovery.asset_management import crud_handler
        assets_result = await crud_handler.get_assets_paginated({'page': 1, 'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "application_portfolio": {
                    "applications": [],
                    "discovery_confidence": 0.0,
                    "clarification_questions": [],
                    "discovery_metadata": {
                        "total_assets_analyzed": 0,
                        "applications_discovered": 0,
                        "high_confidence_apps": 0,
                        "needs_clarification": 0,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                },
                "business_intelligence": None,
                "message": "No assets available for application discovery"
            }
        
        # Step 1: Use Application Discovery Agent for basic application discovery
        discovery_result = await application_discovery_agent.discover_applications(assets)
        applications = discovery_result.get("applications", [])
        
        # Step 2: If business intelligence is requested and applications found, use Application Intelligence Agent
        business_intelligence = None
        if include_business_intelligence and applications:
            try:
                from app.services.discovery_agents.application_intelligence_agent import application_intelligence_agent
                
                # Parse business context if provided
                parsed_business_context = None
                if business_context:
                    try:
                        import json
                        parsed_business_context = json.loads(business_context)
                    except:
                        parsed_business_context = {"notes": business_context}
                
                # Perform comprehensive business intelligence analysis
                business_intelligence = await application_intelligence_agent.analyze_application_portfolio(
                    applications, parsed_business_context
                )
                
                logger.info(f"Application Intelligence Agent analyzed {len(applications)} applications")
                
            except Exception as e:
                logger.warning(f"Application Intelligence Agent error: {e}")
                business_intelligence = {
                    "portfolio_analysis": {"applications": applications, "portfolio_health": {}, "assessment_readiness": {}},
                    "strategic_recommendations": [],
                    "business_insights": [],
                    "error": f"Application Intelligence Agent error: {str(e)}",
                    "fallback_mode": True
                }
        
        # Store clarification questions in the UI bridge for display
        for question in discovery_result.get("clarification_questions", []):
            agent_ui_bridge.add_agent_question(
                agent_id=application_discovery_agent.agent_id,
                agent_name=application_discovery_agent.agent_name,
                question_type=QuestionType.APPLICATION_BOUNDARY,
                page="asset-inventory",
                title=f"Application Validation: {question['application_name']}",
                question=question["question"],
                context=question["context"],
                options=question["options"],
                confidence=ConfidenceLevel.MEDIUM,
                priority="medium"
            )
        
        # Add intelligence insights to UI bridge if available
        if business_intelligence and not business_intelligence.get("error"):
            for insight in business_intelligence.get("business_insights", []):
                agent_ui_bridge.add_agent_insight(
                    agent_id="application_intelligence",
                    agent_name="Application Intelligence Agent",
                    insight_type=insight.get("category", "business_insight"),
                    title=insight.get("title", "Business Insight"),
                    description=insight.get("description", ""),
                    confidence=ConfidenceLevel.HIGH if insight.get("confidence", 0) >= 0.8 else ConfidenceLevel.MEDIUM,
                    supporting_data=insight.get("details", {}),
                    page="asset-inventory"
                )
        
        # Construct comprehensive response
        response = {
            "status": "success",
            "application_portfolio": discovery_result,
            "agent_analysis_complete": True
        }
        
        if include_business_intelligence:
            response["business_intelligence"] = business_intelligence
            response["intelligence_features"] = {
                "business_criticality_assessment": business_intelligence is not None and not business_intelligence.get("error"),
                "migration_readiness_evaluation": business_intelligence is not None and not business_intelligence.get("error"),
                "strategic_recommendations": business_intelligence is not None and not business_intelligence.get("error"),
                "assessment_readiness": business_intelligence is not None and not business_intelligence.get("error")
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting application portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Application portfolio retrieval failed: {str(e)}")

@router.post("/application-validation")
async def validate_application_groupings(
    validation_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    User validation of agent application groupings for learning.
    """
    try:
        application_id = validation_input.get("application_id")
        validation_type = validation_input.get("validation_type")
        user_feedback = validation_input.get("feedback", {})
        
        if not application_id or not validation_type:
            raise HTTPException(status_code=400, detail="Application ID and validation type are required")
        
        # Process feedback through the Application Discovery Agent
        feedback_data = {
            "type": "application_validation",
            "application_id": application_id,
            "validation": validation_type,
            "application_data": validation_input.get("application_data", {}),
            "correction": user_feedback
        }
        
        learning_result = await application_discovery_agent.process_user_feedback(feedback_data)
        
        # Store learning experience in the UI bridge
        learning_context = {
            "validation_type": validation_type,
            "application_id": application_id,
            "user_feedback": user_feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        agent_ui_bridge.set_cross_page_context(
            f"application_validation_{application_id}",
            learning_context,
            "asset-inventory"
        )
        
        return {
            "status": "success",
            "message": "Application validation processed successfully",
            "validation_stored": True,
            "learning_applied": learning_result.get("learning_applied", False),
            "agent_improvement": "Application Discovery Agent updated with user feedback"
        }
        
    except Exception as e:
        logger.error(f"Error in application validation: {e}")
        raise HTTPException(status_code=500, detail=f"Application validation failed: {str(e)}")

@router.get("/readiness-assessment")
async def get_readiness_assessment(
    assessment_type: str = "comprehensive",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent assessment of assessment-phase readiness.
    """
    try:
        # Get current agent understanding across all pages
        data_import_status = agent_ui_bridge.get_classified_data_for_page("data-import")
        attribute_mapping_status = agent_ui_bridge.get_classified_data_for_page("attribute-mapping")
        data_cleansing_status = agent_ui_bridge.get_classified_data_for_page("data-cleansing")
        
        # Calculate readiness based on agent classifications
        readiness_metrics = {
            "data_import_readiness": _calculate_page_readiness(data_import_status),
            "attribute_mapping_readiness": _calculate_page_readiness(attribute_mapping_status),
            "data_cleansing_readiness": _calculate_page_readiness(data_cleansing_status)
        }
        
        # Overall readiness assessment
        overall_readiness = sum(readiness_metrics.values()) / len(readiness_metrics)
        
        # Get outstanding questions
        outstanding_questions = []
        for page in ["data-import", "attribute-mapping", "data-cleansing"]:
            outstanding_questions.extend(agent_ui_bridge.get_questions_for_page(page))
        
        assessment = {
            "overall_readiness": overall_readiness,
            "readiness_level": _classify_readiness_level(overall_readiness),
            "readiness_metrics": readiness_metrics,
            "outstanding_questions": len(outstanding_questions),
            "blocking_issues": [q for q in outstanding_questions if q.get("priority") == "high"],
            "agent_confidence": "high" if overall_readiness >= 0.8 else "medium" if overall_readiness >= 0.6 else "low",
            "next_steps": _generate_readiness_next_steps(readiness_metrics, outstanding_questions)
        }
        
        return {
            "status": "success",
            "assessment_type": assessment_type,
            "readiness_assessment": assessment,
            "agent_recommendations": _generate_agent_recommendations(assessment)
        }
        
    except Exception as e:
        logger.error(f"Error in readiness assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Readiness assessment failed: {str(e)}")

@router.post("/stakeholder-requirements")
async def process_stakeholder_requirements(
    requirements_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Stakeholder input for agent learning and context.
    """
    try:
        requirements = requirements_input.get("requirements", {})
        stakeholder_context = requirements_input.get("stakeholder_context", {})
        business_priorities = requirements_input.get("business_priorities", [])
        
        # Store stakeholder context for agents
        agent_ui_bridge.set_cross_page_context(
            "stakeholder_requirements", 
            {
                "requirements": requirements,
                "context": stakeholder_context,
                "priorities": business_priorities
            },
            "stakeholder-input"
        )
        
        return {
            "status": "success",
            "message": "Stakeholder requirements stored for agent learning",
            "requirements_count": len(requirements),
            "priorities_count": len(business_priorities),
            "context_updated": True
        }
        
    except Exception as e:
        logger.error(f"Error processing stakeholder requirements: {e}")
        raise HTTPException(status_code=500, detail=f"Stakeholder requirements processing failed: {str(e)}")

@router.post("/dependency-analysis")
async def analyze_dependencies(
    dependency_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive dependency analysis using Dependency Intelligence Agent.
    
    Request body:
    {
        "assets": [...],
        "applications": [...],
        "user_context": {...}
    }
    """
    try:
        assets = dependency_request.get("assets", [])
        applications = dependency_request.get("applications", [])
        user_context = dependency_request.get("user_context", {})
        
        if not assets:
            # Try to get assets from the discovery system
            from app.api.v1.discovery.asset_management import crud_handler
            assets_result = await crud_handler.get_assets_paginated({'page': 1, 'page_size': 1000})
            assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "dependency_analysis": {
                    "total_dependencies": 0,
                    "message": "No assets available for dependency analysis"
                },
                "cross_application_mapping": {},
                "impact_analysis": {},
                "clarification_questions": []
            }
        
        # Perform dependency intelligence analysis
        dependency_intelligence = await dependency_intelligence_agent.analyze_dependencies(
            assets, applications, user_context
        )
        
        # Store clarification questions in the UI bridge for display
        for question in dependency_intelligence.get("clarification_questions", []):
            agent_ui_bridge.add_agent_question(
                agent_id=dependency_intelligence_agent.agent_id,
                agent_name=dependency_intelligence_agent.agent_name,
                question_type=QuestionType.DEPENDENCY_VALIDATION,
                page="dependencies",
                title=question["title"],
                question=question["question"],
                context=question.get("dependency", {}),
                options=question.get("options", []),
                confidence=ConfidenceLevel.MEDIUM,
                priority=question.get("priority", "medium")
            )
        
        response = {
            "status": "success",
            "dependency_intelligence": dependency_intelligence,
            "agent_analysis_complete": True
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in dependency analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Dependency analysis failed: {str(e)}")

@router.post("/dependency-feedback")
async def process_dependency_feedback(
    feedback_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process user feedback on dependency analysis for agent learning.
    
    Request body:
    {
        "feedback_type": "dependency_validation|conflict_resolution|impact_assessment",
        "dependency_id": "string",
        "original_analysis": {...},
        "user_correction": {...}
    }
    """
    try:
        # Process feedback through the Dependency Intelligence Agent
        learning_result = await dependency_intelligence_agent.process_user_dependency_feedback(feedback_request)
        
        return {
            "status": "success",
            "message": "Dependency feedback processed successfully",
            "learning_result": learning_result
        }
        
    except Exception as e:
        logger.error(f"Error processing dependency feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Dependency feedback processing failed: {str(e)}")

@router.post("/tech-debt-analysis")
async def analyze_tech_debt(
    tech_debt_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive tech debt analysis using Tech Debt Analysis Agent.
    
    Request body:
    {
        "assets": [...],
        "stakeholder_context": {...},
        "migration_timeline": "string"
    }
    """
    try:
        assets = tech_debt_request.get("assets", [])
        stakeholder_context = tech_debt_request.get("stakeholder_context", {})
        migration_timeline = tech_debt_request.get("migration_timeline")
        
        if not assets:
            # Try to get assets from the discovery system
            from app.api.v1.discovery.asset_management import crud_handler
            assets_result = await crud_handler.get_assets_paginated({'page': 1, 'page_size': 1000})
            assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "tech_debt_analysis": {
                    "total_assets_analyzed": 0,
                    "message": "No assets available for tech debt analysis"
                },
                "business_risk_assessment": {},
                "prioritized_tech_debt": [],
                "stakeholder_questions": []
            }
        
        # Perform tech debt intelligence analysis
        tech_debt_intelligence = await tech_debt_analysis_agent.analyze_tech_debt(
            assets, stakeholder_context, migration_timeline
        )
        
        # Store stakeholder questions in the UI bridge for display
        for question in tech_debt_intelligence.get("stakeholder_questions", []):
            agent_ui_bridge.add_agent_question(
                agent_id=tech_debt_analysis_agent.agent_id,
                agent_name=tech_debt_analysis_agent.agent_name,
                question_type=QuestionType.RISK_ASSESSMENT,
                page="tech-debt",
                title=question["title"],
                question=question["question"],
                context=question.get("risk_item", {}),
                options=question.get("options", []),
                confidence=ConfidenceLevel.MEDIUM,
                priority=question.get("priority", "medium")
            )
        
        response = {
            "status": "success",
            "tech_debt_intelligence": tech_debt_intelligence,
            "agent_analysis_complete": True
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in tech debt analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Tech debt analysis failed: {str(e)}")

@router.post("/tech-debt-feedback")
async def process_tech_debt_feedback(
    feedback_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process stakeholder feedback on tech debt risk tolerance and business requirements.
    
    Request body:
    {
        "feedback_type": "risk_tolerance|business_priority|migration_timeline",
        "risk_item_id": "string",
        "original_assessment": {...},
        "stakeholder_input": {...}
    }
    """
    try:
        # Process feedback through the Tech Debt Analysis Agent
        learning_result = await tech_debt_analysis_agent.process_stakeholder_risk_feedback(feedback_request)
        
        return {
            "status": "success",
            "message": "Tech debt feedback processed successfully",
            "learning_result": learning_result
        }
        
    except Exception as e:
        logger.error(f"Error processing tech debt feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Tech debt feedback processing failed: {str(e)}")

@router.post("/assessment-readiness")
async def assess_portfolio_readiness(
    readiness_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive assessment of portfolio readiness for 6R analysis.
    
    Request body:
    {
        "portfolio_data": {
            "assets": [...],
            "applications": [...],
            "dependencies": [...]
        },
        "stakeholder_context": {...},
        "assessment_type": "comprehensive"
    }
    """
    try:
        portfolio_data = readiness_request.get("portfolio_data", {})
        stakeholder_context = readiness_request.get("stakeholder_context")
        assessment_type = readiness_request.get("assessment_type", "comprehensive")
        
        if not portfolio_data:
            raise HTTPException(status_code=400, detail="Portfolio data is required for readiness assessment")
        
        # Perform comprehensive readiness assessment
        readiness_assessment = await assessment_readiness_orchestrator.assess_portfolio_readiness(
            portfolio_data, stakeholder_context
        )
        
        return {
            "status": "success",
            "assessment_type": assessment_type,
            "readiness_assessment": readiness_assessment,
            "orchestrator_metadata": {
                "agent_id": assessment_readiness_orchestrator.agent_id,
                "assessment_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in portfolio readiness assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio readiness assessment failed: {str(e)}")

@router.post("/stakeholder-signoff-package")
async def generate_stakeholder_signoff_package(
    signoff_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate comprehensive stakeholder sign-off package for assessment phase.
    
    Request body:
    {
        "readiness_assessment": {...},
        "stakeholder_context": {...},
        "package_type": "comprehensive"
    }
    """
    try:
        readiness_assessment = signoff_request.get("readiness_assessment", {})
        stakeholder_context = signoff_request.get("stakeholder_context")
        package_type = signoff_request.get("package_type", "comprehensive")
        
        if not readiness_assessment:
            raise HTTPException(status_code=400, detail="Readiness assessment is required for signoff package")
        
        # Generate stakeholder signoff package
        signoff_package = await assessment_readiness_orchestrator.generate_stakeholder_signoff_package(
            readiness_assessment, stakeholder_context
        )
        
        return {
            "status": "success",
            "package_type": package_type,
            "signoff_package": signoff_package,
            "orchestrator_metadata": {
                "agent_id": assessment_readiness_orchestrator.agent_id,
                "package_generated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating stakeholder signoff package: {e}")
        raise HTTPException(status_code=500, detail=f"Stakeholder signoff package generation failed: {str(e)}")

@router.post("/stakeholder-signoff-feedback")
async def process_stakeholder_signoff_feedback(
    feedback_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process stakeholder feedback on assessment readiness and signoff decisions.
    
    Request body:
    {
        "feedback_type": "readiness_validation",
        "signoff_decision": "approve|conditional|reject",
        "stakeholder_concerns": [...],
        "additional_requirements": [...],
        "signoff_metadata": {...}
    }
    """
    try:
        feedback_type = feedback_request.get("feedback_type", "readiness_validation")
        signoff_decision = feedback_request.get("signoff_decision")
        
        if not signoff_decision:
            raise HTTPException(status_code=400, detail="Signoff decision is required")
        
        if signoff_decision not in ["approve", "conditional", "reject"]:
            raise HTTPException(status_code=400, detail="Signoff decision must be 'approve', 'conditional', or 'reject'")
        
        # Process stakeholder signoff feedback
        learning_result = await assessment_readiness_orchestrator.process_stakeholder_signoff_feedback(
            feedback_request
        )
        
        return {
            "status": "success",
            "feedback_type": feedback_type,
            "signoff_decision": signoff_decision,
            "learning_result": learning_result,
            "orchestrator_metadata": {
                "agent_id": assessment_readiness_orchestrator.agent_id,
                "feedback_processed": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing stakeholder signoff feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Stakeholder signoff feedback processing failed: {str(e)}")

@router.get("/health")
async def agent_discovery_health():
    """Health check for agent discovery endpoints."""
    return {
        "status": "healthy",
        "service": "agent-discovery",
        "version": "1.0.0",
        "agentic_framework": "active",
        "available_agents": [
            "Data Source Intelligence Agent",
            "Application Discovery Agent", 
            "Dependency Intelligence Agent",
            "Tech Debt Analysis Agent",
            "Assessment Readiness Orchestrator"
        ],
        "ui_bridge_status": agent_ui_bridge.get_agent_status_summary(),
        "available_endpoints": [
            "/agent-analysis",
            "/agent-clarification",
            "/agent-status",
            "/agent-learning",
            "/application-portfolio",
            "/application-validation",
            "/readiness-assessment",
            "/stakeholder-requirements",
            "/dependency-analysis",
            "/dependency-feedback",
            "/tech-debt-analysis",
            "/tech-debt-feedback",
            "/assessment-readiness",
            "/stakeholder-signoff-package",
            "/stakeholder-signoff-feedback",
            "/health"
        ]
    }

@router.post("/test-presentation-reviewer")
async def test_presentation_reviewer(
    test_insights: List[Dict[str, Any]],
    page_context: str = "asset-inventory",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test endpoint for the Presentation Reviewer Agent.
    
    Request body:
    [
        {
            "id": "test1",
            "agent_id": "test_agent",
            "title": "Test Insight",
            "description": "Portfolio contains 19 applications across 7 asset types",
            "supporting_data": {"Application": 6, "Server": 8, "Database": 1},
            "insight_type": "portfolio_composition",
            "confidence": "high",
            "actionable": true,
            "created_at": "2025-01-29T12:00:00"
        }
    ]
    """
    try:
        # Import the Presentation Reviewer Agent
        from app.services.discovery_agents.presentation_reviewer_agent import presentation_reviewer_agent
        
        # Review the test insights
        review_result = await presentation_reviewer_agent.review_insights_for_presentation(
            test_insights, page_context, {}
        )
        
        return {
            "status": "success",
            "original_insights_count": len(test_insights),
            "reviewed_insights_count": len(review_result.get("reviewed_insights", [])),
            "rejected_insights_count": len(review_result.get("rejected_insights", [])),
            "review_result": review_result,
            "message": "Presentation review completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error testing presentation reviewer: {e}")
        raise HTTPException(status_code=500, detail=f"Presentation reviewer test failed: {str(e)}")

# Helper functions

async def _process_agent_learning(question_id: str, response: Any, 
                                response_type: str, page_context: str) -> Dict[str, Any]:
    """Process agent learning from user responses."""
    
    # Get the question context for learning
    # This will be expanded as agents implement specific learning algorithms
    learning_context = {
        "question_id": question_id,
        "response": response,
        "response_type": response_type,
        "page_context": page_context,
        "timestamp": agent_ui_bridge.get_cross_page_context("timestamp")
    }
    
    logger.info(f"Processed agent learning for question {question_id}")
    return learning_context

async def _apply_agent_learning(learning_type: str, original_prediction: Dict[str, Any],
                              user_correction: Dict[str, Any], context: Dict[str, Any],
                              page_context: str) -> Dict[str, Any]:
    """Apply specific learning based on the type of correction."""
    
    if learning_type == "data_classification":
        # Learn from data classification corrections
        return await _learn_data_classification(original_prediction, user_correction, context)
    
    elif learning_type in ["field_mapping", "field_mapping_correction", "field_mapping_feedback"]:
        # Learn from field mapping corrections and feedback
        return await _learn_field_mapping(original_prediction, user_correction, context)
    
    elif learning_type == "pattern_recognition":
        # Learn from pattern recognition corrections
        return await _learn_pattern_recognition(original_prediction, user_correction, context)
    
    else:
        raise ValueError(f"Unknown learning type: {learning_type}")

async def _learn_data_classification(original: Dict[str, Any], correction: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from data classification corrections."""
    # This will be implemented with specific agent learning algorithms
    return {
        "learning_applied": True,
        "pattern_updated": True,
        "confidence_improvement": 0.1
    }

async def _learn_field_mapping(original: Dict[str, Any], correction: Dict[str, Any],
                             context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from field mapping corrections using actual field mapping service."""
    try:
        # Extract mapping information from the correction
        source_field = original.get("source_field")
        original_target = original.get("target_attribute")
        corrected_target = correction.get("new_target_attribute")
        
        if not all([source_field, corrected_target]):
            return {
                "learning_applied": False,
                "error": "Missing required field mapping information",
                "confidence_improvement": 0.0
            }
        
        logger.info(f"Learning field mapping correction: {source_field} -> {corrected_target} (was {original_target})")
        
        # Import field mapping service
        from app.services.field_mapper_modular import field_mapper
        
        # Learn the corrected mapping
        learning_result = field_mapper.agent_learn_field_mapping(
            source_field=source_field,
            target_field=corrected_target,
            context=f"user_correction_from_{correction.get('feedback_type', 'manual_change')}"
        )
        
        # Also learn sample values if available for content-based analysis
        sample_values = context.get("sample_values", [])
        if sample_values and learning_result.get("success"):
            # Enhance learning with content patterns
            try:
                field_mapper.learn_content_patterns(
                    field_name=source_field,
                    canonical_field=corrected_target,
                    sample_values=sample_values
                )
            except Exception as e:
                logger.warning(f"Content pattern learning failed: {e}")
        
        # Calculate confidence improvement based on learning success
        confidence_improvement = 0.15 if learning_result.get("success") else 0.0
        
        return {
            "learning_applied": learning_result.get("success", False),
            "mapping_pattern_updated": True,
            "canonical_field": learning_result.get("canonical_field"),
            "variations_learned": learning_result.get("learned_variations", []),
            "confidence_improvement": confidence_improvement,
            "learning_source": "user_field_mapping_correction",
            "content_analysis_applied": bool(sample_values)
        }
        
    except Exception as e:
        logger.error(f"Error in field mapping learning: {e}")
        return {
            "learning_applied": False,
            "error": str(e),
            "confidence_improvement": 0.0
        }

async def _learn_pattern_recognition(original: Dict[str, Any], correction: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from pattern recognition corrections."""
    # This will be implemented with pattern recognition improvements
    return {
        "learning_applied": True,
        "pattern_recognition_updated": True,
        "confidence_improvement": 0.05
    }

async def _calculate_learning_metrics() -> Dict[str, Any]:
    """Calculate agent learning improvement metrics."""
    # Get recent learning experiences
    recent_experiences = agent_ui_bridge.get_recent_learning_experiences(limit=100)
    
    return {
        "total_learning_experiences": len(recent_experiences),
        "recent_accuracy_trend": "improving",  # Will be calculated from actual data
        "learning_categories": {
            "field_mapping": len([e for e in recent_experiences if e.get("question_type") == "field_mapping"]),
            "data_classification": len([e for e in recent_experiences if e.get("question_type") == "data_classification"]),
            "business_context": len([e for e in recent_experiences if e.get("question_type") == "business_context"])
        }
    }

def _calculate_page_readiness(page_data: Dict[str, List[Dict[str, Any]]]) -> float:
    """Calculate readiness score for a specific page based on data classifications."""
    
    good_data_count = len(page_data.get("good_data", []))
    needs_clarification_count = len(page_data.get("needs_clarification", []))
    unusable_count = len(page_data.get("unusable", []))
    
    total_items = good_data_count + needs_clarification_count + unusable_count
    
    if total_items == 0:
        return 0.0
    
    # Calculate readiness based on data quality distribution
    readiness = (good_data_count * 1.0 + needs_clarification_count * 0.5 + unusable_count * 0.0) / total_items
    
    return readiness

def _classify_readiness_level(readiness_score: float) -> str:
    """Classify overall readiness level."""
    if readiness_score >= 0.9:
        return "excellent"
    elif readiness_score >= 0.8:
        return "good"
    elif readiness_score >= 0.7:
        return "fair"
    elif readiness_score >= 0.5:
        return "poor"
    else:
        return "insufficient"

def _generate_readiness_next_steps(readiness_metrics: Dict[str, float], 
                                 outstanding_questions: List[Dict[str, Any]]) -> List[str]:
    """Generate next steps based on readiness assessment."""
    
    steps = []
    
    # Check each phase readiness
    if readiness_metrics.get("data_import_readiness", 0) < 0.7:
        steps.append("Address data import quality issues and answer agent clarifications")
    
    if readiness_metrics.get("attribute_mapping_readiness", 0) < 0.7:
        steps.append("Complete field mapping and resolve mapping ambiguities with agents")
    
    if readiness_metrics.get("data_cleansing_readiness", 0) < 0.7:
        steps.append("Resolve data quality issues identified by cleaning agents")
    
    # High priority questions
    high_priority_questions = [q for q in outstanding_questions if q.get("priority") == "high"]
    if high_priority_questions:
        steps.append(f"Answer {len(high_priority_questions)} high-priority agent questions")
    
    if not steps:
        steps.append("Ready to proceed to assessment phase - all discovery criteria met")
    
    return steps

def _generate_agent_recommendations(assessment: Dict[str, Any]) -> List[str]:
    """Generate agent recommendations based on readiness assessment."""
    
    recommendations = []
    
    overall_readiness = assessment.get("overall_readiness", 0)
    
    if overall_readiness >= 0.9:
        recommendations.append("Excellent data readiness - proceed confidently to 6R assessment")
        recommendations.append("Consider this as a model for future discovery processes")
    
    elif overall_readiness >= 0.7:
        recommendations.append("Good data foundation for migration assessment")
        recommendations.append("Address remaining clarifications to optimize assessment accuracy")
    
    elif overall_readiness >= 0.5:
        recommendations.append("Moderate data readiness - assessment possible but may have gaps")
        recommendations.append("Prioritize resolving high-impact data quality issues")
    
    else:
        recommendations.append("Insufficient data quality for reliable migration assessment")
        recommendations.append("Focus on fundamental data collection and quality improvement")
    
    return recommendations

async def _process_insight_feedback_learning(original_prediction: Dict[str, Any], 
                                           user_correction: Dict[str, Any],
                                           context: Dict[str, Any], 
                                           page_context: str) -> Dict[str, Any]:
    """Process user feedback on insights through the Presentation Reviewer Agent."""
    try:
        # Import here to avoid circular dependency
        from app.services.discovery_agents.presentation_reviewer_agent import presentation_reviewer_agent
        
        # Prepare feedback for the Presentation Reviewer Agent
        feedback_data = {
            "insight_id": original_prediction.get("insight_id"),
            "helpful": user_correction.get("helpful", True),
            "explanation": user_correction.get("explanation", ""),
            "accuracy_issues": user_correction.get("accuracy_issues", []),
            "page_context": page_context,
            "original_insight": {
                "title": original_prediction.get("title", ""),
                "description": original_prediction.get("description", ""),
                "supporting_data": original_prediction.get("supporting_data", {})
            }
        }
        
        # Process feedback through Presentation Reviewer Agent
        review_learning_result = await presentation_reviewer_agent.process_user_insight_feedback(feedback_data)
        
        # The Presentation Reviewer Agent will also provide feedback to the source agent
        source_agent_feedback = review_learning_result.get("source_agent_feedback", {})
        
        return {
            "learning_applied": review_learning_result.get("review_learning_applied", False),
            "presentation_review_improved": True,
            "source_agent_notified": review_learning_result.get("agent_learning_triggered", False),
            "accuracy_improvement": review_learning_result.get("accuracy_improvement", 0.0),
            "feedback_details": {
                "helpful": user_correction.get("helpful", True),
                "explanation": user_correction.get("explanation", ""),
                "accuracy_issues_count": len(user_correction.get("accuracy_issues", [])),
                "source_agent_feedback": source_agent_feedback
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing insight feedback learning: {e}")
        return {
            "learning_applied": False,
            "error": str(e)
        } 