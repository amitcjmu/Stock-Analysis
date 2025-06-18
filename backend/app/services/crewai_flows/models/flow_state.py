"""
Discovery Flow State Model
Enhanced state management for Discovery Flow with CrewAI best practices
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field

class DiscoveryFlowState(BaseModel):
    """Enhanced state for Discovery Flow with CrewAI best practices"""
    
    # Flow identification - using flow service instead of fingerprinting
    session_id: str = ""
    client_account_id: str = ""
    engagement_id: str = ""
    user_id: str = ""
    flow_id: str = ""
    
    # Planning and coordination
    overall_plan: Dict[str, Any] = {}
    crew_coordination: Dict[str, Any] = {}
    agent_assignments: Dict[str, List[str]] = {}
    
    # Memory references
    shared_memory_id: str = ""
    shared_memory_reference: Any = None  # Direct reference to shared memory instance
    knowledge_base_refs: List[str] = []
    
    # Learning Privacy and Isolation Controls
    learning_scope: str = "engagement"  # "engagement", "client", "global", "disabled"
    cross_client_learning_enabled: bool = False
    learning_data_sharing_consent: bool = False
    learning_audit_trail: List[Dict[str, Any]] = []
    memory_isolation_level: str = "strict"  # "strict", "moderate", "open"
    data_residency_requirements: Dict[str, Any] = {}
    
    # Enhanced Phase tracking with manager oversight
    current_phase: str = "initialization"
    phase_managers: Dict[str, str] = Field(default_factory=lambda: {
        "field_mapping": "Field Mapping Manager",
        "data_cleansing": "Data Quality Manager",
        "inventory_building": "Inventory Manager", 
        "app_server_dependencies": "Dependency Manager",
        "app_app_dependencies": "Integration Manager",
        "technical_debt": "Technical Debt Manager"
    })
    crew_status: Dict[str, Dict[str, Any]] = {}
    agent_collaboration_map: Dict[str, List[str]] = Field(default_factory=lambda: {
        "field_mapping": ["Schema Analysis Expert", "Attribute Mapping Specialist"],
        "data_cleansing": ["Data Validation Expert", "Data Standardization Specialist"],
        "inventory_building": ["Server Classification Expert", "Application Discovery Expert", "Device Classification Expert"],
        "app_server_dependencies": ["Hosting Relationship Expert", "Migration Impact Analyst"],
        "app_app_dependencies": ["Integration Pattern Expert", "Business Flow Analyst"],
        "technical_debt": ["Legacy Systems Analyst", "Modernization Expert", "Risk Assessment Specialist"]
    })
    
    # Success criteria tracking for enhanced validation
    success_criteria: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "field_mapping": {"field_mappings_confidence": 0.8, "unmapped_fields_threshold": 0.1, "validation_passed": True},
        "data_cleansing": {"data_quality_score": 0.85, "standardization_complete": True, "validation_passed": True},
        "inventory_building": {"asset_classification_complete": True, "cross_domain_validation": True, "classification_confidence": 0.9},
        "app_server_dependencies": {"hosting_relationships_mapped": True, "topology_validated": True, "dependency_confidence": 0.8},
        "app_app_dependencies": {"communication_patterns_mapped": True, "api_dependencies_identified": True, "integration_analysis_complete": True},
        "technical_debt": {"debt_assessment_complete": True, "six_r_recommendations_ready": True, "risk_analysis_complete": True}
    })
    
    # Phase completion tracking for flow control
    phase_completion: Dict[str, bool] = Field(default_factory=lambda: {
        "field_mapping": False, "data_cleansing": False, "inventory_building": False,
        "app_server_dependencies": False, "app_app_dependencies": False, "technical_debt": False
    })
    
    # Input data
    raw_data: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    data_source_type: str = "cmdb"
    
    # Data processing results with provenance
    field_mappings: Dict[str, Any] = {
        "mappings": {},
        "confidence_scores": {},
        "unmapped_fields": [],
        "validation_results": {},
        "agent_insights": {}
    }
    
    cleaned_data: List[Dict[str, Any]] = []
    data_quality_metrics: Dict[str, Any] = {}
    
    asset_inventory: Dict[str, List[Dict[str, Any]]] = {
        "servers": [],
        "applications": [],
        "devices": [],
        "classification_metadata": {}
    }
    
    app_server_dependencies: Dict[str, Any] = {
        "hosting_relationships": [],
        "resource_mappings": [],
        "topology_insights": {}
    }
    
    app_app_dependencies: Dict[str, Any] = {
        "communication_patterns": [],
        "api_dependencies": [],
        "integration_complexity": {}
    }
    
    technical_debt_assessment: Dict[str, Any] = {
        "debt_scores": {},
        "modernization_recommendations": [],
        "risk_assessments": {},
        "six_r_preparation": {}
    }
    
    # Final integration for Assessment Flow
    discovery_summary: Dict[str, Any] = {}
    assessment_flow_package: Dict[str, Any] = {}
    
    # Error tracking
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    
    def validate_field_mapping_success(self) -> Dict[str, Any]:
        """Validate field mapping phase success criteria"""
        criteria = self.success_criteria["field_mapping"]
        validation = {
            "phase": "field_mapping",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check field mapping confidence
        confidence_scores = self.field_mappings.get("confidence_scores", {})
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        else:
            avg_confidence = 0.0
        confidence_met = avg_confidence >= criteria["field_mappings_confidence"]
        validation["details"]["field_mappings_confidence"] = {
            "required": criteria["field_mappings_confidence"],
            "actual": avg_confidence,
            "passed": confidence_met
        }
        
        # Check unmapped fields threshold
        total_fields = len(self.field_mappings.get("mappings", {})) + len(self.field_mappings.get("unmapped_fields", []))
        unmapped_ratio = len(self.field_mappings.get("unmapped_fields", [])) / max(total_fields, 1)
        unmapped_met = unmapped_ratio <= criteria["unmapped_fields_threshold"]
        validation["details"]["unmapped_fields_threshold"] = {
            "required": criteria["unmapped_fields_threshold"],
            "actual": unmapped_ratio,
            "passed": unmapped_met
        }
        
        # Overall validation
        validation["success"] = confidence_met and unmapped_met
        
        if not validation["success"]:
            if not confidence_met:
                validation["recommendations"].append("Improve field mapping confidence through additional analysis")
            if not unmapped_met:
                validation["recommendations"].append("Reduce unmapped fields through enhanced pattern recognition")
        
        return validation
    
    def validate_data_cleansing_success(self) -> Dict[str, Any]:
        """Validate data cleansing phase success criteria"""
        criteria = self.success_criteria["data_cleansing"]
        validation = {
            "phase": "data_cleansing",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check data quality score
        quality_score = self.data_quality_metrics.get("overall_score", 0.0)
        quality_met = quality_score >= criteria["data_quality_score"]
        validation["details"]["data_quality_score"] = {
            "required": criteria["data_quality_score"],
            "actual": quality_score,
            "passed": quality_met
        }
        
        # Check standardization completion
        standardization_complete = len(self.cleaned_data) > 0 and self.data_quality_metrics.get("standardization_complete", False)
        validation["details"]["standardization_complete"] = {
            "required": True,
            "actual": standardization_complete,
            "passed": standardization_complete
        }
        
        # Overall validation
        validation["success"] = quality_met and standardization_complete
        
        if not validation["success"]:
            if not quality_met:
                validation["recommendations"].append("Improve data quality through enhanced validation rules")
            if not standardization_complete:
                validation["recommendations"].append("Complete data standardization process")
        
        return validation
    
    def validate_inventory_building_success(self) -> Dict[str, Any]:
        """Validate inventory building phase success criteria"""
        criteria = self.success_criteria["inventory_building"]
        validation = {
            "phase": "inventory_building",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check asset classification completion
        total_assets = len(self.asset_inventory["servers"]) + len(self.asset_inventory["applications"]) + len(self.asset_inventory["devices"])
        classification_complete = total_assets > 0
        validation["details"]["asset_classification_complete"] = {
            "required": True,
            "actual": classification_complete,
            "passed": classification_complete
        }
        
        # Check cross-domain validation
        cross_domain_validation = len(self.asset_inventory.get("classification_metadata", {})) > 0
        validation["details"]["cross_domain_validation"] = {
            "required": True,
            "actual": cross_domain_validation,
            "passed": cross_domain_validation
        }
        
        # Check classification confidence
        avg_confidence = self.asset_inventory.get("classification_metadata", {}).get("average_confidence", 0.0)
        confidence_met = avg_confidence >= criteria["classification_confidence"]
        validation["details"]["classification_confidence"] = {
            "required": criteria["classification_confidence"],
            "actual": avg_confidence,
            "passed": confidence_met
        }
        
        # Overall validation
        validation["success"] = classification_complete and cross_domain_validation and confidence_met
        
        if not validation["success"]:
            if not classification_complete:
                validation["recommendations"].append("Complete asset classification across all domains")
            if not cross_domain_validation:
                validation["recommendations"].append("Enhance cross-domain validation and relationship mapping")
            if not confidence_met:
                validation["recommendations"].append("Improve classification confidence through better pattern recognition")
        
        return validation
    
    def validate_app_server_dependencies_success(self) -> Dict[str, Any]:
        """Validate app-server dependencies phase success criteria"""
        criteria = self.success_criteria["app_server_dependencies"]
        validation = {
            "phase": "app_server_dependencies",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check hosting relationships mapping
        hosting_mapped = len(self.app_server_dependencies.get("hosting_relationships", [])) > 0
        validation["details"]["hosting_relationships_mapped"] = {
            "required": True,
            "actual": hosting_mapped,
            "passed": hosting_mapped
        }
        
        # Check topology validation
        topology_validated = len(self.app_server_dependencies.get("topology_insights", {})) > 0
        validation["details"]["topology_validated"] = {
            "required": True,
            "actual": topology_validated,
            "passed": topology_validated
        }
        
        # Check dependency confidence
        dependency_confidence = self.app_server_dependencies.get("topology_insights", {}).get("confidence_score", 0.0)
        confidence_met = dependency_confidence >= criteria["dependency_confidence"]
        validation["details"]["dependency_confidence"] = {
            "required": criteria["dependency_confidence"],
            "actual": dependency_confidence,
            "passed": confidence_met
        }
        
        # Overall validation
        validation["success"] = hosting_mapped and topology_validated and confidence_met
        
        if not validation["success"]:
            if not hosting_mapped:
                validation["recommendations"].append("Complete hosting relationship mapping between applications and servers")
            if not topology_validated:
                validation["recommendations"].append("Validate infrastructure topology and dependencies")
            if not confidence_met:
                validation["recommendations"].append("Improve dependency analysis confidence")
        
        return validation
    
    def validate_app_app_dependencies_success(self) -> Dict[str, Any]:
        """Validate app-app dependencies phase success criteria"""
        criteria = self.success_criteria["app_app_dependencies"]
        validation = {
            "phase": "app_app_dependencies",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check communication patterns mapping
        patterns_mapped = len(self.app_app_dependencies.get("communication_patterns", [])) > 0
        validation["details"]["communication_patterns_mapped"] = {
            "required": True,
            "actual": patterns_mapped,
            "passed": patterns_mapped
        }
        
        # Check API dependencies identification
        api_deps_identified = len(self.app_app_dependencies.get("api_dependencies", [])) > 0
        validation["details"]["api_dependencies_identified"] = {
            "required": True,
            "actual": api_deps_identified,
            "passed": api_deps_identified
        }
        
        # Check integration analysis completion
        integration_complete = len(self.app_app_dependencies.get("integration_complexity", {})) > 0
        validation["details"]["integration_analysis_complete"] = {
            "required": True,
            "actual": integration_complete,
            "passed": integration_complete
        }
        
        # Overall validation
        validation["success"] = patterns_mapped and api_deps_identified and integration_complete
        
        if not validation["success"]:
            if not patterns_mapped:
                validation["recommendations"].append("Complete communication pattern analysis between applications")
            if not api_deps_identified:
                validation["recommendations"].append("Identify and map API dependencies")
            if not integration_complete:
                validation["recommendations"].append("Complete integration complexity analysis")
        
        return validation
    
    def validate_technical_debt_success(self) -> Dict[str, Any]:
        """Validate technical debt phase success criteria"""
        criteria = self.success_criteria["technical_debt"]
        validation = {
            "phase": "technical_debt",
            "success": True,
            "details": {},
            "recommendations": []
        }
        
        # Check debt assessment completion
        debt_complete = len(self.technical_debt_assessment.get("debt_scores", {})) > 0
        validation["details"]["debt_assessment_complete"] = {
            "required": True,
            "actual": debt_complete,
            "passed": debt_complete
        }
        
        # Check 6R recommendations readiness
        six_r_ready = len(self.technical_debt_assessment.get("six_r_preparation", {})) > 0
        validation["details"]["six_r_recommendations_ready"] = {
            "required": True,
            "actual": six_r_ready,
            "passed": six_r_ready
        }
        
        # Check risk analysis completion
        risk_complete = len(self.technical_debt_assessment.get("risk_assessments", {})) > 0
        validation["details"]["risk_analysis_complete"] = {
            "required": True,
            "actual": risk_complete,
            "passed": risk_complete
        }
        
        # Overall validation
        validation["success"] = debt_complete and six_r_ready and risk_complete
        
        if not validation["success"]:
            if not debt_complete:
                validation["recommendations"].append("Complete technical debt assessment across all assets")
            if not six_r_ready:
                validation["recommendations"].append("Prepare 6R strategy recommendations for Assessment Flow")
            if not risk_complete:
                validation["recommendations"].append("Complete risk analysis for migration planning")
        
        return validation
    
    def validate_phase_success(self, phase: str) -> Dict[str, Any]:
        """Validate success criteria for a specific phase"""
        if phase == "field_mapping":
            return self.validate_field_mapping_success()
        elif phase == "data_cleansing":
            return {"phase": phase, "success": len(self.cleaned_data) > 0, "details": {}}
        elif phase == "inventory_building":
            total_assets = len(self.asset_inventory["servers"]) + len(self.asset_inventory["applications"]) + len(self.asset_inventory["devices"])
            return {"phase": phase, "success": total_assets > 0, "details": {"total_assets": total_assets}}
        elif phase == "app_server_dependencies":
            return {"phase": phase, "success": len(self.app_server_dependencies.get("hosting_relationships", [])) > 0, "details": {}}
        elif phase == "app_app_dependencies":
            return {"phase": phase, "success": len(self.app_app_dependencies.get("communication_patterns", [])) > 0, "details": {}}
        elif phase == "technical_debt":
            return {"phase": phase, "success": len(self.technical_debt_assessment.get("debt_scores", {})) > 0, "details": {}}
        else:
            return {"phase": phase, "success": False, "details": {}, "recommendations": [f"Unknown phase: {phase}"]}
    
    def get_overall_success_status(self) -> Dict[str, Any]:
        """Get overall success status across all phases"""
        phases = ["field_mapping", "data_cleansing", "inventory_building", "app_server_dependencies", "app_app_dependencies", "technical_debt"]
        phase_results = {}
        overall_success = True
        
        for phase in phases:
            if self.phase_completion.get(phase, False):
                result = self.validate_phase_success(phase)
                phase_results[phase] = result
                if not result["success"]:
                    overall_success = False
            else:
                phase_results[phase] = {"success": False, "reason": "not_completed"}
                overall_success = False
        
        return {
            "overall_success": overall_success,
            "phase_results": phase_results,
            "completed_phases": sum(1 for completed in self.phase_completion.values() if completed),
            "total_phases": len(phases)
        } 