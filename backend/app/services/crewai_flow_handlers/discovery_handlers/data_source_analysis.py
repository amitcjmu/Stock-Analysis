"""
Data Source Analysis Handler for Discovery Flow
"""
import logging
from typing import Dict, Any, List

from app.services.discovery_agents.data_source_handlers import (
    SourceTypeAnalyzer,
    DataStructureAnalyzer,
    QualityAnalyzer
)
from app.services.crewai_flow_service import DiscoveryFlowState

logger = logging.getLogger(__name__)

class DataSourceAnalysisHandler:
    def __init__(self):
        self.source_type_analyzer = SourceTypeAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.data_structure_analyzer = DataStructureAnalyzer()
        logger.info("DataSourceAnalysisHandler initialized.")

    async def handle(self, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any]) -> DiscoveryFlowState:
        """
        Analyzes the uploaded data source and prepares it for the next steps.
        """
        logger.info(f"Starting data source analysis for session: {flow_state.session_id}")
        flow_state.current_phase = "data_source_analysis"

        file_data = cmdb_data.get('file_data', [])
        metadata = cmdb_data.get('metadata', {})

        source_type = await self.source_type_analyzer.analyze(file_data, metadata)
        quality_assessment = await self.quality_analyzer.classify_data_quality(file_data)
        structure_analysis = await self.data_structure_analyzer.analyze_data_structure(file_data)
        
        flow_state.agent_insights['source_analysis'] = {
            "source_type": source_type,
            "quality": quality_assessment,
            "structure": structure_analysis
        }

        source_name = cmdb_data.get("source", "Unknown")
        record_count = len(cmdb_data.get("data", []))

        analysis_summary = f"Data source analysis complete. Source: {source_name}, Records: {record_count}"
        logger.info(analysis_summary)
        
        flow_state.log_entry(analysis_summary)
        flow_state.processed_data['cmdb_data'] = cmdb_data
        flow_state.data_source_analysis_complete = True
        
        logger.info(f"Data source analysis for session {flow_state.session_id} successful.")
        return flow_state 