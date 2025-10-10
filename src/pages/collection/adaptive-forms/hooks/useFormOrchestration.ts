/**
 * useFormOrchestration Hook
 * Coordinates the main form flow, state management, and initialization logic
 * Extracted from AdaptiveForms.tsx (1212 lines) - Critical state management hook
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useAdaptiveFormFlow } from '@/hooks/collection/useAdaptiveFormFlow';
import {
  useIncompleteCollectionFlows,
  useCollectionFlowManagement,
} from '@/hooks/collection/useCollectionFlowManagement';
import { useCollectionStatePolling } from '@/hooks/collection/useCollectionStatePolling';
import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { toast } from '@/components/ui/use-toast';
import { groupQuestionsByAsset } from '@/utils/questionnaireUtils';
import type { ProgressMilestone } from '@/components/collection/types';
import type { CollectionFormData } from '@/components/collection/types';

// Define types for collection flow
interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

interface QuestionnaireData {
  questions: Array<{
    id: string;
    text: string;
    type: string;
    options?: string[];
  }>;
  metadata?: Record<string, unknown>;
}

interface UseFormOrchestrationReturn {
  // URL params and auth
  applicationId: string | null;
  flowId: string | null;
  client: ReturnType<typeof useAuth>['client'];
  engagement: ReturnType<typeof useAuth>['engagement'];
  user: ReturnType<typeof useAuth>['user'];

  // Initialization state
  initializationAttempts: React.MutableRefObject<Set<string>>;
  isInitializingRef: React.MutableRefObject<boolean>;
  protectedInitializeFlow: () => Promise<void>;

  // Flow blocking state
  skipIncompleteCheck: boolean;
  checkingFlows: boolean;
  hasBlockingFlows: boolean;
  blockingFlows: CollectionFlow[];
  shouldAutoInitialize: boolean;

  // Adaptive form flow state
  formData: ReturnType<typeof useAdaptiveFormFlow>['formData'];
  formValues: ReturnType<typeof useAdaptiveFormFlow>['formValues'];
  validation: ReturnType<typeof useAdaptiveFormFlow>['validation'];
  isLoading: boolean;
  isSaving: boolean;
  isCompleted: boolean;
  error: ReturnType<typeof useAdaptiveFormFlow>['error'];
  activeFlowId: string | null;
  isPolling: boolean;
  completionStatus: ReturnType<typeof useAdaptiveFormFlow>['completionStatus'];
  statusLine: ReturnType<typeof useAdaptiveFormFlow>['statusLine'];

  // Form handlers
  handleFieldChange: ReturnType<typeof useAdaptiveFormFlow>['handleFieldChange'];
  handleValidationChange: ReturnType<typeof useAdaptiveFormFlow>['handleValidationChange'];
  handleSave: ReturnType<typeof useAdaptiveFormFlow>['handleSave'];
  handleSubmit: ReturnType<typeof useAdaptiveFormFlow>['handleSubmit'];
  initializeFlow: ReturnType<typeof useAdaptiveFormFlow>['initializeFlow'];

  // Flow management
  deleteFlow: ReturnType<typeof useCollectionFlowManagement>['deleteFlow'];
  isDeleting: ReturnType<typeof useCollectionFlowManagement>['isDeleting'];
  incompleteFlows: CollectionFlow[];
  refetchFlows: () => void;

  // Polling state
  isPollingActive: boolean;
  requestStatusUpdate: () => Promise<unknown>;
  flowState: ReturnType<typeof useCollectionStatePolling>['flowState'];

  // Collection flow query
  currentCollectionFlow: CollectionFlow | null;
  isLoadingFlow: boolean;
  refetchCollectionFlow: () => void;
  hasApplicationsSelected: (flow: CollectionFlow | null) => boolean;

  // Asset grouping and navigation
  assetGroups: ReturnType<typeof groupQuestionsByAsset>;
  filteredFormData: ReturnType<typeof useAdaptiveFormFlow>['formData'];

  // Progress milestones
  progressMilestones: ProgressMilestone[];
}

/**
 * Main orchestration hook for the adaptive forms page
 * Coordinates all sub-hooks and provides centralized state
 */
export const useFormOrchestration = (): UseFormOrchestrationReturn => {
  const [searchParams] = useSearchParams();
  const routeParams = useParams<{ flowId?: string; applicationId?: string }>();
  const { client, engagement, user } = useAuth();

  // CRITICAL FIX: Ref guard to prevent duplicate initialization calls per flowId
  const initializationAttempts = useRef<Set<string>>(new Set());
  const isInitializingRef = useRef<boolean>(false);

  // Get application ID and flow ID from URL params (route params take precedence over query params)
  const applicationId = routeParams.applicationId || searchParams.get('applicationId');
  const flowId = routeParams.flowId || searchParams.get('flowId');

  // Check for incomplete flows that would block new collection processes
  // Skip checking if we're continuing a specific flow (flowId provided)
  const skipIncompleteCheck = !!flowId;
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows,
    refetch: refetchFlows,
  } = useIncompleteCollectionFlows(); // Always call the hook to maintain consistent hook order

  // Use collection flow management hook for flow operations
  const { deleteFlow, isDeleting } = useCollectionFlowManagement();

  // Calculate autoInitialize value
  const hasBlockingFlows = !skipIncompleteCheck && incompleteFlows.length > 0;
  const shouldAutoInitialize = !checkingFlows && (!hasBlockingFlows || !!flowId);

  // Use the adaptive form flow hook for all flow management
  const {
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    isCompleted,
    error,
    flowId: activeFlowId,
    // New polling state fields
    isPolling,
    completionStatus,
    statusLine,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    autoInitialize: shouldAutoInitialize,
  });

  // Use HTTP polling for real-time updates during workflow initialization
  const { isActive: isPollingActive, requestStatusUpdate, flowState } =
    useCollectionStatePolling({
      flowId: activeFlowId,
      enabled: !!activeFlowId && isLoading && !formData,
      onQuestionnaireReady: (state) => {
        console.log('🎉 HTTP Polling: Questionnaire ready notification');
      },
      onStatusUpdate: (state) => {
        console.log('📊 HTTP Polling: Workflow status update:', state);
      },
      onError: (error) => {
        console.error('❌ HTTP Polling: Collection workflow error:', error);
        // Security: Sanitize error message to avoid exposing sensitive information
        const userFriendlyMessage = typeof error === 'string'
          ? error
          : error?.message || 'An unexpected error occurred during workflow processing';
        toast({
          title: 'Workflow Error',
          description: userFriendlyMessage.includes('network') || userFriendlyMessage.includes('timeout')
            ? 'Network error occurred. Please check your connection and try again.'
            : 'Collection workflow encountered an error. Please try again or contact support if the issue persists.',
          variant: 'destructive',
        });
      },
    });

  // Check if the current Collection flow has application selection
  const { data: currentCollectionFlow, isLoading: isLoadingFlow, refetch: refetchCollectionFlow } = useQuery({
    queryKey: ['collection-flow', activeFlowId],
    queryFn: async () => {
      if (!activeFlowId) return null;
      try {
        console.log('🔍 Fetching collection flow details for application check:', activeFlowId);
        return await apiCall(`/collection/flows/${activeFlowId}`);
      } catch (error) {
        console.error('Failed to fetch collection flow:', error);
        return null;
      }
    },
    enabled: !!activeFlowId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // CRITICAL FIX: Protected initialization function with ref guard
  const protectedInitializeFlow = useCallback(async () => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';

    // Prevent duplicate initializations for the same flow
    if (isInitializingRef.current) {
      console.log('⚠️ Initialization already in progress, skipping duplicate call');
      return;
    }

    if (initializationAttempts.current.has(currentFlowKey)) {
      console.log('⚠️ Already attempted initialization for flow:', currentFlowKey);
      return;
    }

    console.log('🔐 Protected initialization starting for flow:', currentFlowKey);
    isInitializingRef.current = true;
    initializationAttempts.current.add(currentFlowKey);

    try {
      await initializeFlow();
      console.log('✅ Protected initialization completed for flow:', currentFlowKey);
    } catch (error) {
      console.error('❌ Protected initialization failed for flow:', currentFlowKey, error);
      // Remove from attempts on error to allow retry
      initializationAttempts.current.delete(currentFlowKey);
      throw error;
    } finally {
      isInitializingRef.current = false;
    }
  }, [initializeFlow, activeFlowId, flowId]);

  // Reset initialization attempts when flowId changes
  useEffect(() => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';
    // Clear attempts for different flows, but keep current one
    const newAttempts = new Set<string>();
    if (initializationAttempts.current.has(currentFlowKey)) {
      newAttempts.add(currentFlowKey);
    }
    initializationAttempts.current = newAttempts;
  }, [activeFlowId, flowId]);

  // Function to detect if applications are selected in the collection flow
  const hasApplicationsSelected = useCallback((collectionFlow: CollectionFlow | null): boolean => {
    if (!collectionFlow) return false;

    const config = collectionFlow.collection_config || {};
    const selectedApps =
      config.selected_application_ids ||
      config.applications ||
      config.application_ids ||
      [];

    const hasApps = Array.isArray(selectedApps) && selectedApps.length > 0;
    const hasAppsFlag = config.has_applications === true;

    return hasApps || hasAppsFlag;
  }, []);

  // Group questions by asset and auto-select first asset
  const assetGroups = groupQuestionsByAsset(
    formData?.sections?.flatMap(section =>
      section.fields.map(field => ({
        field_id: field.id,
        question_text: field.label,
        field_type: field.fieldType,
        required: field.validation?.required,
        options: field.options,
        metadata: field.metadata,
        ...field
      }))
    ) || [],
    undefined,
    formValues
  );

  // Filter form data to show only selected asset's questions (will be handled in component)
  const filteredFormData = formData;

  // Generate progress milestones dynamically from actual form sections
  const progressMilestones: ProgressMilestone[] = formData?.sections
    ? [
        {
          id: 'form-start',
          title: 'Form Started',
          description: 'Begin adaptive data collection',
          achieved: true,
          achievedAt: new Date().toISOString(),
          weight: 0.1,
          required: true,
        },
        ...formData.sections.map((section, index) => {
          const sectionFields = section.fields.map(f => f.id);
          const completedFields = sectionFields.filter(fieldId => {
            const value = formValues?.[fieldId];
            return value !== null && value !== undefined && value !== '';
          });
          const isCompleted = section.requiredFieldsCount > 0
            ? completedFields.length >= section.requiredFieldsCount
            : completedFields.length === sectionFields.length;

          return {
            id: section.id,
            title: section.title,
            description: section.description || `Complete ${section.title.toLowerCase()}`,
            achieved: isCompleted,
            achievedAt: isCompleted ? new Date().toISOString() : undefined,
            weight: section.completionWeight,
            required: section.requiredFieldsCount > 0,
          };
        }),
      ]
    : [];

  // Filter out the current flow and flows being deleted from the blocking check
  const blockingFlows = skipIncompleteCheck ? [] : incompleteFlows.filter((flow) => {
    const id = String(flow.flow_id || flow.id || '');
    const normalizedFlowId = String(flowId || '');
    if (flowId && (id === normalizedFlowId)) {
      return false;
    }
    return id !== normalizedFlowId;
  });

  return {
    // URL params and auth
    applicationId,
    flowId,
    client,
    engagement,
    user,

    // Initialization state
    initializationAttempts,
    isInitializingRef,
    protectedInitializeFlow,

    // Flow blocking state
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    blockingFlows,
    shouldAutoInitialize,

    // Adaptive form flow state
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    isCompleted,
    error,
    activeFlowId,
    isPolling,
    completionStatus,
    statusLine,

    // Form handlers
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,

    // Flow management
    deleteFlow,
    isDeleting,
    incompleteFlows,
    refetchFlows,

    // Polling state
    isPollingActive,
    requestStatusUpdate,
    flowState,

    // Collection flow query
    currentCollectionFlow,
    isLoadingFlow,
    refetchCollectionFlow,
    hasApplicationsSelected,

    // Asset grouping
    assetGroups,
    filteredFormData,

    // Progress milestones
    progressMilestones,
  };
};
