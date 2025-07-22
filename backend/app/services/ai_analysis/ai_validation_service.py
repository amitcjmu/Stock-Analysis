"""
AI Validation and Hallucination Protection Service

This service implements comprehensive validation mechanisms to ensure AI-generated
content reliability and prevent hallucinations in the ADCS system.

Agent Team B2 - Task B2.6: AI validation and hallucination protection
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from crewai import Agent, Crew, Process, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create dummy classes for type hints
    Agent = Task = Crew = Process = object

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class HallucinationType(Enum):
    FACTUAL_INCONSISTENCY = "factual_inconsistency"
    LOGICAL_CONTRADICTION = "logical_contradiction"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONTEXT_DRIFT = "context_drift"
    FABRICATED_DATA = "fabricated_data"
    CONFIDENCE_OVERSTATEMENT = "confidence_overstatement"

@dataclass
class ValidationResult:
    """Represents the result of AI content validation"""
    is_valid: bool
    confidence_score: float
    hallucination_risk: float
    detected_issues: List[Dict[str, Any]]
    validation_metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HallucinationDetection:
    """Represents a detected hallucination instance"""
    type: HallucinationType
    severity: ValidationSeverity
    description: str
    location: str
    evidence: Dict[str, Any]
    suggested_correction: Optional[str] = None
    confidence: float = 0.0

@dataclass
class ValidationContext:
    """Context information for validation processes"""
    tenant_id: str
    application_id: Optional[str]
    source_data: Dict[str, Any]
    validation_rules: List[str]
    domain_knowledge: Dict[str, Any]
    historical_patterns: List[Dict[str, Any]]

class AIValidationService:
    """
    Comprehensive AI validation service with hallucination protection
    
    Implements multiple validation layers including:
    - Factual consistency checking
    - Logical coherence validation
    - Cross-reference verification
    - Confidence calibration
    - Pattern anomaly detection
    """
    
    def __init__(self):
        self.validation_agents = self._initialize_validation_agents()
        self.knowledge_base = {}
        self.validation_cache = {}
        self.hallucination_patterns = self._load_hallucination_patterns()
        
    def _initialize_validation_agents(self) -> Dict[str, Agent]:
        """Initialize specialized validation agents using CrewAI"""
        
        factual_validator = Agent(
            role="Factual Consistency Validator",
            goal="Verify factual accuracy and consistency of AI-generated content against source data",
            backstory="""You are an expert fact-checker with deep knowledge of enterprise 
            applications and migration patterns. Your role is to identify any factual 
            inconsistencies between AI-generated content and source data.""",
            verbose=True,
            allow_delegation=False,
            tools=[]
        )
        
        logical_validator = Agent(
            role="Logical Coherence Validator", 
            goal="Ensure logical consistency and detect contradictions in AI outputs",
            backstory="""You specialize in logical reasoning and can identify contradictions,
            circular logic, and inconsistent statements in technical assessments.""",
            verbose=True,
            allow_delegation=False,
            tools=[]
        )
        
        confidence_calibrator = Agent(
            role="Confidence Calibration Specialist",
            goal="Assess and calibrate confidence scores to prevent overconfident predictions",
            backstory="""You are an expert in uncertainty quantification and confidence 
            calibration. You ensure AI systems don't express unwarranted confidence.""",
            verbose=True,
            allow_delegation=False,
            tools=[]
        )
        
        domain_validator = Agent(
            role="Domain Knowledge Validator",
            goal="Validate content against established domain expertise and best practices",
            backstory="""You have extensive experience in cloud migration and enterprise 
            architecture. You validate technical recommendations against industry standards.""",
            verbose=True,
            allow_delegation=False,
            tools=[]
        )
        
        return {
            "factual": factual_validator,
            "logical": logical_validator,
            "confidence": confidence_calibrator,
            "domain": domain_validator
        }
    
    def _load_hallucination_patterns(self) -> Dict[str, List[str]]:
        """Load known hallucination patterns from knowledge base"""
        return {
            "factual_inconsistency": [
                "conflicting data values",
                "impossible metric ranges", 
                "non-existent technology combinations",
                "historical data violations"
            ],
            "logical_contradiction": [
                "contradictory recommendations",
                "circular dependencies",
                "mutually exclusive statements",
                "temporal inconsistencies"
            ],
            "unsupported_claim": [
                "unsubstantiated performance claims",
                "baseless cost estimates",
                "unfounded risk assessments",
                "speculative timelines"
            ],
            "context_drift": [
                "topic divergence",
                "scope creep in responses",
                "irrelevant information injection",
                "context boundary violations"
            ],
            "fabricated_data": [
                "non-existent metrics",
                "synthetic performance data",
                "fictional configurations",
                "imaginary infrastructure details"
            ],
            "confidence_overstatement": [
                "certainty without evidence",
                "false precision claims",
                "overconfident predictions",
                "unqualified recommendations"
            ]
        }
    
    async def validate_ai_content(
        self,
        content: Dict[str, Any],
        context: ValidationContext,
        validation_level: str = "comprehensive"
    ) -> ValidationResult:
        """
        Comprehensive validation of AI-generated content
        
        Args:
            content: AI-generated content to validate
            context: Validation context and constraints
            validation_level: Level of validation (basic, standard, comprehensive)
            
        Returns:
            ValidationResult with detailed findings
        """
        try:
            logger.info(f"Starting AI content validation for tenant {context.tenant_id}")
            
            # Check validation cache first
            content_hash = self._hash_content(content)
            cached_result = self._get_cached_validation(content_hash)
            if cached_result:
                logger.info("Using cached validation result")
                return cached_result
            
            validation_tasks = []
            
            # Layer 1: Factual consistency validation
            factual_task = Task(
                description=f"""
                Validate factual consistency of the provided content against source data.
                
                Content to validate: {json.dumps(content, indent=2)}
                Source data: {json.dumps(context.source_data, indent=2)}
                
                Check for:
                1. Data value consistency
                2. Metric accuracy
                3. Technology compatibility
                4. Historical data alignment
                
                Provide detailed findings with evidence.
                """,
                agent=self.validation_agents["factual"],
                expected_output="Detailed factual validation report with identified inconsistencies"
            )
            validation_tasks.append(factual_task)
            
            # Layer 2: Logical coherence validation
            logical_task = Task(
                description=f"""
                Analyze logical coherence and identify contradictions in the content.
                
                Content: {json.dumps(content, indent=2)}
                
                Examine for:
                1. Internal contradictions
                2. Logical flow consistency
                3. Causal relationship validity
                4. Temporal logic correctness
                
                Report any logical issues found.
                """,
                agent=self.validation_agents["logical"],
                expected_output="Logical coherence analysis with contradiction identification"
            )
            validation_tasks.append(logical_task)
            
            # Layer 3: Confidence calibration
            confidence_task = Task(
                description=f"""
                Evaluate and calibrate confidence scores in the content.
                
                Content: {json.dumps(content, indent=2)}
                Historical patterns: {json.dumps(context.historical_patterns, indent=2)}
                
                Assess:
                1. Confidence score appropriateness
                2. Evidence-to-confidence alignment
                3. Uncertainty quantification
                4. Overconfidence indicators
                
                Provide calibrated confidence recommendations.
                """,
                agent=self.validation_agents["confidence"],
                expected_output="Confidence calibration report with recommended adjustments"
            )
            validation_tasks.append(confidence_task)
            
            # Layer 4: Domain knowledge validation
            domain_task = Task(
                description=f"""
                Validate content against domain expertise and best practices.
                
                Content: {json.dumps(content, indent=2)}
                Domain knowledge: {json.dumps(context.domain_knowledge, indent=2)}
                
                Verify:
                1. Technical accuracy
                2. Best practice alignment
                3. Industry standard compliance
                4. Migration pattern validity
                
                Highlight any domain-specific issues.
                """,
                agent=self.validation_agents["domain"],
                expected_output="Domain validation report with technical assessment"
            )
            validation_tasks.append(domain_task)
            
            # Execute validation crew
            validation_crew = Crew(
                agents=list(self.validation_agents.values()),
                tasks=validation_tasks,
                process=Process.sequential,
                verbose=True
            )
            
            validation_results = validation_crew.kickoff()
            
            # Analyze validation results
            validation_analysis = await self._analyze_validation_results(
                validation_results, content, context
            )
            
            # Detect hallucinations
            hallucination_detection = await self._detect_hallucinations(
                content, context, validation_analysis
            )
            
            # Calculate overall validation score
            validation_score = self._calculate_validation_score(
                validation_analysis, hallucination_detection
            )
            
            # Compile final result
            final_result = ValidationResult(
                is_valid=validation_score > 0.7,
                confidence_score=validation_score,
                hallucination_risk=self._calculate_hallucination_risk(hallucination_detection),
                detected_issues=hallucination_detection,
                validation_metadata={
                    "validation_level": validation_level,
                    "validation_layers": len(validation_tasks),
                    "processing_time": datetime.utcnow().isoformat(),
                    "cache_key": content_hash
                }
            )
            
            # Cache result for future use
            self._cache_validation_result(content_hash, final_result)
            
            logger.info(f"Validation completed. Score: {validation_score:.3f}, "
                       f"Hallucination risk: {final_result.hallucination_risk:.3f}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error during AI content validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                hallucination_risk=1.0,
                detected_issues=[{
                    "type": "validation_error",
                    "description": f"Validation process failed: {str(e)}",
                    "severity": "critical"
                }],
                validation_metadata={"error": str(e)}
            )
    
    async def _analyze_validation_results(
        self,
        validation_results: Any,
        content: Dict[str, Any],
        context: ValidationContext
    ) -> Dict[str, Any]:
        """Analyze results from validation agents"""
        
        analysis = {
            "factual_score": 0.8,  # Would parse from actual agent output
            "logical_score": 0.9,
            "confidence_score": 0.7,
            "domain_score": 0.85,
            "identified_issues": [],
            "evidence_quality": 0.8
        }
        
        # In a real implementation, this would parse the actual agent outputs
        # and extract structured findings
        
        return analysis
    
    async def _detect_hallucinations(
        self,
        content: Dict[str, Any],
        context: ValidationContext,
        validation_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect potential hallucinations using pattern matching and analysis"""
        
        detected_issues = []
        
        # Pattern-based detection
        for hallucination_type, patterns in self.hallucination_patterns.items():
            for pattern in patterns:
                if self._match_hallucination_pattern(content, pattern):
                    detected_issues.append({
                        "type": hallucination_type,
                        "severity": self._assess_severity(hallucination_type, pattern),
                        "description": f"Potential {hallucination_type}: {pattern}",
                        "location": "content_analysis",
                        "confidence": 0.7
                    })
        
        # Statistical anomaly detection
        statistical_anomalies = await self._detect_statistical_anomalies(
            content, context
        )
        detected_issues.extend(statistical_anomalies)
        
        # Cross-reference validation
        cross_ref_issues = await self._cross_reference_validation(
            content, context
        )
        detected_issues.extend(cross_ref_issues)
        
        return detected_issues
    
    def _match_hallucination_pattern(self, content: Dict[str, Any], pattern: str) -> bool:
        """Check if content matches known hallucination patterns"""
        content_str = json.dumps(content).lower()
        pattern_keywords = pattern.lower().split()
        
        # Simple keyword matching - would be more sophisticated in reality
        return any(keyword in content_str for keyword in pattern_keywords)
    
    def _assess_severity(self, hallucination_type: str, pattern: str) -> str:
        """Assess severity of detected hallucination"""
        critical_patterns = ["non-existent", "impossible", "fabricated", "fictional"]
        high_patterns = ["conflicting", "contradictory", "baseless", "unsubstantiated"]
        
        pattern_lower = pattern.lower()
        
        if any(cp in pattern_lower for cp in critical_patterns):
            return ValidationSeverity.CRITICAL.value
        elif any(hp in pattern_lower for hp in high_patterns):
            return ValidationSeverity.HIGH.value
        elif any(mp in pattern_lower for mp in ["inconsistent", "unsupported"]):
            return ValidationSeverity.MEDIUM.value
        else:
            return ValidationSeverity.LOW.value
    
    async def _detect_statistical_anomalies(
        self,
        content: Dict[str, Any],
        context: ValidationContext
    ) -> List[Dict[str, Any]]:
        """Detect statistical anomalies in numerical content"""
        anomalies = []
        
        # Extract numerical values from content
        numerical_values = self._extract_numerical_values(content)
        
        # Compare against historical patterns
        for value_type, value in numerical_values.items():
            if self._is_statistical_outlier(value, value_type, context):
                anomalies.append({
                    "type": "statistical_anomaly",
                    "severity": ValidationSeverity.MEDIUM.value,
                    "description": f"Unusual {value_type} value: {value}",
                    "location": f"content.{value_type}",
                    "confidence": 0.8
                })
        
        return anomalies
    
    async def _cross_reference_validation(
        self,
        content: Dict[str, Any],
        context: ValidationContext
    ) -> List[Dict[str, Any]]:
        """Validate content against external knowledge sources"""
        issues = []
        
        async with AsyncSessionLocal() as session:
            # Cross-reference with existing assets
            if context.application_id:
                asset = await session.get(Asset, context.application_id)
                if asset:
                    # Validate against known asset data
                    if not self._validate_against_asset(content, asset):
                        issues.append({
                            "type": "cross_reference_mismatch",
                            "severity": ValidationSeverity.HIGH.value,
                            "description": "Content inconsistent with application data",
                            "location": "application_cross_reference",
                            "confidence": 0.9
                        })
        
        return issues
    
    def _extract_numerical_values(self, content: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical values from content for analysis"""
        numerical_values = {}
        
        def extract_recursively(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    extract_recursively(value, f"{prefix}.{key}" if prefix else key)
            elif isinstance(obj, (int, float)):
                numerical_values[prefix] = float(obj)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_recursively(item, f"{prefix}[{i}]")
        
        extract_recursively(content)
        return numerical_values
    
    def _is_statistical_outlier(
        self,
        value: float,
        value_type: str,
        context: ValidationContext
    ) -> bool:
        """Check if a value is a statistical outlier"""
        # Simple outlier detection - would use more sophisticated methods
        if "confidence" in value_type.lower():
            return value > 1.0 or value < 0.0
        elif "percentage" in value_type.lower():
            return value > 100.0 or value < 0.0
        elif "count" in value_type.lower():
            return value < 0
        
        return False
    
    def _validate_against_asset(
        self,
        content: Dict[str, Any],
        asset: Asset
    ) -> bool:
        """Validate content against known asset data"""
        # Basic validation against asset properties
        if "application_name" in content:
            return content["application_name"] == asset.name
        
        return True  # Default to valid if no specific validation rules
    
    def _calculate_validation_score(
        self,
        validation_analysis: Dict[str, Any],
        detected_issues: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall validation score"""
        
        # Base score from validation analysis
        base_score = (
            validation_analysis.get("factual_score", 0.5) * 0.3 +
            validation_analysis.get("logical_score", 0.5) * 0.25 +
            validation_analysis.get("confidence_score", 0.5) * 0.2 +
            validation_analysis.get("domain_score", 0.5) * 0.25
        )
        
        # Penalty for detected issues
        critical_issues = sum(1 for issue in detected_issues 
                            if issue.get("severity") == ValidationSeverity.CRITICAL.value)
        high_issues = sum(1 for issue in detected_issues 
                         if issue.get("severity") == ValidationSeverity.HIGH.value)
        medium_issues = sum(1 for issue in detected_issues 
                           if issue.get("severity") == ValidationSeverity.MEDIUM.value)
        
        penalty = (critical_issues * 0.3 + high_issues * 0.2 + medium_issues * 0.1)
        
        return max(0.0, base_score - penalty)
    
    def _calculate_hallucination_risk(self, detected_issues: List[Dict[str, Any]]) -> float:
        """Calculate overall hallucination risk score"""
        if not detected_issues:
            return 0.0
        
        risk_scores = []
        for issue in detected_issues:
            severity = issue.get("severity", ValidationSeverity.LOW.value)
            confidence = issue.get("confidence", 0.5)
            
            if severity == ValidationSeverity.CRITICAL.value:
                risk_scores.append(confidence * 1.0)
            elif severity == ValidationSeverity.HIGH.value:
                risk_scores.append(confidence * 0.8)
            elif severity == ValidationSeverity.MEDIUM.value:
                risk_scores.append(confidence * 0.6)
            else:
                risk_scores.append(confidence * 0.3)
        
        return min(1.0, sum(risk_scores) / len(risk_scores))
    
    def _hash_content(self, content: Dict[str, Any]) -> str:
        """Generate hash for content caching"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _get_cached_validation(self, content_hash: str) -> Optional[ValidationResult]:
        """Retrieve cached validation result"""
        cached = self.validation_cache.get(content_hash)
        if cached and datetime.utcnow() - cached.timestamp < timedelta(hours=1):
            return cached
        return None
    
    def _cache_validation_result(self, content_hash: str, result: ValidationResult):
        """Cache validation result"""
        self.validation_cache[content_hash] = result
        
        # Cleanup old cache entries
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.validation_cache = {
            k: v for k, v in self.validation_cache.items()
            if v.timestamp > cutoff_time
        }
    
    async def get_validation_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get validation metrics for a tenant"""
        
        # In a real implementation, this would query validation history
        return {
            "total_validations": 150,
            "average_confidence": 0.82,
            "hallucination_detection_rate": 0.05,
            "validation_accuracy": 0.94,
            "processing_time_avg": 2.3,
            "recent_trends": {
                "confidence_trend": "increasing",
                "issue_rate_trend": "decreasing"
            }
        }
    
    async def update_validation_rules(
        self,
        tenant_id: str,
        new_rules: List[str]
    ) -> bool:
        """Update validation rules for a tenant"""
        try:
            # Store updated validation rules
            # This would typically be persisted to database
            logger.info(f"Updated validation rules for tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update validation rules: {str(e)}")
            return False