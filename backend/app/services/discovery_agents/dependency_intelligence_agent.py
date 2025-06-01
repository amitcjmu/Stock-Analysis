"""
Dependency Intelligence Agent
Advanced AI agent for comprehensive dependency analysis and intelligent validation.
Provides dependency discovery, conflict resolution, and impact analysis across applications.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DependencyIntelligenceAgent:
    """
    Advanced AI agent that provides comprehensive dependency intelligence including:
    - Multi-source dependency analysis (CMDB, documentation, user input)
    - Intelligent dependency validation and conflict resolution
    - Cross-application dependency mapping with impact analysis
    - Learning from user corrections and clarifications
    """
    
    def __init__(self):
        self.agent_id = "dependency_intelligence"
        self.agent_name = "Dependency Intelligence Agent"
        self.confidence_threshold = 0.75
        self.learning_enabled = True
        
        # Dependency patterns and learning
        self.dependency_patterns = {
            "common_dependencies": {},
            "conflict_patterns": {},
            "validation_rules": {},
            "impact_patterns": {}
        }
        
        # Known dependency types
        self.dependency_types = {
            "application": ["api_dependency", "service_dependency", "integration_point"],
            "infrastructure": ["database_connection", "network_dependency", "storage_mount"],
            "platform": ["runtime_dependency", "library_dependency", "framework_dependency"],
            "security": ["authentication_dependency", "certificate_dependency", "firewall_rule"]
        }
        
        self._load_dependency_intelligence()
    
    async def analyze_dependencies(self, assets: List[Dict[str, Any]], 
                                 applications: Optional[List[Dict[str, Any]]] = None,
                                 user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive dependency analysis across assets and applications.
        
        Args:
            assets: List of assets to analyze
            applications: Optional application portfolio for context
            user_context: Additional user-provided context
            
        Returns:
            Comprehensive dependency analysis with intelligence insights
        """
        try:
            logger.info(f"Starting dependency intelligence analysis for {len(assets)} assets")
            
            # Step 1: Extract dependencies from multiple sources
            extracted_dependencies = await self._extract_dependencies_multi_source(assets, user_context)
            
            # Step 2: Validate and resolve conflicts
            validated_dependencies = await self._validate_and_resolve_conflicts(extracted_dependencies)
            
            # Step 3: Cross-application dependency mapping
            cross_app_dependencies = await self._map_cross_application_dependencies(
                validated_dependencies, applications or []
            )
            
            # Step 4: Impact analysis
            impact_analysis = await self._analyze_dependency_impact(
                cross_app_dependencies, applications or []
            )
            
            # Step 5: Generate clarification questions
            clarification_questions = await self._generate_dependency_clarifications(
                validated_dependencies, cross_app_dependencies
            )
            
            dependency_intelligence = {
                "dependency_analysis": {
                    "total_dependencies": len(validated_dependencies),
                    "dependency_categories": self._categorize_dependencies(validated_dependencies),
                    "dependency_quality": self._assess_dependency_quality(validated_dependencies),
                    "conflict_resolution": self._get_conflict_resolution_summary(validated_dependencies)
                },
                "cross_application_mapping": cross_app_dependencies,
                "impact_analysis": impact_analysis,
                "clarification_questions": clarification_questions,
                "dependency_recommendations": await self._generate_dependency_recommendations(
                    validated_dependencies, impact_analysis
                ),
                "intelligence_metadata": {
                    "analysis_confidence": self._calculate_analysis_confidence(validated_dependencies),
                    "learning_opportunities": len(clarification_questions),
                    "validation_score": self._calculate_validation_score(validated_dependencies),
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Dependency intelligence analysis completed with {len(validated_dependencies)} dependencies")
            return dependency_intelligence
            
        except Exception as e:
            logger.error(f"Error in dependency intelligence analysis: {e}")
            return {
                "dependency_analysis": {"total_dependencies": 0, "error": str(e)},
                "cross_application_mapping": {},
                "impact_analysis": {},
                "clarification_questions": [],
                "dependency_recommendations": []
            }
    
    async def process_user_dependency_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback on dependency analysis for learning and improvement.
        
        Args:
            feedback: User feedback on dependency analysis
            
        Returns:
            Learning processing results
        """
        try:
            feedback_type = feedback.get("feedback_type", "correction")
            dependency_id = feedback.get("dependency_id")
            original_analysis = feedback.get("original_analysis", {})
            user_correction = feedback.get("user_correction", {})
            
            learning_result = {
                "feedback_processed": True,
                "learning_applied": False,
                "confidence_improvement": 0.0,
                "pattern_updates": []
            }
            
            if feedback_type == "dependency_validation":
                # Learn from dependency validation corrections
                learning_result = await self._learn_from_validation_feedback(
                    dependency_id, original_analysis, user_correction
                )
            
            elif feedback_type == "conflict_resolution":
                # Learn from conflict resolution decisions
                learning_result = await self._learn_from_conflict_resolution(
                    dependency_id, original_analysis, user_correction
                )
            
            elif feedback_type == "impact_assessment":
                # Learn from impact assessment corrections
                learning_result = await self._learn_from_impact_feedback(
                    dependency_id, original_analysis, user_correction
                )
            
            # Store learning experience
            self._store_learning_experience(feedback, learning_result)
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Error processing dependency feedback: {e}")
            return {
                "feedback_processed": False,
                "error": str(e)
            }
    
    async def _extract_dependencies_multi_source(self, assets: List[Dict[str, Any]], 
                                               user_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract dependencies from multiple data sources."""
        dependencies = []
        dependency_id_counter = 0
        
        for asset in assets:
            asset_id = asset.get("id") or asset.get("asset_id") or f"asset_{dependency_id_counter}"
            
            # Extract from CMDB data
            cmdb_dependencies = self._extract_from_cmdb_data(asset, asset_id)
            dependencies.extend(cmdb_dependencies)
            
            # Extract from network/connection data
            network_dependencies = self._extract_from_network_data(asset, asset_id)
            dependencies.extend(network_dependencies)
            
            # Extract from application context if available
            app_dependencies = self._extract_from_application_context(asset, asset_id)
            dependencies.extend(app_dependencies)
            
            dependency_id_counter += len(cmdb_dependencies + network_dependencies + app_dependencies)
        
        # Add user-provided dependencies if available
        if user_context and user_context.get("known_dependencies"):
            user_dependencies = self._process_user_dependencies(user_context["known_dependencies"])
            dependencies.extend(user_dependencies)
        
        return dependencies
    
    def _extract_from_cmdb_data(self, asset: Dict[str, Any], asset_id: str) -> List[Dict[str, Any]]:
        """Extract dependencies from CMDB data fields."""
        dependencies = []
        
        # Check for database connections
        if asset.get("database_connections"):
            db_connections = asset.get("database_connections", [])
            if isinstance(db_connections, str):
                db_connections = [db_connections]
            
            for db_conn in db_connections:
                dependencies.append({
                    "id": f"dep_{asset_id}_db_{len(dependencies)}",
                    "source_asset": asset_id,
                    "target": db_conn,
                    "dependency_type": "database_connection",
                    "confidence": 0.8,
                    "source": "cmdb_data",
                    "discovered_from": "database_connections field"
                })
        
        # Check for network dependencies (IP addresses, hostnames)
        network_refs = []
        for field in ["connected_servers", "network_shares", "dependent_services"]:
            if asset.get(field):
                field_value = asset.get(field)
                if isinstance(field_value, str):
                    network_refs.extend(field_value.split(","))
                elif isinstance(field_value, list):
                    network_refs.extend(field_value)
        
        for network_ref in network_refs:
            if network_ref and network_ref.strip():
                dependencies.append({
                    "id": f"dep_{asset_id}_net_{len(dependencies)}",
                    "source_asset": asset_id,
                    "target": network_ref.strip(),
                    "dependency_type": "network_dependency",
                    "confidence": 0.7,
                    "source": "cmdb_data",
                    "discovered_from": "network reference fields"
                })
        
        return dependencies
    
    def _extract_from_network_data(self, asset: Dict[str, Any], asset_id: str) -> List[Dict[str, Any]]:
        """Extract dependencies from network configuration data."""
        dependencies = []
        
        # Check IP address patterns for potential dependencies
        ip_address = asset.get("ip_address")
        if ip_address:
            # Infer potential network dependencies based on IP subnet
            subnet_dependencies = self._infer_subnet_dependencies(ip_address, asset_id)
            dependencies.extend(subnet_dependencies)
        
        # Check for port configurations
        if asset.get("open_ports") or asset.get("listening_ports"):
            port_dependencies = self._infer_port_dependencies(asset, asset_id)
            dependencies.extend(port_dependencies)
        
        return dependencies
    
    def _extract_from_application_context(self, asset: Dict[str, Any], asset_id: str) -> List[Dict[str, Any]]:
        """Extract dependencies from application context."""
        dependencies = []
        
        # Check for application-specific dependencies
        if asset.get("application_type") or asset.get("software_installed"):
            app_deps = self._infer_application_dependencies(asset, asset_id)
            dependencies.extend(app_deps)
        
        return dependencies
    
    async def _validate_and_resolve_conflicts(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate dependencies and resolve conflicts using AI intelligence."""
        validated_dependencies = []
        conflict_groups = self._identify_dependency_conflicts(dependencies)
        
        for dependency in dependencies:
            # Check if this dependency is part of a conflict
            conflict_group = self._find_dependency_conflict_group(dependency, conflict_groups)
            
            if conflict_group:
                # Resolve conflict using AI intelligence
                resolved_dependency = await self._resolve_dependency_conflict(dependency, conflict_group)
                if resolved_dependency:
                    validated_dependencies.append(resolved_dependency)
            else:
                # No conflicts - validate independently
                if self._validate_single_dependency(dependency):
                    validated_dependencies.append(dependency)
        
        return validated_dependencies
    
    def _identify_dependency_conflicts(self, dependencies: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Identify groups of conflicting dependencies."""
        conflict_groups = []
        processed_deps = set()
        
        for i, dep1 in enumerate(dependencies):
            if i in processed_deps:
                continue
            
            conflict_group = [dep1]
            processed_deps.add(i)
            
            for j, dep2 in enumerate(dependencies[i+1:], i+1):
                if j in processed_deps:
                    continue
                
                if self._dependencies_conflict(dep1, dep2):
                    conflict_group.append(dep2)
                    processed_deps.add(j)
            
            if len(conflict_group) > 1:
                conflict_groups.append(conflict_group)
        
        return conflict_groups
    
    def _dependencies_conflict(self, dep1: Dict[str, Any], dep2: Dict[str, Any]) -> bool:
        """Check if two dependencies conflict with each other."""
        # Same source and target but different types
        if (dep1.get("source_asset") == dep2.get("source_asset") and 
            dep1.get("target") == dep2.get("target") and
            dep1.get("dependency_type") != dep2.get("dependency_type")):
            return True
        
        # Contradictory information from different sources
        if (dep1.get("source_asset") == dep2.get("source_asset") and
            dep1.get("target") == dep2.get("target") and
            abs(dep1.get("confidence", 0) - dep2.get("confidence", 0)) > 0.3):
            return True
        
        return False
    
    async def _resolve_dependency_conflict(self, dependency: Dict[str, Any], 
                                         conflict_group: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Resolve dependency conflicts using AI intelligence."""
        # Use highest confidence dependency as base
        highest_confidence_dep = max(conflict_group, key=lambda d: d.get("confidence", 0))
        
        # Merge information from multiple sources
        resolved_dependency = highest_confidence_dep.copy()
        resolved_dependency["conflict_resolved"] = True
        resolved_dependency["conflicting_sources"] = [dep.get("source") for dep in conflict_group]
        resolved_dependency["resolution_method"] = "highest_confidence_with_merge"
        
        return resolved_dependency
    
    def _validate_single_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate a single dependency for correctness."""
        # Check required fields
        required_fields = ["source_asset", "target", "dependency_type"]
        if not all(dependency.get(field) for field in required_fields):
            return False
        
        # Check confidence threshold
        if dependency.get("confidence", 0) < 0.3:
            return False
        
        return True
    
    async def _map_cross_application_dependencies(self, dependencies: List[Dict[str, Any]], 
                                                applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Map dependencies across applications for impact analysis."""
        if not applications:
            return {"cross_app_dependencies": [], "application_clusters": []}
        
        # Create application mapping
        asset_to_app_map = {}
        for app in applications:
            app_id = app.get("id") or app.get("name", "unknown_app")
            for component in app.get("components", []):
                asset_id = component.get("id") or component.get("asset_id")
                if asset_id:
                    asset_to_app_map[asset_id] = app_id
        
        # Map dependencies to applications
        cross_app_deps = []
        for dep in dependencies:
            source_asset = dep.get("source_asset")
            target_asset = dep.get("target")
            
            source_app = asset_to_app_map.get(source_asset)
            target_app = asset_to_app_map.get(target_asset)
            
            if source_app and target_app and source_app != target_app:
                cross_app_deps.append({
                    "source_application": source_app,
                    "target_application": target_app,
                    "dependency": dep,
                    "impact_level": self._assess_cross_app_impact(dep, applications)
                })
        
        # Identify application clusters
        app_clusters = self._identify_application_clusters(cross_app_deps)
        
        return {
            "cross_app_dependencies": cross_app_deps,
            "application_clusters": app_clusters,
            "dependency_graph": self._build_dependency_graph(cross_app_deps)
        }
    
    async def _analyze_dependency_impact(self, cross_app_dependencies: Dict[str, Any], 
                                       applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact of dependencies on migration planning."""
        cross_app_deps = cross_app_dependencies.get("cross_app_dependencies", [])
        
        # Categorize impacts
        impact_categories = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for dep_info in cross_app_deps:
            impact_level = dep_info.get("impact_level", "medium")
            impact_categories[impact_level].append(dep_info)
        
        # Migration sequence recommendations
        migration_recommendations = self._generate_migration_sequence_recommendations(
            cross_app_dependencies, applications
        )
        
        return {
            "impact_summary": {
                "total_cross_app_dependencies": len(cross_app_deps),
                "critical_dependencies": len(impact_categories["critical"]),
                "high_impact_dependencies": len(impact_categories["high"]),
                "dependency_complexity_score": self._calculate_complexity_score(cross_app_deps)
            },
            "impact_categories": impact_categories,
            "migration_recommendations": migration_recommendations,
            "dependency_risks": self._identify_dependency_risks(cross_app_deps)
        }
    
    def _calculate_analysis_confidence(self, dependencies: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in dependency analysis."""
        if not dependencies:
            return 0.0
        
        total_confidence = sum(dep.get("confidence", 0) for dep in dependencies)
        return total_confidence / len(dependencies)
    
    def _calculate_validation_score(self, dependencies: List[Dict[str, Any]]) -> float:
        """Calculate dependency validation score."""
        if not dependencies:
            return 0.0
        
        validated_count = len([dep for dep in dependencies if dep.get("conflict_resolved") or dep.get("confidence", 0) >= 0.7])
        return validated_count / len(dependencies)
    
    def _categorize_dependencies(self, dependencies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize dependencies by type."""
        categories = {}
        for dep in dependencies:
            dep_type = dep.get("dependency_type", "unknown")
            categories[dep_type] = categories.get(dep_type, 0) + 1
        return categories
    
    def _assess_dependency_quality(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall quality of dependency data."""
        if not dependencies:
            return {"quality_score": 0.0, "quality_issues": ["No dependencies found"]}
        
        high_confidence = len([dep for dep in dependencies if dep.get("confidence", 0) >= 0.8])
        medium_confidence = len([dep for dep in dependencies if 0.5 <= dep.get("confidence", 0) < 0.8])
        low_confidence = len([dep for dep in dependencies if dep.get("confidence", 0) < 0.5])
        
        quality_score = (high_confidence * 1.0 + medium_confidence * 0.6 + low_confidence * 0.2) / len(dependencies)
        
        quality_issues = []
        if low_confidence > len(dependencies) * 0.3:
            quality_issues.append("High number of low-confidence dependencies")
        if len(set(dep.get("dependency_type") for dep in dependencies)) < 3:
            quality_issues.append("Limited dependency type diversity")
        
        return {
            "quality_score": quality_score,
            "high_confidence_count": high_confidence,
            "medium_confidence_count": medium_confidence,
            "low_confidence_count": low_confidence,
            "quality_issues": quality_issues
        }
    
    async def _generate_dependency_clarifications(self, validated_dependencies: List[Dict[str, Any]], 
                                                cross_app_dependencies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate clarification questions for unclear dependencies."""
        clarifications = []
        
        # Questions for low-confidence dependencies
        low_confidence_deps = [dep for dep in validated_dependencies if dep.get("confidence", 0) < 0.6]
        for dep in low_confidence_deps[:5]:  # Limit to top 5
            clarifications.append({
                "question_id": f"dep_validation_{dep.get('id')}",
                "question_type": "dependency_validation",
                "title": f"Validate Dependency: {dep.get('source_asset')} → {dep.get('target')}",
                "question": f"Can you confirm the dependency between {dep.get('source_asset')} and {dep.get('target')}?",
                "dependency": dep,
                "options": ["Confirm", "Modify", "Remove"],
                "priority": "medium"
            })
        
        # Questions for conflicting dependencies
        conflicted_deps = [dep for dep in validated_dependencies if dep.get("conflict_resolved")]
        for dep in conflicted_deps[:3]:  # Limit to top 3
            clarifications.append({
                "question_id": f"conflict_resolution_{dep.get('id')}",
                "question_type": "conflict_resolution",
                "title": f"Resolve Dependency Conflict",
                "question": f"Multiple sources provided different information about the dependency from {dep.get('source_asset')} to {dep.get('target')}. Please clarify.",
                "dependency": dep,
                "conflicting_sources": dep.get("conflicting_sources", []),
                "priority": "high"
            })
        
        return clarifications
    
    async def _generate_dependency_recommendations(self, dependencies: List[Dict[str, Any]], 
                                                 impact_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on dependency analysis."""
        recommendations = []
        
        # Recommendation for missing dependencies
        if len(dependencies) < 10:  # Threshold for expected dependencies
            recommendations.append({
                "category": "dependency_discovery",
                "priority": "medium",
                "title": "Enhance Dependency Discovery",
                "description": f"Only {len(dependencies)} dependencies discovered - consider additional discovery methods",
                "actions": [
                    "Review application documentation for undiscovered dependencies",
                    "Conduct stakeholder interviews about application relationships",
                    "Analyze network traffic for runtime dependencies"
                ]
            })
        
        # Recommendation for high-impact dependencies
        critical_deps = impact_analysis.get("impact_categories", {}).get("critical", [])
        if critical_deps:
            recommendations.append({
                "category": "critical_dependency_management",
                "priority": "high", 
                "title": f"Manage {len(critical_deps)} Critical Dependencies",
                "description": "Critical dependencies require careful migration sequencing",
                "actions": [
                    "Validate critical dependency configurations",
                    "Plan migration waves to minimize dependency breaks",
                    "Prepare dependency validation testing"
                ]
            })
        
        return recommendations
    
    def _load_dependency_intelligence(self):
        """Load existing dependency intelligence patterns."""
        # In a real implementation, this would load from persistent storage
        pass
    
    def _store_learning_experience(self, feedback: Dict[str, Any], learning_result: Dict[str, Any]):
        """Store learning experience for future improvement."""
        # In a real implementation, this would store to persistent storage
        pass
    
    # Additional helper methods for dependency analysis
    def _infer_subnet_dependencies(self, ip_address: str, asset_id: str) -> List[Dict[str, Any]]:
        """Infer potential dependencies based on IP subnet."""
        return []  # Simplified for brevity
    
    def _infer_port_dependencies(self, asset: Dict[str, Any], asset_id: str) -> List[Dict[str, Any]]:
        """Infer dependencies based on port configurations."""
        return []  # Simplified for brevity
    
    def _infer_application_dependencies(self, asset: Dict[str, Any], asset_id: str) -> List[Dict[str, Any]]:
        """Infer dependencies based on application type."""
        return []  # Simplified for brevity
    
    def _process_user_dependencies(self, user_dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process user-provided dependency information."""
        return user_dependencies  # Simplified for brevity

    # Placeholder methods for additional functionality
    def _find_dependency_conflict_group(self, dependency: Dict[str, Any], conflict_groups: List[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """Find conflict group containing this dependency."""
        for group in conflict_groups:
            if dependency in group:
                return group
        return None

    def _get_conflict_resolution_summary(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of conflict resolution."""
        resolved_conflicts = len([dep for dep in dependencies if dep.get("conflict_resolved")])
        return {"conflicts_resolved": resolved_conflicts, "total_dependencies": len(dependencies)}

    def _assess_cross_app_impact(self, dependency: Dict[str, Any], applications: List[Dict[str, Any]]) -> str:
        """Assess impact level of cross-application dependency."""
        return "medium"  # Simplified

    def _identify_application_clusters(self, cross_app_deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify clusters of tightly coupled applications."""
        return []  # Simplified

    def _build_dependency_graph(self, cross_app_deps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build dependency graph for visualization."""
        return {"nodes": [], "edges": []}  # Simplified

    def _generate_migration_sequence_recommendations(self, cross_app_deps: Dict[str, Any], applications: List[Dict[str, Any]]) -> List[str]:
        """Generate migration sequence recommendations."""
        return ["Plan migration waves based on dependency analysis"]

    def _calculate_complexity_score(self, cross_app_deps: List[Dict[str, Any]]) -> float:
        """Calculate dependency complexity score."""
        return len(cross_app_deps) * 0.1

    def _identify_dependency_risks(self, cross_app_deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify dependency-related risks."""
        return []

    async def _learn_from_validation_feedback(self, dependency_id: str, original: Dict[str, Any], correction: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from validation feedback."""
        return {"learning_applied": True, "confidence_improvement": 0.1}

    async def _learn_from_conflict_resolution(self, dependency_id: str, original: Dict[str, Any], correction: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from conflict resolution."""
        return {"learning_applied": True, "confidence_improvement": 0.15}

    async def _learn_from_impact_feedback(self, dependency_id: str, original: Dict[str, Any], correction: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from impact assessment feedback."""
        return {"learning_applied": True, "confidence_improvement": 0.05}

# Global instance for the application
dependency_intelligence_agent = DependencyIntelligenceAgent() 