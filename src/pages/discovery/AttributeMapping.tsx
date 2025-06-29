import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { RefreshCw, Zap, ArrowRight, AlertTriangle, ArrowLeft, Upload } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useNavigate, useParams } from 'react-router-dom';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import AttributeMappingTabContent from '../../components/discovery/attribute-mapping/AttributeMappingTabContent';
import AttributeMappingStateProvider from '../../components/discovery/attribute-mapping/AttributeMappingStateProvider';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import Sidebar from '../../components/Sidebar';

// Hooks
import { useAttributeMappingLogic } from '../../hooks/discovery/useAttributeMappingLogic';
import { useAttributeMappingNavigation } from '../../hooks/discovery/useAttributeMappingNavigation';

const AttributeMapping: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'mappings' | 'data' | 'critical'>('critical');
  const navigate = useNavigate();
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();

  // Custom hooks for business logic
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
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    canContinueToDataCleansing,
    // Auto-detection info for debugging
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
  } = useAttributeMappingLogic();

  // Navigation logic
  const { handleContinueToDataCleansing } = useAttributeMappingNavigation(
    flowState,
    mappingProgress
  );

  // Determine state conditions
  const isLoading = (isFlowStateLoading && !flowState) || isAgenticLoading;
  const hasError = !!(flowStateError || agenticError);
  const errorMessage = flowStateError?.message || agenticError?.message;
  const hasData = !!(agenticData?.attributes?.length);
  
  // Check for flow not found error
  const isFlowNotFound = errorMessage?.includes('Flow not found') || errorMessage?.includes('404');

  // 🔧 SESSION AND FLOW DISPLAY
  const sessionInfo = {
    sessionId,
    flowId,
    availableDataImports,
    selectedDataImportId,
    hasMultipleSessions: availableDataImports.length > 1
  };

  // Check if we have session data - if not, show redirect message
  const hasSessionData = sessionId || flowState;
  const hasUploadedData = agenticData?.attributes && agenticData.attributes.length > 0;

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

            {/* Show flow not found error */}
            {isFlowNotFound && (
              <Alert className="mb-6 border-red-200 bg-red-50">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <AlertDescription className="text-red-800">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium mb-2">Discovery Flow Not Found</p>
                      <p className="text-sm mb-3">
                        The discovery flow you're trying to access could not be found. This might happen if:
                      </p>
                      <ul className="text-sm list-disc list-inside space-y-1 mb-3">
                        <li>The flow was deleted or expired</li>
                        <li>You're using an invalid or outdated flow ID</li>
                        <li>The flow wasn't created properly during data import</li>
                      </ul>
                      <p className="text-sm">
                        Please start a new discovery flow by uploading your data on the Data Import page.
                      </p>
                    </div>
                    <div className="ml-4 flex flex-col space-y-2">
                      <Button 
                        onClick={() => navigate('/discovery/cmdb-import')}
                        className="bg-red-600 hover:bg-red-700 flex items-center space-x-2"
                      >
                        <Upload className="h-4 w-4" />
                        <span>Start New Import</span>
                      </Button>
                      <Button 
                        onClick={() => navigate('/discovery')}
                        variant="outline"
                        className="flex items-center space-x-2"
                      >
                        <ArrowLeft className="h-4 w-4" />
                        <span>Back to Discovery</span>
                      </Button>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Flow Detection Debug Info (development only) */}
            {process.env.NODE_ENV === 'development' && (
              <Alert className="mb-6 border-blue-200 bg-blue-50">
                <AlertDescription className="text-blue-800">
                  <details className="cursor-pointer">
                    <summary className="font-medium mb-2 hover:text-blue-900">🔍 Flow Detection Debug Info (Click to expand)</summary>
                    <div className="text-sm space-y-1 mt-2">
                      <p><strong>URL Flow ID:</strong> {urlFlowId || 'None'}</p>
                      <p><strong>Auto-detected Flow ID:</strong> {autoDetectedFlowId || 'None'}</p>
                      <p><strong>Effective Flow ID:</strong> {effectiveFlowId || 'None'}</p>
                      <p><strong>Available Flows:</strong> {flowList?.length || 0}</p>
                      {flowList && flowList.length > 0 && (
                        <div>
                          <p><strong>Flow Details:</strong></p>
                          <ul className="list-disc list-inside ml-4">
                            {flowList.map((flow: any, index: number) => (
                              <li key={index}>
                                {flow.flow_id?.substring(0, 8)}... - Status: {flow.status}, Phase: {flow.current_phase || flow.next_phase}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <p><strong>Has Field Mapping Data:</strong> {hasData ? 'Yes' : 'No'}</p>
                      <p><strong>Attributes Count:</strong> {agenticData?.attributes?.length || 0}</p>
                    </div>
                  </details>
                </AlertDescription>
              </Alert>
            )}

            {/* Show message when no flows are available */}
            {!isLoading && !hasData && !isFlowNotFound && (
              <Alert className="mb-6 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium mb-2">No Field Mapping Available</p>
                      <p className="text-sm mb-3">
                        {flowList && flowList.length > 0 
                          ? `Found ${flowList.length} flow(s) but none contain field mapping data ready for attribute mapping.`
                          : 'No discovery flows found for your current context.'
                        }
                      </p>
                      <p className="text-sm">
                        Please import data or trigger field mapping analysis to continue.
                      </p>
                    </div>
                    <div className="ml-4 flex flex-col space-y-2">
                      <Button 
                        onClick={() => navigate('/discovery/cmdb-import')}
                        className="bg-yellow-600 hover:bg-yellow-700 flex items-center space-x-2"
                      >
                        <Upload className="h-4 w-4" />
                        <span>Import Data</span>
                      </Button>
                      {effectiveFlowId && (
                        <Button 
                          onClick={handleTriggerFieldMappingCrew}
                          disabled={isAnalyzing}
                          variant="outline"
                          className="flex items-center space-x-2"
                        >
                          <Zap className="h-4 w-4" />
                          <span>Trigger Field Mapping</span>
                        </Button>
                      )}
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Show redirect message if showing old data */}
            {!sessionId && !isFlowNotFound && hasData && (
              <Alert className="mb-6 border-blue-200 bg-blue-50">
                <Upload className="h-5 w-5 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium mb-2">Viewing Previous Discovery Data</p>
                      <p className="text-sm">
                        You're viewing field mapping data from a previous discovery flow. 
                        To start a new discovery with fresh data, upload a new CMDB file.
                      </p>
                    </div>
                    <Button 
                      onClick={() => navigate('/discovery/cmdb-import')}
                      className="ml-4 bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
                    >
                      <Upload className="h-4 w-4" />
                      <span>Start New Import</span>
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Only render main content if flow is found */}
            {!isFlowNotFound && (
              <>
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900">Field Mapping & Critical Attributes</h1>
                      <p className="text-gray-600">
                        {mappingProgress.total > 0 
                          ? `${mappingProgress.total} attributes analyzed with ${mappingProgress.mapped} mapped and ${mappingProgress.critical_mapped} migration-critical` 
                          : 'AI-powered field mapping and critical attribute identification'
                        }
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <Button
                      onClick={refetchAgentic}
                      disabled={isAgenticLoading}
                      variant="outline"
                      className="flex items-center space-x-2"
                    >
                      {isAgenticLoading ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      <span>Refresh Analysis</span>
                    </Button>
                    
                    <Button
                      onClick={handleTriggerFieldMappingCrew}
                      disabled={isAnalyzing}
                      className="flex items-center space-x-2"
                    >
                      {isAnalyzing ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Zap className="h-4 w-4" />
                      )}
                      <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Field Mapping'}</span>
                    </Button>
                  </div>
                </div>

                <ProgressDashboard 
                  mappingProgress={mappingProgress}
                  isLoading={isAgenticLoading}
                />

                {/* Show agent orchestration panel when we have a flow */}
                {(sessionId || flowState) && (
                  <div className="mb-6">
                    <EnhancedAgentOrchestrationPanel
                      sessionId={sessionId || flowState?.flow_id || effectiveFlowId}
                      flowState={flowState}
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                  <div className="xl:col-span-3 space-y-6">
                    <div className="bg-white rounded-lg shadow-md">
                      <NavigationTabs 
                        activeTab={activeTab}
                        onTabChange={setActiveTab}
                      />
                      
                      <AttributeMappingTabContent
                        activeTab={activeTab}
                        fieldMappings={fieldMappings}
                        criticalAttributes={criticalAttributes}
                        agenticData={agenticData}
                        onApproveMapping={handleApproveMapping}
                        onRejectMapping={handleRejectMapping}
                        onMappingChange={handleMappingChange}
                        refetchAgentic={() => refetchAgentic()}
                        onAttributeUpdate={handleAttributeUpdate}
                        sessionInfo={sessionInfo}
                      />
                    </div>

                    <CrewAnalysisPanel 
                      crewAnalysis={crewAnalysis}
                      isLoading={isAgenticLoading}
                    />

                    {/* Navigation Button */}
                    {canContinueToDataCleansing() && (
                      <div className="flex justify-end">
                        <Button
                          onClick={handleContinueToDataCleansing}
                          className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                        >
                          <span>Continue to Data Cleansing</span>
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>

                  <div className="xl:col-span-1 space-y-6">
                    <AgentClarificationPanel 
                      pageContext="field-mapping"
                      refreshTrigger={0}
                      onQuestionAnswered={(questionId, response) => {
                        console.log('Field mapping question answered:', questionId, response);
                        refetchAgentic();
                      }}
                    />

                    <DataClassificationDisplay 
                      pageContext="field-mapping"
                      refreshTrigger={0}
                      onClassificationUpdate={(itemId, newClassification) => {
                        console.log('Field mapping classification updated:', itemId, newClassification);
                        refetchAgentic();
                      }}
                    />

                    <AgentInsightsSection 
                      pageContext="field-mapping"
                      refreshTrigger={0}
                      onInsightAction={(insightId, action) => {
                        console.log('Field mapping insight action:', insightId, action);
                        if (action === 'apply_insight') {
                          refetchAgentic();
                        }
                      }}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AttributeMappingStateProvider>
  );
};

export default AttributeMapping;
