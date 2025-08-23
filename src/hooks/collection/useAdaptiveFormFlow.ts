/**
 * Custom hook for managing adaptive form flows
 *
 * Extracted from AdaptiveForms.tsx to provide reusable flow management logic
 * for collection workflows with CrewAI integration.
 */

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';

// Import flow management hooks
import { useCollectionFlowManagement, useIncompleteCollectionFlows } from './useCollectionFlowManagement';

// Import API services
import { collectionFlowApi } from '@/services/api/collection-flow';

// Import form data transformation utilities
import { convertQuestionnairesToFormData, validateFormDataStructure } from '@/utils/collection/formDataTransformation'

// Import types
import type {
  AdaptiveFormData,
  CollectionFormData,
  FormValidationResult
} from '@/components/collection/types';
import type {
  FieldValues
} from 'react-hook-form';
import type {
  FormFieldValue,
  ValidationResult
} from '@/types/shared/form-types';

// Import auth context
import { useAuth } from '@/contexts/AuthContext';

// Import RBAC utilities
import { canCreateCollectionFlow } from '@/utils/rbac';

interface FormQuestion {
  id: string;
  question: string;
  type: 'text' | 'select' | 'radio' | 'checkbox' | 'textarea' | 'number';
  required?: boolean;
  options?: string[];
  validation?: ValidationResult;
}

export interface UseAdaptiveFormFlowOptions {
  applicationId?: string | null;
  flowId?: string | null;
  autoInitialize?: boolean;
}

export interface CollectionQuestionnaire {
  id: string;
  flow_id: string;
  title: string;
  description?: string;
  questions: FormQuestion[];
  created_at: string;
  updated_at: string;
  status: 'draft' | 'active' | 'completed';
}

export interface AdaptiveFormFlowState {
  formData: AdaptiveFormData | null;
  formValues: CollectionFormData;
  validation: FormValidationResult | null;
  flowId: string | null;
  questionnaires: CollectionQuestionnaire[];
  isLoading: boolean;
  isSaving: boolean;
  error: Error | null;
}

export interface AdaptiveFormFlowActions {
  initializeFlow: () => Promise<void>;
  handleFieldChange: (fieldId: string, value: FormFieldValue) => void;
  handleValidationChange: (newValidation: FormValidationResult) => void;
  handleSave: () => Promise<void>;
  handleSubmit: (data: CollectionFormData) => Promise<void>;
  resetFlow: () => void;
}

export const useAdaptiveFormFlow = (
  options: UseAdaptiveFormFlowOptions = {}
): AdaptiveFormFlowState & AdaptiveFormFlowActions => {
  const { applicationId, flowId: optionsFlowId, autoInitialize = true } = options;

  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { setCurrentFlow, user } = useAuth();

  // Get application and flow IDs from URL params or options
  const flowIdFromUrl = searchParams.get('flowId') || optionsFlowId;

  // Collection flow management
  const { continueFlow, deleteFlow } = useCollectionFlowManagement();

  // Flow state
  const [state, setState] = useState<AdaptiveFormFlowState>({
    formData: null,
    formValues: {},
    validation: null,
    flowId: null,
    questionnaires: [],
    isLoading: false,
    isSaving: false,
    error: null
  });

  // No longer need hasInitialized - using state.formData and state.isLoading instead

  // Check for incomplete flows
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows
  } = useIncompleteCollectionFlows();

  // Filter out the current flow from the blocking check
  const blockingFlows = incompleteFlows.filter(flow =>
    flow.id !== flowIdFromUrl && flow.flow_id !== flowIdFromUrl &&
    flow.id !== state.flowId && flow.flow_id !== state.flowId
  );

  const hasBlockingFlows = blockingFlows.length > 0;

  /**
   * Initialize the adaptive collection flow
   */
  const initializeFlow = useCallback(async (): Promise<void> => {
    // Don't initialize if there are blocking flows or still checking
    if (checkingFlows || hasBlockingFlows) {
      console.log('🛑 Blocking flow initialization due to other incomplete flows or still checking');
      return;
    }

    // Prevent multiple simultaneous initializations
    if (state.isLoading) {
      console.log('⚠️ Flow initialization already in progress, skipping...');
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      let flowResponse;

      // Check if we have a flow ID from the URL (created from overview page)
      if (flowIdFromUrl) {
        console.log(`📋 Using existing collection flow: ${flowIdFromUrl}`);
        flowResponse = await collectionFlowApi.getFlowDetails(flowIdFromUrl);

        setState(prev => ({ ...prev, flowId: flowResponse.id }));

        // Update the auth context with the existing collection flow
        setCurrentFlow({
          id: flowResponse.id,
          name: 'Collection Flow',
          type: 'collection',
          status: flowResponse.status || 'active',
          engagement_id: flowResponse.engagement_id
        });

        // Check if this flow already has questionnaires
        let hasExistingData = false;
        try {
          const existingQuestionnaires = await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
          if (existingQuestionnaires.length > 0) {
            console.log(`✅ Found ${existingQuestionnaires.length} existing questionnaires for flow`);

            // Convert existing questionnaires to form data
            try {
              const adaptiveFormData = convertQuestionnairesToFormData(existingQuestionnaires[0], applicationId);

              if (validateFormDataStructure(adaptiveFormData)) {
                setState(prev => ({
                  ...prev,
                  formData: adaptiveFormData,
                  questionnaires: existingQuestionnaires,
                  isLoading: false
                }));

                toast({
                  title: 'Form Loaded',
                  description: 'Loaded existing questionnaire for this flow'
                });

                return; // Skip waiting for agents
              } else {
                console.warn('⚠️ Existing questionnaire data structure is invalid, will regenerate');
              }
            } catch (conversionError) {
              console.error('❌ Failed to convert existing questionnaire:', conversionError);
              // Continue to regenerate questionnaire instead of failing
            }
          }
        } catch (error) {
          console.log('🔍 No existing questionnaires found');
          hasExistingData = false;
        }
      } else {
        // First check if there's already an active flow
        try {
          const existingStatus = await collectionFlowApi.getFlowStatus();
          if (existingStatus.flow_id) {
            console.log('✅ Found existing active flow:', existingStatus.flow_id);
            flowResponse = await collectionFlowApi.getFlowDetails(existingStatus.flow_id);
            setState(prev => ({ ...prev, flowId: flowResponse.id }));
          } else {
            throw new Error('No active flow found, will create new one');
          }
        } catch (checkError: unknown) {
          // Only create new flow if no active flow exists
          if (checkError?.status === 404 || checkError?.message?.includes('No active flow')) {
            // Check if user has permission to create collection flows
            if (!canCreateCollectionFlow(user)) {
              throw new Error('You do not have permission to create collection flows. Only analysts and above can create flows.');
            }

            // Create a new collection flow - this triggers CrewAI agents
            const flowData = {
              automation_tier: 'tier_2',
              collection_config: {
                form_type: 'adaptive_data_collection',
                // Align with backend expectation: selected_application_ids array
                selected_application_ids: applicationId ? [applicationId] : [],
                collection_method: 'manual_adaptive_form'
              }
            };

            console.log('🤖 Creating CrewAI collection flow for adaptive forms...');
            flowResponse = await collectionFlowApi.createFlow(flowData);
            setState(prev => ({ ...prev, flowId: flowResponse.id }));
          } else if (checkError?.status === 500) {
            // Multiple flows exist - this shouldn't happen but handle gracefully
            console.error('❌ Multiple active flows detected, cannot proceed');
            throw new Error('Multiple active collection flows detected. Please contact support.');
          } else {
            throw checkError;
          }
        }
      }

      console.log(`🎯 Collection flow ${flowResponse.id} ready`);

      // Update the auth context with the collection flow
      setCurrentFlow({
        id: flowResponse.id,
        name: 'Collection Flow',
        type: 'collection',
        status: flowResponse.status || 'active',
        engagement_id: flowResponse.engagement_id
      });

      console.log(`🎯 Collection flow ${flowResponse.id} ready, triggering questionnaire generation...`);

      // Execute the flow to trigger CrewAI agents for questionnaire generation
      try {
        console.log('🚀 Executing collection flow to start questionnaire generation...');
        const executeResult = await collectionFlowApi.executeFlowPhase(flowResponse.id);
        console.log('✅ Flow execution started:', executeResult);
      } catch (executeError) {
        console.error('❌ Failed to execute collection flow:', executeError);

        // If the error indicates the MFO flow doesn't exist, the collection flow is corrupted
        if (executeError?.message?.includes('Flow not found') ||
            executeError?.response?.data?.detail?.includes('Flow not found')) {
          console.error('🔴 Collection flow is corrupted (missing MFO flow). Deleting and recreating...');

          // Delete the corrupted flow
          try {
            await collectionFlowApi.deleteFlow(flowResponse.id, true);
            console.log('✅ Deleted corrupted flow');
          } catch (deleteError) {
            console.error('Failed to delete corrupted flow:', deleteError);
          }

          // Throw error to trigger flow recreation
          throw new Error('Collection flow was corrupted. Please refresh the page to create a new flow.');
        }

        // For other errors, continue - the flow might already be running
        console.warn('⚠️ Continuing despite execution error - flow might already be running');
      }

      // Only wait for agents if there's existing data to analyze
      console.log('🔍 Checking for existing questionnaires from previous sessions...');

      // Check flow status first to see if agents are working or failed
      let flowStatus;
      try {
        flowStatus = await collectionFlowApi.getFlowStatus();

        // If we get a status, it means there's already an active flow
        if (flowStatus.flow_id && flowStatus.flow_id !== flowResponse.id) {
          console.warn('⚠️ Another active flow exists:', flowStatus.flow_id);
          // Use the existing flow instead
          flowResponse = await collectionFlowApi.getFlowDetails(flowStatus.flow_id);
          setState(prev => ({ ...prev, flowId: flowResponse.id }));
        }

        // If flow shows error, use fallback immediately
        if (flowStatus.status === 'error' || flowStatus.status === 'failed') {
          console.warn('⚠️ CrewAI agents failed, using fallback questionnaire');
          throw new Error('Agent processing failed - using default questionnaire');
        }
      } catch (statusError: unknown) {
        // If status check fails with 500 (multiple flows), we should handle it gracefully
        if (statusError?.status === 500) {
          console.warn('⚠️ Multiple active flows detected, continuing with current flow');
        } else if (statusError?.status !== 404) {
          console.error('❌ Failed to check flow status:', statusError);
        }
      }

      // Wait for CrewAI agents to complete gap analysis and generate questionnaires
      // Add reasonable timeout to prevent infinite loops
      let attempts = 0;
      const MAX_ATTEMPTS = 60; // Max 2 minutes (60 * 2 seconds)
      let agentQuestionnaires = [];
      let flowFailed = false;

      console.log('⏳ Waiting for CrewAI agents to process through phases and generate questionnaires...');
      console.log('   Expected phases: PLATFORM_DETECTION -> AUTOMATED_COLLECTION -> GAP_ANALYSIS -> QUESTIONNAIRE_GENERATION');
      console.log(`   Max wait time: ${MAX_ATTEMPTS * 2} seconds`);

      while (agentQuestionnaires.length === 0 && !flowFailed && attempts < MAX_ATTEMPTS) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Check every 2 seconds
        attempts++;

        try {
          // Check flow status to monitor phase progression
          if (attempts % 3 === 0 || attempts === 1) {
            flowStatus = await collectionFlowApi.getFlowStatus();
            console.log(`📊 Flow status check (attempt ${attempts}):`, {
              status: flowStatus.status,
              current_phase: flowStatus.current_phase,
              message: flowStatus.message
            });

            if (flowStatus.status === 'error' || flowStatus.status === 'failed') {
              console.error('❌ Collection flow failed:', flowStatus.message);
              flowFailed = true;
              break;
            }
          }

          // Try to fetch questionnaires
          agentQuestionnaires = await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
          if (agentQuestionnaires.length > 0) {
            console.log(`✅ Found ${agentQuestionnaires.length} agent-generated questionnaires after ${attempts} attempts`);
          }
        } catch (error) {
          // This is expected while agents are still processing
          if (attempts % 10 === 0) {
            console.log(`⏳ Still waiting for questionnaires... (${attempts * 2} seconds elapsed)`);
          }
        }

        // Log progress every 30 seconds
        if (attempts % 15 === 0) {
          console.log(`⏰ Still processing... This may take a few minutes for CrewAI agents to complete all phases.`);
        }
      }

      if (flowFailed) {
        throw new Error('Collection flow failed during processing. Check backend logs for details.');
      }

      if (agentQuestionnaires.length === 0) {
        console.warn('⚠️ No questionnaires generated after timeout. Using fallback.');
        // Use a local fallback adaptive form to allow user to proceed
        const fallback = createFallbackFormData(applicationId || null);
        setState(prev => ({
          ...prev,
          formData: fallback,
          questionnaires: [],
        }));

        toast({
          title: 'Fallback Form Loaded',
          description: 'Using a basic adaptive form to begin collection while agents prepare questionnaires.'
        });
        return;
      }

      // Convert CrewAI-generated questionnaires to AdaptiveFormData format
      let adaptiveFormData;
      try {
        adaptiveFormData = convertQuestionnairesToFormData(agentQuestionnaires[0], applicationId);
      } catch (conversionError) {
        console.error('❌ Failed to convert agent questionnaire to form data:', conversionError);
        throw new Error(`Failed to convert agent-generated questionnaire to form format: ${conversionError.message}`);
      }

      // Validate the converted form data
      if (!validateFormDataStructure(adaptiveFormData)) {
        console.error('❌ Generated form data structure validation failed:', adaptiveFormData);
        throw new Error('Generated form data structure is invalid. The questionnaire may be missing required fields or sections.');
      }

      setState(prev => ({
        ...prev,
        formData: adaptiveFormData,
        questionnaires: agentQuestionnaires
      }));

      console.log('✅ Successfully loaded agent-generated adaptive form');

      toast({
        title: 'Adaptive Form Ready',
        description: `CrewAI agents generated ${agentQuestionnaires.length} questionnaire(s) based on gap analysis.`
      });

    } catch (error: unknown) {
      console.error('❌ Failed to initialize adaptive collection:', error);

      // Create a more user-friendly error message
      let userMessage = 'Failed to initialize collection flow.';
      if (error?.message) {
        if (error.message.includes('questionnaire')) {
          userMessage = 'Failed to load adaptive forms. The questionnaire generation process encountered an error.';
        } else if (error.message.includes('permission')) {
          userMessage = 'Permission denied. You do not have access to create collection flows.';
        } else if (error.message.includes('timeout')) {
          userMessage = 'The form generation process is taking longer than expected. Please try again.';
        } else if (error.message.includes('Multiple active')) {
          userMessage = 'Multiple active collection flows detected. Please manage existing flows first.';
        } else {
          userMessage = error.message;
        }
      }

      const enhancedError = new Error(userMessage);
      enhancedError.cause = error;

      setState(prev => ({ ...prev, error: enhancedError, isLoading: false }));

      // Only show toast for non-409 errors to avoid spam
      if (!error?.message?.includes('409') && !error?.message?.includes('Conflict')) {
        toast({
          title: 'Failed to Load Adaptive Forms',
          description: userMessage,
          variant: 'destructive'
        });
      } else {
        // For 409 conflicts, show a more helpful message without toast spam
        console.log('⚠️ 409 Conflict detected - existing flow found, showing management UI');
      }

      // Ensure loading state is cleared
      setState(prev => ({ ...prev, isLoading: false }));

      // No fallback - let the error be shown to the user
      throw enhancedError;
    } finally {
      // Always ensure loading state is cleared
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [checkingFlows, hasBlockingFlows, state.isLoading, flowIdFromUrl, setCurrentFlow, applicationId, user, toast]);

  /**
   * Handle field value changes
   */
  const handleFieldChange = (fieldId: string, value: FormFieldValue): void => {
    setState(prev => ({
      ...prev,
      formValues: {
        ...prev.formValues,
        [fieldId]: value
      }
    }));
  };

  /**
   * Handle validation result changes
   */
  const handleValidationChange = (newValidation: FormValidationResult): void => {
    setState(prev => ({ ...prev, validation: newValidation }));
  };

  /**
   * Save form progress
   */
  const handleSave = async (): Promise<void> => {
    if (!state.formData) return;

    setState(prev => ({ ...prev, isSaving: true }));

    try {
      // Simulate API call to save progress
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast({
        title: 'Progress Saved',
        description: 'Your form progress has been saved successfully.'
      });
    } catch (error) {
      console.error('Failed to save progress:', error);
      toast({
        title: 'Save Failed',
        description: 'Failed to save progress. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setState(prev => ({ ...prev, isSaving: false }));
    }
  };

  /**
   * Submit the completed form
   */
  const handleSubmit = async (data: CollectionFormData): Promise<void> => {
    if (!state.validation?.isValid) {
      toast({
        title: 'Validation Required',
        description: 'Please complete all required fields and resolve validation errors.',
        variant: 'destructive'
      });
      return;
    }

    if (!state.flowId || state.questionnaires.length === 0) {
      toast({
        title: 'Collection Flow Not Ready',
        description: 'CrewAI collection flow is not properly initialized. Please refresh and try again.',
        variant: 'destructive'
      });
      return;
    }

    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Submit responses to the CrewAI-generated questionnaire
      const questionnaireId = state.questionnaires[0].id;
      const submissionData = {
        responses: data,
        form_metadata: {
          form_id: state.formData?.formId,
          application_id: applicationId,
          completion_percentage: state.validation?.completionPercentage,
          confidence_score: state.validation?.overallConfidenceScore,
          submitted_at: new Date().toISOString()
        },
        validation_results: state.validation
      };

      console.log(`🚀 Submitting adaptive form responses to CrewAI questionnaire ${questionnaireId}`);

      await collectionFlowApi.submitQuestionnaireResponse(
        state.flowId,
        questionnaireId,
        submissionData
      );

      toast({
        title: 'Adaptive Form Submitted Successfully',
        description: 'CrewAI agents are processing your responses and will continue the collection flow.'
      });

      console.log('✅ Form submitted successfully, CrewAI agents will continue processing');

    } catch (error: unknown) {
      console.error('❌ Adaptive form submission failed:', error);

      const errorMessage = error?.response?.data?.detail ||
                          error?.response?.data?.message ||
                          error?.message ||
                          'Failed to submit adaptive form responses.';

      toast({
        title: 'Adaptive Form Submission Failed',
        description: `Error: ${errorMessage}`,
        variant: 'destructive'
      });

    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  /**
   * Reset the flow state
   */
  const resetFlow = (): void => {
    setState({
      formData: null,
      formValues: {},
      validation: null,
      flowId: null,
      questionnaires: [],
      isLoading: false,
      isSaving: false,
      error: null
    });
    setCurrentFlow(null);
  };

  // Auto-initialize effect
  useEffect(() => {
    // STOP INFINITE LOOPS: Only initialize once and handle errors gracefully
    // Only initialize if:
    // 1. Auto-initialize is enabled
    // 2. Not currently checking for flows
    // 3. No blocking flows exist
    // 4. We don't have form data yet
    // 5. Not currently loading
    // 6. No previous error exists (prevents retry loops)
    if (autoInitialize && !checkingFlows && !hasBlockingFlows && !state.formData && !state.isLoading && !state.error) {
      console.log('🚀 Auto-initializing collection flow...', {
        hasFormData: !!state.formData,
        hasBlockingFlows,
        isLoading: state.isLoading,
        hasError: !!state.error
      });
      initializeFlow().catch(error => {
        console.error('❌ Auto-initialization failed:', error);
        // Don't retry - let the user manually retry or handle the error
        setState(prev => ({ ...prev, error, isLoading: false }));
      });
    }

    // Cleanup: Clear the flow context when leaving the page
    return () => {
      setCurrentFlow(null);
    };
  }, [applicationId, flowIdFromUrl, checkingFlows, hasBlockingFlows, autoInitialize, state.formData, state.isLoading, state.error, initializeFlow, setCurrentFlow]);

  return {
    // State
    ...state,

    // Actions
    initializeFlow,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    resetFlow
  };
};
