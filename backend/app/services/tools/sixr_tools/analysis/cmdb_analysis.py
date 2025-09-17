"""
CMDB Analysis Tool for 6R Migration Strategy Analysis.
Analyzes CMDB application data to extract insights for migration strategies.
"""

from typing import Any, Dict, List

from ..core.base import BaseTool, BaseModel, Field, logger, json, get_sixr_imports


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
        # Lazy import to avoid circular dependencies
        _, _, FieldMapperService, _ = get_sixr_imports()
        if FieldMapperService:
            self.field_mapper = FieldMapperService()
        else:
            self.field_mapper = None

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
