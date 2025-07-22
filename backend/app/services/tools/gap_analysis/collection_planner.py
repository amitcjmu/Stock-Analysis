"""
Collection Planner Tool - Plans optimal collection strategy for gaps
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import BASE_EFFORT_HOURS

logger = logging.getLogger(__name__)


class CollectionPlannerTool(AsyncBaseDiscoveryTool):
    """Plans optimal collection strategy for gaps"""
    
    name: str = "collection_planner"
    description: str = "Create detailed collection plans for prioritized gaps"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="collection_planner",
            description="Create detailed collection plans for prioritized gaps",
            tool_class=cls,
            categories=["gap_analysis", "planning"],
            required_params=["prioritized_gaps", "resources"],
            optional_params=["constraints"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, 
                  prioritized_gaps: List[Dict[str, Any]], 
                  resources: Dict[str, Any],
                  constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create comprehensive collection plan"""
        try:
            self.log_with_context('info', "Creating collection plan")
            
            collection_plan = {
                "plan_summary": {},
                "phases": [],
                "resource_schedule": {},
                "collection_methods": {},
                "success_metrics": [],
                "risk_mitigation": []
            }
            
            # Group gaps by priority
            immediate_gaps = [g for g in prioritized_gaps if g.get("priority_score", 0) >= 80]
            next_sprint_gaps = [g for g in prioritized_gaps if 60 <= g.get("priority_score", 0) < 80]
            backlog_gaps = [g for g in prioritized_gaps if g.get("priority_score", 0) < 60]
            
            # Create phases
            if immediate_gaps:
                phase1 = self._create_collection_phase(
                    "Phase 1: Critical Gap Resolution",
                    immediate_gaps,
                    resources,
                    duration_weeks=1
                )
                collection_plan["phases"].append(phase1)
            
            if next_sprint_gaps:
                phase2 = self._create_collection_phase(
                    "Phase 2: High Priority Collection",
                    next_sprint_gaps,
                    resources,
                    duration_weeks=2
                )
                collection_plan["phases"].append(phase2)
            
            if backlog_gaps and not constraints.get("critical_only", False):
                phase3 = self._create_collection_phase(
                    "Phase 3: Comprehensive Coverage",
                    backlog_gaps,
                    resources,
                    duration_weeks=3
                )
                collection_plan["phases"].append(phase3)
            
            # Create resource schedule
            collection_plan["resource_schedule"] = self._create_resource_schedule(
                collection_plan["phases"], resources
            )
            
            # Define collection methods
            collection_plan["collection_methods"] = self._define_collection_methods(prioritized_gaps)
            
            # Set success metrics
            collection_plan["success_metrics"] = [
                "Achieve 100% coverage of critical attributes",
                "Improve overall attribute coverage to >85%",
                "Complete Phase 1 within 1 week",
                "Maintain data quality score >80%",
                "Zero blocking gaps for migration planning"
            ]
            
            # Risk mitigation
            collection_plan["risk_mitigation"] = self._identify_risks_and_mitigations(
                prioritized_gaps, resources
            )
            
            # Summary
            total_gaps = len(prioritized_gaps)
            total_effort = sum(p["estimated_effort"] for p in collection_plan["phases"])
            
            collection_plan["plan_summary"] = {
                "total_gaps_to_address": total_gaps,
                "phases_count": len(collection_plan["phases"]),
                "total_effort_hours": total_effort,
                "estimated_duration_weeks": sum(p["duration_weeks"] for p in collection_plan["phases"]),
                "critical_gaps_in_phase1": len(immediate_gaps),
                "automation_percentage": self._calculate_automation_percentage(prioritized_gaps)
            }
            
            self.log_with_context('info', "Collection plan created successfully")
            return collection_plan
            
        except Exception as e:
            self.log_with_context('error', f"Error in collection planning: {e}")
            return {"error": str(e)}
    
    def _create_collection_phase(self, name: str, gaps: List[Dict[str, Any]], 
                                resources: Dict[str, Any], duration_weeks: int) -> Dict[str, Any]:
        """Create a collection phase"""
        phase = {
            "name": name,
            "duration_weeks": duration_weeks,
            "gaps_count": len(gaps),
            "activities": [],
            "deliverables": [],
            "estimated_effort": 0
        }
        
        # Group gaps by collection method
        method_groups = {}
        for gap in gaps:
            method = gap.get("recommended_source", "manual_collection")
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(gap)
        
        # Create activities
        for method, method_gaps in method_groups.items():
            activity = {
                "name": f"Collect via {method}",
                "method": method,
                "attributes": [g["attribute"] for g in method_gaps],
                "effort_hours": sum(self._estimate_gap_effort(g) for g in method_gaps),
                "assigned_resources": self._assign_resources(method, resources),
                "tools_required": self._identify_required_tools(method)
            }
            phase["activities"].append(activity)
            phase["estimated_effort"] += activity["effort_hours"]
        
        # Define deliverables
        phase["deliverables"] = [
            f"Complete data for {len(gaps)} attributes",
            "Data quality validation report",
            "Updated CMDB with collected data",
            "Gap closure confirmation"
        ]
        
        return phase
    
    def _create_resource_schedule(self, phases: List[Dict[str, Any]], 
                                resources: Dict[str, Any]) -> Dict[str, Any]:
        """Create resource allocation schedule"""
        schedule = {
            "team_allocation": {},
            "weekly_schedule": [],
            "resource_utilization": {}
        }
        
        team_members = resources.get("team_members", ["Analyst1", "Analyst2"])
        week_counter = 1
        
        for phase in phases:
            for week in range(phase["duration_weeks"]):
                weekly_plan = {
                    "week": week_counter,
                    "phase": phase["name"],
                    "assignments": {}
                }
                
                # Distribute activities across team
                for i, activity in enumerate(phase["activities"]):
                    assigned_to = team_members[i % len(team_members)]
                    if assigned_to not in weekly_plan["assignments"]:
                        weekly_plan["assignments"][assigned_to] = []
                    weekly_plan["assignments"][assigned_to].append(activity["name"])
                
                schedule["weekly_schedule"].append(weekly_plan)
                week_counter += 1
        
        # Calculate utilization
        for member in team_members:
            total_hours = sum(
                sum(a["effort_hours"] for a in p["activities"]) / len(team_members)
                for p in phases
            )
            schedule["resource_utilization"][member] = {
                "total_hours": total_hours,
                "average_hours_per_week": total_hours / max(1, week_counter - 1)
            }
        
        return schedule
    
    def _define_collection_methods(self, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Define collection methods and procedures"""
        methods = {}
        
        method_definitions = {
            "discovery_tools": {
                "description": "Automated discovery using scanning tools",
                "tools": ["Network scanner", "Asset discovery agent"],
                "procedure": "1. Deploy discovery agents\n2. Run network scan\n3. Validate results\n4. Import to CMDB"
            },
            "cmdb_import": {
                "description": "Import from existing CMDB or inventory systems",
                "tools": ["CMDB connector", "Data import wizard"],
                "procedure": "1. Connect to source CMDB\n2. Map fields\n3. Extract data\n4. Transform and load"
            },
            "stakeholder_input": {
                "description": "Collect via stakeholder interviews and surveys",
                "tools": ["Survey platform", "Interview templates"],
                "procedure": "1. Schedule stakeholder sessions\n2. Conduct interviews\n3. Validate responses\n4. Document findings"
            },
            "technical_interview": {
                "description": "Technical deep-dive sessions with SMEs",
                "tools": ["Technical questionnaire", "Architecture templates"],
                "procedure": "1. Identify SMEs\n2. Prepare technical questions\n3. Conduct sessions\n4. Document architecture"
            }
        }
        
        # Include only methods needed for the gaps
        used_methods = set(g.get("recommended_source", "manual_collection") for g in gaps)
        for method in used_methods:
            if method in method_definitions:
                methods[method] = method_definitions[method]
            else:
                methods[method] = {
                    "description": f"Custom collection method: {method}",
                    "tools": ["Manual forms", "Spreadsheet templates"],
                    "procedure": "1. Create collection template\n2. Gather data\n3. Validate\n4. Import"
                }
        
        return methods
    
    def _identify_risks_and_mitigations(self, gaps: List[Dict[str, Any]], 
                                       resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify collection risks and mitigations"""
        risks = []
        
        # Resource risks
        if resources.get("available_team_members", 2) < 3:
            risks.append({
                "risk": "Limited team capacity may delay collection",
                "impact": "medium",
                "mitigation": "Prioritize critical gaps and consider automation"
            })
        
        # Complexity risks
        hard_gaps = [g for g in gaps if g.get("collection_difficulty") in ["hard", "very_hard"]]
        if len(hard_gaps) > 5:
            risks.append({
                "risk": "High number of complex attributes to collect",
                "impact": "high",
                "mitigation": "Engage subject matter experts early and plan extra time"
            })
        
        # Stakeholder risks
        stakeholder_gaps = [g for g in gaps if "stakeholder" in g.get("recommended_source", "")]
        if stakeholder_gaps:
            risks.append({
                "risk": "Stakeholder availability may impact collection timeline",
                "impact": "medium",
                "mitigation": "Schedule sessions early and have backup contacts"
            })
        
        # Data quality risks
        risks.append({
            "risk": "Collected data may not meet quality standards",
            "impact": "medium",
            "mitigation": "Implement validation checkpoints and quality reviews"
        })
        
        return risks
    
    def _estimate_gap_effort(self, gap: Dict[str, Any]) -> float:
        """Estimate effort for a single gap"""
        difficulty = gap.get("collection_difficulty", "medium")
        return BASE_EFFORT_HOURS.get(difficulty, 8)
    
    def _assign_resources(self, method: str, resources: Dict[str, Any]) -> List[str]:
        """Assign appropriate resources for collection method"""
        skill_map = {
            "discovery_tools": ["technical_analyst"],
            "cmdb_import": ["data_analyst"],
            "stakeholder_input": ["business_analyst"],
            "technical_interview": ["solution_architect", "technical_analyst"],
            "manual_collection": ["data_analyst", "business_analyst"]
        }
        
        return skill_map.get(method, ["analyst"])
    
    def _identify_required_tools(self, method: str) -> List[str]:
        """Identify tools required for collection method"""
        tool_map = {
            "discovery_tools": ["ServiceNow Discovery", "Lansweeper", "Device42"],
            "cmdb_import": ["ETL tool", "Data mapping tool", "CMDB API"],
            "stakeholder_input": ["Survey tool", "Forms platform", "Interview guides"],
            "technical_interview": ["Architecture tools", "Diagramming software"],
            "manual_collection": ["Spreadsheet templates", "Data entry forms"]
        }
        
        return tool_map.get(method, ["Manual templates"])
    
    def _calculate_automation_percentage(self, gaps: List[Dict[str, Any]]) -> float:
        """Calculate percentage of gaps that can be automated"""
        automated_sources = ["discovery_tools", "cmdb_import", "monitoring_api", "cloud_api"]
        automated_gaps = [g for g in gaps if g.get("recommended_source") in automated_sources]
        
        if not gaps:
            return 0.0
        
        return (len(automated_gaps) / len(gaps)) * 100