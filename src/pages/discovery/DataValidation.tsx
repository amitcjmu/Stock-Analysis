import React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { usePhaseAwareFlowResolver } from '../../hooks/discovery/attribute-mapping/usePhaseAwareFlowResolver';
import SecureLogger from '../../utils/secureLogger';
import { secureNavigation } from '../../utils/secureNavigation';

// Services
import { DataValidationProfileService } from '../../services/dataValidationProfileService';
import type {
  DataProfileWrapper,
  DataProfileResponse,
  DataIssue,
  FieldDecision,
  FieldProfile,
} from '../../services/dataValidationProfileService';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { Label } from '../../components/ui/label';
import {
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Activity,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronRight,
  Scissors,
  FileX,
  SkipForward,
  Database,
} from 'lucide-react';

/**
 * Data Validation Page Component (Enhanced with ADR-038 Data Profiling)
 *
 * Displays intelligent data profiling results including:
 * - Quality scores (completeness, consistency, constraint compliance)
 * - Critical issues (field length violations)
 * - Warnings (multi-value detection)
 * - User decision controls for handling issues
 *
 * Related: ADR-038, Issue #1204
 */
const DataValidation: React.FC = () => {
  const { user, client, engagement, isLoading: isAuthLoading } = useAuth();
  const { flowId: pathFlowId } = useParams<{ flowId?: string }>();
  const [searchParams] = useSearchParams();

  // Support both path parameter (/discovery/data-validation/:flowId)
  // and query parameter (/discovery/data-validation?flow_id=xxx)
  const urlFlowId = pathFlowId || searchParams.get('flow_id') || undefined;

  // Use phase-aware flow resolver for data validation phase
  const {
    resolvedFlowId: effectiveFlowId,
    isResolving: isFlowListLoading,
    error: flowResolutionError,
    resolutionMethod,
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

  // Local state for data profile
  const [dataProfile, setDataProfile] = useState<DataProfileResponse | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Decision modal state
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisions, setDecisions] = useState<Map<string, FieldDecision>>(new Map());
  const [proceedWithWarnings, setProceedWithWarnings] = useState(false);
  const [isSubmittingDecisions, setIsSubmittingDecisions] = useState(false);

  // Expanded sections state
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());

  // Fetch data profile
  const fetchDataProfile = useCallback(async (): Promise<void> => {
    if (!effectiveFlowId || !client?.id || !engagement?.id) return;

    setIsLoadingProfile(true);
    setProfileError(null);
    try {
      SecureLogger.info('[ADR-038] Fetching data profile', { flowId: effectiveFlowId });

      const response: DataProfileWrapper = await DataValidationProfileService.getDataProfile(
        effectiveFlowId
      );

      if (response.success && response.data_profile) {
        setDataProfile(response.data_profile);
        SecureLogger.info('[ADR-038] Data profile fetched successfully', {
          records: response.data_profile.summary.total_records,
          criticalIssues: response.data_profile.issues.critical.length,
          warnings: response.data_profile.issues.warnings.length,
        });
      } else {
        setProfileError(response.error || 'Failed to fetch data profile');
      }
    } catch (err) {
      SecureLogger.error('[ADR-038] Failed to fetch data profile', err);
      setProfileError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingProfile(false);
    }
  }, [effectiveFlowId, client, engagement]);

  useEffect(() => {
    fetchDataProfile();
  }, [fetchDataProfile]);

  // Initialize decisions from issues
  useEffect(() => {
    if (!dataProfile) return;

    const newDecisions = new Map<string, FieldDecision>();

    // Add critical issues (length violations)
    dataProfile.issues.critical.forEach((issue) => {
      if (!newDecisions.has(issue.field)) {
        newDecisions.set(issue.field, {
          field_name: issue.field,
          action: 'truncate', // Default action for length violations
        });
      }
    });

    // Add warnings (multi-value fields)
    dataProfile.issues.warnings.forEach((issue) => {
      if (issue.is_multi_valued && !newDecisions.has(issue.field)) {
        newDecisions.set(issue.field, {
          field_name: issue.field,
          action: 'keep', // Default action for multi-value
          custom_delimiter: issue.delimiter || undefined,
        });
      }
    });

    setDecisions(newDecisions);
  }, [dataProfile]);

  // Handle decision change
  const handleDecisionChange = (fieldName: string, action: FieldDecision['action']) => {
    setDecisions((prev) => {
      const newDecisions = new Map(prev);
      const existing = newDecisions.get(fieldName);
      newDecisions.set(fieldName, {
        field_name: fieldName,
        action,
        custom_delimiter: existing?.custom_delimiter,
      });
      return newDecisions;
    });
  };

  // Handle submit decisions
  const handleSubmitDecisions = async () => {
    if (!effectiveFlowId) return;

    setIsSubmittingDecisions(true);
    try {
      SecureLogger.info('[ADR-038] Submitting data profile decisions', {
        flowId: effectiveFlowId,
        decisionCount: decisions.size,
      });

      const decisionList = Array.from(decisions.values());
      await DataValidationProfileService.submitDecisions(
        effectiveFlowId,
        decisionList,
        proceedWithWarnings
      );

      setShowDecisionModal(false);
      secureNavigation.navigateToDiscoveryPhase('field-mapping', effectiveFlowId);
    } catch (err) {
      SecureLogger.error('[ADR-038] Failed to submit decisions', err);
      alert(`Failed to submit decisions: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmittingDecisions(false);
    }
  };

  // Handle continue without issues
  const handleContinueWithoutIssues = async () => {
    if (!effectiveFlowId) return;

    try {
      SecureLogger.info('[ADR-038] Marking data validation complete without issues');
      await DataValidationProfileService.markComplete(effectiveFlowId, false);
      secureNavigation.navigateToDiscoveryPhase('field-mapping', effectiveFlowId);
    } catch (err) {
      SecureLogger.error('[ADR-038] Failed to mark validation complete', err);
      alert(`Failed to continue: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Toggle issue expansion
  const toggleIssueExpansion = (issueKey: string) => {
    setExpandedIssues((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(issueKey)) {
        newSet.delete(issueKey);
      } else {
        newSet.add(issueKey);
      }
      return newSet;
    });
  };

  // Handler for refresh
  const handleRefresh = async (): Promise<void> => {
    try {
      SecureLogger.info('Refreshing data validation data');
      await refresh();
      await fetchDataProfile();
    } catch (err) {
      SecureLogger.error('Failed to refresh data validation data', err);
    }
  };

  // Navigation handlers
  const handleBackToDataImport = (): void => {
    secureNavigation.navigateToDiscoveryPhase('data-import', effectiveFlowId);
  };

  // Determine state conditions
  const hasError = !!(error || profileError);
  const errorMessage = error?.message || profileError;
  const isLoadingData = isLoading || isFlowListLoading || isAuthLoading || isLoadingProfile;
  const isMissingContext = !isAuthLoading && !isLoadingData && (!client?.id || !engagement?.id);

  // Extract profile data
  const qualityScores = dataProfile?.summary.quality_scores;
  const criticalIssues = dataProfile?.issues.critical || [];
  const warnings = dataProfile?.issues.warnings || [];
  const infoIssues = dataProfile?.issues.info || [];
  const totalRecords = dataProfile?.summary.total_records || 0;
  const totalFields = dataProfile?.summary.total_fields || 0;
  const blockingIssues = dataProfile?.blocking_issues || 0;
  const requiresUserAction = dataProfile?.user_action_required || false;

  // Can continue if no blocking issues
  const canContinue = !requiresUserAction || blockingIssues === 0;

  // Secure debug logging
  SecureLogger.debug('[ADR-038] DataValidation state', {
    hasUrlFlowId: !!urlFlowId,
    hasEffectiveFlowId: !!effectiveFlowId,
    resolutionMethod,
    hasProfile: !!dataProfile,
    criticalCount: criticalIssues.length,
    warningCount: warnings.length,
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
            <p className="text-gray-600">Analyzing data quality...</p>
            <p className="text-sm text-gray-400 mt-2">This may take a moment for large datasets</p>
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
                  <Button onClick={handleBackToDataImport} variant="secondary">
                    Back to Data Import
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // Render quality score card
  const renderQualityScoreCard = (
    label: string,
    score: number | undefined,
    description: string
  ) => {
    const scoreValue = score ?? 0;
    const getScoreColor = (s: number) => {
      if (s >= 90) return 'text-green-600';
      if (s >= 70) return 'text-yellow-600';
      return 'text-red-600';
    };

    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">{label}</p>
            <p className={`text-3xl font-bold ${getScoreColor(scoreValue)}`}>
              {scoreValue.toFixed(1)}%
            </p>
            <Progress value={scoreValue} className="mt-2" />
            <p className="text-xs text-gray-400 mt-2">{description}</p>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Render issue card
  const renderIssueCard = (
    issue: DataIssue,
    index: number,
    type: 'critical' | 'warning' | 'info'
  ) => {
    const issueKey = `${type}-${issue.field}-${index}`;
    const isExpanded = expandedIssues.has(issueKey);
    const decision = decisions.get(issue.field);

    const iconMap = {
      critical: <AlertCircle className="h-5 w-5 text-red-500" />,
      warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
      info: <Info className="h-5 w-5 text-blue-500" />,
    };

    const bgMap = {
      critical: 'bg-red-50 border-red-200',
      warning: 'bg-yellow-50 border-yellow-200',
      info: 'bg-blue-50 border-blue-200',
    };

    return (
      <div key={issueKey} className={`border rounded-lg p-4 ${bgMap[type]}`}>
        <div
          className="flex items-start gap-3 cursor-pointer"
          onClick={() => toggleIssueExpansion(issueKey)}
        >
          {iconMap[type]}
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{issue.issue}</p>
                <p className="text-sm text-gray-600">Field: {issue.field}</p>
              </div>
              <div className="flex items-center gap-2">
                {issue.affected_count !== undefined && (
                  <Badge variant="secondary">{issue.affected_count} affected</Badge>
                )}
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                )}
              </div>
            </div>
          </div>
        </div>

        {isExpanded && (
          <div className="mt-4 pl-8 space-y-3">
            {/* Details */}
            {issue.schema_limit !== undefined && (
              <div className="text-sm">
                <span className="text-gray-500">Schema limit:</span>{' '}
                <span className="font-medium">{issue.schema_limit} characters</span>
              </div>
            )}
            {issue.max_found !== undefined && (
              <div className="text-sm">
                <span className="text-gray-500">Maximum found:</span>{' '}
                <span className="font-medium text-red-600">{issue.max_found} characters</span>
                {issue.exceeds_by !== undefined && (
                  <span className="text-red-500"> (+{issue.exceeds_by})</span>
                )}
              </div>
            )}
            {issue.delimiter && (
              <div className="text-sm">
                <span className="text-gray-500">Detected delimiter:</span>{' '}
                <Badge variant="outline">{issue.delimiter}</Badge>
              </div>
            )}

            {/* Samples */}
            {issue.samples && issue.samples.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium text-gray-700 mb-2">Sample values:</p>
                <div className="space-y-1">
                  {issue.samples.slice(0, 3).map((sample, i) => (
                    <div key={i} className="text-xs bg-white p-2 rounded border">
                      <span className="text-gray-400">Row {sample.record_index}:</span>{' '}
                      <code className="text-gray-700">
                        {sample.value || sample.preview || '(empty)'}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {(issue.recommendations || issue.recommendation) && (
              <div className="mt-2">
                <p className="text-sm font-medium text-gray-700 mb-1">Recommendations:</p>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {issue.recommendations?.map((rec, i) => <li key={i}>{rec}</li>)}
                  {issue.recommendation && !issue.recommendations && (
                    <li>{issue.recommendation}</li>
                  )}
                </ul>
              </div>
            )}

            {/* Current decision */}
            {decision && (
              <div className="mt-3 p-2 bg-white rounded border">
                <div className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <span>Selected action:</span> <Badge>{decision.action}</Badge>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

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
                <h1 className="text-2xl font-bold text-gray-900">Intelligent Data Validation</h1>
                <p className="text-gray-600 mt-1">
                  Comprehensive data quality analysis before field mapping
                </p>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleRefresh} variant="outline" disabled={isUpdating}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${isUpdating ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Database className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Records</p>
                  <p className="text-2xl font-bold text-blue-600">{totalRecords.toLocaleString()}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Activity className="h-8 w-8 text-purple-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Fields</p>
                  <p className="text-2xl font-bold text-purple-600">{totalFields}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Critical Issues</p>
                  <p className="text-2xl font-bold text-red-600">{criticalIssues.length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Warnings</p>
                  <p className="text-2xl font-bold text-yellow-600">{warnings.length}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quality Scores */}
          {qualityScores && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quality Scores</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {renderQualityScoreCard(
                  'Completeness',
                  qualityScores.completeness,
                  'Non-null values'
                )}
                {renderQualityScoreCard(
                  'Consistency',
                  qualityScores.consistency,
                  'Data type uniformity'
                )}
                {renderQualityScoreCard(
                  'Compliance',
                  qualityScores.constraint_compliance,
                  'Schema constraints'
                )}
                {renderQualityScoreCard(
                  'Overall',
                  qualityScores.overall,
                  'Combined quality score'
                )}
              </div>
            </div>
          )}

          {/* Critical Issues */}
          {criticalIssues.length > 0 && (
            <Card className="mb-6 border-red-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-5 w-5" />
                  Critical Issues ({criticalIssues.length})
                </CardTitle>
                <CardDescription>
                  These issues must be resolved before proceeding. Values exceeding schema limits
                  will cause database errors.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {criticalIssues.map((issue, index) =>
                    renderIssueCard(issue, index, 'critical')
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <Card className="mb-6 border-yellow-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-600">
                  <AlertTriangle className="h-5 w-5" />
                  Warnings ({warnings.length})
                </CardTitle>
                <CardDescription>
                  Multi-valued fields detected. Consider splitting into separate records or using
                  the first value only.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {warnings.map((issue, index) => renderIssueCard(issue, index, 'warning'))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Info */}
          {infoIssues.length > 0 && (
            <Card className="mb-6 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-600">
                  <Info className="h-5 w-5" />
                  Information ({infoIssues.length})
                </CardTitle>
                <CardDescription>
                  Additional observations about your data that may be useful.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {infoIssues.map((issue, index) => renderIssueCard(issue, index, 'info'))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Success State */}
          {dataProfile && criticalIssues.length === 0 && warnings.length === 0 && (
            <Card className="mb-6 border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  Data Validation Passed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Your data meets all quality requirements. No critical issues or warnings were
                  detected.
                </p>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">
                      All field values within schema limits
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">
                      No multi-valued fields detected
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-700">
                      Data ready for field mapping
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* No Profile State */}
          {!dataProfile && !isLoadingProfile && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>No Data Profile Available</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Unable to generate data profile. Please ensure data has been imported and try
                  refreshing.
                </p>
                <Button onClick={handleRefresh} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Profile
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <Button onClick={handleBackToDataImport} variant="outline">
              Back to Data Import
            </Button>
            <div className="flex gap-2">
              {requiresUserAction && (criticalIssues.length > 0 || warnings.length > 0) && (
                <Button onClick={() => setShowDecisionModal(true)} variant="default">
                  <Scissors className="h-4 w-4 mr-2" />
                  Handle Issues ({criticalIssues.length + warnings.length})
                </Button>
              )}
              {canContinue && (
                <Button onClick={handleContinueWithoutIssues}>
                  Continue to Field Mapping
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Decision Modal */}
      <Dialog open={showDecisionModal} onOpenChange={setShowDecisionModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Handle Data Issues</DialogTitle>
            <DialogDescription>
              Choose how to handle each field with detected issues. These decisions will be applied
              during data cleansing.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Critical Issues */}
            {criticalIssues.length > 0 && (
              <div>
                <h3 className="font-medium text-red-600 mb-3 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Critical Issues (Must Resolve)
                </h3>
                <div className="space-y-4">
                  {criticalIssues.map((issue) => (
                    <div key={issue.field} className="p-3 bg-red-50 rounded-lg border border-red-200">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-medium">{issue.field}</p>
                          <p className="text-sm text-gray-600">{issue.issue}</p>
                        </div>
                        <Select
                          value={decisions.get(issue.field)?.action || 'truncate'}
                          onValueChange={(value) =>
                            handleDecisionChange(issue.field, value as FieldDecision['action'])
                          }
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="truncate">
                              <span className="flex items-center gap-2">
                                <Scissors className="h-3 w-3" /> Truncate
                              </span>
                            </SelectItem>
                            <SelectItem value="skip">
                              <span className="flex items-center gap-2">
                                <SkipForward className="h-3 w-3" /> Skip Record
                              </span>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {warnings.length > 0 && (
              <div>
                <h3 className="font-medium text-yellow-600 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Warnings (Optional)
                </h3>
                <div className="space-y-4">
                  {warnings.map((issue) => (
                    <div
                      key={issue.field}
                      className="p-3 bg-yellow-50 rounded-lg border border-yellow-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-medium">{issue.field}</p>
                          <p className="text-sm text-gray-600">
                            Multi-valued field ({issue.delimiter})
                          </p>
                        </div>
                        <Select
                          value={decisions.get(issue.field)?.action || 'keep'}
                          onValueChange={(value) =>
                            handleDecisionChange(issue.field, value as FieldDecision['action'])
                          }
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="keep">
                              <span className="flex items-center gap-2">
                                <Database className="h-3 w-3" /> Keep As-Is
                              </span>
                            </SelectItem>
                            <SelectItem value="split">
                              <span className="flex items-center gap-2">
                                <FileX className="h-3 w-3" /> Split Records
                              </span>
                            </SelectItem>
                            <SelectItem value="first_value">
                              <span className="flex items-center gap-2">
                                <SkipForward className="h-3 w-3" /> First Value
                              </span>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Proceed with warnings checkbox */}
            {warnings.length > 0 && criticalIssues.length === 0 && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="proceed-warnings"
                  checked={proceedWithWarnings}
                  onCheckedChange={(checked) => setProceedWithWarnings(checked === true)}
                />
                <Label htmlFor="proceed-warnings" className="text-sm text-gray-600">
                  I acknowledge the warnings and want to proceed
                </Label>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDecisionModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitDecisions}
              disabled={isSubmittingDecisions}
            >
              {isSubmittingDecisions ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Applying...
                </>
              ) : (
                'Apply & Continue'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataValidation;
