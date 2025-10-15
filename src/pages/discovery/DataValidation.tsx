import React from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { usePhaseAwareFlowResolver } from '../../hooks/discovery/attribute-mapping/usePhaseAwareFlowResolver';
import { apiCall } from '../../config/api';
import SecureLogger from '../../utils/secureLogger';
import { secureNavigation } from '../../utils/secureNavigation';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { CheckCircle, AlertTriangle, RefreshCw, Activity } from 'lucide-react';

/**
 * Validation Issue interface
 */
interface ValidationIssue {
  message: string;
  severity: 'critical' | 'warning' | 'info';
  field?: string;
  suggestion?: string;
}

/**
 * Validation Results interface
 */
interface ValidationResults {
  quality_score: number;
  completeness_score: number;
  validation_issues: ValidationIssue[];
  validated_records: number;
}

/**
 * Data Validation Page Component
 *
 * Displays data quality validation results and allows users to:
 * - View validation status and metrics
 * - See quality scores and completeness
 * - Review validation issues
 * - Navigate to next phase
 */
const DataValidation: React.FC = () => {
  const { user, client, engagement, isLoading: isAuthLoading } = useAuth();
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();

  // Use phase-aware flow resolver for data validation phase
  const {
    resolvedFlowId: effectiveFlowId,
    isResolving: isFlowListLoading,
    error: flowResolutionError,
    resolutionMethod
  } = usePhaseAwareFlowResolver(urlFlowId, 'data_validation');

  // Unified Discovery flow hook
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase,
    isExecutingPhase: isUpdating,
    refreshFlow: refresh,
  } = useUnifiedDiscoveryFlow(effectiveFlowId);

  // Local state for validation data
  const [validationResults, setValidationResults] = useState<ValidationResults | null>(null);
  const [isLoadingValidation, setIsLoadingValidation] = useState(false);

  // Extract flow details
  const progressPercentage = flow?.progress_percentage || 0;
  const currentPhase = flow?.current_phase || '';

  // Fetch validation results
  useEffect(() => {
    const fetchValidationResults = async (): Promise<void> => {
      if (!effectiveFlowId || !client?.id || !engagement?.id) return;

      setIsLoadingValidation(true);
      try {
        SecureLogger.info('Fetching data validation results', { flowId: effectiveFlowId });

        // Try to get validation results from flow state first
        const response = await apiCall(
          `/api/v1/flows/${effectiveFlowId}/validation-results`,
          { method: 'GET' }
        );

        setValidationResults(response);
        SecureLogger.info('Data validation results fetched successfully');
      } catch (error) {
        SecureLogger.error('Failed to fetch validation results', error);
        // Use flow state as fallback
        setValidationResults(null);
      } finally {
        setIsLoadingValidation(false);
      }
    };

    fetchValidationResults();
  }, [effectiveFlowId, client, engagement]);

  // Extract validation metrics from results or flow state
  const qualityScore = validationResults?.quality_score ||
    flow?.data_validation_results?.quality_score ||
    0;

  const completenessScore = validationResults?.completeness_score ||
    flow?.data_validation_results?.completeness_score ||
    0;

  const validationIssues = validationResults?.validation_issues ||
    flow?.data_validation_results?.validation_issues ||
    [];

  const totalRecords = flow?.import_metadata?.record_count ||
    flow?.raw_data?.length ||
    0;

  const validatedRecords = validationResults?.validated_records ||
    Math.floor(totalRecords * (completenessScore / 100));

  // Handler for triggering validation
  const handleTriggerValidation = async (): Promise<void> => {
    if (!effectiveFlowId) {
      SecureLogger.error('No flow ID available for triggering validation');
      return;
    }

    try {
      SecureLogger.info('Triggering data validation for flow');

      await executeFlowPhase('data_validation', {
        force_refresh: true,
        include_agent_analysis: true
      });

      SecureLogger.info('Data validation triggered successfully');

      // Refresh the data to get updated results
      await refresh();
    } catch (error) {
      SecureLogger.error('Failed to trigger data validation', error);
      // Still refresh to get any available data
      await refresh();
    }
  };

  // Handler for refresh
  const handleRefresh = async (): Promise<void> => {
    try {
      SecureLogger.info('Refreshing data validation data');
      await refresh();
    } catch (error) {
      SecureLogger.error('Failed to refresh data validation data', error);
    }
  };

  // Navigation handlers
  const handleBackToDataCleansing = (): void => {
    secureNavigation.navigateToDiscoveryPhase('data-cleansing', effectiveFlowId);
  };

  const handleContinueToInventory = async (): void => {
    try {
      // Mark the data validation phase as complete
      if (flow && !flow.phase_completion?.data_validation) {
        SecureLogger.info('Marking data validation phase as complete');
        await executeFlowPhase('data_validation', { complete: true });
      }

      // Navigate to inventory
      secureNavigation.navigateToDiscoveryPhase('inventory', effectiveFlowId);
    } catch (error) {
      SecureLogger.error('Failed to complete data validation phase', error);
      // Still navigate even if phase completion fails
      secureNavigation.navigateToDiscoveryPhase('inventory', effectiveFlowId);
    }
  };

  // Determine state conditions
  const hasError = !!(error);
  const errorMessage = error?.message;
  const isLoadingData = isLoading || isFlowListLoading || isAuthLoading || isLoadingValidation;
  const isMissingContext = !isAuthLoading && !isLoadingData && (!client?.id || !engagement?.id);

  // Check if validation is complete
  const isValidationComplete = flow?.phase_completion?.data_validation === true;
  const hasValidationResults = validationIssues.length > 0 || qualityScore > 0;
  const canContinue = isValidationComplete || (hasValidationResults && qualityScore >= 80);

  // Secure debug logging
  SecureLogger.debug('DataValidation flow detection summary', {
    hasUrlFlowId: !!urlFlowId,
    hasEffectiveFlowId: !!effectiveFlowId,
    resolutionMethod,
    flowResolutionError: !!flowResolutionError
  });

  // Show loading state
  if (isLoadingData) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading validation data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (hasError || isMissingContext) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  Error Loading Data
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  {errorMessage || 'Missing client or engagement context'}
                </p>
                <div className="flex gap-2">
                  <Button onClick={handleRefresh} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                  <Button onClick={handleBackToDataCleansing} variant="secondary">
                    Back to Data Cleansing
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Data Quality Validation</h1>
                <p className="text-gray-600 mt-1">
                  Validate imported data for quality and completeness
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleRefresh}
                  variant="outline"
                  disabled={isUpdating}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isUpdating ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button
                  onClick={handleTriggerValidation}
                  disabled={isUpdating}
                >
                  <Activity className="h-4 w-4 mr-2" />
                  Run Validation
                </Button>
              </div>
            </div>
          </div>

          {/* Validation Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Quality Score</p>
                  <p className={`text-3xl font-bold ${qualityScore >= 80 ? 'text-green-600' : qualityScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {qualityScore}%
                  </p>
                  <Progress value={qualityScore} className="mt-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Completeness</p>
                  <p className={`text-3xl font-bold ${completenessScore >= 90 ? 'text-green-600' : completenessScore >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {completenessScore}%
                  </p>
                  <Progress value={completenessScore} className="mt-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Records Validated</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {validatedRecords}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">of {totalRecords}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Issues Found</p>
                  <p className="text-3xl font-bold text-red-600">
                    {validationIssues.length}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    {validationIssues.filter((i: ValidationIssue) => i.severity === 'critical').length} critical
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Validation Issues */}
          {validationIssues.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  Validation Issues
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {validationIssues.map((issue: ValidationIssue, index: number) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <Badge
                        variant={issue.severity === 'critical' ? 'destructive' : 'secondary'}
                      >
                        {issue.severity || 'warning'}
                      </Badge>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{issue.message}</p>
                        {issue.field && (
                          <p className="text-sm text-gray-600 mt-1">
                            Field: {issue.field}
                          </p>
                        )}
                        {issue.suggestion && (
                          <p className="text-sm text-blue-600 mt-1">
                            Suggestion: {issue.suggestion}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Validation Success */}
          {hasValidationResults && validationIssues.length === 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  Validation Complete
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Your data has been successfully validated. No critical issues were found.
                </p>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">Quality score &gt;= 80%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">No critical validation issues</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">Completeness &gt;= 90%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* No Data State */}
          {!hasValidationResults && !isUpdating && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>No Validation Results</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  No validation results are available yet. Click "Run Validation" to start the validation process.
                </p>
                <Button onClick={handleTriggerValidation}>
                  <Activity className="h-4 w-4 mr-2" />
                  Run Validation
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <Button
              onClick={handleBackToDataCleansing}
              variant="outline"
            >
              Back to Data Cleansing
            </Button>
            <Button
              onClick={handleContinueToInventory}
              disabled={!canContinue}
            >
              Continue to Inventory
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataValidation;
