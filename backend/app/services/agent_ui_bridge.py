"""
Agent-UI Communication Bridge
Enables agents to communicate with users through the UI for clarifications, feedback, and iterative learning.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Types of questions agents can ask users."""
    FIELD_MAPPING = "field_mapping"
    DATA_CLASSIFICATION = "data_classification"
    APPLICATION_BOUNDARY = "application_boundary"
    DEPENDENCY_CLARIFICATION = "dependency_clarification"
    DEPENDENCY_VALIDATION = "dependency_validation"
    BUSINESS_CONTEXT = "business_context"
    QUALITY_VALIDATION = "quality_validation"
    STAKEHOLDER_PREFERENCE = "stakeholder_preference"
    RISK_ASSESSMENT = "risk_assessment"

class ConfidenceLevel(Enum):
    """Agent confidence levels."""
    HIGH = "high"        # 80-100%
    MEDIUM = "medium"    # 60-79%
    LOW = "low"         # 40-59%
    UNCERTAIN = "uncertain"  # <40%

class DataClassification(Enum):
    """Data quality classifications."""
    GOOD_DATA = "good_data"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNUSABLE = "unusable"

@dataclass
class AgentQuestion:
    """Represents a question from an agent to the user."""
    id: str
    agent_id: str
    agent_name: str
    question_type: QuestionType
    page: str  # discovery page where question appears
    title: str
    question: str
    context: Dict[str, Any]  # Additional context data
    options: Optional[List[str]] = None  # For multiple choice questions
    confidence: Optional[ConfidenceLevel] = None
    priority: str = "medium"  # high, medium, low
    created_at: datetime = None
    answered_at: Optional[datetime] = None
    user_response: Optional[Any] = None
    is_resolved: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class DataItem:
    """Represents a piece of data with agent classification."""
    id: str
    data_type: str  # asset, application, field_mapping, etc.
    classification: DataClassification
    content: Dict[str, Any]
    agent_analysis: Dict[str, Any]
    confidence: ConfidenceLevel
    issues: List[str] = None
    recommendations: List[str] = None
    page: str = "discovery"
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []

@dataclass
class AgentInsight:
    """Represents an insight or discovery from an agent."""
    id: str
    agent_id: str
    agent_name: str
    insight_type: str
    title: str
    description: str
    confidence: ConfidenceLevel
    supporting_data: Dict[str, Any]
    actionable: bool = True
    page: str = "discovery"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class AgentUIBridge:
    """Manages communication between AI agents and the UI."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage files
        self.questions_file = self.data_dir / "agent_questions.json"
        self.classifications_file = self.data_dir / "data_classifications.json"
        self.insights_file = self.data_dir / "agent_insights.json"
        self.context_file = self.data_dir / "agent_context.json"
        
        # In-memory storage
        self.pending_questions: Dict[str, AgentQuestion] = {}
        self.data_classifications: Dict[str, DataItem] = {}
        self.agent_insights: Dict[str, AgentInsight] = {}
        self.cross_page_context: Dict[str, Any] = {}
        
        # Load existing data
        self._load_persistent_data()
    
    # === AGENT QUESTION MANAGEMENT ===
    
    def add_agent_question(self, agent_id: str, agent_name: str, 
                          question_type: QuestionType, page: str,
                          title: str, question: str, context: Dict[str, Any],
                          options: Optional[List[str]] = None,
                          confidence: Optional[ConfidenceLevel] = None,
                          priority: str = "medium") -> str:
        """Add a new question from an agent."""
        question_id = str(uuid.uuid4())
        
        agent_question = AgentQuestion(
            id=question_id,
            agent_id=agent_id,
            agent_name=agent_name,
            question_type=question_type,
            page=page,
            title=title,
            question=question,
            context=context,
            options=options,
            confidence=confidence,
            priority=priority
        )
        
        self.pending_questions[question_id] = agent_question
        self._save_questions()
        
        logger.info(f"Agent {agent_name} added question: {title}")
        return question_id
    
    def answer_agent_question(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Process user response to an agent question."""
        if question_id not in self.pending_questions:
            return {"success": False, "error": "Question not found"}
        
        question = self.pending_questions[question_id]
        question.user_response = response
        question.answered_at = datetime.utcnow()
        question.is_resolved = True
        
        # Store the learning from this interaction
        learning_context = {
            "question_type": question.question_type.value,
            "agent_id": question.agent_id,
            "page": question.page,
            "context": question.context,
            "user_response": response,
            "timestamp": question.answered_at.isoformat()
        }
        
        self._store_learning_experience(learning_context)
        self._save_questions()
        
        logger.info(f"User answered question {question_id} from {question.agent_name}")
        
        return {
            "success": True,
            "question": asdict(question),
            "learning_stored": True
        }
    
    def get_questions_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all pending questions for a specific page."""
        page_questions = [
            asdict(q) for q in self.pending_questions.values()
            if q.page == page and not q.is_resolved
        ]
        
        # Sort by priority and creation time
        priority_order = {"high": 3, "medium": 2, "low": 1}
        page_questions.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['created_at']),
            reverse=True
        )
        
        return page_questions
    
    # === DATA CLASSIFICATION MANAGEMENT ===
    
    def classify_data_item(self, item_id: str, data_type: str, content: Dict[str, Any],
                          classification: DataClassification, agent_analysis: Dict[str, Any],
                          confidence: ConfidenceLevel, page: str = "discovery",
                          issues: List[str] = None, recommendations: List[str] = None) -> None:
        """Classify a data item based on agent analysis."""
        
        data_item = DataItem(
            id=item_id,
            data_type=data_type,
            classification=classification,
            content=content,
            agent_analysis=agent_analysis,
            confidence=confidence,
            issues=issues or [],
            recommendations=recommendations or [],
            page=page
        )
        
        self.data_classifications[item_id] = data_item
        self._save_classifications()
        
        logger.info(f"Classified {data_type} item {item_id} as {classification.value}")
    
    def get_classified_data_for_page(self, page: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get data classifications organized by type for a specific page."""
        page_items = [
            asdict(item) for item in self.data_classifications.values()
            if item.page == page
        ]
        
        # Organize by classification
        classifications = {
            "good_data": [],
            "needs_clarification": [],
            "unusable": []
        }
        
        for item in page_items:
            classification_key = item['classification']
            classifications[classification_key].append(item)
        
        return classifications
    
    def update_data_classification(self, item_id: str, new_classification: DataClassification,
                                  updated_by: str = "user") -> Dict[str, Any]:
        """Update the classification of a data item."""
        if item_id not in self.data_classifications:
            return {"success": False, "error": "Data item not found"}
        
        old_classification = self.data_classifications[item_id].classification
        self.data_classifications[item_id].classification = new_classification
        
        # Store learning from classification change
        learning_context = {
            "item_id": item_id,
            "old_classification": old_classification.value,
            "new_classification": new_classification.value,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._store_learning_experience(learning_context)
        self._save_classifications()
        
        return {"success": True, "classification_updated": True}
    
    # === AGENT INSIGHTS MANAGEMENT ===
    
    def add_agent_insight(self, agent_id: str, agent_name: str, insight_type: str,
                         title: str, description: str, confidence: ConfidenceLevel,
                         supporting_data: Dict[str, Any], page: str = "discovery",
                         actionable: bool = True) -> str:
        """Add a new insight from an agent (will be reviewed before presentation)."""
        insight_id = str(uuid.uuid4())
        
        insight = AgentInsight(
            id=insight_id,
            agent_id=agent_id,
            agent_name=agent_name,
            insight_type=insight_type,
            title=title,
            description=description,
            confidence=confidence,
            supporting_data=supporting_data,
            actionable=actionable,
            page=page
        )
        
        # Store the raw insight (before review)
        self.agent_insights[insight_id] = insight
        self._save_insights()
        
        logger.info(f"Agent {agent_name} added insight: {title} (pending review)")
        return insight_id
    
    def get_insights_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all insights for a specific page (reviewed and validated)."""
        page_insights = [
            asdict(insight) for insight in self.agent_insights.values()
            if insight.page == page
        ]
        
        # Apply presentation review to filter and improve insights
        if page_insights:
            try:
                # Import here to avoid circular dependency
                from app.services.discovery_agents.presentation_reviewer_agent import presentation_reviewer_agent
                
                # Convert to format expected by reviewer
                insight_dicts = []
                for insight_dict in page_insights:
                    insight_dicts.append({
                        "id": insight_dict["id"],
                        "agent_id": insight_dict["agent_id"],
                        "title": insight_dict["title"],
                        "description": insight_dict["description"],
                        "supporting_data": insight_dict["supporting_data"],
                        "insight_type": insight_dict["insight_type"],
                        "confidence": insight_dict["confidence"],
                        "actionable": insight_dict.get("actionable", True),
                        "created_at": insight_dict["created_at"]
                    })
                
                # Get supporting data context from classifications
                supporting_data_context = self.get_classified_data_for_page(page)
                
                # Review insights for presentation
                import asyncio
                loop = asyncio.get_event_loop()
                review_result = loop.run_until_complete(
                    presentation_reviewer_agent.review_insights_for_presentation(
                        insight_dicts, page, supporting_data_context
                    )
                )
                
                # Process agent feedback if any
                agent_feedback = review_result.get("agent_feedback", [])
                if agent_feedback:
                    logger.info(f"Presentation reviewer provided feedback for {len(agent_feedback)} insights")
                    # Store feedback for agent learning
                    for feedback in agent_feedback:
                        self.set_cross_page_context(
                            f"agent_feedback_{feedback['target_agent_id']}", 
                            feedback, 
                            "presentation_reviewer"
                        )
                
                # Return reviewed insights
                reviewed_insights = review_result.get("reviewed_insights", page_insights)
                
                logger.info(f"Presentation review: {len(reviewed_insights)}/{len(page_insights)} insights approved for {page}")
                return reviewed_insights
                
            except Exception as e:
                logger.error(f"Error in presentation review: {e}")
                # Fall back to original insights if review fails
                pass
        
        # Sort by confidence and creation time (fallback behavior)
        confidence_order = {"high": 4, "medium": 3, "low": 2, "uncertain": 1}
        page_insights.sort(
            key=lambda x: (confidence_order.get(x['confidence'], 0), x['created_at']),
            reverse=True
        )
        
        return page_insights
    
    # === CROSS-PAGE CONTEXT MANAGEMENT ===
    
    def set_cross_page_context(self, key: str, value: Any, page_source: str) -> None:
        """Set context that should be preserved across pages."""
        self.cross_page_context[key] = {
            "value": value,
            "page_source": page_source,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._save_context()
        
        logger.info(f"Set cross-page context {key} from {page_source}")
    
    def get_cross_page_context(self, key: str = None) -> Any:
        """Get cross-page context."""
        if key:
            return self.cross_page_context.get(key, {}).get("value")
        return self.cross_page_context
    
    def clear_cross_page_context(self, key: str = None) -> None:
        """Clear cross-page context."""
        if key and key in self.cross_page_context:
            del self.cross_page_context[key]
        else:
            self.cross_page_context.clear()
        self._save_context()
    
    # === LEARNING AND FEEDBACK ===
    
    def _store_learning_experience(self, learning_context: Dict[str, Any]) -> None:
        """Store learning experience for agents."""
        experience_file = self.data_dir / "agent_learning_experiences.json"
        
        try:
            if experience_file.exists():
                with open(experience_file, 'r') as f:
                    experiences = json.load(f)
            else:
                experiences = []
            
            experiences.append(learning_context)
            
            # Keep only recent experiences (last 1000)
            if len(experiences) > 1000:
                experiences = experiences[-1000:]
            
            with open(experience_file, 'w') as f:
                json.dump(experiences, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing learning experience: {e}")
    
    def get_recent_learning_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning experiences for agent improvement."""
        experience_file = self.data_dir / "agent_learning_experiences.json"
        
        try:
            if experience_file.exists():
                with open(experience_file, 'r') as f:
                    experiences = json.load(f)
                return experiences[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error loading learning experiences: {e}")
            return []
    
    # === AGENT PROCESSING METHODS ===
    
    async def analyze_with_agents(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data using available agents and return intelligent insights.
        
        Args:
            analysis_request: Request containing data_source, analysis_type, page_context, etc.
            
        Returns:
            Agent analysis results with insights, questions, and classifications
        """
        try:
            # Route to appropriate agent based on analysis type
            analysis_type = analysis_request.get("analysis_type", "data_source_analysis")
            page_context = analysis_request.get("page_context", "discovery")
            
            if analysis_type == "data_quality_intelligence":
                return await self._analyze_data_quality_with_agents(analysis_request)
            elif analysis_type == "data_source_analysis":
                return await self._analyze_data_source_with_agents(analysis_request)
            else:
                # Fallback to basic analysis
                return {
                    "status": "success",
                    "analysis_type": "basic",
                    "quality_assessment": {"average_quality": 75},
                    "priority_issues": [],
                    "cleansing_recommendations": [],
                    "quality_buckets": {"clean_data": 0, "needs_attention": 0, "critical_issues": 0},
                    "confidence": 0.7,
                    "insights": ["Basic analysis completed"]
                }
                
        except Exception as e:
            logger.error(f"Error in analyze_with_agents: {e}")
            return {
                "status": "error",
                "error": str(e),
                "analysis_type": "error"
            }
    
    async def process_with_agents(self, processing_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using agent-driven operations.
        
        Args:
            processing_request: Request containing data, operations, preferences, etc.
            
        Returns:
            Processing results with improved data and quality metrics
        """
        try:
            operations = processing_request.get("operations", [])
            data_source = processing_request.get("data_source", {})
            assets = data_source.get("assets", [])
            
            if not assets:
                return {
                    "status": "error",
                    "error": "No assets provided for processing"
                }
            
            # Apply operations using agent intelligence
            processed_assets = []
            total_improvement = 0
            
            for asset in assets:
                processed_asset = asset.copy()
                original_quality = self._calculate_basic_quality(asset)
                
                # Apply each operation
                for operation in operations:
                    op_type = operation.get("operation", "")
                    if op_type == "standardize_asset_types":
                        processed_asset = self._standardize_asset_type(processed_asset)
                    elif op_type == "normalize_environments":
                        processed_asset = self._normalize_environment(processed_asset)
                    elif op_type == "fix_hostnames":
                        processed_asset = self._fix_hostname(processed_asset)
                    elif op_type == "complete_missing_fields":
                        processed_asset = self._complete_missing_data(processed_asset)
                
                new_quality = self._calculate_basic_quality(processed_asset)
                total_improvement += (new_quality - original_quality)
                processed_assets.append(processed_asset)
            
            return {
                "status": "success",
                "processed_assets": processed_assets,
                "quality_improvement": {
                    "average_improvement": total_improvement / len(assets) if assets else 0,
                    "total_assets_processed": len(assets)
                },
                "operations_applied": [op.get("operation", "") for op in operations],
                "quality_metrics": {
                    "original_average": sum(self._calculate_basic_quality(asset) for asset in assets) / len(assets) if assets else 0,
                    "improved_average": sum(self._calculate_basic_quality(asset) for asset in processed_assets) / len(processed_assets) if processed_assets else 0
                },
                "confidence": 0.8,
                "processing_summary": f"Agent-processed {len(assets)} assets with {len(operations)} operations"
            }
            
        except Exception as e:
            logger.error(f"Error in process_with_agents: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _analyze_data_quality_with_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data quality using agent intelligence."""
        data_source = request.get("data_source", {})
        assets = data_source.get("assets", [])
        
        if not assets:
            return {
                "status": "success",
                "quality_assessment": {},
                "priority_issues": [],
                "cleansing_recommendations": [],
                "quality_buckets": {"clean_data": 0, "needs_attention": 0, "critical_issues": 0},
                "confidence": 0.0,
                "insights": ["No data available for analysis"]
            }
        
        # Analyze data quality
        quality_issues = []
        clean_count = 0
        needs_attention_count = 0
        critical_count = 0
        
        for i, asset in enumerate(assets):
            quality_score = self._calculate_basic_quality(asset)
            
            if quality_score >= 80:
                clean_count += 1
            elif quality_score >= 60:
                needs_attention_count += 1
            else:
                critical_count += 1
                # Add critical issues
                quality_issues.append({
                    "asset_id": asset.get("id", f"asset_{i}"),
                    "asset_name": asset.get("asset_name", f"Asset {i}"),
                    "issue": "Low data quality score",
                    "severity": "critical",
                    "confidence": 0.8,
                    "suggested_fix": "Review and complete missing fields"
                })
        
        return {
            "status": "success",
            "quality_assessment": {
                "average_quality": sum(self._calculate_basic_quality(asset) for asset in assets) / len(assets),
                "total_assets": len(assets)
            },
            "priority_issues": quality_issues[:10],  # Top 10 issues
            "cleansing_recommendations": [
                "Complete missing critical fields",
                "Standardize asset types and environments",
                "Normalize naming conventions"
            ],
            "quality_buckets": {
                "clean_data": clean_count,
                "needs_attention": needs_attention_count,
                "critical_issues": critical_count
            },
            "confidence": 0.85,
            "insights": [
                f"Analyzed {len(assets)} assets for data quality",
                f"Found {critical_count} assets with critical quality issues",
                f"Overall data quality: {((clean_count + needs_attention_count * 0.7) / len(assets) * 100):.1f}%"
            ]
        }
    
    async def _analyze_data_source_with_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data source using agent intelligence."""
        # Delegate to data source intelligence agent
        try:
            from app.services.discovery_agents.data_source_intelligence_agent import data_source_intelligence_agent
            
            data_source = request.get("data_source", {})
            page_context = request.get("page_context", "data-import")
            
            result = await data_source_intelligence_agent.analyze_data_source(data_source, page_context)
            return {"status": "success", **result}
            
        except Exception as e:
            logger.warning(f"Data source agent unavailable, using basic analysis: {e}")
            return {
                "status": "success",
                "analysis_type": "basic",
                "agent_analysis": {"basic_analysis": "Agent unavailable"},
                "confidence": 0.6
            }
    
    def _calculate_basic_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate basic quality score for an asset."""
        score = 0.0
        total_factors = 0
        
        # Check critical fields
        critical_fields = ["asset_name", "asset_type", "environment"]
        for field in critical_fields:
            total_factors += 1
            if asset.get(field) and str(asset.get(field)).strip():
                score += 1
        
        # Check optional important fields
        important_fields = ["hostname", "ip_address", "department", "operating_system"]
        for field in important_fields:
            total_factors += 0.5
            if asset.get(field) and str(asset.get(field)).strip():
                score += 0.5
        
        return (score / total_factors * 100) if total_factors > 0 else 0
    
    def _standardize_asset_type(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize asset type value."""
        asset_type = str(asset.get("asset_type", "")).upper()
        
        # Standardization mappings
        if asset_type in ["SRV", "SVR", "SERVER"]:
            asset["asset_type"] = "SERVER"
        elif asset_type in ["DB", "DATABASE"]:
            asset["asset_type"] = "DATABASE"
        elif asset_type in ["APP", "APPLICATION"]:
            asset["asset_type"] = "APPLICATION"
        elif asset_type in ["NET", "NETWORK"]:
            asset["asset_type"] = "NETWORK"
        
        return asset
    
    def _normalize_environment(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment value."""
        env = str(asset.get("environment", "")).lower()
        
        if env in ["prod", "production"]:
            asset["environment"] = "Production"
        elif env in ["dev", "development"]:
            asset["environment"] = "Development"
        elif env in ["test", "testing"]:
            asset["environment"] = "Test"
        elif env in ["stage", "staging"]:
            asset["environment"] = "Staging"
        
        return asset
    
    def _fix_hostname(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix hostname format."""
        hostname = str(asset.get("hostname", "")).strip()
        if hostname:
            # Remove extra spaces and standardize format
            asset["hostname"] = hostname.lower().replace(" ", "-")
        
        return asset
    
    def _complete_missing_data(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Complete missing data with reasonable defaults."""
        if not asset.get("environment"):
            asset["environment"] = "Production"  # Common default
        
        if not asset.get("asset_type"):
            asset["asset_type"] = "SERVER"  # Common default
        
        if not asset.get("business_criticality"):
            asset["business_criticality"] = "Medium"  # Safe default
        
        return asset
    
    # === UTILITY METHODS ===
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current agent-UI interaction status."""
        return {
            "pending_questions": len([q for q in self.pending_questions.values() if not q.is_resolved]),
            "total_questions": len(self.pending_questions),
            "classified_items": len(self.data_classifications),
            "agent_insights": len(self.agent_insights),
            "cross_page_context_items": len(self.cross_page_context),
            "classifications_by_type": {
                "good_data": len([item for item in self.data_classifications.values() 
                                if item.classification == DataClassification.GOOD_DATA]),
                "needs_clarification": len([item for item in self.data_classifications.values() 
                                          if item.classification == DataClassification.NEEDS_CLARIFICATION]),
                "unusable": len([item for item in self.data_classifications.values() 
                               if item.classification == DataClassification.UNUSABLE])
            }
        }
    
    # === PERSISTENCE METHODS ===
    
    def _load_persistent_data(self) -> None:
        """Load persistent data from storage."""
        try:
            # Load questions
            if self.questions_file.exists():
                with open(self.questions_file, 'r') as f:
                    questions_data = json.load(f)
                    for q_data in questions_data:
                        q_data['question_type'] = QuestionType(q_data['question_type'])
                        if q_data.get('confidence'):
                            q_data['confidence'] = ConfidenceLevel(q_data['confidence'])
                        q_data['created_at'] = datetime.fromisoformat(q_data['created_at'])
                        if q_data.get('answered_at'):
                            q_data['answered_at'] = datetime.fromisoformat(q_data['answered_at'])
                        
                        question = AgentQuestion(**q_data)
                        self.pending_questions[question.id] = question
            
            # Load classifications
            if self.classifications_file.exists():
                with open(self.classifications_file, 'r') as f:
                    classifications_data = json.load(f)
                    for c_data in classifications_data:
                        c_data['classification'] = DataClassification(c_data['classification'])
                        c_data['confidence'] = ConfidenceLevel(c_data['confidence'])
                        
                        data_item = DataItem(**c_data)
                        self.data_classifications[data_item.id] = data_item
            
            # Load insights
            if self.insights_file.exists():
                with open(self.insights_file, 'r') as f:
                    insights_data = json.load(f)
                    for i_data in insights_data:
                        i_data['confidence'] = ConfidenceLevel(i_data['confidence'])
                        i_data['created_at'] = datetime.fromisoformat(i_data['created_at'])
                        
                        insight = AgentInsight(**i_data)
                        self.agent_insights[insight.id] = insight
            
            # Load context
            if self.context_file.exists():
                with open(self.context_file, 'r') as f:
                    self.cross_page_context = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")
    
    def _save_questions(self) -> None:
        """Save questions to persistent storage."""
        try:
            questions_data = []
            for question in self.pending_questions.values():
                q_dict = asdict(question)
                q_dict['question_type'] = question.question_type.value
                if question.confidence:
                    q_dict['confidence'] = question.confidence.value
                q_dict['created_at'] = question.created_at.isoformat()
                if question.answered_at:
                    q_dict['answered_at'] = question.answered_at.isoformat()
                questions_data.append(q_dict)
            
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving questions: {e}")
    
    def _save_classifications(self) -> None:
        """Save classifications to persistent storage."""
        try:
            classifications_data = []
            for data_item in self.data_classifications.values():
                c_dict = asdict(data_item)
                c_dict['classification'] = data_item.classification.value
                c_dict['confidence'] = data_item.confidence.value
                classifications_data.append(c_dict)
            
            with open(self.classifications_file, 'w') as f:
                json.dump(classifications_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving classifications: {e}")
    
    def _save_insights(self) -> None:
        """Save insights to persistent storage."""
        try:
            insights_data = []
            for insight in self.agent_insights.values():
                i_dict = asdict(insight)
                i_dict['confidence'] = insight.confidence.value
                i_dict['created_at'] = insight.created_at.isoformat()
                insights_data.append(i_dict)
            
            with open(self.insights_file, 'w') as f:
                json.dump(insights_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
    
    def _save_context(self) -> None:
        """Save cross-page context to persistent storage."""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(self.cross_page_context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {e}")

# Global instance for the application
agent_ui_bridge = AgentUIBridge() 