"""
6R Analysis Tools for CrewAI Agents.
Specialized tools for CMDB analysis, parameter scoring, question generation, and validation.
"""

import json
import logging
from typing import Any, Dict, List, Optional

try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    from app.schemas.sixr_analysis import SixRParameterBase, SixRStrategy
    from app.services.field_mapper_modular import FieldMapperService
    from app.services.sixr_engine_modular import SixRDecisionEngine

    SIXR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Tool imports failed: {e}")

    # Fallback classes for testing
    class BaseTool:
        def __init__(self, **kwargs):
            pass

    class BaseModel:
        def __init__(self, **kwargs):
            pass

    def Field(*args, **kwargs):
        return None


logger = logging.getLogger(__name__)


class CMDBAnalysisInput(BaseModel):
    """Input schema for CMDB analysis tool."""

    application_data: Dict[str, Any] = Field(
        ..., description="Application data from CMDB"
    )
    analysis_focus: str = Field(
        default="all", description="Focus area: technical, business, compliance, or all"
    )


class CMDBAnalysisTool(BaseTool):
    """Tool for analyzing CMDB data to extract 6R-relevant insights."""

    name: str = "cmdb_analysis_tool"
    description: str = (
        "Analyze CMDB application data to extract insights for 6R migration strategy analysis"
    )
    args_schema: type[BaseModel] = CMDBAnalysisInput

    def __init__(self):
        super().__init__()
        self.field_mapper = FieldMapperService()

    def _run(
        self, application_data: Dict[str, Any], analysis_focus: str = "all"
    ) -> str:
        """Analyze CMDB data and return structured insights."""
        try:
            insights = {
                "technical_insights": {},
                "business_insights": {},
                "compliance_insights": {},
                "risk_indicators": [],
                "recommended_parameters": {},
            }

            # Technical Analysis
            if analysis_focus in ["technical", "all"]:
                insights["technical_insights"] = self._analyze_technical_aspects(
                    application_data
                )

            # Business Analysis
            if analysis_focus in ["business", "all"]:
                insights["business_insights"] = self._analyze_business_aspects(
                    application_data
                )

            # Compliance Analysis
            if analysis_focus in ["compliance", "all"]:
                insights["compliance_insights"] = self._analyze_compliance_aspects(
                    application_data
                )

            # Risk Analysis
            insights["risk_indicators"] = self._identify_risk_indicators(
                application_data
            )

            # Parameter Recommendations
            insights["recommended_parameters"] = self._recommend_initial_parameters(
                insights
            )

            return json.dumps(insights, indent=2)

        except Exception as e:
            logger.error(f"CMDB analysis failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})

    def _analyze_technical_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical complexity indicators."""
        technical_insights = {
            "complexity_score": 5.0,
            "technology_stack": [],
            "architecture_patterns": [],
            "integration_points": 0,
            "performance_characteristics": {},
        }

        # Analyze technology stack
        if "technology" in data or "tech_stack" in data:
            tech_info = data.get("technology", data.get("tech_stack", ""))
            if isinstance(tech_info, str):
                technical_insights["technology_stack"] = [tech_info]
            elif isinstance(tech_info, list):
                technical_insights["technology_stack"] = tech_info

        # Assess complexity based on various factors
        complexity_factors = []

        # Legacy technology indicators
        legacy_indicators = ["cobol", "mainframe", "as400", "vb6", "classic asp"]
        tech_stack_str = " ".join(technical_insights["technology_stack"]).lower()

        for indicator in legacy_indicators:
            if indicator in tech_stack_str:
                complexity_factors.append(f"Legacy technology: {indicator}")
                technical_insights["complexity_score"] += 2.0

        # Database complexity
        if "database" in data:
            db_info = str(data["database"]).lower()
            if any(db in db_info for db in ["oracle", "db2", "sybase"]):
                complexity_factors.append("Complex database system")
                technical_insights["complexity_score"] += 1.0

        # Integration complexity
        if "dependencies" in data:
            deps = data["dependencies"]
            if isinstance(deps, list):
                technical_insights["integration_points"] = len(deps)
            elif isinstance(deps, str) and deps:
                technical_insights["integration_points"] = len(deps.split(","))

            if technical_insights["integration_points"] > 5:
                complexity_factors.append("High number of dependencies")
                technical_insights["complexity_score"] += 1.5

        # Cap complexity score at 10
        technical_insights["complexity_score"] = min(
            10.0, technical_insights["complexity_score"]
        )
        technical_insights["complexity_factors"] = complexity_factors

        return technical_insights

    def _analyze_business_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business value indicators."""
        business_insights = {
            "business_value_score": 5.0,
            "criticality": "medium",
            "user_base": "unknown",
            "revenue_impact": "unknown",
            "strategic_importance": "medium",
        }

        # Analyze criticality
        if "criticality" in data:
            crit = str(data["criticality"]).lower()
            if crit in ["high", "critical", "tier1"]:
                business_insights["criticality"] = "high"
                business_insights["business_value_score"] = 8.0
            elif crit in ["low", "tier3"]:
                business_insights["criticality"] = "low"
                business_insights["business_value_score"] = 3.0

        # Analyze user base
        if "users" in data or "user_count" in data:
            users = data.get("users", data.get("user_count", 0))
            try:
                user_count = int(users)
                if user_count > 1000:
                    business_insights["user_base"] = "large"
                    business_insights["business_value_score"] += 1.0
                elif user_count > 100:
                    business_insights["user_base"] = "medium"
                else:
                    business_insights["user_base"] = "small"
                    business_insights["business_value_score"] -= 1.0
            except (ValueError, TypeError):
                pass

        # Analyze department/business unit
        if "department" in data or "business_unit" in data:
            dept = str(data.get("department", data.get("business_unit", ""))).lower()
            if any(
                critical_dept in dept
                for critical_dept in ["finance", "trading", "core", "customer"]
            ):
                business_insights["strategic_importance"] = "high"
                business_insights["business_value_score"] += 1.0

        # Cap business value score
        business_insights["business_value_score"] = max(
            1.0, min(10.0, business_insights["business_value_score"])
        )

        return business_insights

    def _analyze_compliance_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance and regulatory requirements."""
        compliance_insights = {
            "compliance_score": 5.0,
            "frameworks": [],
            "data_sensitivity": "medium",
            "regulatory_requirements": [],
        }

        # Check for compliance indicators
        compliance_keywords = {
            "sox": ["sox", "sarbanes", "financial"],
            "pci": ["pci", "payment", "card", "credit"],
            "hipaa": ["hipaa", "health", "medical", "patient"],
            "gdpr": ["gdpr", "privacy", "personal data", "eu"],
            "fisma": ["fisma", "federal", "government"],
        }

        data_str = json.dumps(data).lower()

        for framework, keywords in compliance_keywords.items():
            if any(keyword in data_str for keyword in keywords):
                compliance_insights["frameworks"].append(framework.upper())
                compliance_insights["compliance_score"] += 1.0

        # Analyze data sensitivity
        if "data_classification" in data:
            classification = str(data["data_classification"]).lower()
            if classification in ["confidential", "restricted", "sensitive"]:
                compliance_insights["data_sensitivity"] = "high"
                compliance_insights["compliance_score"] += 1.0
            elif classification in ["public", "internal"]:
                compliance_insights["data_sensitivity"] = "low"
                compliance_insights["compliance_score"] -= 1.0

        # Cap compliance score
        compliance_insights["compliance_score"] = max(
            1.0, min(10.0, compliance_insights["compliance_score"])
        )

        return compliance_insights

    def _identify_risk_indicators(self, data: Dict[str, Any]) -> List[str]:
        """Identify risk indicators from application data."""
        risk_indicators = []

        # Age-based risks
        if "install_date" in data or "created_date" in data:
            date_str = data.get("install_date", data.get("created_date", ""))
            if date_str:
                try:
                    # Simple age check - applications older than 10 years are risky
                    if "2014" in str(date_str) or any(
                        year in str(date_str)
                        for year in ["2013", "2012", "2011", "2010"]
                    ):
                        risk_indicators.append("Legacy application (>10 years old)")
                except Exception:
                    pass

        # Technology risks
        if "operating_system" in data:
            os_info = str(data["operating_system"]).lower()
            if any(
                legacy_os in os_info
                for legacy_os in ["windows 2008", "windows 2003", "aix", "solaris"]
            ):
                risk_indicators.append("Legacy operating system")

        # Support risks
        if "support_status" in data:
            support = str(data["support_status"]).lower()
            if "end of life" in support or "deprecated" in support:
                risk_indicators.append("End of life technology")

        # Security risks
        if "security_scan" in data:
            scan_results = str(data["security_scan"]).lower()
            if "high" in scan_results or "critical" in scan_results:
                risk_indicators.append("Security vulnerabilities identified")

        return risk_indicators

    def _recommend_initial_parameters(
        self, insights: Dict[str, Any]
    ) -> Dict[str, float]:
        """Recommend initial parameter values based on analysis."""
        params = {
            "business_value": 5.0,
            "technical_complexity": 5.0,
            "migration_urgency": 5.0,
            "compliance_requirements": 5.0,
            "cost_sensitivity": 5.0,
            "risk_tolerance": 5.0,
            "innovation_priority": 5.0,
        }

        # Set business value from analysis
        if "business_insights" in insights:
            params["business_value"] = insights["business_insights"].get(
                "business_value_score", 5.0
            )

        # Set technical complexity from analysis
        if "technical_insights" in insights:
            params["technical_complexity"] = insights["technical_insights"].get(
                "complexity_score", 5.0
            )

        # Set compliance requirements from analysis
        if "compliance_insights" in insights:
            params["compliance_requirements"] = insights["compliance_insights"].get(
                "compliance_score", 5.0
            )

        # Adjust urgency based on risk indicators
        risk_count = len(insights.get("risk_indicators", []))
        if risk_count > 3:
            params["migration_urgency"] = 8.0
        elif risk_count > 1:
            params["migration_urgency"] = 6.0

        return params


class ParameterScoringInput(BaseModel):
    """Input schema for parameter scoring tool."""

    parameters: Dict[str, float] = Field(..., description="6R parameters to score")
    strategy: str = Field(..., description="6R strategy to score against")


class ParameterScoringTool(BaseTool):
    """Tool for scoring parameters against specific 6R strategies."""

    name: str = "parameter_scoring_tool"
    description: str = "Score 6R parameters against a specific migration strategy"
    args_schema: type[BaseModel] = ParameterScoringInput

    def __init__(self):
        super().__init__()
        self.decision_engine = SixRDecisionEngine()

    def _run(self, parameters: Dict[str, float], strategy: str) -> str:
        """Score parameters against a specific strategy."""
        try:
            # Convert parameters to SixRParameterBase
            param_obj = SixRParameterBase(**parameters)

            # Get strategy enum
            strategy_enum = SixRStrategy(strategy.lower())

            # Calculate score for the specific strategy
            score_data = self.decision_engine._calculate_strategy_score(
                strategy_enum, param_obj, None
            )

            return json.dumps(score_data, indent=2)

        except Exception as e:
            logger.error(f"Parameter scoring failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})


class QuestionGenerationInput(BaseModel):
    """Input schema for question generation tool."""

    information_gaps: List[str] = Field(
        ..., description="List of information gaps to address"
    )
    application_context: Dict[str, Any] = Field(..., description="Application context")
    priority_focus: str = Field(default="all", description="Priority focus area")


class QuestionGenerationTool(BaseTool):
    """Tool for generating qualifying questions based on information gaps."""

    name: str = "question_generation_tool"
    description: str = (
        "Generate targeted qualifying questions to address information gaps"
    )
    args_schema: type[BaseModel] = QuestionGenerationInput

    def _run(
        self,
        information_gaps: List[str],
        application_context: Dict[str, Any],
        priority_focus: str = "all",
    ) -> str:
        """Generate questions based on information gaps."""
        try:
            questions = []

            # Question templates based on common gaps
            question_templates = {
                "application_type": {
                    "question": "What type of application is this?",
                    "type": "select",
                    "options": [
                        {
                            "value": "custom",
                            "label": "Custom-built application (developed in-house)",
                        },
                        {
                            "value": "cots",
                            "label": "Commercial Off-The-Shelf (COTS) application",
                        },
                        {
                            "value": "hybrid",
                            "label": "Hybrid (mix of custom and COTS components)",
                        },
                    ],
                    "category": "Application Classification",
                    "priority": 1,
                    "help_text": "COTS applications cannot be rewritten, only replaced with alternatives",
                },
                "dependencies": {
                    "question": "How many external dependencies does this application have?",
                    "type": "select",
                    "options": [
                        {"value": "none", "label": "No external dependencies"},
                        {"value": "few", "label": "1-3 dependencies"},
                        {"value": "moderate", "label": "4-10 dependencies"},
                        {"value": "many", "label": "More than 10 dependencies"},
                    ],
                    "category": "Technical Architecture",
                    "priority": 1,
                },
                "compliance": {
                    "question": "What compliance frameworks apply to this application?",
                    "type": "multiselect",
                    "options": [
                        {"value": "sox", "label": "SOX (Sarbanes-Oxley)"},
                        {"value": "pci", "label": "PCI DSS"},
                        {"value": "hipaa", "label": "HIPAA"},
                        {"value": "gdpr", "label": "GDPR"},
                        {
                            "value": "none",
                            "label": "No specific compliance requirements",
                        },
                    ],
                    "category": "Compliance",
                    "priority": 2,
                },
                "business_impact": {
                    "question": "What is the business impact if this application is unavailable?",
                    "type": "select",
                    "options": [
                        {
                            "value": "low",
                            "label": "Minimal impact - can be down for days",
                        },
                        {
                            "value": "medium",
                            "label": "Moderate impact - can be down for hours",
                        },
                        {
                            "value": "high",
                            "label": "High impact - can be down for minutes",
                        },
                        {
                            "value": "critical",
                            "label": "Critical - must be always available",
                        },
                    ],
                    "category": "Business Impact",
                    "priority": 1,
                },
                "technical_debt": {
                    "question": "How would you rate the technical debt of this application?",
                    "type": "select",
                    "options": [
                        {"value": "low", "label": "Low - well maintained, modern code"},
                        {"value": "medium", "label": "Medium - some legacy components"},
                        {"value": "high", "label": "High - significant legacy code"},
                        {
                            "value": "very_high",
                            "label": "Very High - mostly legacy, hard to maintain",
                        },
                    ],
                    "category": "Technical Quality",
                    "priority": 2,
                },
                "data_volume": {
                    "question": "What is the approximate data volume for this application?",
                    "type": "select",
                    "options": [
                        {"value": "small", "label": "Small (< 1 GB)"},
                        {"value": "medium", "label": "Medium (1-100 GB)"},
                        {"value": "large", "label": "Large (100 GB - 1 TB)"},
                        {"value": "very_large", "label": "Very Large (> 1 TB)"},
                    ],
                    "category": "Data Management",
                    "priority": 3,
                },
            }

            # Generate questions based on gaps
            for gap in information_gaps:
                gap_lower = gap.lower()

                # Match gaps to question templates
                for template_key, template in question_templates.items():
                    if template_key in gap_lower or any(
                        keyword in gap_lower for keyword in template_key.split("_")
                    ):
                        question = {
                            "id": f"{template_key}_{len(questions)}",
                            "question": template["question"],
                            "question_type": template["type"],
                            "category": template["category"],
                            "priority": template["priority"],
                            "required": template["priority"] <= 2,
                            "options": template.get("options", []),
                            "help_text": f"This information helps address: {gap}",
                        }
                        questions.append(question)
                        break

            # Add default questions if no specific gaps matched
            if not questions:
                for template_key, template in list(question_templates.items())[:3]:
                    question = {
                        "id": f"default_{template_key}",
                        "question": template["question"],
                        "question_type": template["type"],
                        "category": template["category"],
                        "priority": template["priority"],
                        "required": template["priority"] <= 2,
                        "options": template.get("options", []),
                        "help_text": "General information to improve analysis accuracy",
                    }
                    questions.append(question)

            # Sort by priority
            questions.sort(key=lambda x: x["priority"])

            return json.dumps(
                {"questions": questions, "total_count": len(questions)}, indent=2
            )

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})


class CodeAnalysisInput(BaseModel):
    """Input schema for code analysis tool."""

    file_content: str = Field(..., description="Content of uploaded code file")
    file_type: str = Field(..., description="Type of file (e.g., .java, .py, .cs)")
    analysis_type: str = Field(
        default="complexity", description="Type of analysis to perform"
    )


class CodeAnalysisTool(BaseTool):
    """Tool for analyzing uploaded code artifacts."""

    name: str = "code_analysis_tool"
    description: str = (
        "Analyze uploaded code files to assess complexity and migration factors"
    )
    args_schema: type[BaseModel] = CodeAnalysisInput

    def _run(
        self, file_content: str, file_type: str, analysis_type: str = "complexity"
    ) -> str:
        """Analyze code content for migration insights."""
        try:
            analysis_result = {
                "complexity_score": 5.0,
                "technology_indicators": [],
                "migration_challenges": [],
                "recommendations": [],
                "file_stats": {},
            }

            # Basic file statistics
            lines = file_content.split("\n")
            analysis_result["file_stats"] = {
                "total_lines": len(lines),
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "comment_lines": len(
                    [
                        line
                        for line in lines
                        if line.strip().startswith(("//", "#", "/*", "*", "<!--"))
                    ]
                ),
                "file_type": file_type,
            }

            # Technology-specific analysis
            if file_type.lower() in [".java", ".jsp"]:
                analysis_result.update(self._analyze_java_code(file_content))
            elif file_type.lower() in [".py"]:
                analysis_result.update(self._analyze_python_code(file_content))
            elif file_type.lower() in [".cs", ".vb"]:
                analysis_result.update(self._analyze_dotnet_code(file_content))
            elif file_type.lower() in [".js", ".ts"]:
                analysis_result.update(self._analyze_javascript_code(file_content))
            else:
                analysis_result.update(self._analyze_generic_code(file_content))

            return json.dumps(analysis_result, indent=2)

        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})

    def _analyze_java_code(self, content: str) -> Dict[str, Any]:
        """Analyze Java code for migration factors."""
        analysis = {
            "complexity_score": 5.0,
            "technology_indicators": ["Java"],
            "migration_challenges": [],
            "recommendations": [],
        }

        # Check for legacy Java patterns
        if "import javax.servlet" in content:
            analysis["technology_indicators"].append("Java Servlets")
            analysis["complexity_score"] += 1.0

        if "import java.sql" in content:
            analysis["technology_indicators"].append("JDBC")
            analysis["migration_challenges"].append(
                "Direct database access may need refactoring"
            )

        if "import org.springframework" in content:
            analysis["technology_indicators"].append("Spring Framework")
            analysis["recommendations"].append(
                "Spring applications often migrate well to cloud"
            )

        # Check for EJB usage
        if "@EJB" in content or "import javax.ejb" in content:
            analysis["technology_indicators"].append("Enterprise Java Beans")
            analysis["complexity_score"] += 2.0
            analysis["migration_challenges"].append(
                "EJB dependencies may require significant refactoring"
            )

        return analysis

    def _analyze_python_code(self, content: str) -> Dict[str, Any]:
        """Analyze Python code for migration factors."""
        analysis = {
            "complexity_score": 4.0,  # Python generally easier to migrate
            "technology_indicators": ["Python"],
            "migration_challenges": [],
            "recommendations": [],
        }

        # Check for web frameworks
        if "from django" in content or "import django" in content:
            analysis["technology_indicators"].append("Django")
            analysis["recommendations"].append(
                "Django applications migrate well to cloud platforms"
            )

        if "from flask" in content or "import flask" in content:
            analysis["technology_indicators"].append("Flask")
            analysis["recommendations"].append("Flask applications are cloud-friendly")

        # Check for data science libraries
        if any(
            lib in content for lib in ["pandas", "numpy", "scikit-learn", "tensorflow"]
        ):
            analysis["technology_indicators"].append("Data Science Libraries")
            analysis["recommendations"].append(
                "Consider cloud-native ML services for data science workloads"
            )

        return analysis

    def _analyze_dotnet_code(self, content: str) -> Dict[str, Any]:
        """Analyze .NET code for migration factors."""
        analysis = {
            "complexity_score": 5.0,
            "technology_indicators": [".NET"],
            "migration_challenges": [],
            "recommendations": [],
        }

        # Check for .NET Framework vs .NET Core
        if "using System.Web" in content:
            analysis["technology_indicators"].append(".NET Framework")
            analysis["complexity_score"] += 1.5
            analysis["migration_challenges"].append(
                ".NET Framework may require porting to .NET Core/.NET 5+"
            )

        if "Microsoft.AspNetCore" in content:
            analysis["technology_indicators"].append(".NET Core/5+")
            analysis["recommendations"].append(".NET Core applications are cloud-ready")

        # Check for WCF
        if "System.ServiceModel" in content:
            analysis["technology_indicators"].append("WCF")
            analysis["complexity_score"] += 2.0
            analysis["migration_challenges"].append(
                "WCF services may need to be replaced with REST APIs"
            )

        return analysis

    def _analyze_javascript_code(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code for migration factors."""
        analysis = {
            "complexity_score": 3.0,  # JavaScript generally cloud-friendly
            "technology_indicators": ["JavaScript"],
            "migration_challenges": [],
            "recommendations": [],
        }

        # Check for Node.js
        if "require(" in content or "import " in content:
            analysis["technology_indicators"].append("Node.js")
            analysis["recommendations"].append(
                "Node.js applications are highly cloud-compatible"
            )

        # Check for frontend frameworks
        if "react" in content.lower():
            analysis["technology_indicators"].append("React")
        elif "angular" in content.lower():
            analysis["technology_indicators"].append("Angular")
        elif "vue" in content.lower():
            analysis["technology_indicators"].append("Vue.js")

        return analysis

    def _analyze_generic_code(self, content: str) -> Dict[str, Any]:
        """Generic code analysis for unknown file types."""
        analysis = {
            "complexity_score": 5.0,
            "technology_indicators": ["Unknown"],
            "migration_challenges": ["Unknown technology - manual assessment required"],
            "recommendations": ["Conduct detailed technology assessment"],
        }

        # Basic complexity indicators
        if len(content) > 10000:  # Large file
            analysis["complexity_score"] += 1.0
            analysis["migration_challenges"].append(
                "Large file size may indicate complexity"
            )

        return analysis


class RecommendationValidationInput(BaseModel):
    """Input schema for recommendation validation tool."""

    recommendation: Dict[str, Any] = Field(
        ..., description="6R recommendation to validate"
    )
    application_context: Dict[str, Any] = Field(..., description="Application context")
    validation_criteria: List[str] = Field(
        default=[], description="Specific validation criteria"
    )


class RecommendationValidationTool(BaseTool):
    """Tool for validating 6R recommendations."""

    name: str = "recommendation_validation_tool"
    description: str = "Validate 6R recommendations for accuracy and feasibility"
    args_schema: type[BaseModel] = RecommendationValidationInput

    def _run(
        self,
        recommendation: Dict[str, Any],
        application_context: Dict[str, Any],
        validation_criteria: List[str] = [],
    ) -> str:
        """Validate a 6R recommendation."""
        try:
            validation_result = {
                "overall_status": "approved",
                "confidence_score": 0.8,
                "validation_checks": [],
                "warnings": [],
                "recommendations": [],
                "implementation_readiness": "ready",
            }

            # Validate strategy alignment
            strategy = recommendation.get("recommended_strategy", "")
            confidence = recommendation.get("confidence_score", 0.0)

            # Check confidence threshold
            if confidence < 0.6:
                validation_result["warnings"].append(
                    "Low confidence score - consider gathering more information"
                )
                validation_result["overall_status"] = "needs_review"

            # Strategy-specific validation
            if strategy == "retire":
                if application_context.get("business_criticality") == "high":
                    validation_result["warnings"].append(
                        "Retire recommendation for high-criticality application needs careful review"
                    )

            elif strategy == "rearchitect":
                if application_context.get("migration_urgency", 5) > 7:
                    validation_result["warnings"].append(
                        "Rearchitect strategy conflicts with high urgency requirements"
                    )

            elif strategy == "rewrite":
                if application_context.get("innovation_priority", 5) < 6:
                    validation_result["warnings"].append(
                        "Rewrite strategy requires high innovation priority and commitment"
                    )

            # Technical feasibility checks
            tech_complexity = application_context.get("technical_complexity", 5)
            if tech_complexity > 8 and strategy in [
                "refactor",
                "rearchitect",
                "rewrite",
            ]:
                validation_result["warnings"].append(
                    "High technical complexity may increase implementation risk"
                )

            # Business alignment checks
            business_value = application_context.get("business_value", 5)
            if business_value > 7 and strategy == "retire":
                validation_result["overall_status"] = "needs_revision"
                validation_result["warnings"].append(
                    "High business value conflicts with retire recommendation"
                )

            # Set final status
            if len(validation_result["warnings"]) > 2:
                validation_result["overall_status"] = "needs_review"

            if validation_result["overall_status"] == "needs_revision":
                validation_result["implementation_readiness"] = "blocked"
            elif validation_result["overall_status"] == "needs_review":
                validation_result["implementation_readiness"] = "conditional"

            return json.dumps(validation_result, indent=2)

        except Exception as e:
            logger.error(f"Recommendation validation failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})


# Tool registry for easy access
SIXR_TOOLS = {
    "cmdb_analysis": CMDBAnalysisTool,
    "parameter_scoring": ParameterScoringTool,
    "question_generation": QuestionGenerationTool,
    "code_analysis": CodeAnalysisTool,
    "recommendation_validation": RecommendationValidationTool,
}


def get_sixr_tools() -> List[BaseTool]:
    """Get all 6R analysis tools."""
    return [tool_class() for tool_class in SIXR_TOOLS.values()]


def get_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    """Get a specific tool by name."""
    tool_class = SIXR_TOOLS.get(tool_name)
    return tool_class() if tool_class else None
