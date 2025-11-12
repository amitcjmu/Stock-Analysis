import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ProgressDashboard from '../../../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../../../components/discovery/attribute-mapping/NavigationTabs';
import AttributeMappingTabContent from '../../../../components/discovery/attribute-mapping/AttributeMappingTabContent';
import AgentClarificationPanel from '../../../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../../../components/discovery/AgentInsightsSection';
import EnhancedAgentOrchestrationPanel from '../../../../components/discovery/EnhancedAgentOrchestrationPanel';
import { discoveryFlowService } from '../../../../services/api/discoveryFlowService';
import type {
  FieldMappingLearningApprovalRequest,
  FieldMappingLearningRejectionRequest,
  BulkFieldMappingLearningRequest
} from '../../../../services/api/discoveryFlowService';
import { useLearningToasts } from '../../../../hooks/useLearningToasts';
import { useAuth } from '../../../../contexts/AuthContext';
import type { AttributeMappingState, NavigationState } from '../types';

interface AttributeMappingContentProps {
  state: AttributeMappingState;
  navigation: NavigationState;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string) => void;
  onRemoveMapping?: (mappingId: string) => Promise<void>;
  onMappingChange: (mappingId: string, updates: unknown) => void;
  onAttributeUpdate: (attributeId: string, updates: unknown) => void;
  onDataImportSelection: (importId: string) => void;
  refetchAgentic?: () => void;
  refetchCriticalAttributes?: () => void;
  // NEW AGENTIC PROPS: SSE integration
  flowUpdates?: unknown;
  sseLastUpdate?: Date | null;
  // Continue to data cleansing props
  canContinueToDataCleansing?: boolean;
  onContinueToDataCleansing?: () => void;
}

export const AttributeMappingContent: React.FC<AttributeMappingContentProps> = ({
  state,
  navigation,
  onApproveMapping,
  onRejectMapping,
  onRemoveMapping,
  onMappingChange,
  onAttributeUpdate,
  onDataImportSelection,
  refetchAgentic,
  refetchCriticalAttributes,
  flowUpdates,
  sseLastUpdate,
  canContinueToDataCleansing,
  onContinueToDataCleansing
}) => {
  const {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    flowId,
    availableDataImports,
    selectedDataImportId,
    isAgenticLoading,
    effectiveFlowId
  } = state;

  const { activeTab, setActiveTab } = navigation;
  const { client, engagement } = useAuth();
  const {
    showApprovalSuccess,
    showApprovalError,
    showRejectionSuccess,
    showRejectionError,
    showBulkLearningSuccess,
    showBulkLearningError
  } = useLearningToasts();

  // Learning state
  const [learnedMappings, setLearnedMappings] = useState<Set<string>>(new Set());
  const [isLearningServiceEnabled, setIsLearningServiceEnabled] = useState(false);

  // Check if learning service is available
  useEffect(() => {
    const hasRequiredAuth = client?.id && engagement?.id;
    const hasLearningEndpoints = Boolean(
      discoveryFlowService.approveFieldMapping &&
      discoveryFlowService.rejectFieldMapping
    );
    setIsLearningServiceEnabled(hasRequiredAuth && hasLearningEndpoints);
  }, [client?.id, engagement?.id]);

  // Load learned mappings on component mount
  useEffect(() => {
    const loadLearnedMappings = async () => {
      if (!isLearningServiceEnabled || !client?.id || !engagement?.id) return;

      try {
        const response = await discoveryFlowService.getLearnedFieldMappingPatterns(
          client.id.toString(),
          engagement.id.toString(),
          'field_mapping_approval',
          'field_mapping_suggestion',
          100
        );

        if (response.success && response.patterns.length > 0) {
          const learnedMappingIds = new Set(
            response.patterns
              .map(pattern => pattern.metadata?.mapping_id)
              .filter((id): id is string => typeof id === 'string')
          );
          setLearnedMappings(learnedMappingIds);
        }
      } catch (error) {
        console.warn('Failed to load learned mappings:', error);
        // Don't show error to user as this is not critical
      }
    };

    loadLearnedMappings();
  }, [isLearningServiceEnabled, client?.id, engagement?.id, effectiveFlowId]);

  // Learning service handlers
  const handleApproveMappingWithLearning = useCallback(async (
    mappingId: string,
    request: FieldMappingLearningApprovalRequest
  ) => {
    if (!client?.id || !engagement?.id) {
      console.error('Missing authentication context for learning');
      return;
    }

    try {
      const response = await discoveryFlowService.approveFieldMapping(
        mappingId,
        request,
        client.id.toString(),
        engagement.id.toString()
      );

      if (response.success) {
        const mapping = fieldMappings.find(m => m.id === mappingId);
        if (mapping) {
          showApprovalSuccess(response, mapping.source_field);
        }

        // Mark as learned and refresh data
        setLearnedMappings(prev => new Set([...prev, mappingId]));
        if (refetchAgentic) {
          refetchAgentic();
        }
      } else {
        throw new Error(response.error_message || 'Failed to approve mapping');
      }
    } catch (error) {
      const mapping = fieldMappings.find(m => m.id === mappingId);
      showApprovalError(error, mapping?.source_field || mappingId);
    }
  }, [client?.id, engagement?.id, fieldMappings, showApprovalSuccess, showApprovalError, refetchAgentic]);

  const handleRejectMappingWithLearning = useCallback(async (
    mappingId: string,
    request: FieldMappingLearningRejectionRequest
  ) => {
    if (!client?.id || !engagement?.id) {
      console.error('Missing authentication context for learning');
      return;
    }

    try {
      const response = await discoveryFlowService.rejectFieldMapping(
        mappingId,
        request,
        client.id.toString(),
        engagement.id.toString()
      );

      if (response.success) {
        const mapping = fieldMappings.find(m => m.id === mappingId);
        if (mapping) {
          showRejectionSuccess(response, mapping.source_field);
        }

        // Refresh data
        if (refetchAgentic) {
          refetchAgentic();
        }
      } else {
        throw new Error(response.error_message || 'Failed to reject mapping');
      }
    } catch (error) {
      const mapping = fieldMappings.find(m => m.id === mappingId);
      showRejectionError(error, mapping?.source_field || mappingId);
    }
  }, [client?.id, engagement?.id, fieldMappings, showRejectionSuccess, showRejectionError, refetchAgentic]);

  const handleBulkLearnMappings = useCallback(async (request: BulkFieldMappingLearningRequest) => {
    if (!client?.id || !engagement?.id) {
      console.error('Missing authentication context for bulk learning');
      return;
    }

    try {
      const response = await discoveryFlowService.bulkLearnFieldMappings(
        request,
        client.id.toString(),
        engagement.id.toString()
      );

      showBulkLearningSuccess(response);

      // Update learned mappings from successful actions
      const approvedMappingIds = request.actions
        .filter(action => action.action_type === 'approve')
        .map(action => action.mapping_id);

      setLearnedMappings(prev => new Set([...prev, ...approvedMappingIds]));

      // Refresh data
      if (refetchAgentic) {
        refetchAgentic();
      }
    } catch (error) {
      showBulkLearningError(error, request.actions.length);
    }
  }, [client?.id, engagement?.id, showBulkLearningSuccess, showBulkLearningError, refetchAgentic]);

  return (
    <>
      {/* Progress Dashboard */}
      <div className="mb-6">
        <ProgressDashboard
          progress={mappingProgress}
          agentAnalysis={crewAnalysis}
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
          onRemoveMapping={onRemoveMapping}
          onMappingChange={onMappingChange}
          onAttributeUpdate={onAttributeUpdate}
          refetchAgentic={refetchAgentic}
          refetchCriticalAttributes={refetchCriticalAttributes}
          isLoading={isAgenticLoading}
          sessionInfo={{
            flowId: flowId || effectiveFlowId,
            availableDataImports: availableDataImports,
            selectedDataImportId: selectedDataImportId || effectiveFlowId,
            hasMultipleSessions: availableDataImports && availableDataImports.length > 1
          }}
          // Learning-related props
          onApproveMappingWithLearning={isLearningServiceEnabled ? handleApproveMappingWithLearning : undefined}
          onRejectMappingWithLearning={isLearningServiceEnabled ? handleRejectMappingWithLearning : undefined}
          onBulkLearnMappings={isLearningServiceEnabled ? handleBulkLearnMappings : undefined}
          learnedMappings={learnedMappings}
          clientAccountId={client?.id?.toString()}
          engagementId={engagement?.id?.toString()}
          // Continue to data cleansing props
          canContinueToDataCleansing={canContinueToDataCleansing}
          onContinueToDataCleansing={onContinueToDataCleansing}
        />
      </div>

      {/* Agent Panels */}
      {agenticData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <AgentClarificationPanel
            pageContext="attribute_mapping"
            flowId={effectiveFlowId || flowId}
          />
          <DataClassificationDisplay
            pageContext="attribute_mapping"
          />
        </div>
      )}

      {/* Agent Insights and Orchestration - ENHANCED WITH SSE */}
      {flowState && (
        <div className="space-y-6">
          <AgentInsightsSection
            pageContext="attribute_mapping"
            refreshTrigger={sseLastUpdate ? sseLastUpdate.getTime() : undefined}
            isProcessing={flowUpdates?.status === 'running' || flowUpdates?.phase === 'attribute_mapping'}
          />

          <EnhancedAgentOrchestrationPanel
            flowId={effectiveFlowId || flowId}
            currentPhase="attribute_mapping"
            flowState={flowState}
          />
        </div>
      )}
    </>
  );
};
