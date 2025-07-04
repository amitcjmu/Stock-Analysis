"""
Move Group Analyzer - Identifies move group hints for the Planning Flow

This tool analyzes applications to identify optimal groupings for migration,
considering technical dependencies, business process relationships, and risk profiles.
"""

import logging
from typing import Dict, Any, List

from app.models.assessment_flow_state import SixRStrategy

logger = logging.getLogger(__name__)


class MoveGroupAnalyzer:
    """
    Identifies move group hints for the Planning Flow.
    
    Analyzes:
    - Technical dependencies between applications
    - Business process relationships
    - Data dependencies and integrations
    - Risk profiles and complexity alignment
    - Resource and timing constraints
    """
    
    def __init__(self):
        self.name = "move_group_analyzer"
        self.description = "Identifies migration grouping hints for planning"
        logger.info("Initialized MoveGroupAnalyzer")
    
    def _run(self, application_decisions: List[Dict[str, Any]], 
             dependency_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze applications to identify move group hints.
        
        Args:
            application_decisions: List of 6R decisions for applications
            dependency_data: Dependency information between applications
            
        Returns:
            Dict with move group recommendations and rationale
        """
        try:
            # Extract application details
            app_details = {}
            for decision in application_decisions:
                app_id = decision.get("application_id")
                app_details[app_id] = {
                    "name": decision.get("application_name"),
                    "strategy": decision.get("overall_strategy"),
                    "complexity": decision.get("complexity_score", 50),
                    "risk_factors": decision.get("risk_factors", []),
                    "components": decision.get("component_treatments", [])
                }
            
            # Identify dependency clusters
            dependency_groups = self._identify_dependency_clusters(
                app_details, dependency_data
            )
            
            # Group by strategy affinity
            strategy_groups = self._group_by_strategy_affinity(app_details)
            
            # Identify risk-based groups
            risk_groups = self._group_by_risk_profile(app_details)
            
            # Generate move group recommendations
            move_groups = self._synthesize_move_groups(
                dependency_groups, strategy_groups, risk_groups
            )
            
            # Generate group rationale
            group_rationale = self._generate_group_rationale(move_groups, app_details)
            
            # Calculate group metrics
            group_metrics = self._calculate_group_metrics(move_groups, app_details)
            
            return {
                "recommended_move_groups": move_groups,
                "group_rationale": group_rationale,
                "group_metrics": group_metrics,
                "dependency_constraints": self._get_dependency_constraints(dependency_data),
                "sequencing_recommendations": self._get_sequencing_recommendations(
                    move_groups, app_details
                )
            }
            
        except Exception as e:
            logger.error(f"Error in MoveGroupAnalyzer: {str(e)}")
            return {
                "recommended_move_groups": [],
                "error": str(e),
                "group_rationale": ["Unable to analyze move groups due to error"]
            }
    
    def _identify_dependency_clusters(self, app_details: Dict[str, Any],
                                    dependency_data: Dict[str, Any]) -> List[List[str]]:
        """Identify tightly coupled application clusters"""
        
        clusters = []
        processed = set()
        
        # Build dependency graph
        dependencies = dependency_data.get("dependencies", {})
        
        for app_id in app_details:
            if app_id in processed:
                continue
            
            # Find connected applications
            cluster = self._find_connected_apps(app_id, dependencies, processed)
            
            if len(cluster) > 1:
                clusters.append(cluster)
                processed.update(cluster)
            else:
                processed.add(app_id)
        
        return clusters
    
    def _find_connected_apps(self, start_app: str, dependencies: Dict[str, List[str]],
                           processed: set) -> List[str]:
        """Find all applications connected to the start app"""
        
        connected = [start_app]
        to_check = [start_app]
        checked = set()
        
        while to_check:
            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)
            
            # Check outgoing dependencies
            for dep in dependencies.get(current, []):
                if dep not in connected and dep not in processed:
                    connected.append(dep)
                    to_check.append(dep)
            
            # Check incoming dependencies
            for app, deps in dependencies.items():
                if current in deps and app not in connected and app not in processed:
                    connected.append(app)
                    to_check.append(app)
        
        return connected
    
    def _group_by_strategy_affinity(self, app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group applications by compatible strategies"""
        
        strategy_groups = {
            "modernization": [],  # Rewrite, Rearchitect, Refactor
            "replatform": [],     # Replatform
            "lift_and_shift": [], # Rehost
            "minimal_change": []  # Retain, Retire
        }
        
        modernization_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.REFACTOR.value
        ]
        
        for app_id, details in app_details.items():
            strategy = details.get("strategy")
            
            if strategy in modernization_strategies:
                strategy_groups["modernization"].append(app_id)
            elif strategy == SixRStrategy.REPLATFORM.value:
                strategy_groups["replatform"].append(app_id)
            elif strategy == SixRStrategy.REHOST.value:
                strategy_groups["lift_and_shift"].append(app_id)
            else:
                strategy_groups["minimal_change"].append(app_id)
        
        # Remove empty groups
        return {k: v for k, v in strategy_groups.items() if v}
    
    def _group_by_risk_profile(self, app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group applications by risk level"""
        
        risk_groups = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": []
        }
        
        for app_id, details in app_details.items():
            risk_factors = details.get("risk_factors", [])
            complexity = details.get("complexity", 50)
            
            # Calculate risk score
            risk_score = len(risk_factors) * 10 + (complexity / 10)
            
            if risk_score > 70:
                risk_groups["high_risk"].append(app_id)
            elif risk_score > 40:
                risk_groups["medium_risk"].append(app_id)
            else:
                risk_groups["low_risk"].append(app_id)
        
        return risk_groups
    
    def _synthesize_move_groups(self, dependency_groups: List[List[str]],
                              strategy_groups: Dict[str, List[str]],
                              risk_groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Synthesize final move group recommendations"""
        
        move_groups = []
        assigned_apps = set()
        
        # Priority 1: Keep dependent applications together
        for idx, dep_group in enumerate(dependency_groups):
            move_groups.append({
                "group_id": f"dependency_group_{idx + 1}",
                "applications": dep_group,
                "group_type": "dependency_cluster",
                "priority": "high",
                "rationale": "Tightly coupled applications that should migrate together"
            })
            assigned_apps.update(dep_group)
        
        # Priority 2: Group remaining apps by strategy
        for strategy_type, apps in strategy_groups.items():
            unassigned = [app for app in apps if app not in assigned_apps]
            
            if unassigned:
                # Split large groups
                chunk_size = 5  # Max apps per group
                for i in range(0, len(unassigned), chunk_size):
                    chunk = unassigned[i:i + chunk_size]
                    move_groups.append({
                        "group_id": f"{strategy_type}_group_{i // chunk_size + 1}",
                        "applications": chunk,
                        "group_type": "strategy_affinity",
                        "priority": "medium",
                        "rationale": f"Applications with {strategy_type} migration approach"
                    })
                    assigned_apps.update(chunk)
        
        # Priority 3: Risk-based adjustments
        high_risk_apps = risk_groups.get("high_risk", [])
        for group in move_groups:
            group_apps = group["applications"]
            high_risk_in_group = [app for app in group_apps if app in high_risk_apps]
            
            if high_risk_in_group and len(high_risk_in_group) < len(group_apps):
                # Mixed risk group - flag for attention
                group["risk_warning"] = "Contains mix of high and lower risk applications"
        
        return move_groups
    
    def _generate_group_rationale(self, move_groups: List[Dict[str, Any]],
                                app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate detailed rationale for each move group"""
        
        group_rationale = {}
        
        for group in move_groups:
            group_id = group["group_id"]
            apps = group["applications"]
            rationale = [group["rationale"]]
            
            # Add strategy details
            strategies = set()
            for app_id in apps:
                strategy = app_details.get(app_id, {}).get("strategy")
                if strategy:
                    strategies.add(strategy)
            
            if len(strategies) > 1:
                rationale.append(f"Mixed strategies: {', '.join(strategies)}")
            else:
                rationale.append(f"Unified strategy: {strategies.pop() if strategies else 'Unknown'}")
            
            # Add complexity assessment
            avg_complexity = sum(
                app_details.get(app_id, {}).get("complexity", 50)
                for app_id in apps
            ) / len(apps) if apps else 0
            
            if avg_complexity > 70:
                rationale.append("High complexity group - requires experienced team")
            elif avg_complexity < 30:
                rationale.append("Low complexity group - suitable for parallel execution")
            
            # Add size recommendation
            if len(apps) > 7:
                rationale.append("Large group - consider splitting if resources are limited")
            elif len(apps) == 1:
                rationale.append("Single application - can be combined with other groups")
            
            group_rationale[group_id] = rationale
        
        return group_rationale
    
    def _calculate_group_metrics(self, move_groups: List[Dict[str, Any]],
                               app_details: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for move groups"""
        
        metrics = {
            "total_groups": len(move_groups),
            "avg_group_size": 0,
            "largest_group_size": 0,
            "dependency_groups": 0,
            "strategy_groups": 0,
            "estimated_waves": 0
        }
        
        if not move_groups:
            return metrics
        
        group_sizes = []
        for group in move_groups:
            size = len(group["applications"])
            group_sizes.append(size)
            
            if group["group_type"] == "dependency_cluster":
                metrics["dependency_groups"] += 1
            elif group["group_type"] == "strategy_affinity":
                metrics["strategy_groups"] += 1
        
        metrics["avg_group_size"] = sum(group_sizes) / len(group_sizes)
        metrics["largest_group_size"] = max(group_sizes)
        
        # Estimate waves based on group priorities
        high_priority = sum(1 for g in move_groups if g.get("priority") == "high")
        medium_priority = sum(1 for g in move_groups if g.get("priority") == "medium")
        
        # Assume 3-4 groups per wave
        metrics["estimated_waves"] = max(1, (high_priority + medium_priority) // 3)
        
        return metrics
    
    def _get_dependency_constraints(self, dependency_data: Dict[str, Any]) -> List[str]:
        """Extract key dependency constraints for planning"""
        
        constraints = []
        
        dependencies = dependency_data.get("dependencies", {})
        
        # Find circular dependencies
        for app, deps in dependencies.items():
            for dep in deps:
                if app in dependencies.get(dep, []):
                    constraints.append(f"Circular dependency between {app} and {dep}")
        
        # Find hub applications (many dependencies)
        for app, deps in dependencies.items():
            if len(deps) > 5:
                constraints.append(f"{app} has {len(deps)} dependencies - migration will impact many systems")
        
        # Find critical path dependencies
        incoming_counts = {}
        for deps in dependencies.values():
            for dep in deps:
                incoming_counts[dep] = incoming_counts.get(dep, 0) + 1
        
        for app, count in incoming_counts.items():
            if count > 3:
                constraints.append(f"{app} is depended upon by {count} applications - critical path item")
        
        return constraints
    
    def _get_sequencing_recommendations(self, move_groups: List[Dict[str, Any]],
                                      app_details: Dict[str, Any]) -> List[str]:
        """Generate sequencing recommendations for move groups"""
        
        recommendations = []
        
        # Recommend starting with low-risk groups
        low_complexity_groups = []
        high_complexity_groups = []
        
        for group in move_groups:
            avg_complexity = sum(
                app_details.get(app_id, {}).get("complexity", 50)
                for app_id in group["applications"]
            ) / len(group["applications"]) if group["applications"] else 0
            
            if avg_complexity < 40:
                low_complexity_groups.append(group["group_id"])
            elif avg_complexity > 70:
                high_complexity_groups.append(group["group_id"])
        
        if low_complexity_groups:
            recommendations.append(
                f"Start with low-complexity groups for quick wins: {', '.join(low_complexity_groups[:2])}"
            )
        
        if high_complexity_groups:
            recommendations.append(
                f"Schedule high-complexity groups with adequate resources: {', '.join(high_complexity_groups[:2])}"
            )
        
        # Recommend parallel execution where possible
        independent_groups = [
            g for g in move_groups 
            if g["group_type"] != "dependency_cluster" and len(g["applications"]) < 4
        ]
        
        if len(independent_groups) > 2:
            recommendations.append(
                f"{len(independent_groups)} groups can potentially be migrated in parallel"
            )
        
        # Dependency-based sequencing
        dep_groups = [g for g in move_groups if g["group_type"] == "dependency_cluster"]
        if dep_groups:
            recommendations.append(
                "Migrate dependency clusters as atomic units to maintain system integrity"
            )
        
        return recommendations