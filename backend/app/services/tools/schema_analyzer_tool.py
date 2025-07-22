"""
Schema Analyzer Tool for data structure analysis
"""

import json
from typing import Any, Dict

from sqlalchemy import select

from app.core.database_context import get_context_db
from app.models import RawImportRecord
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata


class SchemaAnalyzerTool(AsyncBaseDiscoveryTool):
    """Analyzes data schema and structure"""
    
    name: str = "schema_analyzer"
    description: str = "Analyze data schema, types, patterns, and quality"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="schema_analyzer",
            description="Comprehensive schema and data structure analysis",
            tool_class=cls,
            categories=["analysis", "validation", "data_quality"],
            required_params=[],
            optional_params=["import_id", "sample_size"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self, 
        import_id: str,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze schema of imported data.
        
        Args:
            import_id: ID of the data import to analyze
            sample_size: Number of records to sample
            
        Returns:
            Schema analysis with field characteristics
        """
        async with get_context_db() as db:
            # Get sample records
            result = await db.execute(
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == import_id)
                .limit(sample_size)
            )
            records = result.scalars().all()
            
            if not records:
                return {"error": "No records found for import"}
            
            # Analyze schema
            schema_analysis = {}
            
            for record in records:
                data = json.loads(record.raw_data) if isinstance(record.raw_data, str) else record.raw_data
                
                for field, value in data.items():
                    if field not in schema_analysis:
                        schema_analysis[field] = {
                            "field_name": field,
                            "data_types": set(),
                            "null_count": 0,
                            "unique_values": set(),
                            "min_length": float('inf'),
                            "max_length": 0,
                            "patterns": set(),
                            "sample_values": []
                        }
                    
                    field_info = schema_analysis[field]
                    
                    # Analyze value
                    if value is None:
                        field_info["null_count"] += 1
                    else:
                        # Data type
                        field_info["data_types"].add(type(value).__name__)
                        
                        # Unique values (limit to prevent memory issues)
                        if len(field_info["unique_values"]) < 100:
                            field_info["unique_values"].add(str(value))
                        
                        # String analysis
                        if isinstance(value, str):
                            field_info["min_length"] = min(
                                field_info["min_length"], 
                                len(value)
                            )
                            field_info["max_length"] = max(
                                field_info["max_length"], 
                                len(value)
                            )
                            
                            # Pattern detection
                            if value.isdigit():
                                field_info["patterns"].add("numeric_string")
                            if '@' in value:
                                field_info["patterns"].add("email_like")
                            if '-' in value and len(value.split('-')) == 3:
                                field_info["patterns"].add("date_like")
                        
                        # Sample values
                        if len(field_info["sample_values"]) < 5:
                            field_info["sample_values"].append(value)
            
            # Convert sets to lists for JSON serialization
            for field_info in schema_analysis.values():
                field_info["data_types"] = list(field_info["data_types"])
                field_info["unique_values"] = list(field_info["unique_values"])[:20]
                field_info["patterns"] = list(field_info["patterns"])
                field_info["null_percentage"] = (
                    field_info["null_count"] / len(records) * 100
                )
                field_info["unique_count"] = len(field_info["unique_values"])
                
                # Clean up infinity values
                if field_info["min_length"] == float('inf'):
                    field_info["min_length"] = 0
            
            return {
                "import_id": import_id,
                "records_analyzed": len(records),
                "field_count": len(schema_analysis),
                "schema": schema_analysis
            }