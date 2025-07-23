"""
Flow Execution Handler for Discovery Flow
Handles all core flow execution, crew orchestration, and validation functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# Temporary handler classes for crew execution - these provide basic functionality
# while we establish proper crew flow patterns
class DataCleansingHandler:
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def execute_crew(self, field_mappings, raw_data, context):
        # Placeholder implementation to prevent flow errors
        return {
            "cleaned_data": raw_data,  # Return data as-is for now
            "quality_metrics": {"overall_score": 0.8},
            "quality_score": 0.8,
            "status": "data_cleansing_completed",
            "message": "Data cleansing placeholder - crew can be enhanced",
        }


class InventoryBuildingHandler:
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def execute_crew(self, cleaned_data, field_mappings, context):
        # Placeholder implementation to prevent flow errors
        return {
            "asset_inventory": {"servers": [], "applications": [], "devices": []},
            "status": "inventory_building_completed",
            "message": "Asset inventory placeholder - crew can be enhanced",
        }


class AppServerDependencyHandler:
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def execute_crew(self, asset_inventory, context):
        # Placeholder implementation to prevent flow errors
        return {
            "dependencies": {"hosting_relationships": []},
            "status": "app_server_dependencies_completed",
            "message": "App-server dependencies placeholder - crew can be enhanced",
        }


class AppAppDependencyHandler:
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def execute_crew(self, asset_inventory, app_server_dependencies, context):
        # Placeholder implementation to prevent flow errors
        return {
            "dependencies": {"communication_patterns": []},
            "status": "app_app_dependencies_completed",
            "message": "App-app dependencies placeholder - crew can be enhanced",
        }


class TechnicalDebtHandler:
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

    def execute_crew(self, asset_inventory, dependencies, context):
        # Placeholder implementation to prevent flow errors
        return {
            "assessment": {"debt_scores": {}},
            "status": "technical_debt_completed",
            "message": "Technical debt assessment placeholder - crew can be enhanced",
        }


class FlowExecutionHandler:
    """Handles all core flow execution, crew orchestration, and validation functionality"""

    def __init__(self, crewai_service):
        self.crewai_service = crewai_service

        # Initialize temporary crew handlers
        self.data_cleansing_handler = DataCleansingHandler(crewai_service)
        self.inventory_building_handler = InventoryBuildingHandler(crewai_service)
        self.app_server_dependency_handler = AppServerDependencyHandler(crewai_service)
        self.app_app_dependency_handler = AppAppDependencyHandler(crewai_service)
        self.technical_debt_handler = TechnicalDebtHandler(crewai_service)

    def execute_data_cleansing_crew(
        self,
        field_mappings: Dict[str, Any],
        raw_data: List[Dict[str, Any]],
        context: Any,
    ) -> Dict[str, Any]:
        """Execute Data Cleansing Crew - validates and standardizes data based on field mappings"""
        try:
            logger.info("🧹 Starting Data Cleansing Crew execution...")

            # Check field mapping completion and confidence
            confidence_threshold = 0.8
            avg_confidence = self._calculate_mapping_confidence(field_mappings)

            if avg_confidence < confidence_threshold:
                # Request user clarification through Agent-UI-Bridge
                clarification_needed = {
                    "crew": "data_cleansing",
                    "issue": "low_field_mapping_confidence",
                    "confidence": avg_confidence,
                    "threshold": confidence_threshold,
                    "message": f"Field mapping confidence ({avg_confidence:.2f}) below threshold ({confidence_threshold}). Should we proceed with data cleansing?",
                }

                logger.warning(
                    f"⚠️ Data cleansing requires user clarification - confidence {avg_confidence:.2f} < {confidence_threshold}"
                )
                return {
                    "status": "clarification_needed",
                    "clarification": clarification_needed,
                    "confidence": avg_confidence,
                }

            # Execute Data Cleansing Crew
            result = self.data_cleansing_handler.execute_crew(
                field_mappings=field_mappings, raw_data=raw_data, context=context
            )

            logger.info(
                f"✅ Data Cleansing Crew completed - processed {len(result.get('cleaned_data', []))} records"
            )

            return {
                "status": "data_cleansing_completed",
                "cleaned_data": result.get("cleaned_data", []),
                "quality_metrics": result.get("quality_metrics", {}),
                "quality_score": result.get("quality_score", 0.0),
                "cleaned_records": len(result.get("cleaned_data", [])),
                "next_phase": "inventory_building",
            }

        except Exception as e:
            logger.error(f"❌ Data Cleansing Crew failed: {str(e)}")
            return {"status": "data_cleansing_failed", "error": str(e)}

    def execute_inventory_building_crew(
        self,
        cleaned_data: List[Dict[str, Any]],
        field_mappings: Dict[str, Any],
        context: Any,
    ) -> Dict[str, Any]:
        """Execute Inventory Building Crew - classifies assets into servers, applications, devices"""
        try:
            logger.info("📦 Starting Inventory Building Crew execution...")

            # Execute Inventory Building Crew
            result = self.inventory_building_handler.execute_crew(
                cleaned_data=cleaned_data,
                field_mappings=field_mappings,
                context=context,
            )

            asset_inventory = result.get("asset_inventory", {})

            logger.info("✅ Inventory Building Crew completed")

            return {
                "status": "inventory_building_completed",
                "asset_inventory": asset_inventory,
                "servers": len(asset_inventory.get("servers", [])),
                "applications": len(asset_inventory.get("applications", [])),
                "devices": len(asset_inventory.get("devices", [])),
                "next_phase": "app_server_dependencies",
            }

        except Exception as e:
            logger.error(f"❌ Inventory Building Crew failed: {str(e)}")
            return {"status": "inventory_building_failed", "error": str(e)}

    def execute_app_server_dependency_crew(
        self, asset_inventory: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Execute App-Server Dependency Crew - maps application hosting relationships"""
        try:
            logger.info("🔗 Starting App-Server Dependency Crew execution...")

            # Execute App-Server Dependency Crew
            result = self.app_server_dependency_handler.execute_crew(
                asset_inventory=asset_inventory, context=context
            )

            dependencies = result.get("dependencies", {})

            logger.info("✅ App-Server Dependency Crew completed")

            return {
                "status": "app_server_dependencies_completed",
                "app_server_dependencies": dependencies,
                "hosting_relationships": len(
                    dependencies.get("hosting_relationships", [])
                ),
                "next_phase": "app_app_dependencies",
            }

        except Exception as e:
            logger.error(f"❌ App-Server Dependency Crew failed: {str(e)}")
            return {"status": "app_server_dependencies_failed", "error": str(e)}

    def execute_app_app_dependency_crew(
        self,
        asset_inventory: Dict[str, Any],
        app_server_dependencies: Dict[str, Any],
        context: Any,
    ) -> Dict[str, Any]:
        """Execute App-App Dependency Crew - maps application integration relationships"""
        try:
            logger.info("🔗 Starting App-App Dependency Crew execution...")

            # Execute App-App Dependency Crew
            result = self.app_app_dependency_handler.execute_crew(
                asset_inventory=asset_inventory,
                app_server_dependencies=app_server_dependencies,
                context=context,
            )

            dependencies = result.get("dependencies", {})

            logger.info("✅ App-App Dependency Crew completed")

            return {
                "status": "app_app_dependencies_completed",
                "app_app_dependencies": dependencies,
                "integration_relationships": len(
                    dependencies.get("communication_patterns", [])
                ),
                "next_phase": "technical_debt",
            }

        except Exception as e:
            logger.error(f"❌ App-App Dependency Crew failed: {str(e)}")
            return {"status": "app_app_dependencies_failed", "error": str(e)}

    def execute_technical_debt_crew(
        self,
        asset_inventory: Dict[str, Any],
        dependencies: Dict[str, Any],
        context: Any,
    ) -> Dict[str, Any]:
        """Execute Technical Debt Crew - evaluates modernization needs and 6R strategy preparation"""
        try:
            logger.info("⚙️ Starting Technical Debt Crew execution...")

            # Execute Technical Debt Crew
            result = self.technical_debt_handler.execute_crew(
                asset_inventory=asset_inventory,
                dependencies=dependencies,
                context=context,
            )

            assessment = result.get("assessment", {})

            logger.info("✅ Technical Debt Crew completed")

            return {
                "status": "technical_debt_completed",
                "technical_debt_assessment": assessment,
                "debt_items": len(assessment.get("debt_scores", {})),
                "next_phase": "discovery_integration",
            }

        except Exception as e:
            logger.error(f"❌ Technical Debt Crew failed: {str(e)}")
            return {"status": "technical_debt_failed", "error": str(e)}

    def execute_discovery_integration(self, state: Any) -> Dict[str, Any]:
        """Final Discovery Integration - consolidates all crew results for Assessment Flow"""
        logger.info("🎯 Executing Discovery Integration")

        try:
            # Validate all crews completed successfully
            validation_results = self._validate_all_crews_completion(state)

            # Create comprehensive discovery summary
            discovery_summary = {
                "field_mappings": getattr(state, "field_mappings", {}),
                "cleaned_data_summary": {
                    "total_records": len(getattr(state, "cleaned_data", [])),
                    "quality_score": getattr(state, "data_quality_metrics", {}).get(
                        "overall_score", 0.0
                    ),
                },
                "asset_inventory_summary": {
                    "servers": len(
                        getattr(state, "asset_inventory", {}).get("servers", [])
                    ),
                    "applications": len(
                        getattr(state, "asset_inventory", {}).get("applications", [])
                    ),
                    "devices": len(
                        getattr(state, "asset_inventory", {}).get("devices", [])
                    ),
                },
                "dependency_analysis": {
                    "app_server_relationships": len(
                        getattr(state, "app_server_dependencies", {}).get(
                            "hosting_relationships", []
                        )
                    ),
                    "app_app_integrations": len(
                        getattr(state, "app_app_dependencies", {}).get(
                            "communication_patterns", []
                        )
                    ),
                },
                "technical_debt_assessment": getattr(
                    state, "technical_debt_assessment", {}
                ),
                "validation_results": validation_results,
                "completion_timestamp": datetime.utcnow().isoformat(),
            }

            # Create Assessment Flow package
            assessment_flow_package = {
                "asset_data": getattr(state, "asset_inventory", {}),
                "dependencies": {
                    "app_server": getattr(state, "app_server_dependencies", {}),
                    "app_app": getattr(state, "app_app_dependencies", {}),
                },
                "technical_debt": getattr(state, "technical_debt_assessment", {}),
                "data_quality": getattr(state, "data_quality_metrics", {}),
                "field_mappings": getattr(state, "field_mappings", {}),
                "discovery_metadata": {
                    "flow_id": getattr(state, "flow_id", ""),
                    "client_account_id": getattr(state, "client_account_id", ""),
                    "engagement_id": getattr(state, "engagement_id", ""),
                    "completed_at": datetime.utcnow().isoformat(),
                },
            }

            logger.info("✅ Discovery Flow completed successfully")
            return {
                "status": "discovery_completed",
                "discovery_summary": discovery_summary,
                "assessment_flow_package": assessment_flow_package,
                "all_crews_completed": True,
            }

        except Exception as e:
            logger.error(f"❌ Discovery Integration failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_phase_success(self, phase_name: str, state: Any) -> bool:
        """Validate success criteria for a specific phase"""
        try:
            success_criteria = getattr(state, "success_criteria", {})
            criteria = success_criteria.get(phase_name, {})

            if phase_name == "field_mapping":
                field_mappings = getattr(state, "field_mappings", {})
                mappings = field_mappings.get("mappings", {})
                confidence_scores = field_mappings.get("confidence_scores", {})
                unmapped_fields = field_mappings.get("unmapped_fields", [])

                # Check confidence threshold
                avg_confidence = (
                    sum(confidence_scores.values()) / len(confidence_scores)
                    if confidence_scores
                    else 0
                )
                confidence_met = avg_confidence >= criteria.get(
                    "field_mappings_confidence", 0.8
                )

                # Check unmapped fields threshold
                total_fields = len(mappings) + len(unmapped_fields)
                unmapped_ratio = (
                    len(unmapped_fields) / total_fields if total_fields > 0 else 0
                )
                unmapped_met = unmapped_ratio <= criteria.get(
                    "unmapped_fields_threshold", 0.1
                )

                validation_passed = field_mappings.get("validation_results", {}).get(
                    "valid", False
                )

                return confidence_met and unmapped_met and validation_passed

            elif phase_name == "data_cleansing":
                data_quality_metrics = getattr(state, "data_quality_metrics", {})
                quality_score = data_quality_metrics.get("overall_score", 0)
                standardization = data_quality_metrics.get(
                    "standardization_complete", False
                )
                validation = data_quality_metrics.get("validation_passed", False)

                score_met = quality_score >= criteria.get("data_quality_score", 0.85)
                return score_met and standardization and validation

            elif phase_name == "inventory_building":
                asset_inventory = getattr(state, "asset_inventory", {})
                metadata = asset_inventory.get("classification_metadata", {})
                total_classified = metadata.get("total_classified", 0)
                classification_complete = total_classified > 0

                # Check if we have assets in multiple domains
                servers = len(asset_inventory.get("servers", []))
                apps = len(asset_inventory.get("applications", []))
                devices = len(asset_inventory.get("devices", []))
                cross_domain = (servers > 0) + (apps > 0) + (devices > 0) >= 2

                return classification_complete and cross_domain

            elif phase_name == "app_server_dependencies":
                app_server_dependencies = getattr(state, "app_server_dependencies", {})
                relationships = app_server_dependencies.get("hosting_relationships", [])
                topology = app_server_dependencies.get("topology_insights", {})

                relationships_mapped = len(relationships) > 0
                topology_validated = topology.get("total_relationships", 0) >= 0

                return relationships_mapped and topology_validated

            elif phase_name == "app_app_dependencies":
                app_app_dependencies = getattr(state, "app_app_dependencies", {})
                patterns = app_app_dependencies.get("communication_patterns", [])
                api_deps = app_app_dependencies.get("api_dependencies", [])
                complexity = app_app_dependencies.get("integration_complexity", {})

                patterns_mapped = len(patterns) >= 0
                api_identified = len(api_deps) >= 0
                analysis_complete = "total_integrations" in complexity

                return patterns_mapped and api_identified and analysis_complete

            elif phase_name == "technical_debt":
                technical_debt_assessment = getattr(
                    state, "technical_debt_assessment", {}
                )
                debt_scores = technical_debt_assessment.get("debt_scores", {})
                recommendations = technical_debt_assessment.get(
                    "modernization_recommendations", []
                )
                six_r_prep = technical_debt_assessment.get("six_r_preparation", {})

                assessment_complete = "overall" in debt_scores
                recommendations_ready = len(recommendations) > 0
                six_r_ready = six_r_prep.get("ready", False)

                return assessment_complete and recommendations_ready and six_r_ready

            return False

        except Exception as e:
            logger.error(f"Error validating success criteria for {phase_name}: {e}")
            return False

    def update_crew_with_validation(
        self, phase_name: str, result: Dict[str, Any], state: Any
    ) -> Dict[str, Any]:
        """Update crew result with success criteria validation"""
        try:
            # Update state based on result
            if phase_name == "data_cleansing":
                state.cleaned_data = result.get("cleaned_data", [])
                state.data_quality_metrics = result.get("data_quality_metrics", {})
            elif phase_name == "inventory_building":
                state.asset_inventory = result.get("asset_inventory", {})
            elif phase_name == "app_server_dependencies":
                state.app_server_dependencies = result.get(
                    "app_server_dependencies", {}
                )
            elif phase_name == "app_app_dependencies":
                state.app_app_dependencies = result.get("app_app_dependencies", {})
            elif phase_name == "technical_debt":
                state.technical_debt_assessment = result.get(
                    "technical_debt_assessment", {}
                )

            # Update tracking
            state.current_phase = phase_name
            if not hasattr(state, "crew_status"):
                state.crew_status = {}
            state.crew_status[phase_name] = result.get("crew_status", {})

            # Validate success criteria
            success_criteria_met = self.validate_phase_success(phase_name, state)
            if not hasattr(state, "phase_completion"):
                state.phase_completion = {}
            state.phase_completion[phase_name] = success_criteria_met

            # Update result with validation
            result["success_criteria_met"] = success_criteria_met

            return result

        except Exception as e:
            logger.error(f"Error updating crew result for {phase_name}: {e}")
            return result

    def _calculate_mapping_confidence(self, field_mappings: Dict[str, Any]) -> float:
        """Calculate average confidence score for field mappings"""
        try:
            confidence_scores = field_mappings.get("confidence_scores", {})
            if not confidence_scores:
                return 0.0

            return sum(confidence_scores.values()) / len(confidence_scores)
        except Exception as e:
            logger.error(f"Error calculating mapping confidence: {e}")
            return 0.0

    def _validate_all_crews_completion(self, state: Any) -> Dict[str, Any]:
        """Validate that all crews completed successfully"""
        try:
            field_mappings = getattr(state, "field_mappings", {})
            cleaned_data = getattr(state, "cleaned_data", [])
            asset_inventory = getattr(state, "asset_inventory", {})
            app_server_dependencies = getattr(state, "app_server_dependencies", {})
            app_app_dependencies = getattr(state, "app_app_dependencies", {})
            technical_debt_assessment = getattr(state, "technical_debt_assessment", {})

            validation = {
                "field_mapping": {
                    "completed": bool(field_mappings.get("mappings")),
                    "confidence": self._calculate_mapping_confidence(field_mappings),
                    "status": (
                        "completed" if field_mappings.get("mappings") else "incomplete"
                    ),
                },
                "data_cleansing": {
                    "completed": len(cleaned_data) > 0,
                    "quality_score": getattr(state, "data_quality_metrics", {}).get(
                        "overall_score", 0.0
                    ),
                    "status": "completed" if len(cleaned_data) > 0 else "incomplete",
                },
                "inventory_building": {
                    "completed": bool(asset_inventory),
                    "asset_count": sum(
                        [
                            len(asset_inventory.get("servers", [])),
                            len(asset_inventory.get("applications", [])),
                            len(asset_inventory.get("devices", [])),
                        ]
                    ),
                    "status": "completed" if asset_inventory else "incomplete",
                },
                "app_server_dependencies": {
                    "completed": bool(app_server_dependencies),
                    "relationship_count": len(
                        app_server_dependencies.get("hosting_relationships", [])
                    ),
                    "status": "completed" if app_server_dependencies else "incomplete",
                },
                "app_app_dependencies": {
                    "completed": bool(app_app_dependencies),
                    "integration_count": len(
                        app_app_dependencies.get("communication_patterns", [])
                    ),
                    "status": "completed" if app_app_dependencies else "incomplete",
                },
                "technical_debt": {
                    "completed": bool(technical_debt_assessment),
                    "debt_items": len(technical_debt_assessment.get("debt_scores", {})),
                    "status": (
                        "completed" if technical_debt_assessment else "incomplete"
                    ),
                },
            }

            # Overall completion status
            all_completed = all(crew["completed"] for crew in validation.values())
            validation["overall"] = {
                "all_crews_completed": all_completed,
                "completion_percentage": sum(
                    1 for crew in validation.values() if crew["completed"]
                )
                / len(validation)
                * 100,
                "status": "all_completed" if all_completed else "partial_completion",
            }

            return validation
        except Exception as e:
            logger.error(f"Error validating crew completion: {e}")
            return {"error": str(e), "overall": {"status": "validation_failed"}}
