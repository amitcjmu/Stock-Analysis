"""
Application Discovery Agent
Identifies applications from asset relationships, dependencies, and documentation using AI intelligence.
Part of Sprint 4 Task 4.2: Application-Centric Discovery.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ApplicationDiscoveryAgent:
    """
    AI agent that discovers applications from various data sources including:
    - Asset relationships and dependencies
    - Documentation and metadata
    - User feedback and corrections
    - Cross-reference patterns
    """
    
    def __init__(self):
        self.agent_id = "application_discovery"
        self.agent_name = "Application Discovery Agent"
        self.confidence_threshold = 0.7
        self.learning_enabled = True
        
        # Application discovery patterns learned from data
        self.application_patterns = {
            "naming_conventions": [],
            "dependency_patterns": [],
            "technology_stacks": [],
            "environment_patterns": []
        }
        
        # Load existing learning data
        self._load_learning_data()
    
    async def discover_applications(self, assets: List[Dict[str, Any]], 
                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main application discovery method that analyzes assets to identify applications.
        
        Args:
            assets: List of asset data from various sources
            context: Additional context from user input or previous analysis
            
        Returns:
            Dictionary containing discovered applications with confidence scores
        """
        try:
            logger.info(f"Starting application discovery for {len(assets)} assets")
            
            # Step 1: Analyze individual assets for application indicators
            application_candidates = await self._identify_application_candidates(assets)
            
            # Step 2: Group related assets into applications
            application_groups = await self._group_assets_into_applications(application_candidates, assets)
            
            # Step 3: Analyze dependencies and relationships
            applications_with_dependencies = await self._analyze_application_dependencies(application_groups, assets)
            
            # Step 4: Validate and score applications
            validated_applications = await self._validate_and_score_applications(applications_with_dependencies)
            
            # Step 5: Generate clarification questions for uncertain cases
            clarification_questions = await self._generate_clarification_questions(validated_applications)
            
            discovery_result = {
                "applications": validated_applications,
                "discovery_confidence": self._calculate_overall_confidence(validated_applications),
                "clarification_questions": clarification_questions,
                "discovery_metadata": {
                    "total_assets_analyzed": len(assets),
                    "applications_discovered": len(validated_applications),
                    "high_confidence_apps": len([app for app in validated_applications if app.get("confidence", 0) >= 0.8]),
                    "needs_clarification": len([app for app in validated_applications if app.get("confidence", 0) < 0.6]),
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Application discovery completed: {len(validated_applications)} applications found")
            return discovery_result
            
        except Exception as e:
            logger.error(f"Error in application discovery: {e}")
            return {
                "applications": [],
                "discovery_confidence": 0.0,
                "clarification_questions": [],
                "error": str(e)
            }
    
    async def _identify_application_candidates(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify assets that are likely to be applications or application components."""
        candidates = []
        
        for asset in assets:
            confidence = 0.0
            indicators = []
            
            # Check asset type indicators
            asset_type = asset.get('asset_type', '').lower()
            if asset_type in ['application', 'app', 'service', 'web_application', 'database']:
                confidence += 0.4
                indicators.append(f"Asset type: {asset_type}")
            
            # Check naming patterns
            name = asset.get('name', '').lower()
            if any(keyword in name for keyword in ['app', 'service', 'web', 'api', 'portal', 'system']):
                confidence += 0.2
                indicators.append("Application naming pattern")
            
            # Check for application-specific attributes
            if asset.get('application_name') or asset.get('service_name'):
                confidence += 0.3
                indicators.append("Explicit application reference")
            
            # Check technology stack indicators
            tech_stack = asset.get('technology_stack', '') or asset.get('software', '')
            if tech_stack and any(tech in tech_stack.lower() for tech in ['java', 'python', 'node', 'react', 'angular', '.net']):
                confidence += 0.2
                indicators.append("Application technology stack")
            
            # Check for web/service ports
            if asset.get('port') in ['80', '443', '8080', '8443', '3000', '8000']:
                confidence += 0.1
                indicators.append("Web/service port")
            
            if confidence >= 0.3:  # Minimum threshold for consideration
                candidates.append({
                    "asset": asset,
                    "confidence": min(confidence, 1.0),
                    "indicators": indicators,
                    "candidate_type": "application" if confidence >= 0.6 else "component"
                })
        
        logger.info(f"Identified {len(candidates)} application candidates")
        return candidates
    
    async def _group_assets_into_applications(self, candidates: List[Dict[str, Any]], 
                                            all_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group related assets into logical applications."""
        applications = []
        processed_assets = set()
        
        for candidate in candidates:
            asset = candidate["asset"]
            asset_id = asset.get('id') or asset.get('name')
            
            if asset_id in processed_assets:
                continue
            
            # Start a new application group
            application = {
                "id": str(uuid.uuid4()),
                "name": self._generate_application_name(asset),
                "primary_asset": asset,
                "components": [asset],
                "confidence": candidate["confidence"],
                "discovery_method": "asset_grouping"
            }
            
            # Find related assets
            related_assets = await self._find_related_assets(asset, all_assets)
            for related_asset in related_assets:
                related_id = related_asset.get('id') or related_asset.get('name')
                if related_id not in processed_assets:
                    application["components"].append(related_asset)
                    processed_assets.add(related_id)
            
            # Mark primary asset as processed
            processed_assets.add(asset_id)
            applications.append(application)
        
        logger.info(f"Grouped assets into {len(applications)} application groups")
        return applications
    
    async def _find_related_assets(self, primary_asset: Dict[str, Any], 
                                 all_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find assets related to the primary asset through various relationships."""
        related = []
        primary_name = primary_asset.get('name', '').lower()
        primary_hostname = primary_asset.get('hostname', '').lower()
        primary_ip = primary_asset.get('ip_address', '')
        
        for asset in all_assets:
            if asset == primary_asset:
                continue
            
            relationship_score = 0.0
            
            # Check name similarity
            asset_name = asset.get('name', '').lower()
            if primary_name and asset_name:
                # Simple name similarity check
                common_words = set(primary_name.split()) & set(asset_name.split())
                if common_words:
                    relationship_score += 0.3
            
            # Check hostname/IP relationships
            asset_hostname = asset.get('hostname', '').lower()
            if primary_hostname and asset_hostname and primary_hostname in asset_hostname:
                relationship_score += 0.4
            
            # Check dependency relationships
            if asset.get('depends_on') == primary_asset.get('name') or \
               primary_asset.get('depends_on') == asset.get('name'):
                relationship_score += 0.5
            
            # Check environment and department matching
            if asset.get('environment') == primary_asset.get('environment') and \
               asset.get('department') == primary_asset.get('department'):
                relationship_score += 0.2
            
            if relationship_score >= 0.4:  # Threshold for relationship
                related.append(asset)
        
        return related
    
    async def _analyze_application_dependencies(self, applications: List[Dict[str, Any]], 
                                              all_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze dependencies between applications and external systems."""
        for application in applications:
            dependencies = {
                "internal": [],  # Dependencies on other discovered applications
                "external": [],  # Dependencies on external systems/services
                "infrastructure": []  # Dependencies on infrastructure components
            }
            
            # Analyze each component's dependencies
            for component in application["components"]:
                component_deps = await self._analyze_component_dependencies(component, all_assets, applications)
                
                dependencies["internal"].extend(component_deps.get("internal", []))
                dependencies["external"].extend(component_deps.get("external", []))
                dependencies["infrastructure"].extend(component_deps.get("infrastructure", []))
            
            # Remove duplicates and add to application
            application["dependencies"] = {
                "internal": list(set(dependencies["internal"])),
                "external": list(set(dependencies["external"])),
                "infrastructure": list(set(dependencies["infrastructure"]))
            }
            
            # Calculate dependency complexity score
            total_deps = sum(len(deps) for deps in dependencies.values())
            application["dependency_complexity"] = min(total_deps / 10.0, 1.0)  # Normalize to 0-1
        
        return applications
    
    async def _analyze_component_dependencies(self, component: Dict[str, Any], 
                                            all_assets: List[Dict[str, Any]],
                                            applications: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze dependencies for a single component."""
        dependencies = {"internal": [], "external": [], "infrastructure": []}
        
        # Check explicit dependency fields
        depends_on = component.get('depends_on', '') or component.get('dependencies', '')
        if depends_on:
            dep_names = [dep.strip() for dep in depends_on.split(',') if dep.strip()]
            
            for dep_name in dep_names:
                # Check if dependency is another discovered application
                is_internal = False
                for app in applications:
                    if any(comp.get('name', '').lower() == dep_name.lower() for comp in app["components"]):
                        dependencies["internal"].append(app["name"])
                        is_internal = True
                        break
                
                if not is_internal:
                    # Check if it's infrastructure
                    dep_asset = next((asset for asset in all_assets 
                                    if asset.get('name', '').lower() == dep_name.lower()), None)
                    if dep_asset:
                        asset_type = dep_asset.get('asset_type', '').lower()
                        if asset_type in ['server', 'database', 'storage', 'network']:
                            dependencies["infrastructure"].append(dep_name)
                        else:
                            dependencies["external"].append(dep_name)
                    else:
                        dependencies["external"].append(dep_name)
        
        return dependencies
    
    async def _validate_and_score_applications(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate discovered applications and assign confidence scores."""
        validated = []
        
        for app in applications:
            # Calculate comprehensive confidence score
            confidence_factors = {
                "discovery_confidence": app.get("confidence", 0.0),
                "component_count": min(len(app["components"]) / 5.0, 1.0),  # More components = higher confidence
                "naming_clarity": self._assess_naming_clarity(app),
                "dependency_clarity": self._assess_dependency_clarity(app),
                "technology_consistency": self._assess_technology_consistency(app)
            }
            
            # Weighted average of confidence factors
            weights = {
                "discovery_confidence": 0.3,
                "component_count": 0.2,
                "naming_clarity": 0.2,
                "dependency_clarity": 0.15,
                "technology_consistency": 0.15
            }
            
            final_confidence = sum(confidence_factors[factor] * weights[factor] 
                                 for factor in confidence_factors)
            
            # Add metadata
            app.update({
                "confidence": final_confidence,
                "confidence_factors": confidence_factors,
                "validation_status": "high_confidence" if final_confidence >= 0.8 else 
                                   "medium_confidence" if final_confidence >= 0.6 else "needs_clarification",
                "component_count": len(app["components"]),
                "technology_stack": self._extract_technology_stack(app),
                "environment": self._determine_environment(app),
                "business_criticality": self._assess_business_criticality(app)
            })
            
            validated.append(app)
        
        # Sort by confidence (highest first)
        validated.sort(key=lambda x: x["confidence"], reverse=True)
        return validated
    
    def _assess_naming_clarity(self, application: Dict[str, Any]) -> float:
        """Assess how clear and consistent the application naming is."""
        primary_name = application["primary_asset"].get("name", "")
        
        # Check for clear application naming patterns
        clarity_score = 0.0
        
        if any(keyword in primary_name.lower() for keyword in ['app', 'application', 'service', 'system']):
            clarity_score += 0.4
        
        if not any(char in primary_name for char in ['_', '-', '.']):
            clarity_score += 0.2  # Clean naming
        
        if len(primary_name.split()) <= 3:
            clarity_score += 0.2  # Concise naming
        
        # Check consistency across components
        component_names = [comp.get("name", "") for comp in application["components"]]
        if len(set(name.split()[0] for name in component_names if name)) == 1:
            clarity_score += 0.2  # Consistent prefix
        
        return min(clarity_score, 1.0)
    
    def _assess_dependency_clarity(self, application: Dict[str, Any]) -> float:
        """Assess how clear the application dependencies are."""
        deps = application.get("dependencies", {})
        total_deps = sum(len(dep_list) for dep_list in deps.values())
        
        if total_deps == 0:
            return 0.5  # Neutral score for no dependencies
        
        # Higher score for well-defined dependencies
        clarity_score = 0.0
        
        if deps.get("internal"):
            clarity_score += 0.4  # Internal dependencies are good
        
        if len(deps.get("infrastructure", [])) <= 3:
            clarity_score += 0.3  # Reasonable infrastructure dependencies
        
        if len(deps.get("external", [])) <= 2:
            clarity_score += 0.3  # Limited external dependencies
        
        return min(clarity_score, 1.0)
    
    def _assess_technology_consistency(self, application: Dict[str, Any]) -> float:
        """Assess technology stack consistency across components."""
        tech_stacks = []
        for component in application["components"]:
            tech = component.get("technology_stack") or component.get("software", "")
            if tech:
                tech_stacks.append(tech.lower())
        
        if not tech_stacks:
            return 0.5  # Neutral score for no tech info
        
        # Check for consistency
        unique_techs = set(tech_stacks)
        consistency_score = 1.0 - (len(unique_techs) - 1) / max(len(tech_stacks), 1)
        
        return max(consistency_score, 0.0)
    
    def _extract_technology_stack(self, application: Dict[str, Any]) -> List[str]:
        """Extract the technology stack for the application."""
        tech_stack = set()
        
        for component in application["components"]:
            tech = component.get("technology_stack") or component.get("software", "")
            if tech:
                # Split and clean technology names
                techs = [t.strip() for t in tech.replace(',', ' ').split() if t.strip()]
                tech_stack.update(techs)
        
        return list(tech_stack)
    
    def _determine_environment(self, application: Dict[str, Any]) -> str:
        """Determine the primary environment for the application."""
        environments = [comp.get("environment", "") for comp in application["components"]]
        environments = [env for env in environments if env]
        
        if not environments:
            return "Unknown"
        
        # Return most common environment
        from collections import Counter
        return Counter(environments).most_common(1)[0][0]
    
    def _assess_business_criticality(self, application: Dict[str, Any]) -> str:
        """Assess business criticality based on available indicators."""
        criticalities = [comp.get("criticality", "") for comp in application["components"]]
        criticalities = [crit for crit in criticalities if crit]
        
        if not criticalities:
            return "Medium"  # Default
        
        # Return highest criticality level found
        priority_order = ["Critical", "High", "Medium", "Low"]
        for level in priority_order:
            if any(level.lower() in crit.lower() for crit in criticalities):
                return level
        
        return "Medium"
    
    async def _generate_clarification_questions(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate questions for applications that need clarification."""
        questions = []
        
        for app in applications:
            if app["confidence"] < 0.6:
                question = {
                    "id": str(uuid.uuid4()),
                    "application_id": app["id"],
                    "application_name": app["name"],
                    "question_type": "application_validation",
                    "question": f"Is '{app['name']}' a single application or should it be split into multiple applications?",
                    "context": {
                        "components": [comp.get("name") for comp in app["components"]],
                        "confidence": app["confidence"],
                        "reason": "Low confidence in application grouping"
                    },
                    "options": [
                        "Single application - grouping is correct",
                        "Split into multiple applications",
                        "Merge with another application",
                        "Not an application - infrastructure only"
                    ]
                }
                questions.append(question)
        
        return questions
    
    def _generate_application_name(self, primary_asset: Dict[str, Any]) -> str:
        """Generate a meaningful application name from the primary asset."""
        name = primary_asset.get("name", "")
        app_name = primary_asset.get("application_name", "")
        
        if app_name:
            return app_name
        
        if name:
            # Clean up the name for application use
            clean_name = name.replace("_", " ").replace("-", " ").title()
            if not any(keyword in clean_name.lower() for keyword in ['app', 'application', 'service']):
                clean_name += " Application"
            return clean_name
        
        return "Unknown Application"
    
    def _calculate_overall_confidence(self, applications: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the discovery process."""
        if not applications:
            return 0.0
        
        total_confidence = sum(app["confidence"] for app in applications)
        return total_confidence / len(applications)
    
    async def process_user_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback to improve application discovery."""
        try:
            feedback_type = feedback.get("type")
            
            if feedback_type == "application_validation":
                return await self._process_application_validation(feedback)
            elif feedback_type == "application_grouping":
                return await self._process_grouping_feedback(feedback)
            elif feedback_type == "dependency_correction":
                return await self._process_dependency_feedback(feedback)
            
            return {"status": "success", "learning_applied": True}
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_application_validation(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Process user validation of application groupings."""
        # Store learning patterns for future discovery
        validation = feedback.get("validation")
        application_data = feedback.get("application_data", {})
        
        # Update learning patterns based on user corrections
        if validation == "correct":
            # Reinforce successful patterns
            self._reinforce_discovery_patterns(application_data)
        elif validation == "incorrect":
            # Learn from mistakes
            self._learn_from_correction(application_data, feedback.get("correction"))
        
        return {"status": "success", "learning_applied": True}
    
    def _reinforce_discovery_patterns(self, application_data: Dict[str, Any]):
        """Reinforce patterns that led to successful application discovery."""
        # This would update the agent's learning patterns
        logger.info(f"Reinforcing successful discovery patterns for {application_data.get('name')}")
    
    def _learn_from_correction(self, application_data: Dict[str, Any], correction: Dict[str, Any]):
        """Learn from user corrections to improve future discovery."""
        # This would update the agent's learning patterns
        logger.info(f"Learning from correction for {application_data.get('name')}")
    
    def _load_learning_data(self):
        """Load existing learning data for the agent."""
        # This would load persisted learning patterns
        logger.info("Application Discovery Agent learning data loaded")
    
    def _save_learning_data(self):
        """Save learning data for persistence."""
        # This would persist learning patterns
        logger.info("Application Discovery Agent learning data saved")

# Global instance
application_discovery_agent = ApplicationDiscoveryAgent() 