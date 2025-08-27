"""
Flow Handler Helper Methods
Internal utility methods for flow processing
"""

import logging
from typing import Dict

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class FlowHandlerHelpers:
    """Helper methods for flow processing operations"""

    @staticmethod
    async def check_actual_data_via_import_id(flow) -> Dict:
        """Check for actual data via data_import_id - CRITICAL ARCHITECTURE FIX"""
        try:
            if not flow.data_import_id:
                return {
                    "has_import_data": False,
                    "has_field_mappings": False,
                    "field_mapping_count": 0,
                }

            from sqlalchemy import text

            async with AsyncSessionLocal() as db:
                # Check for field mappings (proves data was imported and mapped)
                result = await db.execute(
                    text(
                        """
                    SELECT COUNT(*) as mapping_count,
                           COUNT(CASE WHEN status = 'approved' THEN 1 END)
                           as approved_count
                    FROM import_field_mappings
                    WHERE data_import_id = :data_import_id
                """
                    ),
                    {"data_import_id": flow.data_import_id},
                )

                row = result.fetchone()
                mapping_count = row.mapping_count if row else 0
                approved_count = row.approved_count if row else 0

                # Check for raw imported data
                data_result = await db.execute(
                    text(
                        """
                    SELECT COUNT(*) as data_count
                    FROM data_imports
                    WHERE id = :data_import_id AND status IN
                    ('completed', 'processing', 'discovery_initiated')
                """
                    ),
                    {"data_import_id": flow.data_import_id},
                )

                data_row = data_result.fetchone()
                has_import_data = (data_row.data_count > 0) if data_row else False

                logger.info(
                    f"Data import check for {flow.data_import_id}: "
                    f"mappings={mapping_count}, approved={approved_count}, "
                    f"has_data={has_import_data}"
                )

                return {
                    "has_import_data": has_import_data,
                    "has_field_mappings": mapping_count > 0,
                    "field_mapping_count": mapping_count,
                    "approved_mappings": approved_count,
                    "data_import_exists": has_import_data,
                }

        except Exception as e:
            logger.error(f"Error checking actual data via import_id: {e}")
            return {
                "has_import_data": False,
                "has_field_mappings": False,
                "field_mapping_count": 0,
            }

    @staticmethod
    def determine_actual_current_phase(actual_phases: Dict, flow) -> str:
        """Determine current phase based on actual data detection"""
        try:
            # Phase order for discovery flows
            phase_order = [
                "data_import",
                "field_mapping",
                "data_cleansing",
                "asset_inventory",
                "dependency_analysis",
                "tech_debt_assessment",
            ]

            # Find the first incomplete phase
            for phase in phase_order:
                if not actual_phases.get(phase, False):
                    return phase

            # All phases complete
            return "completed"

        except Exception as e:
            logger.error(f"Error determining current phase: {e}")
            return "data_import"

    @staticmethod
    def determine_next_phase(actual_phases: Dict) -> str:
        """Determine next phase based on actual completion status"""
        try:
            # Phase progression mapping
            phase_progression = {
                "data_import": "field_mapping",
                "field_mapping": "data_cleansing",
                "data_cleansing": "asset_inventory",
                "asset_inventory": "dependency_analysis",
                "dependency_analysis": "tech_debt_assessment",
                "tech_debt_assessment": "completed",
            }

            # Find current phase
            current_phase = FlowHandlerHelpers.determine_actual_current_phase(
                actual_phases, None
            )

            # Return next phase
            return phase_progression.get(current_phase, "completed")

        except Exception as e:
            logger.error(f"Error determining next phase: {e}")
            return "field_mapping"
