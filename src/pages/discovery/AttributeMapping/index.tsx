import React from 'react';

// Components
import ContextBreadcrumbs from '../../../components/context/ContextBreadcrumbs';
import AttributeMappingStateProvider from '../../../components/discovery/attribute-mapping/AttributeMappingStateProvider';
import Sidebar from '../../../components/Sidebar';

// Custom hooks and components
import { useAttributeMapping } from './hooks/useAttributeMapping';
import { useFlowUpdates } from '../../../hooks/useFlowUpdates';
import { AttributeMappingHeader } from './components/AttributeMappingHeader';
import { ErrorAndStatusAlerts } from './components/ErrorAndStatusAlerts';
import { AttributeMappingContent } from './components/AttributeMappingContent';
import { AgentReasoningDisplay } from './components/AgentReasoningDisplay';

const AttributeMappingContainer: React.FC = () => {
  // Add error boundary state
  const [hasRenderError, setHasRenderError] = React.useState(false);

  // Always call hooks in the same order - no conditional hook calls
  const {
    // Core state
    state,
    actions,
    navigation,

    // Computed state
    isLoading,
    hasError,
    errorMessage,
    hasData,
    isFlowNotFound,
    hasSessionData,
    hasUploadedData,
    sessionInfo,

    // Navigation actions
    handleContinueToDataCleansing,

    // URL params
    urlFlowId
  } = useAttributeMapping();

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
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList
  } = state;

  // Add real-time flow updates via SSE - must be called before any conditional returns
  const {
    data: flowUpdates,
    isConnected: isSSEConnected,
    connectionType,
    error: sseError,
    lastUpdate: sseLastUpdate,
    refetch: refetchSSE
  } = useFlowUpdates(effectiveFlowId || urlFlowId, {
    enableSSE: true,
    enablePolling: true,
    pollingInterval: 10000 // 10 seconds fallback polling
  });

  // Debug field mappings - must be called before any conditional returns
  React.useEffect(() => {
    console.log('🔍 [AttributeMapping] Field mappings debug:', {
      fieldMappings_length: fieldMappings?.length || 0,
      fieldMappings_sample: fieldMappings?.slice(0, 3),
      state_keys: Object.keys(state),
      agenticData: agenticData,
      flowState: flowState,
      effectiveFlowId: effectiveFlowId,
      isLoading: isLoading,
      hasData: hasData
    });
  }, [fieldMappings, state, agenticData, flowState, effectiveFlowId, isLoading, hasData]);

  // Early return if there's a render error
  if (hasRenderError) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Application Error</h2>
            <p className="text-gray-600 mb-4">Something went wrong while loading the attribute mapping page.</p>
            <button
              onClick={() => setHasRenderError(false)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const {
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    refetchCriticalAttributes,
    canContinueToDataCleansing
  } = actions;

  return (
    <AttributeMappingStateProvider
      isLoading={isLoading}
      hasError={hasError}
      errorMessage={errorMessage}
      hasData={hasData}
      onTriggerAnalysis={handleTriggerFieldMappingCrew}
      isAnalyzing={isAnalyzing}
    >
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            {/* Always show breadcrumbs at the top */}
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>

            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Attribute Mapping</h1>
              <p className="text-gray-600">Map your data fields to standard migration attributes and verify data quality.</p>
            </div>

            {/* Error and Status Alerts */}
            <ErrorAndStatusAlerts
              isFlowNotFound={isFlowNotFound}
              isLoading={isLoading}
              hasData={hasData}
              flowId={flowId}
              flowList={flowList}
              effectiveFlowId={effectiveFlowId}
              isAnalyzing={isAnalyzing}
              onTriggerFieldMappingCrew={handleTriggerFieldMappingCrew}
            />

            {/* Only render main content if flow is found */}
            {!isFlowNotFound && (
              <>
                {/* Agent Reasoning Display - NEW AGENTIC UI */}
                <div className="mb-6">
                  <AgentReasoningDisplay
                    flowUpdates={flowUpdates}
                    isSSEConnected={isSSEConnected}
                    connectionType={connectionType}
                    sseError={sseError}
                    lastUpdate={sseLastUpdate}
                    fieldMappings={fieldMappings}
                    onRefresh={() => {
                      refetchSSE();
                      refetchAgentic();
                    }}
                  />
                </div>

                {/* Header */}
                <AttributeMappingHeader
                  mappingProgress={mappingProgress}
                  isAgenticLoading={isAgenticLoading}
                  canContinueToDataCleansing={canContinueToDataCleansing}
                  onRefetch={refetchAgentic}
                  onTriggerAnalysis={handleTriggerFieldMappingCrew}
                  onContinueToDataCleansing={handleContinueToDataCleansing}
                  flowStatus={flowState?.status}
                  hasFieldMappings={fieldMappings && fieldMappings.length > 0}
                  // Pass SSE connection info to header
                  isSSEConnected={isSSEConnected}
                  connectionType={connectionType}
                />

                {/* Main Content */}
                <AttributeMappingContent
                  state={state}
                  navigation={navigation}
                  onApproveMapping={handleApproveMapping}
                  onRejectMapping={handleRejectMapping}
                  onMappingChange={handleMappingChange}
                  onAttributeUpdate={handleAttributeUpdate}
                  onDataImportSelection={handleDataImportSelection}
                  refetchAgentic={refetchAgentic}
                  refetchCriticalAttributes={refetchCriticalAttributes}
                  // Pass SSE data for real-time updates
                  flowUpdates={flowUpdates}
                  sseLastUpdate={sseLastUpdate}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </AttributeMappingStateProvider>
  );
};

export default AttributeMappingContainer;
