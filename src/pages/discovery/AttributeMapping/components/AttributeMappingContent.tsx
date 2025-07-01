import React from 'react';
import ProgressDashboard from '../../../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../../../components/discovery/attribute-mapping/NavigationTabs';
import AttributeMappingTabContent from '../../../../components/discovery/attribute-mapping/AttributeMappingTabContent';
import AgentClarificationPanel from '../../../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../../../components/discovery/AgentInsightsSection';
import EnhancedAgentOrchestrationPanel from '../../../../components/discovery/EnhancedAgentOrchestrationPanel';
import type { AttributeMappingState, NavigationState } from '../types';

interface AttributeMappingContentProps {
  state: AttributeMappingState;
  navigation: NavigationState;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string) => void;
  onMappingChange: (mappingId: string, updates: any) => void;
  onAttributeUpdate: (attributeId: string, updates: any) => void;
  onDataImportSelection: (importId: string) => void;
}

export const AttributeMappingContent: React.FC<AttributeMappingContentProps> = ({
  state,
  navigation,
  onApproveMapping,
  onRejectMapping,
  onMappingChange,
  onAttributeUpdate,
  onDataImportSelection
}) => {
  const {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    sessionId,
    flowId,
    availableDataImports,
    selectedDataImportId,
    isAgenticLoading,
    effectiveFlowId
  } = state;

  const { activeTab, setActiveTab } = navigation;

  return (
    <>
      {/* Progress Dashboard */}
      <div className="mb-6">
        <ProgressDashboard 
          progress={mappingProgress}
          agentAnalysis={crewAnalysis}
          sessionId={sessionId}
          flowId={flowId}
          effectiveFlowId={effectiveFlowId}
          availableDataImports={availableDataImports}
          selectedDataImportId={selectedDataImportId}
          onDataImportSelection={onDataImportSelection}
        />
      </div>

      {/* Crew Analysis Panel */}
      {crewAnalysis && (
        <div className="mb-6">
          <CrewAnalysisPanel 
            analysis={crewAnalysis}
            flowState={flowState}
            isLoading={isAgenticLoading}
          />
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="mb-6">
        <NavigationTabs 
          activeTab={activeTab}
          onTabChange={setActiveTab}
          progress={mappingProgress}
        />
      </div>

      {/* Tab Content */}
      <div className="mb-6">
        <AttributeMappingTabContent
          activeTab={activeTab}
          agenticData={agenticData}
          fieldMappings={fieldMappings}
          criticalAttributes={criticalAttributes}
          onApproveMapping={onApproveMapping}
          onRejectMapping={onRejectMapping}
          onMappingChange={onMappingChange}
          onAttributeUpdate={onAttributeUpdate}
          isLoading={isAgenticLoading}
        />
      </div>

      {/* Agent Panels */}
      {agenticData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <AgentClarificationPanel 
            data={agenticData}
            flowId={effectiveFlowId || sessionId}
          />
          <DataClassificationDisplay 
            data={agenticData}
          />
        </div>
      )}

      {/* Agent Insights and Orchestration */}
      {flowState && (
        <div className="space-y-6">
          <AgentInsightsSection 
            flowId={effectiveFlowId || sessionId}
            flowState={flowState}
            currentPhase="attribute_mapping"
          />
          
          <EnhancedAgentOrchestrationPanel 
            flowId={effectiveFlowId || sessionId}
            currentPhase="attribute_mapping"
            flowState={flowState}
          />
        </div>
      )}
    </>
  );
};