"""
Flow State Detection Service

This service provides intelligent detection of incomplete flow initialization states
and flow routing logic to handle phase transition failures.

CC Enhanced for critical flow routing issue where Discovery Flow fails on attribute mapping
when resuming from incomplete initialization phase.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow

logger = get_logger(__name__)


class FlowInitializationIssue:
    """Represents a detected flow initialization issue"""

    def __init__(
        self,
        flow_id: str,
        issue_type: str,
        severity: str,
        description: str,
        suggested_action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.flow_id = flow_id
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.suggested_action = suggested_action
        self.metadata = metadata or {}
        self.detected_at = datetime.utcnow()


class FlowStateDetector:
    """
    Detects and analyzes flow initialization and state consistency issues.

    This service identifies when flows are in inconsistent states such as:
    - Attribute mapping phase without proper initialization
    - Field mappings exist but flow initialization returns 404
    - Missing data import linkages
    - Orphaned flow states
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        logger.info(
            f"✅ Flow State Detector initialized for client {context.client_account_id}"
        )

    async def detect_incomplete_initialization(
        self, flow_id: str
    ) -> List[FlowInitializationIssue]:
        """
        Detect incomplete flow initialization issues for a specific flow.

        Args:
            flow_id: The flow ID to analyze

        Returns:
            List of detected issues
        """
        issues = []

        try:
            logger.info(f"🔍 Analyzing flow initialization state for: {flow_id}")

            # Get master flow
            master_flow = await self._get_master_flow(flow_id)
            if not master_flow:
                issues.append(
                    FlowInitializationIssue(
                        flow_id=flow_id,
                        issue_type="missing_master_flow",
                        severity="critical",
                        description="Master flow record not found",
                        suggested_action="recreate_flow",
                        metadata={"error": "No master flow record exists"},
                    )
                )
                return issues

            # Get discovery flow if it's a discovery type
            if master_flow.flow_type == "discovery":
                discovery_flow = await self._get_discovery_flow(flow_id)
                discovery_issues = await self._analyze_discovery_flow_state(
                    master_flow, discovery_flow
                )
                issues.extend(discovery_issues)

            # Check data import linkage
            data_import_issues = await self._analyze_data_import_linkage(
                master_flow, flow_id
            )
            issues.extend(data_import_issues)

            # Check field mapping consistency
            field_mapping_issues = await self._analyze_field_mapping_consistency(
                master_flow, flow_id
            )
            issues.extend(field_mapping_issues)

            logger.info(
                f"🔍 Detected {len(issues)} initialization issues for flow {flow_id}"
            )
            return issues

        except Exception as e:
            logger.error(f"❌ Error detecting initialization issues for {flow_id}: {e}")
            issues.append(
                FlowInitializationIssue(
                    flow_id=flow_id,
                    issue_type="detection_error",
                    severity="high",
                    description=f"Error during issue detection: {str(e)}",
                    suggested_action="manual_investigation",
                )
            )
            return issues

    async def _get_master_flow(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow record"""
        try:
            query = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id
                    == self.context.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting master flow {flow_id}: {e}")
            return None

    async def _get_discovery_flow(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow record"""
        try:
            query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == self.context.client_account_id,
                    DiscoveryFlow.engagement_id == self.context.engagement_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting discovery flow {flow_id}: {e}")
            return None

    async def _analyze_discovery_flow_state(
        self,
        master_flow: CrewAIFlowStateExtensions,
        discovery_flow: Optional[DiscoveryFlow],
    ) -> List[FlowInitializationIssue]:
        """Analyze discovery flow state consistency"""
        issues = []
        flow_id = str(master_flow.flow_id)

        if not discovery_flow:
            issues.append(
                FlowInitializationIssue(
                    flow_id=flow_id,
                    issue_type="missing_discovery_flow",
                    severity="critical",
                    description="Discovery flow record not found for discovery type master flow",
                    suggested_action="create_discovery_flow_record",
                )
            )
            return issues

        # Check if flow is in attribute mapping but missing initialization
        current_phase = getattr(discovery_flow, "current_phase", None)
        if current_phase == "field_mapping" or current_phase == "attribute_mapping":
            # Check if data import is actually complete
            if not discovery_flow.data_import_completed:
                issues.append(
                    FlowInitializationIssue(
                        flow_id=flow_id,
                        issue_type="incomplete_data_import",
                        severity="high",
                        description="Flow is in field mapping phase but data import is not marked complete",
                        suggested_action="route_to_data_import",
                        metadata={
                            "current_phase": current_phase,
                            "data_import_completed": discovery_flow.data_import_completed,
                        },
                    )
                )

            # Check if flow has raw data
            if (
                not discovery_flow.imported_data
                and not discovery_flow.crewai_state_data.get("raw_data")
            ):
                issues.append(
                    FlowInitializationIssue(
                        flow_id=flow_id,
                        issue_type="missing_raw_data",
                        severity="high",
                        description="Flow is in field mapping phase but has no raw data",
                        suggested_action="route_to_data_import",
                        metadata={
                            "current_phase": current_phase,
                            "has_imported_data": bool(discovery_flow.imported_data),
                            "has_state_raw_data": bool(
                                discovery_flow.crewai_state_data.get("raw_data")
                            ),
                        },
                    )
                )

        # Check for state inconsistencies
        master_status = master_flow.flow_status
        discovery_status = discovery_flow.status
        if master_status != discovery_status:
            issues.append(
                FlowInitializationIssue(
                    flow_id=flow_id,
                    issue_type="status_inconsistency",
                    severity="medium",
                    description=(
                        f"Master flow status ({master_status}) doesn't match "
                        f"discovery flow status ({discovery_status})"
                    ),
                    suggested_action="sync_flow_status",
                    metadata={
                        "master_status": master_status,
                        "discovery_status": discovery_status,
                    },
                )
            )

        return issues

    async def _analyze_data_import_linkage(
        self, master_flow: CrewAIFlowStateExtensions, flow_id: str
    ) -> List[FlowInitializationIssue]:
        """Analyze data import linkage and consistency"""
        issues = []

        try:
            # Check if flow has data_import_id in persistence data
            persistence_data = master_flow.flow_persistence_data or {}
            data_import_id = persistence_data.get("data_import_id")

            if data_import_id:
                # Verify the data import exists and is valid
                data_import = await self._get_data_import(data_import_id)
                if not data_import:
                    issues.append(
                        FlowInitializationIssue(
                            flow_id=flow_id,
                            issue_type="invalid_data_import_reference",
                            severity="high",
                            description=f"Flow references data_import_id {data_import_id} but data import not found",
                            suggested_action="find_or_recreate_data_import",
                            metadata={"data_import_id": data_import_id},
                        )
                    )
                else:
                    # Check if data import has raw data
                    raw_data_count = await self._count_raw_import_records(
                        data_import_id
                    )
                    if raw_data_count == 0:
                        issues.append(
                            FlowInitializationIssue(
                                flow_id=flow_id,
                                issue_type="empty_data_import",
                                severity="high",
                                description=f"Data import {data_import_id} exists but has no raw data records",
                                suggested_action="reimport_data",
                                metadata={
                                    "data_import_id": data_import_id,
                                    "raw_data_count": raw_data_count,
                                },
                            )
                        )
            else:
                # No data_import_id - try to find orphaned data imports
                orphaned_imports = await self._find_orphaned_data_imports()
                if orphaned_imports:
                    issues.append(
                        FlowInitializationIssue(
                            flow_id=flow_id,
                            issue_type="missing_data_import_linkage",
                            severity="medium",
                            description="Flow has no data_import_id but orphaned data imports exist",
                            suggested_action="link_orphaned_data_import",
                            metadata={
                                "orphaned_import_count": len(orphaned_imports),
                                "orphaned_import_ids": [
                                    str(imp.id) for imp in orphaned_imports[:3]
                                ],  # Show first 3
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"❌ Error analyzing data import linkage for {flow_id}: {e}")

        return issues

    async def _analyze_field_mapping_consistency(
        self, master_flow: CrewAIFlowStateExtensions, flow_id: str
    ) -> List[FlowInitializationIssue]:
        """Analyze field mapping consistency"""
        issues = []

        try:
            # Get field mappings for this flow
            field_mappings = await self._get_field_mappings(flow_id, master_flow.id)

            if field_mappings:
                # Flow has field mappings - verify they have valid data_import_id
                data_import_ids = set()
                for mapping in field_mappings:
                    if mapping.data_import_id:
                        data_import_ids.add(mapping.data_import_id)

                if not data_import_ids:
                    issues.append(
                        FlowInitializationIssue(
                            flow_id=flow_id,
                            issue_type="orphaned_field_mappings",
                            severity="high",
                            description=f"Flow has {len(field_mappings)} field mappings but none have data_import_id",
                            suggested_action="link_field_mappings_to_data_import",
                            metadata={
                                "field_mapping_count": len(field_mappings),
                                "orphaned_mappings": True,
                            },
                        )
                    )
                else:
                    # Verify data imports exist for all referenced IDs
                    for data_import_id in data_import_ids:
                        data_import = await self._get_data_import(data_import_id)
                        if not data_import:
                            issues.append(
                                FlowInitializationIssue(
                                    flow_id=flow_id,
                                    issue_type="invalid_field_mapping_reference",
                                    severity="high",
                                    description=(
                                        f"Field mappings reference non-existent "
                                        f"data_import_id: {data_import_id}"
                                    ),
                                    suggested_action="fix_field_mapping_references",
                                    metadata={
                                        "invalid_data_import_id": str(data_import_id)
                                    },
                                )
                            )

        except Exception as e:
            logger.error(
                f"❌ Error analyzing field mapping consistency for {flow_id}: {e}"
            )

        return issues

    async def _get_data_import(self, data_import_id: str) -> Optional[DataImport]:
        """Get data import by ID"""
        try:
            query = select(DataImport).where(DataImport.id == data_import_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error getting data import {data_import_id}: {e}")
            return None

    async def _count_raw_import_records(self, data_import_id: str) -> int:
        """Count raw import records for a data import"""
        try:
            from sqlalchemy import func

            query = select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == data_import_id
            )
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(
                f"❌ Error counting raw import records for {data_import_id}: {e}"
            )
            return 0

    async def _find_orphaned_data_imports(self) -> List[DataImport]:
        """Find data imports that aren't linked to any flow"""
        try:
            query = (
                select(DataImport)
                .where(
                    and_(
                        DataImport.client_account_id == self.context.client_account_id,
                        DataImport.engagement_id == self.context.engagement_id,
                        DataImport.master_flow_id.is_(
                            None
                        ),  # Orphaned imports have no master_flow_id
                    )
                )
                .limit(10)
            )  # Limit to avoid overwhelming results

            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"❌ Error finding orphaned data imports: {e}")
            return []

    async def _get_field_mappings(
        self, flow_id: str, master_flow_db_id: int
    ) -> List[ImportFieldMapping]:
        """Get field mappings for a flow"""
        try:
            query = select(ImportFieldMapping).where(
                ImportFieldMapping.master_flow_id == master_flow_db_id
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"❌ Error getting field mappings for flow {flow_id}: {e}")
            return []

    async def suggest_flow_recovery_action(
        self, flow_id: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze flow issues and suggest the best recovery action.

        Args:
            flow_id: The flow ID to analyze

        Returns:
            Tuple of (action_type, action_metadata)
        """
        try:
            issues = await self.detect_incomplete_initialization(flow_id)

            if not issues:
                return (
                    "no_action_needed",
                    {"message": "Flow appears to be in good state"},
                )

            # Prioritize actions based on severity and type
            critical_issues = [i for i in issues if i.severity == "critical"]
            high_issues = [i for i in issues if i.severity == "high"]

            # If missing master or discovery flow, need to recreate
            if any(
                i.issue_type in ["missing_master_flow", "missing_discovery_flow"]
                for i in critical_issues
            ):
                return (
                    "recreate_flow",
                    {
                        "reason": "Critical flow records missing",
                        "issues": [i.__dict__ for i in critical_issues],
                    },
                )

            # If in field mapping but data import incomplete, route to data import
            if any(
                i.issue_type in ["incomplete_data_import", "missing_raw_data"]
                for i in high_issues
            ):
                return (
                    "route_to_data_import",
                    {
                        "reason": "Flow in field mapping phase but data import incomplete",
                        "issues": [i.__dict__ for i in high_issues],
                    },
                )

            # If orphaned data exists, link it
            if any(
                i.issue_type
                in ["missing_data_import_linkage", "orphaned_field_mappings"]
                for i in issues
            ):
                return (
                    "link_orphaned_data",
                    {
                        "reason": "Orphaned data found that can be linked to flow",
                        "issues": [
                            i.__dict__
                            for i in issues
                            if "orphaned" in i.issue_type or "linkage" in i.issue_type
                        ],
                    },
                )

            # Default to manual investigation
            return (
                "manual_investigation",
                {
                    "reason": "Complex issues require manual investigation",
                    "issues": [i.__dict__ for i in issues],
                },
            )

        except Exception as e:
            logger.error(f"❌ Error suggesting recovery action for {flow_id}: {e}")
            return ("error", {"error": str(e)})

    async def detect_system_wide_issues(self) -> Dict[str, Any]:
        """
        Detect system-wide flow initialization issues across all flows.

        Returns:
            Dictionary containing system-wide analysis
        """
        try:
            logger.info("🔍 Performing system-wide flow state analysis")

            # Get all active flows
            master_flows_query = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id
                    == self.context.engagement_id,
                    CrewAIFlowStateExtensions.flow_status.in_(
                        ["active", "running", "waiting_for_approval", "paused"]
                    ),
                )
            )
            result = await self.db.execute(master_flows_query)
            master_flows = list(result.scalars().all())

            system_analysis = {
                "total_active_flows": len(master_flows),
                "flows_with_issues": 0,
                "issue_summary": {},
                "critical_flows": [],
                "recommended_actions": [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

            for master_flow in master_flows:
                flow_id = str(master_flow.flow_id)
                issues = await self.detect_incomplete_initialization(flow_id)

                if issues:
                    system_analysis["flows_with_issues"] += 1

                    # Count issue types
                    for issue in issues:
                        issue_type = issue.issue_type
                        if issue_type not in system_analysis["issue_summary"]:
                            system_analysis["issue_summary"][issue_type] = 0
                        system_analysis["issue_summary"][issue_type] += 1

                        # Track critical flows
                        if issue.severity == "critical":
                            system_analysis["critical_flows"].append(
                                {
                                    "flow_id": flow_id,
                                    "flow_name": master_flow.flow_name,
                                    "issue": issue.description,
                                    "suggested_action": issue.suggested_action,
                                }
                            )

            # Generate system-wide recommendations
            if system_analysis["flows_with_issues"] > 0:
                most_common_issue = (
                    max(system_analysis["issue_summary"].items(), key=lambda x: x[1])[0]
                    if system_analysis["issue_summary"]
                    else None
                )

                if most_common_issue:
                    system_analysis["recommended_actions"].append(
                        {
                            "action": f"bulk_fix_{most_common_issue}",
                            "description": (
                                f"Address {most_common_issue} affecting "
                                f"{system_analysis['issue_summary'][most_common_issue]} flows"
                            ),
                            "priority": "high",
                        }
                    )

            logger.info(
                (
                    f"🔍 System-wide analysis complete: {system_analysis['flows_with_issues']}/"
                    f"{system_analysis['total_active_flows']} flows have issues"
                )
            )
            return system_analysis

        except Exception as e:
            logger.error(f"❌ Error in system-wide flow state analysis: {e}")
            return {
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }
