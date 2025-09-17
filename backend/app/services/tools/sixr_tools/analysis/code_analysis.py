"""
Code Analysis Tool for 6R Migration Strategy Analysis.
Analyzes uploaded code files to assess complexity and migration factors.
"""

from typing import Any, Dict

from ..core.base import BaseTool, BaseModel, Field, logger, json


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
