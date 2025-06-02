"""
Tech Debt Analysis Agent
Advanced AI agent for comprehensive tech debt assessment and intelligent risk analysis.
Provides OS version analysis, application lifecycle assessment, and business-aligned risk prioritization.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class TechDebtAnalysisAgent:
    """
    Advanced AI agent that provides comprehensive tech debt intelligence including:
    - OS versions and application versions analysis across all data
    - Intelligent tech debt risk assessment based on business context
    - Agent learning from stakeholder risk tolerance and requirements
    - Dynamic tech debt prioritization based on migration strategy and costs
    """
    
    def __init__(self):
        self.agent_id = "tech_debt_analysis"
        self.agent_name = "Tech Debt Analysis Agent"
        self.confidence_threshold = 0.75
        self.learning_enabled = True
        
        # Tech debt patterns and learning
        self.tech_debt_patterns = {
            "os_lifecycle_patterns": {},
            "application_risk_patterns": {},
            "business_risk_tolerance": {},
            "migration_cost_patterns": {}
        }
        
        # Known tech debt categories
        self.tech_debt_categories = {
            "operating_system": {
                "critical_indicators": ["end_of_life", "unsupported", "legacy"],
                "risk_factors": ["security_vulnerabilities", "compliance_issues", "vendor_support"]
            },
            "application_versions": {
                "critical_indicators": ["deprecated", "end_of_support", "security_risk"],
                "risk_factors": ["compatibility_issues", "maintenance_cost", "upgrade_complexity"]
            },
            "infrastructure": {
                "critical_indicators": ["hardware_eol", "firmware_outdated", "capacity_limits"],
                "risk_factors": ["performance_degradation", "reliability_issues", "scalability_constraints"]
            },
            "security": {
                "critical_indicators": ["unpatched_vulnerabilities", "weak_authentication", "data_exposure"],
                "risk_factors": ["compliance_violations", "breach_risk", "audit_findings"]
            }
        }
        
        # Risk assessment thresholds
        self.risk_thresholds = {
            "critical": 0.8,
            "high": 0.6,
            "medium": 0.4,
            "low": 0.2
        }
        
        self._load_tech_debt_intelligence()
    
    async def analyze_tech_debt(self, assets: List[Dict[str, Any]], 
                              stakeholder_context: Optional[Dict[str, Any]] = None,
                              migration_timeline: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive tech debt analysis across all assets.
        
        Args:
            assets: List of assets to analyze for tech debt
            stakeholder_context: Business context and risk tolerance
            migration_timeline: Planned migration timeline for prioritization
            
        Returns:
            Comprehensive tech debt analysis with risk assessment
        """
        try:
            logger.info(f"Starting tech debt analysis for {len(assets)} assets")
            
            # Step 1: Analyze OS versions and lifecycle status
            os_analysis = await self._analyze_operating_systems(assets)
            
            # Step 2: Analyze application versions and support status
            app_analysis = await self._analyze_application_versions(assets)
            
            # Step 3: Assess infrastructure tech debt
            infrastructure_analysis = await self._analyze_infrastructure_debt(assets)
            
            # Step 4: Security-related tech debt assessment
            security_analysis = await self._analyze_security_debt(assets)
            
            # Step 5: Business context integration
            business_risk_assessment = await self._assess_business_risk_context(
                {
                    "os_analysis": os_analysis,
                    "app_analysis": app_analysis,
                    "infrastructure_analysis": infrastructure_analysis,
                    "security_analysis": security_analysis
                },
                stakeholder_context,
                migration_timeline
            )
            
            # Step 6: Dynamic prioritization
            prioritized_debt = await self._prioritize_tech_debt(
                business_risk_assessment, stakeholder_context, migration_timeline
            )
            
            # Step 7: Generate stakeholder questions
            stakeholder_questions = await self._generate_stakeholder_questions(
                prioritized_debt, stakeholder_context, migration_timeline
            )
            
            tech_debt_intelligence = {
                "tech_debt_analysis": {
                    "total_assets_analyzed": len(assets),
                    "os_analysis": os_analysis,
                    "application_analysis": app_analysis,
                    "infrastructure_analysis": infrastructure_analysis,
                    "security_analysis": security_analysis,
                    "overall_risk_score": self._calculate_overall_risk_score(business_risk_assessment)
                },
                "business_risk_assessment": business_risk_assessment,
                "prioritized_tech_debt": prioritized_debt,
                "stakeholder_questions": stakeholder_questions,
                "migration_recommendations": await self._generate_migration_recommendations(
                    prioritized_debt, migration_timeline
                ),
                "intelligence_metadata": {
                    "analysis_confidence": self._calculate_analysis_confidence(prioritized_debt),
                    "business_alignment_score": self._calculate_business_alignment(business_risk_assessment),
                    "stakeholder_input_needed": len(stakeholder_questions),
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Tech debt analysis completed with {len(prioritized_debt)} prioritized items")
            return tech_debt_intelligence
            
        except Exception as e:
            logger.error(f"Error in tech debt analysis: {e}")
            return {
                "tech_debt_analysis": {"total_assets_analyzed": 0, "error": str(e)},
                "business_risk_assessment": {},
                "prioritized_tech_debt": [],
                "stakeholder_questions": []
            }
    
    async def process_stakeholder_risk_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process stakeholder feedback on risk tolerance and business requirements.
        
        Args:
            feedback: Stakeholder feedback on risk assessment
            
        Returns:
            Learning processing results
        """
        try:
            feedback_type = feedback.get("feedback_type", "risk_tolerance")
            risk_item_id = feedback.get("risk_item_id")
            original_assessment = feedback.get("original_assessment", {})
            stakeholder_input = feedback.get("stakeholder_input", {})
            
            learning_result = {
                "feedback_processed": True,
                "learning_applied": False,
                "risk_tolerance_updated": False,
                "prioritization_adjusted": False
            }
            
            if feedback_type == "risk_tolerance":
                # Learn from risk tolerance feedback
                learning_result = await self._learn_risk_tolerance(
                    risk_item_id, original_assessment, stakeholder_input
                )
            
            elif feedback_type == "business_priority":
                # Learn from business priority adjustments
                learning_result = await self._learn_business_priorities(
                    risk_item_id, original_assessment, stakeholder_input
                )
            
            elif feedback_type == "migration_timeline":
                # Learn from migration timeline constraints
                learning_result = await self._learn_timeline_constraints(
                    risk_item_id, original_assessment, stakeholder_input
                )
            
            # Store learning experience
            self._store_stakeholder_learning(feedback, learning_result)
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Error processing stakeholder feedback: {e}")
            return {
                "feedback_processed": False,
                "error": str(e)
            }
    
    async def _analyze_operating_systems(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze operating system versions and lifecycle status."""
        os_analysis = {
            "os_inventory": {},
            "lifecycle_status": {},
            "risk_assessment": {},
            "upgrade_recommendations": []
        }
        
        for asset in assets:
            os_info = self._extract_os_information(asset)
            if os_info:
                os_name = os_info.get("os_name", "unknown")
                os_version = os_info.get("os_version", "unknown")
                
                # Track OS inventory
                os_key = f"{os_name}_{os_version}"
                if os_key not in os_analysis["os_inventory"]:
                    os_analysis["os_inventory"][os_key] = {
                        "os_name": os_name,
                        "os_version": os_version,
                        "asset_count": 0,
                        "assets": []
                    }
                
                os_analysis["os_inventory"][os_key]["asset_count"] += 1
                os_analysis["os_inventory"][os_key]["assets"].append(asset.get("id", "unknown"))
                
                # Assess lifecycle status
                lifecycle_status = self._assess_os_lifecycle(os_name, os_version)
                os_analysis["lifecycle_status"][os_key] = lifecycle_status
                
                # Risk assessment
                risk_score = self._calculate_os_risk_score(lifecycle_status, os_info)
                os_analysis["risk_assessment"][os_key] = risk_score
        
        # Generate upgrade recommendations
        os_analysis["upgrade_recommendations"] = self._generate_os_upgrade_recommendations(
            os_analysis["os_inventory"], os_analysis["lifecycle_status"]
        )
        
        return os_analysis
    
    async def _analyze_application_versions(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze application versions and support lifecycle status."""
        app_analysis = {
            "application_inventory": {},
            "support_status": {},
            "version_risks": {},
            "upgrade_priorities": []
        }
        
        for asset in assets:
            applications = self._extract_application_information(asset)
            for app_info in applications:
                app_name = app_info.get("name", "unknown")
                app_version = app_info.get("version", "unknown")
                
                # Track application inventory
                app_key = f"{app_name}_{app_version}"
                if app_key not in app_analysis["application_inventory"]:
                    app_analysis["application_inventory"][app_key] = {
                        "name": app_name,
                        "version": app_version,
                        "asset_count": 0,
                        "assets": []
                    }
                
                app_analysis["application_inventory"][app_key]["asset_count"] += 1
                app_analysis["application_inventory"][app_key]["assets"].append(asset.get("id", "unknown"))
                
                # Assess support status
                support_status = self._assess_application_support_status(app_name, app_version)
                app_analysis["support_status"][app_key] = support_status
                
                # Version risk assessment
                version_risk = self._calculate_application_risk_score(support_status, app_info)
                app_analysis["version_risks"][app_key] = version_risk
        
        # Generate upgrade priorities
        app_analysis["upgrade_priorities"] = self._generate_application_upgrade_priorities(
            app_analysis["application_inventory"], app_analysis["version_risks"]
        )
        
        return app_analysis
    
    async def _analyze_infrastructure_debt(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze infrastructure-related tech debt."""
        infrastructure_analysis = {
            "hardware_lifecycle": {},
            "capacity_constraints": {},
            "performance_issues": {},
            "modernization_opportunities": []
        }
        
        for asset in assets:
            # Hardware lifecycle analysis
            hardware_info = self._extract_hardware_information(asset)
            if hardware_info:
                hardware_age = self._calculate_hardware_age(hardware_info)
                infrastructure_analysis["hardware_lifecycle"][asset.get("id", "unknown")] = {
                    "age_years": hardware_age,
                    "lifecycle_stage": self._determine_hardware_lifecycle_stage(hardware_age),
                    "replacement_priority": self._calculate_replacement_priority(hardware_info, hardware_age)
                }
            
            # Capacity constraints
            capacity_info = self._analyze_capacity_constraints(asset)
            if capacity_info:
                infrastructure_analysis["capacity_constraints"][asset.get("id", "unknown")] = capacity_info
            
            # Performance issues
            performance_info = self._analyze_performance_indicators(asset)
            if performance_info:
                infrastructure_analysis["performance_issues"][asset.get("id", "unknown")] = performance_info
        
        # Generate modernization opportunities
        infrastructure_analysis["modernization_opportunities"] = self._identify_modernization_opportunities(
            infrastructure_analysis
        )
        
        return infrastructure_analysis
    
    async def _analyze_security_debt(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security-related tech debt."""
        security_analysis = {
            "vulnerability_assessment": {},
            "compliance_gaps": {},
            "security_controls": {},
            "remediation_priorities": []
        }
        
        for asset in assets:
            asset_id = asset.get("id", "unknown")
            
            # Vulnerability assessment
            vulnerabilities = self._assess_security_vulnerabilities(asset)
            if vulnerabilities:
                security_analysis["vulnerability_assessment"][asset_id] = vulnerabilities
            
            # Compliance gaps
            compliance_status = self._assess_compliance_status(asset)
            if compliance_status:
                security_analysis["compliance_gaps"][asset_id] = compliance_status
            
            # Security controls
            security_controls = self._evaluate_security_controls(asset)
            if security_controls:
                security_analysis["security_controls"][asset_id] = security_controls
        
        # Generate remediation priorities
        security_analysis["remediation_priorities"] = self._prioritize_security_remediation(
            security_analysis
        )
        
        return security_analysis
    
    async def _assess_business_risk_context(self, technical_analysis: Dict[str, Any],
                                          stakeholder_context: Optional[Dict[str, Any]],
                                          migration_timeline: Optional[str]) -> Dict[str, Any]:
        """Assess tech debt in business context."""
        business_risk = {
            "risk_categories": {},
            "business_impact": {},
            "cost_implications": {},
            "timeline_constraints": {}
        }
        
        # Categorize risks by business impact
        for category, analysis in technical_analysis.items():
            business_risk["risk_categories"][category] = self._categorize_business_risk(
                analysis, stakeholder_context
            )
        
        # Assess business impact
        business_risk["business_impact"] = self._assess_business_impact(
            technical_analysis, stakeholder_context
        )
        
        # Calculate cost implications
        business_risk["cost_implications"] = self._calculate_cost_implications(
            technical_analysis, migration_timeline
        )
        
        # Timeline constraints
        if migration_timeline:
            business_risk["timeline_constraints"] = self._assess_timeline_constraints(
                technical_analysis, migration_timeline
            )
        
        return business_risk
    
    async def _prioritize_tech_debt(self, business_risk_assessment: Dict[str, Any],
                                  stakeholder_context: Optional[Dict[str, Any]],
                                  migration_timeline: Optional[str]) -> List[Dict[str, Any]]:
        """Dynamically prioritize tech debt based on business context."""
        prioritized_items = []
        
        # Extract all risk items from business assessment
        for category, risks in business_risk_assessment.get("risk_categories", {}).items():
            for risk_item in risks.get("items", []):
                priority_score = self._calculate_priority_score(
                    risk_item, stakeholder_context, migration_timeline
                )
                
                prioritized_items.append({
                    "category": category,
                    "risk_item": risk_item,
                    "priority_score": priority_score,
                    "business_justification": self._generate_business_justification(risk_item),
                    "recommended_action": self._recommend_action(risk_item, migration_timeline)
                })
        
        # Sort by priority score (highest first)
        prioritized_items.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return prioritized_items
    
    async def _generate_stakeholder_questions(self, prioritized_debt: List[Dict[str, Any]],
                                            stakeholder_context: Optional[Dict[str, Any]],
                                            migration_timeline: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate questions for stakeholder input on risk tolerance."""
        questions = []
        
        # Questions about high-priority items
        high_priority_items = [item for item in prioritized_debt if item["priority_score"] > 0.7]
        for item in high_priority_items[:5]:  # Limit to top 5
            questions.append({
                "question_id": f"risk_tolerance_{item['risk_item'].get('id', 'unknown')}",
                "question_type": "risk_tolerance",
                "title": f"Risk Tolerance: {item['category'].title()} Issue",
                "question": f"What is your organization's tolerance for the {item['category']} risk: {item['risk_item'].get('description', 'Unknown risk')}?",
                "risk_item": item["risk_item"],
                "options": ["Acceptable", "Needs Attention", "Migration Blocker"],
                "business_context": item["business_justification"],
                "priority": "high"
            })
        
        # Questions about business priorities
        if not stakeholder_context or not stakeholder_context.get("business_priorities"):
            questions.append({
                "question_id": "business_priorities_general",
                "question_type": "business_priority",
                "title": "Business Priority Assessment",
                "question": "What are your organization's top priorities for this migration?",
                "options": ["Cost Reduction", "Security Improvement", "Performance Enhancement", "Compliance", "Innovation"],
                "priority": "medium"
            })
        
        # Questions about migration timeline constraints
        if not migration_timeline:
            questions.append({
                "question_id": "migration_timeline_constraints",
                "question_type": "migration_timeline",
                "title": "Migration Timeline Constraints",
                "question": "What are your timeline constraints for addressing critical tech debt?",
                "options": ["Immediate (< 3 months)", "Short-term (3-6 months)", "Medium-term (6-12 months)", "Long-term (> 12 months)"],
                "priority": "medium"
            })
        
        return questions
    
    async def _generate_migration_recommendations(self, prioritized_debt: List[Dict[str, Any]],
                                                migration_timeline: Optional[str]) -> List[Dict[str, Any]]:
        """Generate actionable migration recommendations."""
        recommendations = []
        
        # Critical items requiring immediate attention
        critical_items = [item for item in prioritized_debt if item["priority_score"] > 0.8]
        if critical_items:
            recommendations.append({
                "category": "critical_tech_debt",
                "priority": "critical",
                "title": f"Address {len(critical_items)} Critical Tech Debt Items",
                "description": "Critical tech debt items that could block migration success",
                "actions": [
                    "Prioritize remediation of critical security vulnerabilities",
                    "Plan immediate upgrades for end-of-life operating systems",
                    "Assess business impact of delaying migration for critical items"
                ],
                "timeline": "Immediate (before migration planning)",
                "affected_items": len(critical_items)
            })
        
        # OS modernization recommendations
        os_items = [item for item in prioritized_debt if item["category"] == "os_analysis"]
        if os_items:
            recommendations.append({
                "category": "os_modernization",
                "priority": "high",
                "title": f"Operating System Modernization for {len(os_items)} Systems",
                "description": "Upgrade legacy operating systems to supported versions",
                "actions": [
                    "Create OS upgrade roadmap aligned with migration timeline",
                    "Test application compatibility with target OS versions",
                    "Plan phased OS upgrades to minimize business disruption"
                ],
                "timeline": migration_timeline or "Medium-term (6-12 months)",
                "affected_items": len(os_items)
            })
        
        return recommendations
    
    # Helper methods for tech debt analysis
    def _extract_os_information(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract OS information from asset data."""
        os_info = {}
        
        # Check various OS fields
        if asset.get("operating_system"):
            os_info["os_name"] = asset["operating_system"]
        elif asset.get("os"):
            os_info["os_name"] = asset["os"]
        
        # Check for version information in various fields
        if asset.get("os_version"):
            os_info["os_version"] = asset["os_version"]
        elif asset.get("version"):
            os_info["os_version"] = asset["version"]
        elif asset.get("version/hostname"):
            # Extract version from version/hostname field if it contains version info
            version_hostname = asset["version/hostname"]
            if version_hostname and any(char.isdigit() for char in str(version_hostname)):
                os_info["os_version"] = str(version_hostname)
        
        # Add asset metadata
        if os_info:
            os_info["asset_id"] = asset.get("id", "unknown")
            os_info["asset_name"] = asset.get("name", asset.get("asset_name", "unknown"))
            os_info["asset_type"] = asset.get("asset_type", asset.get("type", "unknown"))
        
        return os_info if os_info else None
    
    def _extract_application_information(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract application information from asset data."""
        applications = []
        
        # Check for software installed
        if asset.get("software_installed"):
            software_list = asset["software_installed"]
            if isinstance(software_list, str):
                # Parse software string
                for software in software_list.split(","):
                    software = software.strip()
                    if software:
                        applications.append({"name": software, "version": "unknown"})
            elif isinstance(software_list, list):
                for software in software_list:
                    if isinstance(software, dict):
                        applications.append(software)
                    else:
                        applications.append({"name": str(software), "version": "unknown"})
        
        return applications
    
    def _assess_os_lifecycle(self, os_name: str, os_version: str) -> Dict[str, Any]:
        """Assess OS lifecycle status."""
        # Default lifecycle assessment
        lifecycle_status = {
            "status": "supported",
            "end_of_life_date": None,
            "support_level": "full",
            "risk_level": "low"
        }
        
        os_name_lower = os_name.lower()
        
        # Windows Server lifecycle assessment
        if "windows server" in os_name_lower:
            if "2008" in os_name_lower or "2003" in os_name_lower:
                lifecycle_status.update({
                    "status": "end_of_life",
                    "end_of_life_date": "2020-01-14",
                    "support_level": "none",
                    "risk_level": "critical"
                })
            elif "2012" in os_name_lower:
                lifecycle_status.update({
                    "status": "end_of_life",
                    "end_of_life_date": "2023-10-10",
                    "support_level": "none",
                    "risk_level": "critical"
                })
            elif "2016" in os_name_lower:
                lifecycle_status.update({
                    "status": "extended_support",
                    "end_of_life_date": "2027-01-12",
                    "support_level": "security_only",
                    "risk_level": "high"
                })
            elif "2019" in os_name_lower:
                lifecycle_status.update({
                    "status": "supported",
                    "end_of_life_date": "2029-01-09",
                    "support_level": "full",
                    "risk_level": "low"
                })
            elif "windows server" in os_name_lower and not any(year in os_name_lower for year in ["2016", "2019", "2022"]):
                # Generic Windows Server without version - assume legacy
                lifecycle_status.update({
                    "status": "unknown_version",
                    "support_level": "unknown",
                    "risk_level": "high"
                })
        
        # Red Hat Enterprise Linux lifecycle assessment
        elif "red hat" in os_name_lower or "rhel" in os_name_lower:
            if "6" in os_name_lower:
                lifecycle_status.update({
                    "status": "end_of_life",
                    "end_of_life_date": "2020-11-30",
                    "support_level": "none",
                    "risk_level": "critical"
                })
            elif "7" in os_name_lower:
                lifecycle_status.update({
                    "status": "extended_support",
                    "end_of_life_date": "2024-06-30",
                    "support_level": "security_only",
                    "risk_level": "medium"
                })
            elif "8" in os_name_lower:
                lifecycle_status.update({
                    "status": "supported",
                    "end_of_life_date": "2029-05-31",
                    "support_level": "full",
                    "risk_level": "low"
                })
            elif "red hat" in os_name_lower and not any(ver in os_name_lower for ver in ["7", "8", "9"]):
                # Generic RHEL without version - assume legacy
                lifecycle_status.update({
                    "status": "unknown_version",
                    "support_level": "unknown",
                    "risk_level": "high"
                })
        
        # Ubuntu Server lifecycle assessment
        elif "ubuntu" in os_name_lower:
            if "16.04" in os_name_lower:
                lifecycle_status.update({
                    "status": "end_of_life",
                    "end_of_life_date": "2024-04-30",
                    "support_level": "none",
                    "risk_level": "medium"
                })
            elif "18.04" in os_name_lower:
                lifecycle_status.update({
                    "status": "supported",
                    "end_of_life_date": "2028-04-30",
                    "support_level": "full",
                    "risk_level": "low"
                })
            elif "20.04" in os_name_lower or "22.04" in os_name_lower:
                lifecycle_status.update({
                    "status": "supported",
                    "support_level": "full",
                    "risk_level": "low"
                })
        
        # Cisco IOS lifecycle assessment
        elif "cisco ios" in os_name_lower or "ios" in os_name_lower:
            lifecycle_status.update({
                "status": "version_check_needed",
                "support_level": "unknown",
                "risk_level": "medium"
            })
        
        # Unknown OS
        elif "unknown" in os_name_lower:
            lifecycle_status.update({
                "status": "unknown_os",
                "support_level": "unknown",
                "risk_level": "high"
            })
        
        return lifecycle_status
    
    def _calculate_os_risk_score(self, lifecycle_status: Dict[str, Any], os_info: Dict[str, Any]) -> float:
        """Calculate risk score for OS."""
        base_score = 0.0
        
        if lifecycle_status["status"] == "end_of_life":
            base_score = 0.9
        elif lifecycle_status["status"] == "extended_support":
            base_score = 0.7
        elif lifecycle_status["status"] == "mainstream_support":
            base_score = 0.3
        else:
            base_score = 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_overall_risk_score(self, business_risk_assessment: Dict[str, Any]) -> float:
        """Calculate overall tech debt risk score."""
        risk_scores = []
        
        for category, risks in business_risk_assessment.get("risk_categories", {}).items():
            if isinstance(risks, dict) and "average_risk" in risks:
                risk_scores.append(risks["average_risk"])
        
        return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
    
    def _calculate_analysis_confidence(self, prioritized_debt: List[Dict[str, Any]]) -> float:
        """Calculate confidence in tech debt analysis."""
        if not prioritized_debt:
            return 0.0
        
        confidence_scores = [item.get("confidence", 0.5) for item in prioritized_debt]
        return sum(confidence_scores) / len(confidence_scores)
    
    def _calculate_business_alignment(self, business_risk_assessment: Dict[str, Any]) -> float:
        """Calculate business alignment score."""
        # Simplified business alignment calculation
        return 0.75  # Placeholder
    
    # Placeholder methods for comprehensive implementation
    def _extract_hardware_information(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract hardware information."""
        return None  # Simplified
    
    def _calculate_hardware_age(self, hardware_info: Dict[str, Any]) -> float:
        """Calculate hardware age."""
        return 3.0  # Simplified
    
    def _assess_application_support_status(self, app_name: str, app_version: str) -> Dict[str, Any]:
        """Assess application support status."""
        return {"status": "supported", "risk_level": "low"}  # Simplified
    
    def _calculate_application_risk_score(self, support_status: Dict[str, Any], app_info: Dict[str, Any]) -> float:
        """Calculate application risk score."""
        return 0.3  # Simplified
    
    def _load_tech_debt_intelligence(self):
        """Load existing tech debt intelligence patterns."""
        pass  # Simplified
    
    def _store_stakeholder_learning(self, feedback: Dict[str, Any], learning_result: Dict[str, Any]):
        """Store stakeholder learning experience."""
        pass  # Simplified

    # Additional placeholder methods for complete implementation
    def _generate_os_upgrade_recommendations(self, os_inventory: Dict, lifecycle_status: Dict) -> List[str]:
        """Generate OS upgrade recommendations."""
        return ["Upgrade legacy Windows Server 2008 systems", "Plan OS modernization roadmap"]

    def _generate_application_upgrade_priorities(self, app_inventory: Dict, version_risks: Dict) -> List[str]:
        """Generate application upgrade priorities."""
        return ["Prioritize critical application updates", "Plan application compatibility testing"]

    def _determine_hardware_lifecycle_stage(self, hardware_age: float) -> str:
        """Determine hardware lifecycle stage."""
        if hardware_age > 5:
            return "end_of_life"
        elif hardware_age > 3:
            return "mature"
        else:
            return "current"

    def _calculate_replacement_priority(self, hardware_info: Dict, hardware_age: float) -> str:
        """Calculate hardware replacement priority."""
        return "high" if hardware_age > 4 else "medium"

    def _analyze_capacity_constraints(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze capacity constraints."""
        return None  # Simplified

    def _analyze_performance_indicators(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze performance indicators."""
        return None  # Simplified

    def _identify_modernization_opportunities(self, infrastructure_analysis: Dict) -> List[str]:
        """Identify modernization opportunities."""
        return ["Cloud migration opportunities", "Infrastructure consolidation potential"]

    def _assess_security_vulnerabilities(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess security vulnerabilities."""
        return None  # Simplified

    def _assess_compliance_status(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess compliance status."""
        return None  # Simplified

    def _evaluate_security_controls(self, asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate security controls."""
        return None  # Simplified

    def _prioritize_security_remediation(self, security_analysis: Dict) -> List[str]:
        """Prioritize security remediation."""
        return ["Address critical vulnerabilities", "Implement security controls"]

    def _categorize_business_risk(self, analysis: Dict, stakeholder_context: Optional[Dict]) -> Dict[str, Any]:
        """Categorize business risk."""
        risk_items = []
        risk_scores = []
        
        # Process OS analysis results
        if "os_inventory" in analysis:
            for os_key, os_data in analysis["os_inventory"].items():
                lifecycle_status = analysis.get("lifecycle_status", {}).get(os_key, {})
                risk_score = analysis.get("risk_assessment", {}).get(os_key, 0.5)
                
                if lifecycle_status.get("risk_level") in ["high", "critical"]:
                    risk_items.append({
                        "id": f"os_risk_{os_key}",
                        "asset_id": os_data.get("assets", ["unknown"])[0],
                        "asset_name": os_data.get("os_name", "Unknown OS"),
                        "category": "operating_system",
                        "technology": os_data.get("os_name", "Unknown"),
                        "current_version": os_data.get("os_version", "Unknown"),
                        "latest_version": self._get_latest_os_version(os_data.get("os_name", "")),
                        "support_status": lifecycle_status.get("status", "unknown"),
                        "end_of_life_date": lifecycle_status.get("end_of_life_date"),
                        "risk_level": lifecycle_status.get("risk_level", "medium"),
                        "migration_effort": self._assess_migration_effort(lifecycle_status),
                        "business_impact": self._assess_business_impact_level(risk_score),
                        "recommended_action": self._generate_os_recommendation(lifecycle_status),
                        "dependencies": [],
                        "description": f"{os_data.get('os_name', 'Unknown OS')} requires attention due to {lifecycle_status.get('status', 'unknown status')}",
                        "confidence": 0.8
                    })
                    risk_scores.append(risk_score)
        
        # Process application analysis results
        if "application_inventory" in analysis:
            for app_key, app_data in analysis["application_inventory"].items():
                support_status = analysis.get("support_status", {}).get(app_key, {})
                version_risk = analysis.get("version_risks", {}).get(app_key, 0.3)
                
                if support_status.get("risk_level") in ["high", "critical"]:
                    risk_items.append({
                        "id": f"app_risk_{app_key}",
                        "asset_id": app_data.get("assets", ["unknown"])[0],
                        "asset_name": app_data.get("name", "Unknown App"),
                        "category": "application_versions",
                        "technology": app_data.get("name", "Unknown"),
                        "current_version": app_data.get("version", "Unknown"),
                        "latest_version": "Latest Available",
                        "support_status": support_status.get("status", "unknown"),
                        "risk_level": support_status.get("risk_level", "medium"),
                        "migration_effort": "medium",
                        "business_impact": "medium",
                        "recommended_action": f"Upgrade {app_data.get('name', 'application')} to supported version",
                        "dependencies": [],
                        "description": f"{app_data.get('name', 'Application')} version {app_data.get('version', 'unknown')} needs updating",
                        "confidence": 0.7
                    })
                    risk_scores.append(version_risk)
        
        average_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        return {
            "items": risk_items,
            "average_risk": average_risk,
            "total_items": len(risk_items)
        }

    def _assess_business_impact(self, technical_analysis: Dict, stakeholder_context: Optional[Dict]) -> Dict[str, Any]:
        """Assess business impact."""
        return {"impact_score": 0.6, "business_areas_affected": []}

    def _calculate_cost_implications(self, technical_analysis: Dict, migration_timeline: Optional[str]) -> Dict[str, Any]:
        """Calculate cost implications."""
        return {"estimated_cost": "medium", "cost_factors": []}

    def _assess_timeline_constraints(self, technical_analysis: Dict, migration_timeline: str) -> Dict[str, Any]:
        """Assess timeline constraints."""
        return {"timeline_feasible": True, "constraints": []}

    def _calculate_priority_score(self, risk_item: Dict, stakeholder_context: Optional[Dict], migration_timeline: Optional[str]) -> float:
        """Calculate priority score."""
        return 0.7  # Simplified

    def _generate_business_justification(self, risk_item: Dict) -> str:
        """Generate business justification."""
        return "Business impact assessment needed"

    def _recommend_action(self, risk_item: Dict, migration_timeline: Optional[str]) -> str:
        """Recommend action."""
        return "Assess and plan remediation"

    async def _learn_risk_tolerance(self, risk_item_id: str, original: Dict, stakeholder_input: Dict) -> Dict[str, Any]:
        """Learn from risk tolerance feedback."""
        return {"learning_applied": True, "risk_tolerance_updated": True}

    async def _learn_business_priorities(self, risk_item_id: str, original: Dict, stakeholder_input: Dict) -> Dict[str, Any]:
        """Learn from business priority feedback."""
        return {"learning_applied": True, "prioritization_adjusted": True}

    async def _learn_timeline_constraints(self, risk_item_id: str, original: Dict, stakeholder_input: Dict) -> Dict[str, Any]:
        """Learn from timeline constraint feedback."""
        return {"learning_applied": True, "timeline_constraints_updated": True}

    def _get_latest_os_version(self, os_name: str) -> str:
        """Get the latest version for a given OS."""
        os_name_lower = os_name.lower()
        if "windows server" in os_name_lower:
            return "Windows Server 2022"
        elif "red hat" in os_name_lower or "rhel" in os_name_lower:
            return "RHEL 9"
        elif "ubuntu" in os_name_lower:
            return "Ubuntu 22.04 LTS"
        elif "cisco ios" in os_name_lower:
            return "Latest IOS Version"
        else:
            return "Latest Available"

    def _assess_migration_effort(self, lifecycle_status: Dict) -> str:
        """Assess migration effort based on lifecycle status."""
        risk_level = lifecycle_status.get("risk_level", "low")
        status = lifecycle_status.get("status", "supported")
        
        if status == "end_of_life":
            return "high"
        elif status in ["extended_support", "unknown_version"]:
            return "medium"
        elif risk_level == "critical":
            return "high"
        else:
            return "low"

    def _assess_business_impact_level(self, risk_score: float) -> str:
        """Assess business impact level based on risk score."""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _generate_os_recommendation(self, lifecycle_status: Dict) -> str:
        """Generate OS-specific recommendation."""
        status = lifecycle_status.get("status", "supported")
        risk_level = lifecycle_status.get("risk_level", "low")
        
        if status == "end_of_life":
            return "Immediate upgrade required - OS is no longer supported"
        elif status == "extended_support":
            return "Plan upgrade to current supported version"
        elif status == "unknown_version":
            return "Verify OS version and plan upgrade if legacy"
        elif risk_level == "critical":
            return "Critical security update required"
        else:
            return "Monitor for updates and plan future upgrade"

# Global instance for the application
tech_debt_analysis_agent = TechDebtAnalysisAgent() 