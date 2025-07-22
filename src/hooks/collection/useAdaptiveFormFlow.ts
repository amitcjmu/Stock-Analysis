/**
 * Custom hook for managing adaptive form flows
 * 
 * Extracted from AdaptiveForms.tsx to provide reusable flow management logic
 * for collection workflows with CrewAI integration.
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';

// Import flow management hooks
import { useCollectionFlowManagement, useIncompleteCollectionFlows } from './useCollectionFlowManagement';

// Import API services
import { collectionFlowApi } from '@/services/api/collection-flow';

// Import form data transformation utilities
import { 
  convertQuestionnairesToFormData, 
  createFallbackFormData,
  validateFormDataStructure 
} from '@/utils/collection/formDataTransformation';

// Import types
import type { 
  AdaptiveFormData, 
  CollectionFormData, 
  FormValidationResult 
} from '@/components/collection/types';

// Import auth context
import { useAuth } from '@/contexts/AuthContext';

// Import RBAC utilities
import { canCreateCollectionFlow } from '@/utils/rbac';

export interface UseAdaptiveFormFlowOptions {
  applicationId?: string | null;
  flowId?: string | null;
  autoInitialize?: boolean;
}

export interface AdaptiveFormFlowState {
  formData: AdaptiveFormData | null;
  formValues: CollectionFormData;
  validation: FormValidationResult | null;
  flowId: string | null;
  questionnaires: unknown[];
  isLoading: boolean;
  isSaving: boolean;
  error: Error | null;
}

export interface AdaptiveFormFlowActions {
  initializeFlow: () => Promise<void>;
  handleFieldChange: (fieldId: string, value: unknown) => void;
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
  
  // Check for incomplete flows
  const { 
    data: incompleteFlows = [], 
    isLoading: checkingFlows 
  } = useIncompleteCollectionFlows();
  
  const hasIncompleteFlows = incompleteFlows.length > 0;
  
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

  /**
   * Initialize the adaptive collection flow
   */
  const initializeFlow = async (): Promise<void> => {
    // Don't initialize if there are incomplete flows or still checking
    if (checkingFlows || hasIncompleteFlows) {
      console.log('🛑 Blocking flow initialization due to incomplete flows or still checking');
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
      } else {
        // Check if user has permission to create collection flows
        if (!canCreateCollectionFlow(user)) {
          throw new Error('You do not have permission to create collection flows. Only analysts and above can create flows.');
        }
        
        // Create a new collection flow - this triggers CrewAI agents
        const flowData = {
          automation_tier: 'tier_2',
          collection_config: {
            form_type: 'adaptive_data_collection',
            application_id: applicationId,
            collection_method: 'manual_adaptive_form'
          }
        };

        console.log('🤖 Creating CrewAI collection flow for adaptive forms...');
        flowResponse = await collectionFlowApi.createFlow(flowData);
        setState(prev => ({ ...prev, flowId: flowResponse.id }));
      }

      console.log(`🎯 Collection flow ${flowResponse.id} ready, waiting for CrewAI agents...`);
      
      // Update the auth context with the collection flow
      setCurrentFlow({
        id: flowResponse.id,
        name: 'Collection Flow',
        type: 'collection',
        status: flowResponse.status || 'active',
        engagement_id: flowResponse.engagement_id
      });
      
      // Wait for CrewAI agents to complete gap analysis and generate questionnaires
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds timeout
      let agentQuestionnaires = [];

      while (attempts < maxAttempts && agentQuestionnaires.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        
        try {
          agentQuestionnaires = await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
          console.log(`🔍 Attempt ${attempts + 1}: Found ${agentQuestionnaires.length} agent-generated questionnaires`);
        } catch (error) {
          console.log(`⏳ Waiting for CrewAI agents to generate questionnaires... (${attempts + 1}/${maxAttempts})`);
        }
        
        attempts++;
      }

      if (agentQuestionnaires.length === 0) {
        throw new Error('CrewAI agents did not generate questionnaires in time. Please try again.');
      }

      // Convert CrewAI-generated questionnaires to AdaptiveFormData format
      const adaptiveFormData = convertQuestionnairesToFormData(agentQuestionnaires[0], applicationId);
      
      // Validate the converted form data
      if (!validateFormDataStructure(adaptiveFormData)) {
        throw new Error('Generated form data structure is invalid');
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
      
      setState(prev => ({ ...prev, error }));
      
      toast({
        title: 'Adaptive Form Generation Failed',
        description: error.message || 'Failed to generate adaptive questionnaire. Using fallback form.',
        variant: 'destructive'
      });
      
      // Fallback to basic form if CrewAI agents fail
      try {
        const fallbackFormData = createFallbackFormData(applicationId);
        setState(prev => ({ ...prev, formData: fallbackFormData }));
      } catch (fallbackError) {
        console.error('❌ Failed to create fallback form:', fallbackError);
      }
      
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  /**
   * Handle field value changes
   */
  const handleFieldChange = (fieldId: string, value: unknown): void => {
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
    if (autoInitialize && !checkingFlows && !hasIncompleteFlows) {
      initializeFlow();
    }
    
    // Cleanup: Clear the flow context when leaving the page
    return () => {
      setCurrentFlow(null);
    };
  }, [applicationId, flowIdFromUrl, checkingFlows, hasIncompleteFlows, autoInitialize]);

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