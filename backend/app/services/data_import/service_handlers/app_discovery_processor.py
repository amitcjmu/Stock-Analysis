"""
Application discovery import processor.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.dependency_repository import DependencyRepository
from app.services.asset_service.base import AssetService
from app.services.data_import.background_execution_service.utils import (
    update_flow_status,
)
from app.services.data_import.service_handlers.topology_normalizer import (
    NormalizationResult,
    normalize_topology_records,
)
from app.services.multi_model_service import TaskComplexity, multi_model_service
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)

from .base_processor import BaseDataImportProcessor


class ApplicationDiscoveryProcessor(BaseDataImportProcessor):
    """Processor for application discovery imports."""

    category = "app_discovery"

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        self.asset_service = AssetService(db, context)
        self.dependency_repository = DependencyRepository(
            db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )
        self._normalization: Optional[NormalizationResult] = None
        self._asset_cache: Dict[str, Any] = {}

    async def process(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        validation_result = await self.validate_data(
            data_import_id=data_import_id,
            raw_records=raw_records,
            processing_config=processing_config,
        )

        if not validation_result.get("valid"):
            return {
                "status": "failed",
                "validation": validation_result,
                "enrichment": None,
            }

        normalized_records = validation_result.get("normalized_records") or raw_records

        enrichment_result = await self.enrich_assets(
            data_import_id=data_import_id,
            validated_records=normalized_records,
            processing_config=processing_config,
        )

        return {
            "status": "completed",
            "validation": validation_result,
            "enrichment": enrichment_result,
        }

    async def validate_data(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize incoming rows and run schema validation."""
        normalization = normalize_topology_records(
            raw_records,
            source_system=(
                processing_config.get("source_system")
                if isinstance(processing_config, dict)
                else None
            ),
        )
        self._normalization = normalization

        warnings = list(normalization.warnings)
        validation_errors = list(normalization.errors)

        if normalization.normalized_records:
            await self._run_validation_agent(normalization.normalized_records)

        if validation_errors:
            await self._publish_status(
                status="failed",
                phase="data_validation",
                payload={
                    "import_category": self.category,
                    "detected_columns": normalization.detected_fields,
                    "errors": validation_errors,
                    "warnings": warnings,
                },
            )
            return {
                "valid": False,
                "validation_errors": validation_errors,
                "warnings": warnings,
            }

        await self._publish_status(
            status="processing",
            phase="data_validation",
            payload={
                "import_category": self.category,
                "detected_columns": normalization.detected_fields,
                "normalized_preview": normalization.normalized_records[:5],
                "warnings": warnings,
            },
        )

        return {
            "valid": True,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "normalized_records": normalization.normalized_records,
        }

    def _extract_network_discovery_fields(
        self, record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract network discovery fields from record (Issue #833).

        Returns dict with: port, protocol_name, conn_count, bytes_total, first_seen, last_seen
        """
        component_name = record.get("component_name", "unknown")
        dep_target = record.get("dependency_target", "unknown")
        self.logger.info(
            f"🔍 [DEPENDENCY EXTRACTION] Processing dependency for "
            f"{component_name} → {dep_target}"
        )
        self.logger.info(
            f"📋 [DEPENDENCY EXTRACTION] All record keys: {sorted(list(record.keys()))}"
        )

        # Extract port
        port_raw = record.get("port") or record.get("Port") or record.get("PORT")
        self.logger.info(
            f"🔍 [PORT] Raw port value: {port_raw} "
            f"(type: {type(port_raw)}, repr: {repr(port_raw)})"
        )
        port = None
        if port_raw is not None:
            try:
                if isinstance(port_raw, int):
                    port = port_raw
                    self.logger.info(f"✅ [PORT] Port is already int: {port}")
                else:
                    port = int(float(str(port_raw).strip()))
                    self.logger.info(
                        f"✅ [PORT] Parsed port: {port} "
                        f"(from '{port_raw}' type={type(port_raw)})"
                    )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"⚠️ [PORT] Failed to parse port '{port_raw}' "
                    f"(type={type(port_raw)}): {e}"
                )
                port = None

        # Extract protocol
        protocol_name = (
            record.get("protocol_name")
            or record.get("protocol")
            or record.get("Protocol")
        )
        self.logger.info(f"🔍 [PROTOCOL] protocol_name: {protocol_name}")

        # Extract connection count
        conn_count_raw = (
            record.get("conn_count")
            or record.get("connection_count")
            or record.get("Connection Count")
            or record.get("connectionCount")
            or record.get("connCount")
        )
        self.logger.info(
            f"🔍 [CONN_COUNT] Raw value: {conn_count_raw} "
            f"(type: {type(conn_count_raw)}, repr: {repr(conn_count_raw)})"
        )
        conn_val = record.get("conn_count")
        conn_count_val = record.get("connection_count")
        conn_count_title = record.get("Connection Count")
        self.logger.info(
            f"🔍 [CONN_COUNT] Tried keys: conn_count={conn_val}, "
            f"connection_count={conn_count_val}, "
            f"Connection Count={conn_count_title}"
        )

        conn_count = None
        if conn_count_raw is not None:
            try:
                if isinstance(conn_count_raw, int):
                    conn_count = conn_count_raw
                    self.logger.info(
                        f"✅ [CONN_COUNT] conn_count is already int: {conn_count}"
                    )
                else:
                    conn_count = int(float(str(conn_count_raw).strip()))
                    self.logger.info(
                        f"✅ [CONN_COUNT] Parsed: {conn_count} "
                        f"(from '{conn_count_raw}' type={type(conn_count_raw)})"
                    )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"⚠️ [CONN_COUNT] Failed to parse '{conn_count_raw}' "
                    f"(type={type(conn_count_raw)}): {e}"
                )
                conn_count = None
        else:
            record_keys = list(record.keys())
            self.logger.warning(
                f"⚠️ [CONN_COUNT] conn_count is None - not found. "
                f"Record keys: {record_keys}"
            )

        # Extract bytes_total
        bytes_total_raw = (
            record.get("bytes_total")
            or record.get("bytes")
            or record.get("Bytes Total")
        )
        bytes_total = None
        if bytes_total_raw is not None:
            try:
                if isinstance(bytes_total_raw, int):
                    bytes_total = bytes_total_raw
                else:
                    bytes_total = int(float(str(bytes_total_raw).strip()))
            except (ValueError, TypeError):
                bytes_total = None

        # Extract timestamps
        first_seen = record.get("first_seen")
        last_seen = record.get("last_seen")

        self.logger.info(
            f"📊 [DEPENDENCY EXTRACTION] Final extracted values: "
            f"port={port}, protocol_name={protocol_name}, conn_count={conn_count}, "
            f"bytes_total={bytes_total}, first_seen={first_seen}, last_seen={last_seen}"
        )

        return {
            "port": port,
            "protocol_name": protocol_name,
            "conn_count": conn_count,
            "bytes_total": bytes_total,
            "first_seen": first_seen,
            "last_seen": last_seen,
        }

    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist normalized dependency records into Asset/AssetDependency tables."""
        if not validated_records:
            return {
                "assets_enriched": 0,
                "dependencies_created": 0,
                "unmatched_components": 0,
            }

        dependencies_created = 0
        unmatched_components = 0

        for record in validated_records:
            source_asset = await self._get_or_create_component_asset(
                record, role="source"
            )
            if not source_asset:
                unmatched_components += 1
                continue

            target_asset = await self._get_or_create_target_asset(record)
            if not target_asset:
                unmatched_components += 1
                continue

            try:
                # Extract network discovery fields
                network_fields = self._extract_network_discovery_fields(record)

                self.logger.info(
                    f"🚀 [CREATE_DEPENDENCY] Creating dependency: "
                    f"source={source_asset.name} ({source_asset.id}) → "
                    f"target={target_asset.name} ({target_asset.id}) with "
                    f"port={network_fields['port']}, "
                    f"conn_count={network_fields['conn_count']}, "
                    f"protocol={network_fields['protocol_name']}"
                )

                dependency = await self.dependency_repository.create_dependency(
                    source_asset_id=str(source_asset.id),
                    target_asset_id=str(target_asset.id),
                    dependency_type=record.get("dependency_type")
                    or "application_dependency",
                    confidence_score=record.get("confidence_score") or 0.7,
                    description=self._build_dependency_description(record),
                    port=network_fields["port"],
                    protocol_name=network_fields["protocol_name"],
                    conn_count=network_fields["conn_count"],
                    bytes_total=network_fields["bytes_total"],
                    first_seen=network_fields["first_seen"],
                    last_seen=network_fields["last_seen"],
                )

                self.logger.info(
                    f"✅ [CREATE_DEPENDENCY] Dependency created: ID={dependency.id}, "
                    f"port={dependency.port}, conn_count={dependency.conn_count}, "
                    f"protocol={dependency.protocol_name}"
                )

                dependencies_created += 1
            except Exception as exc:
                self.logger.warning(
                    "Failed to create dependency for %s -> %s: %s",
                    source_asset.name,
                    target_asset.name,
                    exc,
                )
                unmatched_components += 1

        assets_enriched = len(self._asset_cache)

        await self._publish_status(
            status="processing",
            phase="asset_creation",
            payload={
                "import_category": self.category,
                "normalized_preview": validated_records[:5],
                "assets_enriched": assets_enriched,
                "dependencies_created": dependencies_created,
                "unmatched_components": unmatched_components,
            },
        )

        return {
            "assets_enriched": assets_enriched,
            "dependencies_created": dependencies_created,
            "unmatched_components": unmatched_components,
        }

    async def _run_validation_agent(
        self, normalized_records: List[Dict[str, Any]]
    ) -> None:
        """Run schema validation via agent + LLM tracking."""
        preview = normalized_records[:5]
        prompt = (
            "Validate the following application dependency records. "
            "Ensure each item has application_name, component_name, host_name, "
            "dependency_target, and dependency_type fields populated. "
            "Respond with any anomalies.\n"
            f"Records: {preview}"
        )

        callback_handler = None
        if self.master_flow_id:
            callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=str(self.master_flow_id),
                context=self.context,
            )

        try:
            agent = await TenantScopedAgentPool.get_agent(
                self.context, "topology_schema_agent"
            )

            def _record_task_start() -> None:
                if not callback_handler:
                    return
                callback_handler._step_callback(
                    {
                        "agent": "topology_schema_agent",
                        "task": "topology_schema_validation",
                        "type": "task_start",
                        "status": "starting",
                        "content": "Validating topology schema for imported data",
                    }
                )

            def _record_task_completion(duration: float, status: str) -> None:
                if not callback_handler:
                    return
                callback_handler._task_completion_callback(
                    {
                        "agent": "topology_schema_agent",
                        "task_name": "topology_schema_validation",
                        "task_id": "topology_schema_validation",
                        "status": status,
                        "duration": duration,
                        "output": {
                            "records_sampled": len(preview),
                            "warnings_found": False,
                        },
                    }
                )

            execution_start: Optional[float] = None

            if hasattr(agent, "execute_async"):
                _record_task_start()
                execution_start = time.perf_counter()
                await agent.execute_async(inputs={"task": prompt})
                _record_task_completion(
                    time.perf_counter() - execution_start if execution_start else 0.0,
                    "completed",
                )
            elif hasattr(agent, "execute"):
                _record_task_start()
                execution_start = time.perf_counter()
                agent.execute(task=prompt)
                _record_task_completion(
                    time.perf_counter() - execution_start if execution_start else 0.0,
                    "completed",
                )
        except Exception as exc:
            if callback_handler:
                _record_task_completion(0.0, "failed")
            self.logger.debug(
                "Topology schema agent unavailable, continuing with LLM validation: %s",
                exc,
            )

        try:
            await multi_model_service.generate_response(
                prompt=prompt,
                task_type="topology_validation",
                complexity=TaskComplexity.MEDIUM,
            )
        except Exception as exc:
            self.logger.warning(
                "multi_model_service validation failed for app discovery import: %s",
                exc,
            )

    async def _get_or_create_component_asset(self, record: Dict[str, Any], role: str):
        """Create or retrieve the component asset for source records."""
        cache_key = self._cache_key(record, role)
        if cache_key in self._asset_cache:
            return self._asset_cache[cache_key]

        asset_payload = {
            "asset_type": "component",
            "application_name": record.get("application_name"),
            "name": f"{record.get('application_name')}::{record.get('component_name')}",
            "hostname": record.get("host_name"),
            "environment": record.get("environment"),
            "custom_attributes": {
                "status": record.get("status"),
                "component_type": record.get("component_type"),
                "language": record.get("language"),
                "host_name": record.get("host_name"),
                "import_category": self.category,
            },
            "raw_data": record.get("raw_record", {}),
        }

        try:
            asset, _ = await self.asset_service.create_or_update_asset(
                asset_payload, flow_id=self.master_flow_id
            )
            self._asset_cache[cache_key] = asset
            return asset
        except Exception as exc:
            self.logger.error("Failed to create component asset: %s", exc)
            return None

    async def _get_or_create_target_asset(self, record: Dict[str, Any]):
        """Create or retrieve the downstream dependency asset."""
        target_name = record.get("dependency_target")
        if not target_name:
            return None

        cache_key = f"target::{target_name}".lower()
        if cache_key in self._asset_cache:
            return self._asset_cache[cache_key]

        asset_payload = {
            "asset_type": record.get("dependency_target_type") or "component",
            "application_name": record.get("application_name"),
            "name": target_name,
            "environment": record.get("environment"),
            "custom_attributes": {
                "import_category": self.category,
                "linked_component": record.get("component_name"),
            },
            "raw_data": record.get("raw_record", {}),
        }

        try:
            asset, _ = await self.asset_service.create_or_update_asset(
                asset_payload, flow_id=self.master_flow_id
            )
            self._asset_cache[cache_key] = asset
            return asset
        except Exception as exc:
            self.logger.error("Failed to create target asset: %s", exc)
            return None

    def _cache_key(self, record: Dict[str, Any], role: str) -> str:
        """Build a cache key for deduplication."""
        app = record.get("application_name") or ""
        component = (
            record.get("component_name")
            if role == "source"
            else record.get("dependency_target")
        ) or ""
        host = record.get("host_name") or ""
        return f"{role}::{app}::{component}::{host}".lower()

    def _build_dependency_description(self, record: Dict[str, Any]) -> str:
        """Construct a human-readable description for the dependency."""
        latency = record.get("avg_latency_ms")
        calls = record.get("call_count")
        protocol = record.get("protocol")

        parts = [
            f"{record.get('component_name')} ➜ {record.get('dependency_target')}",
            f"type={record.get('dependency_type')}",
        ]
        if protocol:
            parts.append(f"protocol={protocol}")
        if latency is not None:
            parts.append(f"avg_latency_ms={latency}")
        if calls is not None:
            parts.append(f"call_count={calls}")

        return " | ".join(parts)

    async def _publish_status(
        self, *, status: str, phase: str, payload: Dict[str, Any]
    ) -> None:
        """Update the flow status for downstream consumers."""
        if not self.master_flow_id:
            return
        try:
            await update_flow_status(
                flow_id=self.master_flow_id,
                status=status,
                phase_data={"phase": phase, **payload},
                context=self.context,
            )
        except Exception as exc:
            self.logger.warning("Failed to publish flow status update: %s", exc)
