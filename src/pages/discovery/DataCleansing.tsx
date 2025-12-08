import React from 'react'
import { useState, useCallback } from 'react'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { isFlowTerminal } from '../../constants/flowStates';
import { usePhaseAwareFlowResolver } from '../../hooks/discovery/attribute-mapping/usePhaseAwareFlowResolver';
import { logTerminalStateAuditEvent } from '../../utils/auditLogger';
import { useLatestImport, useAssets, useDataCleansingStats, useDataCleansingAnalysis, useTriggerDataCleansingAnalysis } from '../../hooks/discovery/useDataCleansingQueries';
import { downloadRawData, downloadCleanedData, applyRecommendation } from '../../services/dataCleansingService';
import { API_CONFIG } from '../../config/api'
import { apiCall } from '../../config/api'
import SecureLogger from '../../utils/secureLogger';
import { secureNavigation } from '../../utils/secureNavigation';

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
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import AssetConflictModal from '../../components/discovery/AssetConflictModal';
import QualityIssueGridModal from '../../components/discovery/data-cleansing/QualityIssueGridModal';
import { AssetCreationPreviewModal } from '../../components/discovery/AssetCreationPreviewModal';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { AlertTriangle } from 'lucide-react'
import { Download, FileText, CheckCircle, Activity } from 'lucide-react'
import { assetConflictService } from '../../services/api/assetConflictService';
import type { AssetConflict } from '../../types/assetConflict';

const DataCleansing: React.FC = () => {
  const { user, client, engagement, isLoading: isAuthLoading, setCurrentFlow, getAuthHeaders } = useAuth();
  const [pendingQuestions, setPendingQuestions] = useState(0);

  // Asset conflict resolution state
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [assetConflicts, setAssetConflicts] = useState<AssetConflict[]>([]);

  // Asset preview state (Issue #907)
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  // Quality issue grid (AG Grid) state
  const [showIssueGrid, setShowIssueGrid] = useState(false);
  const [currentIssueId, setCurrentIssueId] = useState<string | null>(null);
  const [currentIssueRows, setCurrentIssueRows] = useState<Array<Record<string, unknown>>>([]);

  // Get URL flow ID from params
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();

  // Use phase-aware flow resolver for data cleansing phase
  const {
    resolvedFlowId: effectiveFlowId,
    isResolving: isFlowListLoading,
    error: flowResolutionError,
    resolutionMethod
  } = usePhaseAwareFlowResolver(urlFlowId, 'data_cleansing');

  const hasEffectiveFlow = !!effectiveFlowId;

  // Unified Discovery flow hook with auto-detected flow ID
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase,
    isExecutingPhase: isUpdating,
    refreshFlow: refresh,
    isPhaseComplete,
    getPhaseData
  } = useUnifiedDiscoveryFlow(effectiveFlowId);

  // Extract flow details from unified flow state
  const progressPercentage = flow?.progress_percentage || 0;
  const currentPhase = flow?.current_phase || '';
  const completedPhases = flow?.phase_completion ?
    Object.entries(flow.phase_completion)
      .filter(([_, completed]) => completed)
      .map(([phase, _]) => phase) : [];
  const nextPhase = currentPhase === 'data_cleansing' ? 'inventory' : '';

  // Use new data cleansing hooks for proper API calls
  const {
    data: dataCleansingStats,
    isLoading: isDataCleansingStatsLoading,
    error: dataCleansingStatsError,
    refetch: refetchStats
  } = useDataCleansingStats(effectiveFlowId);

  const {
    data: dataCleansingAnalysis,
    isLoading: isDataCleansingAnalysisLoading,
    error: dataCleansingAnalysisError,
    refetch: refetchAnalysis
  } = useDataCleansingAnalysis(effectiveFlowId);

  const triggerAnalysisMutation = useTriggerDataCleansingAnalysis();

  // Use data cleansing hooks - fallback to simple approach since complex hooks aren't working (legacy)
  const {
    data: latestImportData,
    isLoading: isLatestImportLoading,
    error: latestImportError
  } = useLatestImport();

  // Extract data cleansing results from API response or flow state as fallback
  const totalRecords = dataCleansingStats?.total_records ??
    dataCleansingAnalysis?.total_records ??
    flow?.raw_data?.length ??
    flow?.import_metadata?.record_count ??
    latestImportData?.data?.length ??
    0;

  const cleanedRecords = dataCleansingStats?.clean_records ??
    dataCleansingAnalysis?.total_records ??
    totalRecords;

  const recordsWithIssues = dataCleansingStats?.records_with_issues ?? 0;

  const fieldsAnalyzed = dataCleansingAnalysis?.total_fields ??
    Object.keys(flow?.field_mappings || {}).length;

  const qualityScore = dataCleansingAnalysis?.quality_score ?? 0;

  const completionPercentage = dataCleansingStats?.completion_percentage ??
    (totalRecords > 0 ? Math.round((cleanedRecords / totalRecords) * 100) : 0);

  // Extract quality issues and recommendations from analysis
  const allQualityIssues = dataCleansingAnalysis?.quality_issues || [];
  const agentRecommendations = dataCleansingAnalysis?.recommendations || [];

  // Filter out resolved/ignored issues for counting (only show pending issues)
  const qualityIssues = allQualityIssues.filter(issue =>
    !issue.status || issue.status === 'pending'
  );

  // Count resolved and ignored issues separately
  const resolvedIssues = allQualityIssues.filter(issue => issue.status === 'resolved');
  const ignoredIssues = allQualityIssues.filter(issue => issue.status === 'ignored');

  const cleansingProgress = {
    total_records: totalRecords,
    quality_score: qualityScore || (totalRecords > 0 ? 85 : 0), // Use API data or default
    completion_percentage: completionPercentage,
    cleaned_records: cleanedRecords,
    records_with_issues: recordsWithIssues,
    issues_resolved: resolvedIssues.length, // Count actually resolved issues
    issues_ignored: ignoredIssues.length, // Count ignored issues
    issues_found: qualityIssues.length, // Only pending issues
    issues_total: allQualityIssues.length, // Total issues including resolved/ignored
    crew_completion_status: dataCleansingAnalysis?.processing_status || 'unknown',
    fields_analyzed: fieldsAnalyzed,
    data_types_identified: fieldsAnalyzed,
    validation_rules_applied: agentRecommendations.filter((r) => r.category === 'validation').length,
    transformations_applied: agentRecommendations.filter((r) => r.category === 'standardization').length
  };

  // Secure debug logging - data availability check
  SecureLogger.debug('DataCleansing data availability check', {
    hasFlow: !!flow,
    hasDataCleansingResults: !!dataCleansingStats || !!dataCleansingAnalysis,
    qualityIssuesCount: qualityIssues.length, // Only pending issues
    resolvedIssuesCount: resolvedIssues.length,
    ignoredIssuesCount: ignoredIssues.length,
    totalIssuesCount: allQualityIssues.length,
    recommendationsCount: agentRecommendations.length,
    totalRecords,
    cleanedRecords,
    fieldsAnalyzed,
    progressPercentage: flow?.progress_percentage || 0,
    usingApiData: !!dataCleansingStats
  });

  // Handle data cleansing execution - Now actually triggers analysis
  const handleTriggerDataCleansingCrew = async (): void => {
    if (!effectiveFlowId) {
      SecureLogger.warn('No flow ID available for triggering analysis, attempting to refresh flow list');

      // Try to refresh the flow
      try {
        await refresh();
      } catch (refreshError) {
        SecureLogger.error('Failed to refresh flows', refreshError);
      }

      SecureLogger.error('No flow ID available for triggering analysis after refresh');
      return;
    }

    try {
      SecureLogger.info('Triggering data cleansing analysis for flow');

      // Use the new mutation hook
      await triggerAnalysisMutation.mutateAsync({
        flowId: effectiveFlowId,
        force_refresh: true,
        include_agent_analysis: true
      });

      SecureLogger.info('Data cleansing analysis triggered successfully');

      // Refresh the data to get updated results
      await Promise.all([refetchStats(), refetchAnalysis(), refresh()]);

    } catch (error) {
      SecureLogger.error('Failed to trigger data cleansing analysis', error);
      // Still refresh to get any available data
      await Promise.all([refetchStats(), refetchAnalysis(), refresh()]);
    }
  };

  // Enhanced refresh handler that includes data cleansing endpoints
  const handleRefresh = async (): Promise<void> => {
    try {
      SecureLogger.info('Refreshing data cleansing data');
      await Promise.all([refetchStats(), refetchAnalysis(), refresh()]);
    } catch (error) {
      SecureLogger.error('Failed to refresh data cleansing data', error);
    }
  };

  // Handler for applying/rejecting recommendations
  const handleApplyRecommendation = async (recommendationId: string, action: 'apply' | 'reject'): Promise<void> => {
    if (!effectiveFlowId) {
      SecureLogger.error('No flow ID available for applying recommendation');
      return;
    }

    try {
      SecureLogger.info('Applying/rejecting recommendation', { recommendationId, action, flowId: effectiveFlowId });

      // Call backend PATCH endpoint - this is the critical operation
      await applyRecommendation(effectiveFlowId, recommendationId, action);

      SecureLogger.info('Recommendation action completed successfully', { recommendationId, action });

      // Refresh data to show updated state - handle refresh failures separately
      // If refresh fails, the action was still successful, so don't show error to user
      try {
        await Promise.all([refetchAnalysis(), refresh()]);
      } catch (refreshError) {
        // Refresh failed but action succeeded - log error but don't show failure to user
        SecureLogger.warn('Recommendation action succeeded but refresh failed', {
          refreshError,
          recommendationId,
          action,
          flowId: effectiveFlowId
        });
        // Action was successful, UI will update on next manual refresh or page reload
      }

    } catch (error) {
      // This catch only handles applyRecommendation failures (actual operation failures)
      SecureLogger.error('Failed to apply recommendation', { error, recommendationId, action, flowId: effectiveFlowId });
      alert(`Failed to ${action === 'apply' ? 'apply' : 'reject'} recommendation. Please try again.`);
    }
  };

  // Handler for resolving quality issues
  const handleResolveQualityIssue = async (issueId: string, action: 'resolve' | 'ignore'): Promise<void> => {
    if (!effectiveFlowId) {
      SecureLogger.error('No flow ID available for resolving quality issue');
      return;
    }

    // Intercept resolve to open AG Grid editor first
    if (action === 'resolve') {
      try {
        // Build rows containing only records where the issue field is empty so user can fill them
        const issue = allQualityIssues.find((i) => i.id === issueId);
        const issueField = issue?.field_name || '';

        // Columns to show: the issue field (required) + useful context fields
        const contextColumns = ['ip_address', 'hostname', 'cpu', 'cpu_cores', 'memory_gb'];
        const desiredColumns = new Set<string>([...contextColumns]);

        // Helpers to resolve actual data key
        const collectAllKeys = (rows: unknown[]): Set<string> => {
          const keys = new Set<string>();
          rows.forEach((r) => Object.keys((r as Record<string, unknown>) || {}).forEach((k) => keys.add(k)));
          return keys;
        };
        const resolveIssueDataKey = (availableKeys: Set<string>, label: string): string => {
          if (!label) return label;
          if (availableKeys.has(label)) return label;
          const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
          const labelNorm = norm(label);
          for (const k of availableKeys) {
            if (norm(k) === labelNorm) return k;
          }
          const aliasMap: Record<string, string[]> = {
            os: ['operating_system', 'os', 'os_name'],
            cpu: ['cpu', 'cpu_cores', 'processor', 'vcpu'],
            ip: ['ip', 'ip_address', 'ipaddr', 'ipaddress'],
          };
          for (const [alias, candidates] of Object.entries(aliasMap)) {
            if (labelNorm === alias || candidates.some((c) => norm(c) === labelNorm)) {
              const found = candidates.find((c) => availableKeys.has(c));
              if (found) return found;
            }
          }
          const snakeGuess = label.replace(/\s+/g, '_').replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
          if (availableKeys.has(snakeGuess)) return snakeGuess;
          return label;
        };

        // Establish available keys and resolve the actual issue data key
        let availableKeys = new Set<string>();
        if (Array.isArray(flow?.raw_data) && flow.raw_data.length > 0) {
          availableKeys = collectAllKeys(flow.raw_data as unknown[]);
        } else if (latestImportData?.data && Array.isArray(latestImportData.data)) {
          availableKeys = collectAllKeys(latestImportData.data as unknown[]);
        }
        const issueDataKey = resolveIssueDataKey(availableKeys, issueField);
        if (issueDataKey) desiredColumns.add(issueDataKey);

        // Use backend agent/utility suggestions
        let suggestResp: any = null;
        try {
          suggestResp = await apiCall(
            `/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${issueId}/suggest?limit=200`,
            { method: 'POST', headers: { 'Content-Type': 'application/json' } }
          );
        } catch (postErr) {
          // Retry with GET if POST not supported
          try {
            suggestResp = await apiCall(
              `/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${issueId}/suggest?limit=200`,
              { method: 'GET' }
            );
          } catch (getErr) {
            SecureLogger.error('Suggestion endpoint failed (POST and GET)', { postErr, getErr });
          }
        }
        if (suggestResp && Array.isArray(suggestResp.rows)) {
          setCurrentIssueRows(suggestResp.rows as Array<Record<string, unknown>>);
        } else {
          // Fallback to showing basic sample if suggestions not available
          const fallback: Array<Record<string, unknown>> = [];
          if (Array.isArray(flow?.raw_data) && flow.raw_data.length > 0) {
            (flow.raw_data as unknown[]).slice(0, 50).forEach((r) => fallback.push(r as Record<string, unknown>));
          } else if (latestImportData?.data && Array.isArray(latestImportData.data)) {
            (latestImportData.data as unknown[]).slice(0, 50).forEach((r) => fallback.push(r as Record<string, unknown>));
          }
          setCurrentIssueRows(fallback);
        }
        setCurrentIssueId(issueId);
        setShowIssueGrid(true);
      } catch (e) {
        SecureLogger.error('Failed to prepare data for issue grid', e);
        // Fallback to direct resolve if grid cannot be opened
      }
      return;
    }

    // Map action to backend status format
    const status = action === 'resolve' ? 'resolved' : 'ignored';

    try {
      SecureLogger.info('Resolving quality issue', { issueId, action, status, flowId: effectiveFlowId });

      // Call backend PATCH endpoint with request body (NOT query params) - this is the critical operation
      const response = await apiCall(`/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${issueId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: status,
          resolution_notes: `Issue ${status} by user at ${new Date().toISOString()}`
        })
      });

      SecureLogger.info('Quality issue resolved successfully', { issueId, status });

      // Refresh data to show updated state - handle refresh failures separately
      // If refresh fails, the action was still successful, so don't show error to user
      try {
        await Promise.all([refetchAnalysis(), refresh()]);
      } catch (refreshError) {
        // Refresh failed but action succeeded - log error but don't show failure to user
        SecureLogger.warn('Quality issue resolution succeeded but refresh failed', {
          refreshError,
          issueId,
          action,
          status,
          flowId: effectiveFlowId
        });
        // Action was successful, UI will update on next manual refresh or page reload
      }

    } catch (error) {
      // This catch only handles PATCH failures (actual operation failures)
      SecureLogger.error('Failed to resolve quality issue', { error, issueId, action, status, flowId: effectiveFlowId });
      alert(`Failed to ${action === 'resolve' ? 'resolve' : 'ignore'} quality issue. Please try again.`);
    }
  };

  // Save handler from AG Grid modal: mark issue resolved (resolutions are already applied automatically when Update Fields is clicked)
  const handleIssueGridSave = async (updatedRows: Array<Record<string, unknown>>): Promise<void> => {
    if (!effectiveFlowId || !currentIssueId) {
      setShowIssueGrid(false);
      return;
    }
    try {
      SecureLogger.info('Marking quality issue as resolved', {
        flowId: effectiveFlowId,
        issueId: currentIssueId,
        rowsCount: updatedRows.length
      });

      // Mark the issue as resolved (resolutions were already applied when Update Fields was clicked) - this is the critical operation
      await apiCall(`/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${currentIssueId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: 'resolved',
          resolution_notes: `Issue resolved via AG Grid editor with ${updatedRows.length} rows reviewed and applied to raw_import_records at ${new Date().toISOString()}`
        })
      });

      setShowIssueGrid(false);
      setCurrentIssueId(null);
      setCurrentIssueRows([]);

      // Refresh data to show updated state - handle refresh failures separately
      // If refresh fails, the action was still successful, so don't show error to user
      try {
        await Promise.all([refetchAnalysis(), refresh()]);
      } catch (refreshError) {
        // Refresh failed but action succeeded - log error but don't show failure to user
        SecureLogger.warn('Issue resolution succeeded but refresh failed', {
          refreshError,
          issueId: currentIssueId,
          flowId: effectiveFlowId
        });
        // Action was successful, UI will update on next manual refresh or page reload
      }

      alert('Issue marked as resolved. Resolution values have been applied to raw_import_records.');
    } catch (error) {
      // This catch only handles PATCH failures (actual operation failures)
      SecureLogger.error('Failed to resolve issue', error);
      alert('Failed to resolve issue. Please try again.');
    }
  };

  // Download handlers
  const handleDownloadRawData = async (): Promise<void> => {
    if (!effectiveFlowId) {
      SecureLogger.error('No flow ID available for download');
      return;
    }

    try {
      SecureLogger.info('Downloading raw data', { flowId: effectiveFlowId });
      await downloadRawData(effectiveFlowId);
      SecureLogger.info('Raw data download completed');
    } catch (error) {
      SecureLogger.error('Failed to download raw data', error);
      // Show user-friendly error message (could be enhanced with toast notifications)
      alert('Failed to download raw data. Please try again.');
    }
  };

  const handleDownloadCleanedData = async (): Promise<void> => {
    if (!effectiveFlowId) {
      SecureLogger.error('No flow ID available for download');
      return;
    }

    try {
      SecureLogger.info('Downloading cleaned data', { flowId: effectiveFlowId });
      await downloadCleanedData(effectiveFlowId);
      SecureLogger.info('Cleaned data download completed');
    } catch (error) {
      SecureLogger.error('Failed to download cleaned data', error);
      // Show user-friendly error message (could be enhanced with toast notifications)
      alert('Failed to download cleaned data. Please try again.');
    }
  };

  // Navigation handlers
  const handleBackToAttributeMapping = (): void => {
    // Secure navigation back to attribute mapping
    secureNavigation.navigateToDiscoveryPhase('attribute-mapping', effectiveFlowId);
  };

  const handleContinueToInventory = async (): void => {
    try {
      // First, mark the data cleansing phase as complete
      if (flow && !flow.phase_completion?.data_cleansing) {
        SecureLogger.info('Marking data cleansing phase as complete');
        await executeFlowPhase('data_cleansing', { complete: true });
      }

      // CRITICAL FIX FOR ISSUE #306: Ensure flow ID is properly set in AuthContext
      // before navigation to prevent race condition
      if (effectiveFlowId && flow && setCurrentFlow) {
        SecureLogger.info('Setting flow context before navigation', { flowId: effectiveFlowId });

        // Update localStorage first for immediate availability
        const flowContext = {
          id: effectiveFlowId,
          name: flow.name || 'Discovery Flow',
          status: flow.status || 'active',
          engagement_id: engagement?.id
        };

        // Synchronously update localStorage to ensure it's available immediately
        localStorage.setItem('auth_flow', JSON.stringify({
          id: effectiveFlowId,
          name: flow.name || 'Discovery Flow',
          status: flow.status || 'active'
        }));

        // Then update the auth context (this should be synchronous)
        setCurrentFlow(flowContext);

        // Verify the context was set properly
        const storedFlow = localStorage.getItem('auth_flow');
        if (!storedFlow || !JSON.parse(storedFlow).id) {
          SecureLogger.error('Flow context not properly stored, retrying');
          localStorage.setItem('auth_flow', JSON.stringify({
            id: effectiveFlowId,
            name: flow.name || 'Discovery Flow',
            status: flow.status || 'active'
          }));
        }

        SecureLogger.info('Flow context set successfully before navigation');
      }

      // CRITICAL FIX: Navigate to inventory with flow_id query parameter
      // This maintains flow context across pages, consistent with attribute-mapping fix
      // Use effectiveFlowId from hook, or fallback to flow.flow_id if hook hasn't resolved yet
      const flowIdForNavigation = effectiveFlowId || flow?.flow_id;

      if (flowIdForNavigation) {
        SecureLogger.info('Navigating to inventory with flow ID', { flowId: flowIdForNavigation });
        window.location.href = `/discovery/inventory?flow_id=${flowIdForNavigation}`;
      } else {
        SecureLogger.warn('No flow ID available, navigating to inventory without flow context');
        window.location.href = '/discovery/inventory';
      }
    } catch (error) {
      SecureLogger.error('Failed to complete data cleansing phase', error);
      // Still navigate even if phase completion fails
      const flowIdForNavigation = effectiveFlowId || flow?.flow_id;
      if (flowIdForNavigation) {
        window.location.href = `/discovery/inventory?flow_id=${flowIdForNavigation}`;
      } else {
        window.location.href = '/discovery/inventory';
      }
    }
  };

  // Determine state conditions - use real data cleansing analysis
  // Ignore latestImportError if it's due to missing context during loading
  const hasError = !!(error);
  const errorMessage = error?.message;

  // Enhanced data availability detection with better edge case handling
  const hasRawData = !!(
    (flow?.raw_data && Array.isArray(flow.raw_data) && flow.raw_data.length > 0) ||
    (latestImportData?.data && Array.isArray(latestImportData.data) && latestImportData.data.length > 0)
  );

  const hasFieldMappings = !!(
    flow?.field_mappings &&
    typeof flow.field_mappings === 'object' &&
    Object.keys(flow.field_mappings).length > 0
  );

  const hasImportMetadata = !!(
    flow?.import_metadata?.record_count > 0 ||
    flow?.data_import_id ||
    (flow?.summary && flow.summary.total_records > 0)
  );

  // Check if previous phases are complete
  const isDataImportComplete = !!(
    flow?.phase_completion?.data_import ||
    flow?.phase_completion?.['data_import'] ||
    (flow?.current_phase && flow.current_phase !== 'data_import' && flow.progress_percentage > 0)
  );

  const isFieldMappingComplete = !!(
    flow?.phase_completion?.field_mapping ||
    flow?.phase_completion?.attribute_mapping ||
    flow?.phase_completion?.['field_mapping'] ||
    flow?.phase_completion?.['attribute_mapping'] ||
    hasFieldMappings
  );

  // More comprehensive data availability check
  const hasImportedData = hasRawData || hasFieldMappings || hasImportMetadata;

  const hasCleansingResults = !!(
    qualityIssues.length > 0 ||
    agentRecommendations.length > 0 ||
    cleansingProgress.total_records > 0 ||
    (flow?.data_cleansing_results && Object.keys(flow.data_cleansing_results).length > 0)
  );

  // Check if flow has progressed past initial phases
  const hasFlowProgression = !!(
    flow && (
      flow.progress_percentage > 0 ||
      isDataImportComplete ||
      isFieldMappingComplete ||
      flow.current_phase === 'data_cleansing' ||
      flow.current_phase === 'field_mapping' ||
      flow.current_phase === 'attribute_mapping'
    )
  );

  // Determine if we have enough data to show the data cleansing interface
  // Be more lenient - if we have an effective flow ID, we should show the interface
  const hasData = hasImportedData || hasCleansingResults || hasFlowProgression || !!effectiveFlowId;

  const isAnalyzing = isUpdating;

  // Keep showing loading state until auth is complete and we have context
  const isLoadingData = isLoading || isLatestImportLoading || isFlowListLoading || isAuthLoading;

  // Check if we're missing required context
  // Only show error if auth is fully loaded and we still don't have context
  // This should be rare as fetchDefaultContext should establish context during auth init
  const isMissingContext = !isAuthLoading && !isLoadingData && (!client?.id || !engagement?.id);

  // Check for pending agent questions (disabled polling for now as endpoint returns empty array)
  useEffect(() => {
    const checkPendingQuestions = async (): Promise<void> => {
      if (!client?.id || !engagement?.id) return;

      try {
        const response = await apiCall(
          `/api/v1/agents/discovery/agent-questions?page=data-cleansing`,
          { method: 'GET' }
        );

        // Handle both array and object response formats
        let questions = [];
        if (Array.isArray(response)) {
          questions = response;
        } else if (response?.questions) {
          questions = response.questions;
        }

        const unansweredQuestions = questions.filter(q => !q.is_resolved) || [];
        setPendingQuestions(unansweredQuestions.length);
      } catch (error) {
        SecureLogger.error('Failed to check pending questions', error);
        // Set to 0 if endpoint fails
        setPendingQuestions(0);
      }
    };

    // Only check once on mount - no polling since endpoint returns empty array
    checkPendingQuestions();
  }, [client, engagement]);

  // Check for asset conflicts (duplicate detection during import)
  useEffect(() => {
    const checkForConflicts = async (): Promise<void> => {
      if (!effectiveFlowId || !flow) return;

      // Check if flow is paused for conflict resolution
      // Backend sets phase_state.conflict_resolution_pending = true when conflicts exist
      const has_conflicts = flow?.phase_state?.conflict_resolution_pending === true;

      if (has_conflicts) {
        try {
          SecureLogger.info('Conflict resolution pending, fetching conflicts', {
            flowId: effectiveFlowId,
          });

          // Fetch pending conflicts from backend
          const conflicts = await assetConflictService.listConflicts(effectiveFlowId);

          if (conflicts.length > 0) {
            SecureLogger.info('Found pending asset conflicts', {
              conflictCount: conflicts.length,
            });
            setAssetConflicts(conflicts);
            setShowConflictModal(true);
          } else {
            // No conflicts found, clear the pending flag
            SecureLogger.info('No conflicts found, clearing modal');
            setAssetConflicts([]);
            setShowConflictModal(false);
          }
        } catch (error) {
          SecureLogger.error('Failed to fetch asset conflicts', error);
          // Don't show modal if fetch fails
          setShowConflictModal(false);
        }
      }
    };

    checkForConflicts();
  }, [effectiveFlowId, flow?.phase_state]);

  // Handle conflict resolution completion
  const handleConflictResolutionComplete = async (): Promise<void> => {
    SecureLogger.info('Conflict resolution completed, refreshing flow state');

    // Close modal
    setShowConflictModal(false);
    setAssetConflicts([]);

    // Refresh flow state to get updated phase_state
    await refresh();

    // If flow was paused, it should auto-resume after conflicts are resolved
    // Backend handles this automatically
  };

  // Get data cleansing specific data from V2 flow (keep for compatibility)
  const isDataCleansingComplete = completedPhases.includes('data_cleansing') ||
    flow?.phase_completion?.data_cleansing === true;
  const allQuestionsAnswered = pendingQuestions === 0;
  const hasMinimumProgress = cleansingProgress.completion_percentage >= 50 || cleansingProgress.total_records > 0;
  // Allow continuing if:
  // 1. Phase is already marked complete OR
  // 2. All questions answered and has progress OR
  // 3. No data to cleanse (total_records === 0) and phase is current
  const noDataToProcess = cleansingProgress.total_records === 0 && currentPhase === 'data_cleansing';

  // CRITICAL FIX: Check if flow is in terminal state - disable navigation for completed/cancelled flows
  const flowStatus = flow?.status;
  const isFlowTerminalState = isFlowTerminal(flowStatus);

  const canContinueToInventory = !isFlowTerminalState && (
    isDataCleansingComplete ||
    (allQuestionsAnswered && hasMinimumProgress) ||
    (noDataToProcess && allQuestionsAnswered)
  );

  // Handler for blocked navigation due to terminal state
  const handleBlockedNavigation = React.useCallback(() => {
    if (isFlowTerminalState) {
      logTerminalStateAuditEvent(
        {
          action_type: 'continue_to_inventory_blocked',
          resource_type: 'discovery_flow',
          resource_id: effectiveFlowId,
          result: 'blocked',
          reason: `Navigation blocked: Flow is in terminal state (${flowStatus})`,
          details: {
            flow_status: flowStatus,
            action_name: 'Continue to Inventory',
          },
        },
        effectiveFlowId,
        client?.id,
        engagement?.id,
        getAuthHeaders()
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isFlowTerminalState, flowStatus, effectiveFlowId, client?.id, engagement?.id]);
  // Note: getAuthHeaders is intentionally excluded from dependencies
  // to prevent unnecessary re-renders. It's called at execution time.

  // CC FIX: Use sample data from dataCleansingAnalysis API response (ADR-038)
  // Fall back to flow data for backward compatibility
  const rawDataSample = dataCleansingAnalysis?.raw_data_sample || flow?.raw_data?.slice(0, 3) || [];
  const cleanedDataSample = dataCleansingAnalysis?.cleaned_data_sample || [];

  // Secure debug logging for flow detection and data state
  SecureLogger.debug('DataCleansing flow detection summary', {
    hasUrlFlowId: !!urlFlowId,
    hasEffectiveFlowId: !!effectiveFlowId,
    resolutionMethod,
    flowResolutionError: !!flowResolutionError
  });

  SecureLogger.debug('DataCleansing data state summary', {
    hasFlow: !!flow,
    hasDataCleansingResults: !!dataCleansingAnalysis,
    qualityIssuesCount: qualityIssues.length,
    recommendationsCount: agentRecommendations.length,
    hasRawData,
    hasFieldMappings,
    hasImportMetadata,
    isDataImportComplete,
    isFieldMappingComplete,
    hasData,
    hasError,
    isLoadingData
  });

  return (
    <DataCleansingStateProvider
      isLoading={isLoadingData}
      hasError={hasError || isMissingContext}
      errorMessage={errorMessage || (isMissingContext ? 'Missing client or engagement context' : undefined)}
      hasData={hasData && !isMissingContext}
      onBackToAttributeMapping={handleBackToAttributeMapping}
      onTriggerAnalysis={handleTriggerDataCleansingCrew}
      isAnalyzing={isAnalyzing}
    >
      {/* Asset Conflict Resolution Modal (Issue #910) */}
      {client && engagement && effectiveFlowId && (
        <AssetConflictModal
          conflicts={assetConflicts}
          isOpen={showConflictModal}
          onClose={() => setShowConflictModal(false)}
          onResolutionComplete={handleConflictResolutionComplete}
          client_account_id={client.id.toString()}
          engagement_id={engagement.id.toString()}
          flow_id={effectiveFlowId}
        />
      )}

      {/* Asset Creation Preview Modal (Issue #907) */}
      {effectiveFlowId && (
        <AssetCreationPreviewModal
          flow_id={effectiveFlowId}
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          onSuccess={() => {
            setShowPreviewModal(false);
            refresh();
          }}
        />
      )}

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

            {/* Quality Issue AG Grid Modal */}
            {currentIssueId && (
              <QualityIssueGridModal
                isOpen={showIssueGrid}
                onClose={() => {
                  setShowIssueGrid(false);
                  setCurrentIssueId(null);
                  setCurrentIssueRows([]);
                }}
                onSave={handleIssueGridSave}
                onUpdateFields={async (updatedRows) => {
                  if (!effectiveFlowId || !currentIssueId) {
                    return;
                  }
                  try {
                    SecureLogger.info('Storing resolution values and applying to raw_import_records', {
                      flowId: effectiveFlowId,
                      issueId: currentIssueId,
                      rowsCount: updatedRows.length
                    });
                    const issue = allQualityIssues.find((i) => i.id === currentIssueId || '');
                    const field_name = issue?.field_name || '';
                    const response = await apiCall(`/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${currentIssueId}/resolution`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        field_name,
                        rows: updatedRows,
                      }),
                    });
                    SecureLogger.info('Resolution values stored and applied successfully', response);
                    const appliedCount = (response as { applied_to_raw_records?: number })?.applied_to_raw_records || 0;

                    // Mark the issue as resolved after successful update
                    SecureLogger.info('Marking quality issue as resolved after successful update', {
                      flowId: effectiveFlowId,
                      issueId: currentIssueId
                    });

                    await apiCall(`/api/v1/flows/${effectiveFlowId}/data-cleansing/quality-issues/${currentIssueId}`, {
                      method: 'PATCH',
                      headers: {
                        'Content-Type': 'application/json'
                      },
                      body: JSON.stringify({
                        status: 'resolved',
                        resolution_notes: `Issue resolved via Update Fields with ${appliedCount} raw_import_record(s) updated at ${new Date().toISOString()}`
                      })
                    });

                    // Close the modal
                    setShowIssueGrid(false);
                    setCurrentIssueId(null);
                    setCurrentIssueRows([]);

                    // Success: Values stored and applied - modal closed
                    SecureLogger.info(`Successfully stored and applied ${appliedCount} raw_import_record(s). Issue marked as resolved.`);

                    // Refresh data to show updated state - handle refresh failures separately
                    // If refresh fails, the action was still successful, so don't show error to user
                    try {
                      await Promise.all([refetchAnalysis(), refresh()]);
                    } catch (refreshError) {
                      // Refresh failed but action succeeded - log error but don't show failure to user
                      SecureLogger.warn('Resolution values stored and applied successfully but refresh failed', {
                        refreshError,
                        issueId: currentIssueId,
                        flowId: effectiveFlowId
                      });
                      // Action was successful, UI will update on next manual refresh or page reload
                    }
                  } catch (err) {
                    // This catch only handles POST/PATCH failures (actual operation failures)
                    SecureLogger.error('Failed to store and apply resolution values', err);
                    // Error logged - user can see issue still in list if operation failed
                  }
                }}
                issue={allQualityIssues.find((i) => i.id === currentIssueId) || null}
                rows={currentIssueRows}
              />
            )}

            <DataCleansingProgressDashboard
              progress={{
                ...cleansingProgress,
                crew_completion_status: {}
              }}
              isLoading={isLoadingData}
            />

            {/* Agent Clarifications - Primary Focus */}
            <div className="mb-6">
              <AgentClarificationPanel
                pageContext="data-cleansing"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  SecureLogger.info('Data cleansing question answered');
                  refresh();
                }}
              />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              <div className="xl:col-span-3 space-y-6">
                {/* Only show Quality Issues if there are actual issues or we have analyzed data */}
                {(totalRecords > 0 || qualityIssues.length > 0 || isLoadingData) && (
                  <QualityIssuesPanel
                    qualityIssues={qualityIssues}
                    onResolveIssue={handleResolveQualityIssue}
                    isLoading={isLoadingData}
                  />
                )}

                {/* Only show Recommendations if there are actual recommendations */}
                {(agentRecommendations.length > 0 || isLoadingData) && (
                  <CleansingRecommendationsPanel
                    recommendations={agentRecommendations}
                    onApplyRecommendation={handleApplyRecommendation}
                    isLoading={isLoadingData}
                  />
                )}

                {/* Show cleansing summary when data has been processed */}
                {!isLoadingData && totalRecords > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-blue-600" />
                        Data Cleansing Summary
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Records Processed</p>
                          <p className="text-lg font-semibold">{cleansingProgress.cleaned_records} / {cleansingProgress.total_records}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Fields Analyzed</p>
                          <p className="text-lg font-semibold">{cleansingProgress.fields_analyzed}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Data Quality Score</p>
                          <p className="text-lg font-semibold">{cleansingProgress.quality_score}%</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Completeness</p>
                          <p className="text-lg font-semibold">{cleansingProgress.completion_percentage}%</p>
                        </div>
                      </div>
                      {cleansingProgress.issues_found > 0 && (
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-sm text-gray-600">
                            Found {cleansingProgress.issues_found} quality issue{cleansingProgress.issues_found > 1 ? 's' : ''},
                            resolved {cleansingProgress.issues_resolved}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Show placeholder when no issues or recommendations */}
                {!isLoadingData && qualityIssues.length === 0 && agentRecommendations.length === 0 && totalRecords === 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        Data Analysis In Progress
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-600">
                        Your data is being analyzed by our AI agents. No quality issues have been detected yet.
                      </p>
                      <p className="text-gray-600 mt-2">
                        {pendingQuestions > 0 ? (
                          <>
                            <span className="font-medium text-amber-600">
                              {pendingQuestions} agent question{pendingQuestions > 1 ? 's' : ''} pending
                            </span> - Please answer the questions above to proceed with the analysis.
                          </>
                        ) : (
                          <>
                            <span className="font-medium text-green-600">All questions answered</span> -
                            {canContinueToInventory ? ' You can now proceed to the inventory phase.' : ' Analysis is being finalized.'}
                          </>
                        )}
                      </p>
                    </CardContent>
                  </Card>
                )}

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
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleDownloadRawData}
                          disabled={!effectiveFlowId || isLoadingData}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download Raw Data
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleDownloadCleanedData}
                          disabled={!effectiveFlowId || isLoadingData}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download Cleaned Data
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Asset Preview Button (Issue #907) */}
                <Card className="mb-4">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold">Asset Creation Preview</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Review and approve transformed assets before creating them in the database
                        </p>
                      </div>
                      <Button
                        onClick={() => setShowPreviewModal(true)}
                        variant="outline"
                        disabled={!effectiveFlowId}
                      >
                        <FileText className="mr-2 h-4 w-4" />
                        Preview Assets
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <DataCleansingNavigationButtons
                  canContinue={canContinueToInventory}
                  onBackToAttributeMapping={handleBackToAttributeMapping}
                  onContinueToInventory={() => {
                    if (isFlowTerminalState) {
                      handleBlockedNavigation();
                    } else {
                      handleContinueToInventory();
                    }
                  }}
                />
              </div>

              <div className="xl:col-span-1 space-y-6">
                {/* Agent Insights */}
                <AgentInsightsSection
                  pageContext="data-cleansing"
                  refreshTrigger={0}
                  onInsightAction={(insightId, action) => {
                    SecureLogger.info('Data cleansing insight action triggered');
                    if (action === 'apply_insight') {
                      refresh();
                    }
                  }}
                />

                {/* Agent Planning Dashboard */}
                <AgentPlanningDashboard pageContext="data-cleansing" />
              </div>
            </div>

            {/* Removed Discovery Flow Crew Progress - never had useful info */}
          </div>
        </div>
      </div>
    </DataCleansingStateProvider>
  );
};

export default DataCleansing;
