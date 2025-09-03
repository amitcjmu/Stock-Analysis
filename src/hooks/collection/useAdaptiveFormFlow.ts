/**
 * Custom hook for managing adaptive form flows
 *
 * Extracted from AdaptiveForms.tsx to provide reusable flow management logic
 * for collection workflows with CrewAI integration.
 */

import React, { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';

// Import flow management hooks
import { useCollectionFlowManagement, useIncompleteCollectionFlows } from './useCollectionFlowManagement';

// Import API services
import { collectionFlowApi } from '@/services/api/collection-flow';
import { apiCall } from '@/config/api';

// Import form data transformation utilities
import { convertQuestionnairesToFormData, convertQuestionnaireToFormData, validateFormDataStructure, createFallbackFormData } from '@/utils/collection/formDataTransformation'

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

/**
 * Extract existing responses from questionnaire to populate form values
 * Handles both array and object response formats for backward compatibility
 */
function extractExistingResponses(questionnaire: CollectionQuestionnaire): CollectionFormData {
  const responses: CollectionFormData = {};

  try {
    // Check if questionnaire has responses_collected field
    const responsesData = (questionnaire as any).responses_collected;

    if (!responsesData) {
      console.log('📝 No existing responses found in questionnaire');
      return responses;
    }

    let latestPayload: any = null;

    // Handle different response formats
    if (Array.isArray(responsesData)) {
      // Array format: get the latest submission
      const latestSubmission = responsesData[responsesData.length - 1];
      latestPayload = latestSubmission?.payload;
    } else if (typeof responsesData === 'object') {
      // Object format: check for latest_submission or history
      if (responsesData.latest_submission?.payload) {
        latestPayload = responsesData.latest_submission.payload;
      } else if (responsesData.history && Array.isArray(responsesData.history)) {
        const latestFromHistory = responsesData.history[responsesData.history.length - 1];
        latestPayload = latestFromHistory?.payload;
      } else {
        // Direct payload format
        latestPayload = responsesData;
      }
    }

    if (latestPayload && typeof latestPayload === 'object') {
      // Convert the payload to form values format
      Object.keys(latestPayload).forEach(fieldId => {
        const value = latestPayload[fieldId];

        // Handle different value types appropriately
        if (value !== null && value !== undefined) {
          // Convert to the expected FormFieldValue type
          if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
            responses[fieldId] = value;
          } else if (Array.isArray(value)) {
            // Handle array values (e.g., multi-select)
            responses[fieldId] = value;
          } else if (typeof value === 'object') {
            // Handle object values (convert to JSON string for text fields)
            responses[fieldId] = JSON.stringify(value);
          }
        }
      });

      console.log(`📝 Extracted ${Object.keys(responses).length} existing responses from questionnaire`);
    }

  } catch (error) {
    console.error('❌ Failed to extract existing responses:', error);
    // Return empty responses if extraction fails
  }

  return responses;
}

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
  isCompleted: boolean;
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
    isCompleted: false,
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
                // Fetch saved responses from the backend
                let existingResponses: CollectionFormData = {};

                const questionnaireId = existingQuestionnaires[0]?.id || 'default-questionnaire';
                try {
                  const savedResponsesData = await collectionFlowApi.getQuestionnaireResponses(
                    flowResponse.id,
                    questionnaireId
                  );

                  if (savedResponsesData?.responses && Object.keys(savedResponsesData.responses).length > 0) {
                    existingResponses = savedResponsesData.responses;
                    console.log(`📝 Loaded ${Object.keys(existingResponses).length} saved responses from backend:`, existingResponses);
                  } else {
                    // Fallback to extracting from questionnaire if backend doesn't have responses
                    existingResponses = extractExistingResponses(existingQuestionnaires[0]);
                  }
                } catch (err) {
                  console.warn('Failed to fetch saved responses, using fallback:', err);
                  // Fallback to extracting from questionnaire
                  existingResponses = extractExistingResponses(existingQuestionnaires[0]);
                }

                setState(prev => ({
                  ...prev,
                  formData: adaptiveFormData,
                  formValues: existingResponses, // Load existing responses into form values
                  questionnaires: existingQuestionnaires,
                  isLoading: false
                }));

                toast({
                  title: 'Form Loaded',
                  description: 'Loaded existing questionnaire with saved responses'
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
      // Using HTTP polling instead of WebSocket for Vercel/Railway compatibility
      const INITIALIZATION_TIMEOUT = 10000; // 10 seconds max wait time

      let agentQuestionnaires = [];
      let timeoutReached = false;

      console.log('⏳ Waiting for CrewAI agents to process through phases and generate questionnaires...');
      console.log('   Expected phases: PLATFORM_DETECTION -> AUTOMATED_COLLECTION -> GAP_ANALYSIS -> QUESTIONNAIRE_GENERATION');
      console.log(`   Using HTTP polling with ${INITIALIZATION_TIMEOUT / 1000}s timeout`);

      // Setup HTTP polling with timeout
      const startTime = Date.now();

      const pollForQuestionnaires = async (): Promise<void> => {
        while (agentQuestionnaires.length === 0 && !timeoutReached) {
          const elapsed = Date.now() - startTime;

          if (elapsed >= INITIALIZATION_TIMEOUT) {
            timeoutReached = true;
            console.warn(`⚠️ HTTP polling timeout after ${elapsed}ms`);
            break;
          }

          try {
            // Check flow status to monitor phase progression
            flowStatus = await collectionFlowApi.getFlowStatus();
            console.log(`📊 Flow status check (${elapsed}ms elapsed):`, {
              status: flowStatus.status,
              current_phase: flowStatus.current_phase,
              message: flowStatus.message
            });

            if (flowStatus.status === 'error' || flowStatus.status === 'failed') {
              console.error('❌ Collection flow failed:', flowStatus.message);
              throw new Error(`Collection flow failed: ${flowStatus.message}`);
            }

            // Try to fetch questionnaires
            agentQuestionnaires = await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
            if (agentQuestionnaires.length > 0) {
              console.log(`✅ Found ${agentQuestionnaires.length} agent-generated questionnaires after ${elapsed}ms`);
              return;
            }
          } catch (error) {
            // Re-throw flow errors, but continue polling on questionnaire fetch errors
            if (error?.message?.includes('Collection flow failed')) {
              throw error;
            }

            console.log(`⏳ Still waiting for questionnaires... (${elapsed}ms elapsed)`);
          }

          // Smart polling interval based on flow state
          const isActive = flowStatus?.status === 'running' || flowStatus?.current_phase === 'processing';
          const pollInterval = isActive ? 2000 : 5000; // 2s for active, 5s for waiting
          await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
      };

      try {
        await pollForQuestionnaires();
      } catch (error) {
        console.warn('⚠️ Agent processing failure, proceeding with fallback:', error.message);
        // Don't throw here - let the fallback logic handle it below
      }

      // Handle timeout or no questionnaires generated
      if (agentQuestionnaires.length === 0 || timeoutReached) {
        console.warn('⚠️ No questionnaires generated within timeout period. Using fallback form.');

        // Use a local fallback adaptive form to allow user to proceed
        const fallback = createFallbackFormData(applicationId || null);
        setState(prev => ({
          ...prev,
          formData: fallback,
          questionnaires: [],
          isLoading: false,
          error: null // Clear any previous errors since we have a fallback
        }));

        toast({
          title: 'Fallback Form Loaded',
          description: `CrewAI agents are taking longer than expected (>${INITIALIZATION_TIMEOUT / 1000}s). Using a basic adaptive form to begin collection.`,
          variant: 'default'
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
      let shouldUseFallback = false;

      if (error?.message) {
        if (error.message.includes('timeout') || error.message.includes('HTTP polling timeout')) {
          userMessage = `Collection initialization timed out after ${INITIALIZATION_TIMEOUT / 1000} seconds. Using fallback form to allow you to proceed.`;
          shouldUseFallback = true;
        } else if (error.message.includes('questionnaire')) {
          userMessage = 'Failed to load adaptive forms. The questionnaire generation process encountered an error.';
          shouldUseFallback = true;
        } else if (error.message.includes('permission')) {
          userMessage = 'Permission denied. You do not have access to create collection flows.';
        } else if (error.message.includes('Multiple active')) {
          userMessage = 'Multiple active collection flows detected. Please manage existing flows first.';
        } else {
          userMessage = error.message;
          // For unknown errors, provide fallback if it's not an auth/permission issue
          shouldUseFallback = !error.message.includes('permission') && !error.message.includes('auth');
        }
      }

      // If we should use fallback, provide it instead of showing error
      if (shouldUseFallback) {
        console.warn('⚠️ Using fallback form due to initialization error:', userMessage);

        const fallback = createFallbackFormData(applicationId || null);
        setState(prev => ({
          ...prev,
          formData: fallback,
          questionnaires: [],
          isLoading: false,
          error: null // Clear error since we have a working fallback
        }));

        toast({
          title: 'Fallback Form Loaded',
          description: userMessage,
          variant: 'default'
        });

        return; // Exit early with fallback, don't throw error
      }

      // For non-fallback errors, show error state
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

      // Throw error for non-fallback cases
      throw enhancedError;
    } finally {
      // Always ensure loading state is cleared
      setState(prev => ({ ...prev, isLoading: false }));

      // Clear any pending timers
      console.log('✨ Collection workflow initialization completed');
    }
  }, [checkingFlows, hasBlockingFlows, state.isLoading, flowIdFromUrl, setCurrentFlow, applicationId, user, toast]);

  /**
   * Handle field value changes - wrapped in useCallback for performance
   */
  const handleFieldChange = useCallback((fieldId: string, value: FormFieldValue): void => {
    setState(prev => ({
      ...prev,
      formValues: {
        ...prev.formValues,
        [fieldId]: value
      }
    }));
  }, []); // No dependencies needed as setState is stable

  /**
   * Handle validation result changes - wrapped in useCallback for performance
   */
  const handleValidationChange = useCallback((newValidation: FormValidationResult): void => {
    setState(prev => ({ ...prev, validation: newValidation }));
  }, []); // No dependencies needed as setState is stable

  /**
   * Save form progress - wrapped in useCallback to prevent unnecessary re-renders
   */
  const handleSave = useCallback(async (): Promise<void> => {
    console.log('🔴 SAVE BUTTON CLICKED - handleSave triggered', {
      hasFormData: !!state.formData,
      hasFlowId: !!state.flowId,
      flowId: state.flowId,
      formValues: state.formValues,
      timestamp: new Date().toISOString()
    });

    if (!state.formData || !state.flowId) {
      console.error('❌ Cannot save: Missing formData or flowId', {
        formData: state.formData,
        flowId: state.flowId
      });
      return;
    }

    setState(prev => ({ ...prev, isSaving: true }));

    try {
      // Get the first questionnaire (assuming single questionnaire for now)
      const questionnaire = state.questionnaires?.[0];
      const questionnaireId = questionnaire?.id || 'default-questionnaire';

      console.log('📋 Preparing to save questionnaire:', {
        questionnaireId,
        hasQuestionnaire: !!questionnaire,
        totalQuestionnaires: state.questionnaires?.length || 0
      });

      // Prepare the submission data in the format expected by the backend
      const submissionData = {
        responses: state.formValues,
        form_metadata: {
          form_id: state.formData.formId,
          application_id: applicationId || null,
          completion_percentage: state.validation?.completionPercentage || 0,
          confidence_score: state.validation?.overallConfidenceScore || 0,
          submitted_at: new Date().toISOString(),
        },
        validation_results: {
          isValid: state.validation?.isValid || false,
          fieldResults: state.validation?.fieldResults || {},
        },
      };

      // Submit the questionnaire responses to the backend
      const endpoint = `/collection/flows/${state.flowId}/questionnaires/${questionnaireId}/responses`;
      console.log('🚀 Submitting to endpoint:', endpoint, {
        submissionData
      });

      const response = await apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify(submissionData),
      });

      console.log('💾 Questionnaire responses saved successfully:', response);

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
  }, [state.formData, state.flowId, state.formValues, state.validation, state.questionnaires, applicationId, toast]); // Dependencies for useCallback

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

      // For bootstrap questionnaires, when submitted, mark as 100% complete
      const isBootstrapForm = questionnaireId.startsWith('bootstrap_');
      const completionPercentage = isBootstrapForm ? 100 : (state.validation?.completionPercentage || 0);

      const submissionData = {
        responses: data,
        form_metadata: {
          form_id: state.formData?.formId,
          application_id: applicationId,
          completion_percentage: completionPercentage,
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

      // Refresh questionnaires after successful submission to get the next set
      console.log('🔄 Refreshing questionnaires to check for follow-up questions...');

      // Wait a moment for the backend to process and generate new questionnaires
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Re-fetch questionnaires to get the next set
      if (state.flowId) {
        try {
          const updatedQuestionnaires = await collectionFlowApi.getFlowQuestionnaires(state.flowId);
          console.log(`📋 Retrieved ${updatedQuestionnaires.length} questionnaires after submission`);

          setState(prev => ({
            ...prev,
            questionnaires: updatedQuestionnaires
          }));

          // If we have new questionnaires, load the first one
          if (updatedQuestionnaires.length > 0) {
            const nextQuestionnaire = updatedQuestionnaires.find(q =>
              q.completion_status === 'pending' ||
              q.completion_status === 'in_progress'
            ) || updatedQuestionnaires[0];

            if (nextQuestionnaire) {
              console.log(`📝 Loading next questionnaire: ${nextQuestionnaire.id}`);

              // Convert the questionnaire to form data format
              const nextFormData = convertQuestionnaireToFormData(nextQuestionnaire);

              // Extract any existing responses for this questionnaire
              const existingResponses = extractExistingResponses(nextQuestionnaire);

              setState(prev => ({
                ...prev,
                formData: nextFormData,
                formValues: existingResponses, // Load existing responses if available
                validation: null
              }));

              toast({
                title: 'Next Section Ready',
                description: `Please continue with: ${nextQuestionnaire.title || 'Next questionnaire'}`
              });
            }
          } else {
            // No more questionnaires returned - collection is complete
            console.log('✅ No more questionnaires - collection flow is complete');
            setState(prev => ({ ...prev, isCompleted: true }));

            // Check if this was a bootstrap form completion
            if (isBootstrapForm) {
              toast({
                title: 'Application Details Saved',
                description: 'Application information has been saved successfully! You can now proceed to the next phase.',
                variant: 'default'
              });
            } else {
              toast({
                title: 'Collection Complete',
                description: 'All required information has been collected successfully!',
                variant: 'default'
              });
            }
          }
        } catch (refreshError) {
          console.error('Failed to refresh questionnaires:', refreshError);
          toast({
            title: 'Warning',
            description: 'Form submitted successfully, but unable to load next section. Please refresh the page.',
            variant: 'default'
          });
        }
      }

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
      isCompleted: false,
      error: null
    });
    setCurrentFlow(null);
  };

  // Auto-initialize effect - Fixed to prevent infinite loops
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
  }, [applicationId, flowIdFromUrl, checkingFlows, hasBlockingFlows, autoInitialize, state.formData, state.isLoading, state.error]); // Removed initializeFlow from dependencies to prevent infinite loop

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Clear the flow context when component unmounts
      setCurrentFlow(null);

      // Clear any pending timeouts or intervals
      console.log('🧹 Cleaning up collection workflow state');
    };
  }, [setCurrentFlow]);

  // CC: Debugging - Log hook return only when key values change
  React.useEffect(() => {
    console.log('🔍 useAdaptiveFormFlow state updated:', {
      hasHandleSave: typeof handleSave === 'function',
      flowId: state.flowId,
      hasFormData: !!state.formData,
    });
  }, [state.flowId, !!state.formData, typeof handleSave]); // Only log when key values change

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
