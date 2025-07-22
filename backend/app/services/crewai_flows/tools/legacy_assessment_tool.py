"""
Legacy Assessment Tools for Technical Debt Crew
Provides specialized tools for assessing legacy technology and modernization needs
"""

import json
import logging
from typing import Any, Dict, List

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

class LegacyAssessmentTool(BaseTool):
    name: str = "legacy_assessment_tool"
    description: str = "Assesses legacy technology characteristics and modernization urgency"
    
    def _run(self, assessment_data: str) -> str:
        """
        Assess legacy technology characteristics and modernization needs
        
        Args:
            assessment_data: JSON string containing technology assessment information
            
        Returns:
            JSON string with legacy assessment results
        """
        try:
            data = json.loads(assessment_data)
            assets = data.get("assets", [])
            
            assessment_results = {
                "legacy_inventory": self._build_legacy_inventory(assets),
                "technology_age_analysis": self._analyze_technology_age(assets),
                "modernization_urgency": self._assess_modernization_urgency(assets),
                "legacy_risk_assessment": self._assess_legacy_risks(assets),
                "modernization_roadmap": self._generate_modernization_roadmap(assets)
            }
            
            return json.dumps(assessment_results)
            
        except Exception as e:
            logger.error(f"Error in legacy assessment: {e}")
            return json.dumps({"error": str(e)})
    
    def _build_legacy_inventory(self, assets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Build inventory of legacy systems by category"""
        inventory = {
            "operating_systems": [],
            "applications": [],
            "databases": [],
            "middleware": [],
            "programming_languages": []
        }
        
        legacy_indicators = {
            "operating_systems": {
                "critical": ["windows 2003", "windows xp", "centos 5", "rhel 5"],
                "high": ["windows 2008", "centos 6", "rhel 6", "ubuntu 12", "aix 6"],
                "medium": ["windows 2012", "centos 7", "rhel 7", "ubuntu 14", "solaris 10"]
            },
            "applications": {
                "critical": ["ie6", "ie7", "java 6", "java 7"],
                "high": ["java 8", "net framework 2", "net framework 3"],
                "medium": ["java 11", "net framework 4", "php 5"]
            },
            "databases": {
                "critical": ["sql server 2005", "oracle 9i", "mysql 5.0"],
                "high": ["sql server 2008", "oracle 10g", "mysql 5.1", "postgresql 8"],
                "medium": ["sql server 2012", "oracle 11g", "mysql 5.5", "postgresql 9"]
            }
        }
        
        for asset in assets:
            asset_info = str(asset).lower()
            asset_name = asset.get("name", "unknown")
            
            for category, severity_levels in legacy_indicators.items():
                for severity, technologies in severity_levels.items():
                    for tech in technologies:
                        if tech in asset_info:
                            inventory[category].append({
                                "asset": asset_name,
                                "technology": tech,
                                "severity": severity,
                                "details": self._extract_technology_details(asset, tech)
                            })
        
        return inventory
    
    def _analyze_technology_age(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the age and lifecycle status of technologies"""
        technology_age = {
            "end_of_life": [],
            "end_of_support": [],
            "extended_support": [],
            "current": [],
            "age_distribution": {}
        }
        
        # Technology lifecycle mapping (simplified)
        lifecycle_status = {
            "windows 2003": "end_of_life",
            "windows 2008": "end_of_support", 
            "windows 2012": "extended_support",
            "windows 2016": "current",
            "java 6": "end_of_life",
            "java 7": "end_of_life",
            "java 8": "extended_support",
            "java 11": "current",
            "sql server 2005": "end_of_life",
            "sql server 2008": "end_of_support",
            "sql server 2012": "extended_support"
        }
        
        for asset in assets:
            asset_info = str(asset).lower()
            asset_name = asset.get("name", "unknown")
            
            for tech, status in lifecycle_status.items():
                if tech in asset_info:
                    technology_age[status].append({
                        "asset": asset_name,
                        "technology": tech,
                        "estimated_age": self._estimate_technology_age(tech)
                    })
        
        # Calculate age distribution
        total_assets = len(assets)
        technology_age["age_distribution"] = {
            "end_of_life_percentage": (len(technology_age["end_of_life"]) / total_assets) * 100 if total_assets > 0 else 0,
            "end_of_support_percentage": (len(technology_age["end_of_support"]) / total_assets) * 100 if total_assets > 0 else 0,
            "extended_support_percentage": (len(technology_age["extended_support"]) / total_assets) * 100 if total_assets > 0 else 0,
            "current_percentage": (len(technology_age["current"]) / total_assets) * 100 if total_assets > 0 else 0
        }
        
        return technology_age
    
    def _assess_modernization_urgency(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the urgency of modernization for each asset"""
        urgency_assessment = {
            "immediate": [],
            "high": [],
            "medium": [],
            "low": [],
            "urgency_factors": {}
        }
        
        for asset in assets:
            asset_name = asset.get("name", "unknown")
            asset_info = str(asset).lower()
            
            urgency_score = 0
            factors = []
            
            # Security risk factors
            if any(tech in asset_info for tech in ["windows 2003", "windows xp", "java 6", "java 7"]):
                urgency_score += 3
                factors.append("End-of-life technology with security vulnerabilities")
            
            # Compliance risk factors
            if any(indicator in asset_info for indicator in ["pci", "hipaa", "sox", "gdpr"]):
                urgency_score += 2
                factors.append("Compliance requirements increase modernization urgency")
            
            # Business criticality factors
            if any(indicator in asset_info for indicator in ["critical", "production", "core"]):
                urgency_score += 2
                factors.append("Business critical system requires attention")
            
            # Vendor support factors
            if any(tech in asset_info for tech in ["windows 2008", "sql server 2008"]):
                urgency_score += 1
                factors.append("Limited vendor support available")
            
            # Performance factors
            if any(indicator in asset_info for indicator in ["slow", "performance", "capacity"]):
                urgency_score += 1
                factors.append("Performance issues identified")
            
            # Categorize urgency
            if urgency_score >= 5:
                urgency_level = "immediate"
            elif urgency_score >= 3:
                urgency_level = "high"
            elif urgency_score >= 1:
                urgency_level = "medium"
            else:
                urgency_level = "low"
            
            urgency_assessment[urgency_level].append(asset_name)
            urgency_assessment["urgency_factors"][asset_name] = {
                "score": urgency_score,
                "factors": factors,
                "level": urgency_level
            }
        
        return urgency_assessment
    
    def _assess_legacy_risks(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks associated with legacy systems"""
        risk_assessment = {
            "security_risks": [],
            "compliance_risks": [],
            "operational_risks": [],
            "business_risks": [],
            "overall_risk_score": 0.0
        }
        
        total_assets = len(assets)
        risk_counts = {"security": 0, "compliance": 0, "operational": 0, "business": 0}
        
        for asset in assets:
            asset_name = asset.get("name", "unknown")
            asset_info = str(asset).lower()
            
            # Security risks
            if any(tech in asset_info for tech in ["windows 2003", "windows xp", "ie6", "ie7"]):
                risk_assessment["security_risks"].append({
                    "asset": asset_name,
                    "risk": "Unpatched security vulnerabilities",
                    "severity": "critical"
                })
                risk_counts["security"] += 1
            
            # Compliance risks
            if any(indicator in asset_info for indicator in ["pci", "hipaa", "sox"]):
                if any(tech in asset_info for tech in ["windows 2008", "sql server 2008"]):
                    risk_assessment["compliance_risks"].append({
                        "asset": asset_name,
                        "risk": "Compliance framework requires supported technology",
                        "severity": "high"
                    })
                    risk_counts["compliance"] += 1
            
            # Operational risks
            if any(tech in asset_info for tech in ["windows 2003", "sql server 2005"]):
                risk_assessment["operational_risks"].append({
                    "asset": asset_name,
                    "risk": "No vendor support available",
                    "severity": "high"
                })
                risk_counts["operational"] += 1
            
            # Business risks
            if any(indicator in asset_info for indicator in ["critical", "revenue", "customer"]):
                if any(tech in asset_info for tech in ["windows 2008", "java 7"]):
                    risk_assessment["business_risks"].append({
                        "asset": asset_name,
                        "risk": "Business critical system on legacy technology",
                        "severity": "medium"
                    })
                    risk_counts["business"] += 1
        
        # Calculate overall risk score
        if total_assets > 0:
            risk_assessment["overall_risk_score"] = (
                (risk_counts["security"] * 3 + 
                 risk_counts["compliance"] * 2.5 + 
                 risk_counts["operational"] * 2 + 
                 risk_counts["business"] * 1.5) / total_assets
            )
        
        return risk_assessment
    
    def _generate_modernization_roadmap(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a high-level modernization roadmap"""
        roadmap = {
            "phase_1_immediate": [],
            "phase_2_short_term": [],
            "phase_3_medium_term": [],
            "phase_4_long_term": [],
            "modernization_strategies": {}
        }
        
        urgency_assessment = self._assess_modernization_urgency(assets)
        
        # Phase 1: Immediate (0-6 months) - Critical security and compliance
        roadmap["phase_1_immediate"] = urgency_assessment["immediate"]
        
        # Phase 2: Short-term (6-12 months) - High urgency items
        roadmap["phase_2_short_term"] = urgency_assessment["high"]
        
        # Phase 3: Medium-term (1-2 years) - Medium urgency items
        roadmap["phase_3_medium_term"] = urgency_assessment["medium"]
        
        # Phase 4: Long-term (2+ years) - Low urgency items
        roadmap["phase_4_long_term"] = urgency_assessment["low"]
        
        # Define modernization strategies for each asset
        for asset in assets:
            asset_name = asset.get("name", "unknown")
            str(asset).lower()
            
            strategy = self._recommend_modernization_strategy(asset)
            roadmap["modernization_strategies"][asset_name] = strategy
        
        return roadmap
    
    def _extract_technology_details(self, asset: Dict[str, Any], technology: str) -> Dict[str, Any]:
        """Extract detailed information about a specific technology"""
        return {
            "version": self._extract_version(asset, technology),
            "installation_date": asset.get("installation_date", "unknown"),
            "last_update": asset.get("last_update", "unknown"),
            "support_status": self._get_support_status(technology)
        }
    
    def _estimate_technology_age(self, technology: str) -> int:
        """Estimate the age of a technology in years"""
        # Simplified age estimation based on technology release dates
        age_mapping = {
            "windows 2003": 20,
            "windows 2008": 15,
            "windows 2012": 11,
            "windows 2016": 7,
            "java 6": 17,
            "java 7": 12,
            "java 8": 9,
            "java 11": 5,
            "sql server 2005": 18,
            "sql server 2008": 15,
            "sql server 2012": 11
        }
        
        return age_mapping.get(technology, 0)
    
    def _extract_version(self, asset: Dict[str, Any], technology: str) -> str:
        """Extract version information for a technology"""
        # Simplified version extraction
        asset_info = str(asset).lower()
        
        if technology in asset_info:
            # Look for version patterns near the technology name
            words = asset_info.split()
            tech_index = -1
            
            for i, word in enumerate(words):
                if technology.replace(" ", "") in word.replace(" ", ""):
                    tech_index = i
                    break
            
            if tech_index != -1 and tech_index + 1 < len(words):
                next_word = words[tech_index + 1]
                if any(char.isdigit() for char in next_word):
                    return next_word
        
        return "unknown"
    
    def _get_support_status(self, technology: str) -> str:
        """Get vendor support status for a technology"""
        support_mapping = {
            "windows 2003": "End of Life",
            "windows 2008": "End of Support", 
            "windows 2012": "Extended Support",
            "windows 2016": "Mainstream Support",
            "java 6": "End of Life",
            "java 7": "End of Life",
            "java 8": "Extended Support",
            "java 11": "Active Support"
        }
        
        return support_mapping.get(technology, "Unknown")
    
    def _recommend_modernization_strategy(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend 6R modernization strategy for an asset"""
        asset_info = str(asset).lower()
        
        # Default strategy
        strategy = {
            "primary_strategy": "rehost",
            "rationale": "Standard lift-and-shift migration",
            "complexity": "low",
            "estimated_effort": "weeks"
        }
        
        # Replatform indicators
        if any(indicator in asset_info for indicator in ["database", "middleware"]):
            strategy = {
                "primary_strategy": "replatform",
                "rationale": "Platform modernization opportunities identified",
                "complexity": "medium",
                "estimated_effort": "months"
            }
        
        # Refactor indicators
        if any(indicator in asset_info for indicator in ["monolith", "legacy_code", "performance"]):
            strategy = {
                "primary_strategy": "refactor",
                "rationale": "Code modernization required for performance and maintainability",
                "complexity": "high",
                "estimated_effort": "months"
            }
        
        # Rearchitect indicators
        if any(indicator in asset_info for indicator in ["distributed", "microservices", "cloud_native"]):
            strategy = {
                "primary_strategy": "rearchitect",
                "rationale": "Architecture transformation for cloud-native benefits",
                "complexity": "very_high",
                "estimated_effort": "quarters"
            }
        
        # Retire indicators
        if any(indicator in asset_info for indicator in ["deprecated", "unused", "redundant"]):
            strategy = {
                "primary_strategy": "retire",
                "rationale": "Asset identified as candidate for retirement",
                "complexity": "low",
                "estimated_effort": "weeks"
            }
        
        # Retain indicators
        if any(indicator in asset_info for indicator in ["compliance", "specialized", "recent"]):
            strategy = {
                "primary_strategy": "retain",
                "rationale": "Asset should remain in current environment",
                "complexity": "none",
                "estimated_effort": "none"
            }
        
        return strategy

class TechnologyAnalysisTool(BaseTool):
    name: str = "technology_analysis_tool"
    description: str = "Analyzes technology stack composition and modernization patterns"
    
    def _run(self, technology_data: str) -> str:
        """
        Analyze technology stack and identify modernization patterns
        
        Args:
            technology_data: JSON string containing technology stack information
            
        Returns:
            JSON string with technology analysis results
        """
        try:
            data = json.loads(technology_data)
            assets = data.get("assets", [])
            
            analysis_results = {
                "technology_inventory": self._build_technology_inventory(assets),
                "stack_analysis": self._analyze_technology_stacks(assets),
                "modernization_patterns": self._identify_modernization_patterns(assets),
                "technology_dependencies": self._map_technology_dependencies(assets)
            }
            
            return json.dumps(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in technology analysis: {e}")
            return json.dumps({"error": str(e)})
    
    def _build_technology_inventory(self, assets: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Build comprehensive technology inventory"""
        inventory = {
            "operating_systems": {},
            "programming_languages": {},
            "databases": {},
            "web_servers": {},
            "application_servers": {},
            "frameworks": {}
        }
        
        technology_patterns = {
            "operating_systems": ["windows", "linux", "unix", "aix", "solaris"],
            "programming_languages": ["java", "c#", "python", "javascript", "php", "ruby"],
            "databases": ["sql server", "oracle", "mysql", "postgresql", "mongodb"],
            "web_servers": ["apache", "nginx", "iis"],
            "application_servers": ["tomcat", "jboss", "websphere", "weblogic"],
            "frameworks": ["spring", "dotnet", "rails", "django", "angular", "react"]
        }
        
        for asset in assets:
            asset_info = str(asset).lower()
            
            for category, technologies in technology_patterns.items():
                for tech in technologies:
                    if tech in asset_info:
                        inventory[category][tech] = inventory[category].get(tech, 0) + 1
        
        return inventory
    
    def _analyze_technology_stacks(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze common technology stack patterns"""
        stacks = {
            "lamp_stack": 0,
            "mean_stack": 0,
            "microsoft_stack": 0,
            "java_enterprise": 0,
            "cloud_native": 0
        }
        
        for asset in assets:
            asset_info = str(asset).lower()
            
            # LAMP stack (Linux, Apache, MySQL, PHP)
            if all(tech in asset_info for tech in ["linux", "apache", "mysql", "php"]):
                stacks["lamp_stack"] += 1
            
            # MEAN stack (MongoDB, Express, Angular, Node.js)
            elif all(tech in asset_info for tech in ["mongodb", "express", "angular", "node"]):
                stacks["mean_stack"] += 1
            
            # Microsoft stack
            elif any(tech in asset_info for tech in ["windows", "iis", "sql server", "dotnet"]):
                stacks["microsoft_stack"] += 1
            
            # Java Enterprise
            elif any(tech in asset_info for tech in ["java", "jboss", "websphere", "spring"]):
                stacks["java_enterprise"] += 1
            
            # Cloud Native
            elif any(tech in asset_info for tech in ["docker", "kubernetes", "microservice"]):
                stacks["cloud_native"] += 1
        
        return {
            "stack_distribution": stacks,
            "dominant_stack": max(stacks, key=stacks.get) if any(stacks.values()) else "mixed"
        }
    
    def _identify_modernization_patterns(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify technology modernization patterns and opportunities"""
        patterns = {
            "containerization_candidates": [],
            "cloud_migration_candidates": [],
            "microservices_candidates": [],
            "database_modernization_candidates": [],
            "legacy_replacement_candidates": []
        }
        
        for asset in assets:
            asset_name = asset.get("name", "unknown")
            asset_info = str(asset).lower()
            
            # Containerization candidates
            if any(tech in asset_info for tech in ["java", "nodejs", "python", "ruby"]) and "docker" not in asset_info:
                patterns["containerization_candidates"].append(asset_name)
            
            # Cloud migration candidates  
            if any(tech in asset_info for tech in ["stateless", "api", "web"]) and "cloud" not in asset_info:
                patterns["cloud_migration_candidates"].append(asset_name)
            
            # Microservices candidates
            if any(tech in asset_info for tech in ["monolith", "large", "coupled"]):
                patterns["microservices_candidates"].append(asset_name)
            
            # Database modernization candidates
            if any(tech in asset_info for tech in ["sql server 2008", "oracle 10g", "mysql 5"]):
                patterns["database_modernization_candidates"].append(asset_name)
            
            # Legacy replacement candidates
            if any(tech in asset_info for tech in ["cobol", "fortran", "mainframe"]):
                patterns["legacy_replacement_candidates"].append(asset_name)
        
        return patterns
    
    def _map_technology_dependencies(self, assets: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Map dependencies between technologies"""
        dependencies = {}
        
        for asset in assets:
            asset_name = asset.get("name", "unknown")
            asset_info = str(asset).lower()
            asset_dependencies = []
            
            # Common technology dependencies
            if "java" in asset_info:
                asset_dependencies.append("JVM")
                if "spring" in asset_info:
                    asset_dependencies.append("Spring Framework")
            
            if "dotnet" in asset_info:
                asset_dependencies.append(".NET Framework")
                if "windows" in asset_info:
                    asset_dependencies.append("Windows OS")
            
            if any(db in asset_info for db in ["mysql", "postgresql", "oracle"]):
                asset_dependencies.append("Database Server")
            
            if any(web in asset_info for web in ["apache", "nginx", "iis"]):
                asset_dependencies.append("Web Server")
            
            dependencies[asset_name] = asset_dependencies
        
        return dependencies 