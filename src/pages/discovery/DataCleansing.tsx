import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useDiscoveryFlowV2 } from '../../hooks/discovery/useDiscoveryFlowV2';
import { useDiscoveryFlowAutoDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useLatestImport, useAssets } from '../../hooks/discovery/useDataCleansingQueries';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import DataCleansingStateProvider from '../../components/discovery/data-cleansing/DataCleansingStateProvider';
import DataCleansingHeader from '../../components/discovery/data-cleansing/DataCleansingHeader';
import DataCleansingProgressDashboard from '../../components/discovery/data-cleansing/DataCleansingProgressDashboard';
import QualityIssuesPanel from '../../components/discovery/data-cleansing/QualityIssuesPanel';
import CleansingRecommendationsPanel from '../../components/discovery/data-cleansing/CleansingRecommendationsPanel';
import DataCleansingNavigationButtons from '../../components/discovery/data-cleansing/DataCleansingNavigationButtons';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Download, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

const DataCleansing: React.FC = () => {
  const { user } = useAuth();
  
  // Use the auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useDiscoveryFlowAutoDetection();
  
  // V2 Discovery flow hook with auto-detected flow ID
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    isUpdating,
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase,
    refresh
  } = useDiscoveryFlowV2(effectiveFlowId);

  // Use data cleansing hooks - fallback to simple approach since complex hooks aren't working
  const {
    data: latestImportData,
    isLoading: isLatestImportLoading,
    error: latestImportError
  } = useLatestImport();

  // Extract data cleansing results from flow state
  const flowDataCleansing = flow?.results?.data_cleansing || flow?.data_cleansing_results || {};
  const qualityIssues = flowDataCleansing?.quality_issues || [];
  const agentRecommendations = flowDataCleansing?.recommendations || [];
  const cleansingProgress = {
    total_records: flowDataCleansing?.metrics?.total_records || 0,
    quality_score: flowDataCleansing?.metrics?.quality_score || 0,
    completion_percentage: flowDataCleansing?.metrics?.completion_percentage || 0,
    cleaned_records: flowDataCleansing?.metrics?.cleaned_records || 0,
    issues_resolved: flowDataCleansing?.metrics?.quality_issues_resolved || 0,
    crew_completion_status: flowDataCleansing?.processing_status?.phase || 'pending'
  };

  // Handle data cleansing execution
  const handleTriggerDataCleansingCrew = async () => {
    try {
      console.log('🧹 Triggering data cleansing phase...');
      await updatePhase('data_cleansing', { action: 'start_cleansing' });
      // Refresh the data after triggering
      setTimeout(() => {
        refresh();
      }, 2000);
    } catch (error) {
      console.error('Failed to execute data cleansing phase:', error);
    }
  };

  // Navigation handlers
  const handleBackToAttributeMapping = () => {
    // Navigate back to attribute mapping
    window.history.back();
  };

  const handleContinueToInventory = () => {
    // Navigate to asset inventory
    window.location.href = '/discovery/inventory';
  };

  // Determine state conditions - use real data cleansing analysis
  const hasError = !!(error || latestImportError);
  const errorMessage = error?.message || latestImportError?.message;
  const hasData = !!(qualityIssues.length > 0 || agentRecommendations.length > 0 || cleansingProgress.total_records > 0);
  const isAnalyzing = isUpdating;
  const isLoadingData = isLoading || isLatestImportLoading || isFlowListLoading;

  // Get data cleansing specific data from V2 flow (keep for compatibility)
  const isDataCleansingComplete = completedPhases.includes('data_cleansing');
  const canContinueToInventory = completedPhases.includes('data_cleansing') || cleansingProgress.completion_percentage >= 80;

  // Enhanced data samples for display - extract from flow state
  const rawDataSample = flowDataCleansing?.raw_data?.slice(0, 3) || [];
  const cleanedDataSample = flowDataCleansing?.cleaned_data?.slice(0, 3) || [];

  // Debug info for flow detection
  console.log('🔍 DataCleansing flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

  return (
    <DataCleansingStateProvider
      isLoading={isLoadingData}
      hasError={hasError}
      errorMessage={errorMessage}
      hasData={hasData}
      onBackToAttributeMapping={handleBackToAttributeMapping}
      onTriggerAnalysis={handleTriggerDataCleansingCrew}
      isAnalyzing={isAnalyzing}
    >
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>

            <DataCleansingHeader 
              totalRecords={cleansingProgress.total_records}
              qualityScore={cleansingProgress.quality_score}
              completionPercentage={cleansingProgress.completion_percentage}
              issuesCount={qualityIssues.length}
              recommendationsCount={agentRecommendations.length}
              isAnalyzing={isAnalyzing}
              isLoading={isLoadingData}
              onRefresh={refresh}
              onTriggerAnalysis={handleTriggerDataCleansingCrew}
            />

            <DataCleansingProgressDashboard 
              progress={{
                ...cleansingProgress,
                crew_completion_status: {}
              }}
              isLoading={isLoadingData}
            />

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              <div className="xl:col-span-3 space-y-6">
                <QualityIssuesPanel 
                  qualityIssues={qualityIssues}
                  onResolveIssue={(issueId) => {
                    console.log('Resolving issue:', issueId);
                    // Implementation for resolving issues
                  }}
                  isLoading={isLoadingData}
                />

                <CleansingRecommendationsPanel 
                  recommendations={agentRecommendations}
                  onApplyRecommendation={(recommendationId) => {
                    console.log('Applying recommendation:', recommendationId);
                    // Implementation for applying recommendations
                  }}
                  isLoading={isLoadingData}
                />

                {/* Enhanced Data Samples Section */}
                {(rawDataSample.length > 0 || cleanedDataSample.length > 0) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        Data Processing Samples
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Raw Data Sample */}
                        {rawDataSample.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <Badge variant="outline">Raw Data</Badge>
                              <span className="text-sm text-gray-600">Before Processing</span>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-3 max-h-64 overflow-auto">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    {Object.keys(rawDataSample[0] || {}).slice(0, 4).map((key) => (
                                      <TableHead key={key} className="text-xs">{key}</TableHead>
                                    ))}
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {rawDataSample.map((record, index) => (
                                    <TableRow key={index}>
                                      {Object.values(record).slice(0, 4).map((value, i) => (
                                        <TableCell key={i} className="text-xs">
                                          {String(value).length > 20 ? `${String(value).substring(0, 20)}...` : String(value)}
                                        </TableCell>
                                      ))}
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                          </div>
                        )}

                        {/* Cleaned Data Sample */}
                        {cleanedDataSample.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <Badge variant="default">Cleaned Data</Badge>
                              <span className="text-sm text-gray-600">After Processing</span>
                            </div>
                            <div className="bg-green-50 rounded-lg p-3 max-h-64 overflow-auto">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    {Object.keys(cleanedDataSample[0] || {}).slice(0, 4).map((key) => (
                                      <TableHead key={key} className="text-xs">{key}</TableHead>
                                    ))}
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {cleanedDataSample.map((record, index) => (
                                    <TableRow key={index}>
                                      {Object.values(record).slice(0, 4).map((value, i) => (
                                        <TableCell key={i} className="text-xs">
                                          {String(value).length > 20 ? `${String(value).substring(0, 20)}...` : String(value)}
                                        </TableCell>
                                      ))}
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Download Actions */}
                      <div className="flex gap-2 mt-4">
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4 mr-2" />
                          Download Raw Data
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4 mr-2" />
                          Download Cleaned Data
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <DataCleansingNavigationButtons 
                  canContinue={canContinueToInventory}
                  onBackToAttributeMapping={handleBackToAttributeMapping}
                  onContinueToInventory={handleContinueToInventory}
                />
              </div>

              <div className="xl:col-span-1 space-y-6">
                <AgentClarificationPanel 
                  pageContext="data-cleansing"
                  refreshTrigger={0}
                  onQuestionAnswered={(questionId, response) => {
                    console.log('Data cleansing question answered:', questionId, response);
                    refresh();
                  }}
                />

                <EnhancedAgentOrchestrationPanel
                  sessionId={flow.flow_id}
                  flowState={flow}
                />
              </div>
            </div>

            {/* Move crew progress to bottom of page */}
            {flow?.flow_id && (
              <div className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle>Discovery Flow Crew Progress</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EnhancedAgentOrchestrationPanel
                      sessionId={flow.flow_id}
                      flowState={flow}
                    />
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </DataCleansingStateProvider>
  );
};

export default DataCleansing; 