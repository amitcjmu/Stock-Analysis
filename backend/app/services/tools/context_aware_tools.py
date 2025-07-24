"""
Example context-aware tools for CrewAI agents
"""

from typing import Any, Dict, List

from app.core.context_aware import ContextAwareTool
from app.core.database_context import get_context_db
from sqlalchemy import select

# Import models safely
try:
    from app.models.asset import Asset
    from app.models.data_import import DataImport

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    Asset = None
    DataImport = None


class AssetSearchTool(ContextAwareTool):
    """Tool to search assets with automatic context filtering"""

    name: str = "asset_search"
    description: str = "Search for assets within the current tenant context"

    async def run(self, query: str) -> List[Dict[str, Any]]:
        """Search assets with automatic context filtering"""
        if not MODELS_AVAILABLE or not Asset:
            self.log_with_context("error", "Asset model not available")
            return []

        async with get_context_db() as db:
            # Query automatically filtered by RLS
            result = await db.execute(
                select(Asset).where(Asset.name.ilike(f"%{query}%"))
            )
            assets = result.scalars().all()

            self.log_with_context(
                "info", f"Found {len(assets)} assets matching '{query}'"
            )

            return [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type,
                    "status": asset.status,
                }
                for asset in assets
            ]


class DataImportTool(ContextAwareTool):
    """Tool to access data imports with context"""

    name: str = "data_import_access"
    description: str = "Access data imports for the current context"

    async def run(self, import_id: str) -> Dict[str, Any]:
        """Get data import with context validation"""
        if not MODELS_AVAILABLE or not DataImport:
            self.log_with_context("error", "DataImport model not available")
            return {"error": "DataImport model not available"}

        async with get_context_db() as db:
            result = await db.execute(
                select(DataImport).where(DataImport.id == import_id)
            )
            data_import = result.scalar_one_or_none()

            if not data_import:
                self.log_with_context(
                    "warning", f"Data import {import_id} not found or access denied"
                )
                return {"error": "Import not found or access denied"}

            return {
                "id": str(data_import.id),
                "filename": data_import.filename,
                "status": data_import.status,
                "record_count": data_import.record_count,
            }


class FieldMappingTool(ContextAwareTool):
    """Tool for field mapping operations with context"""

    name: str = "field_mapping"
    description: str = "Perform field mapping operations within tenant context"

    async def run(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Perform field mapping operations"""
        self.log_with_context(
            "info", f"Performing field mapping operation: {operation}"
        )

        if operation == "analyze_fields":
            return await self._analyze_fields(kwargs.get("import_id"))
        elif operation == "suggest_mapping":
            return await self._suggest_mapping(
                kwargs.get("source_field"), kwargs.get("available_targets", [])
            )
        else:
            return {"error": f"Unknown operation: {operation}"}

    async def _analyze_fields(self, import_id: str) -> Dict[str, Any]:
        """Analyze fields in an import"""
        # Implementation would analyze field types, patterns, etc.
        self.log_with_context("info", f"Analyzing fields for import {import_id}")

        return {
            "analysis": "Field analysis complete",
            "field_count": 10,  # Mock data
            "patterns_detected": ["hostname", "ip_address", "environment"],
        }

    async def _suggest_mapping(
        self, source_field: str, available_targets: List[str]
    ) -> Dict[str, Any]:
        """Suggest mapping for a source field"""
        # Simple pattern matching for demonstration
        suggestions = []

        if "host" in source_field.lower():
            suggestions.append({"target": "hostname", "confidence": 0.9})
        elif "ip" in source_field.lower():
            suggestions.append({"target": "ip_address", "confidence": 0.85})
        elif "env" in source_field.lower():
            suggestions.append({"target": "environment", "confidence": 0.8})

        self.log_with_context(
            "info",
            f"Generated {len(suggestions)} mapping suggestions for {source_field}",
        )

        return {"source_field": source_field, "suggestions": suggestions}


class QualityAnalysisTool(ContextAwareTool):
    """Tool for data quality analysis with context"""

    name: str = "quality_analysis"
    description: str = "Analyze data quality within tenant context"

    async def run(self, analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quality analysis"""
        self.log_with_context("info", f"Performing quality analysis: {analysis_type}")

        if analysis_type == "completeness":
            return self._analyze_completeness(data)
        elif analysis_type == "consistency":
            return self._analyze_consistency(data)
        elif analysis_type == "accuracy":
            return self._analyze_accuracy(data)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    def _analyze_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data completeness"""
        # Mock analysis
        return {
            "completeness_score": 0.85,
            "missing_fields": ["description", "owner"],
            "complete_records": 850,
            "total_records": 1000,
        }

    def _analyze_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data consistency"""
        # Mock analysis
        return {
            "consistency_score": 0.92,
            "inconsistencies": [
                {"field": "environment", "issue": "Mixed case values"},
                {"field": "asset_type", "issue": "Inconsistent naming"},
            ],
        }

    def _analyze_accuracy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data accuracy"""
        # Mock analysis
        return {
            "accuracy_score": 0.88,
            "accuracy_issues": [
                {"field": "ip_address", "issue": "Invalid IP format"},
                {"field": "hostname", "issue": "Duplicate hostnames"},
            ],
        }
