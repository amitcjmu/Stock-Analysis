import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save, Send } from 'lucide-react';

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Import existing collection components
import { AdaptiveForm } from '@/components/collection/AdaptiveForm';
import { ProgressTracker } from '@/components/collection/ProgressTracker';
import { ValidationDisplay } from '@/components/collection/ValidationDisplay';
import { BulkDataGrid } from '@/components/collection/BulkDataGrid';

// Import types
import type { 
  AdaptiveFormData, 
  CollectionFormData, 
  FormValidationResult,
  ProgressMilestone 
} from '@/components/collection/types';

// Import collection flow API and management hooks
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useCollectionFlowManagement, useIncompleteCollectionFlows } from '@/hooks/collection/useCollectionFlowManagement';
import { CollectionUploadBlocker } from '@/components/collection/CollectionUploadBlocker';

// Import auth context for flow management
import { useAuth } from '@/contexts/AuthContext';

// Import RBAC utilities
import { canCreateCollectionFlow } from '@/utils/rbac';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

/**
 * Adaptive Forms collection page
 * Integrates the AdaptiveForm component with progress tracking and validation
 */
const AdaptiveForms: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { setCurrentFlow, user } = useAuth();

  // Collection flow management
  const { 
    continueFlow, 
    deleteFlow 
  } = useCollectionFlowManagement();
  
  // Check for incomplete flows that would block new collection processes
  const { 
    data: incompleteFlows = [], 
    isLoading: checkingFlows, 
    refetch: refetchFlows 
  } = useIncompleteCollectionFlows();
  
  const hasIncompleteFlows = incompleteFlows.length > 0;
  
  // Debug logging
  console.log('🔍 Collection Flow Debug:', {
    checkingFlows,
    incompleteFlows,
    hasIncompleteFlows,
    incompleteFlowsLength: incompleteFlows.length
  });

  // State management
  const [formData, setFormData] = useState<AdaptiveFormData | null>(null);
  const [formValues, setFormValues] = useState<CollectionFormData>({});
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [bulkMode, setBulkMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [flowId, setFlowId] = useState<string | null>(null);
  const [questionnaires, setQuestionnaires] = useState<any[]>([]);
  const [showFlowManager, setShowFlowManager] = useState(false);

  // Get application ID and flow ID from URL params if provided
  const applicationId = searchParams.get('applicationId');
  const flowIdFromUrl = searchParams.get('flowId');

  // Flow management handlers
  const handleContinueFlow = async (flowId: string) => {
    try {
      await continueFlow(flowId);
      // Navigate to appropriate collection phase
      navigate(`/collection/progress/${flowId}`);
    } catch (error) {
      console.error('Failed to continue collection flow:', error);
    }
  };

  const handleDeleteFlow = async (flowId: string) => {
    try {
      await deleteFlow(flowId, false);
      // Refresh flows after deletion
      refetchFlows();
    } catch (error) {
      console.error('Failed to delete collection flow:', error);
    }
  };

  const handleViewFlowDetails = (flowId: string, phase: string) => {
    // Navigate to flow details or progress page
    navigate(`/collection/progress/${flowId}`);
  };

  const handleManageFlows = () => {
    // Navigate to collection flow management page
    navigate('/collection/management');
  };

  // Initialize collection flow and get adaptive questionnaires from CrewAI agents
  useEffect(() => {
    console.log('🔍 useEffect triggered:', {
      checkingFlows,
      hasIncompleteFlows,
      shouldReturn: checkingFlows || hasIncompleteFlows
    });
    
    // Don't initialize if there are incomplete flows or still checking
    if (checkingFlows || hasIncompleteFlows) {
      console.log('🛑 Blocking flow initialization due to incomplete flows or still checking');
      return;
    }

    const initializeAdaptiveCollection = async () => {
      setIsLoading(true);
      try {
        let flowResponse;
        
        // Check if we have a flow ID from the URL (created from overview page)
        if (flowIdFromUrl) {
          console.log(`📋 Using existing collection flow: ${flowIdFromUrl}`);
          flowResponse = await collectionFlowApi.getFlowDetails(flowIdFromUrl);
          setFlowId(flowResponse.id);
          
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
          
          // Step 1: Create a new collection flow - this triggers CrewAI agents
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
          setFlowId(flowResponse.id);
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
        
        // Step 2: Wait for CrewAI agents to complete gap analysis and generate questionnaires
        // Poll for questionnaires until they're ready
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

        // Step 3: Convert CrewAI-generated questionnaires to AdaptiveFormData format
        const adaptiveFormData = convertQuestionnairesToFormData(agentQuestionnaires[0], applicationId);
        setFormData(adaptiveFormData);
        setQuestionnaires(agentQuestionnaires);

        console.log('✅ Successfully loaded agent-generated adaptive form');
        
        toast({
          title: 'Adaptive Form Ready',
          description: `CrewAI agents generated ${agentQuestionnaires.length} questionnaire(s) based on gap analysis.`
        });

      } catch (error: any) {
        console.error('❌ Failed to initialize adaptive collection:', error);
        
        toast({
          title: 'Adaptive Form Generation Failed',
          description: error.message || 'Failed to generate adaptive questionnaire. Using fallback form.',
          variant: 'destructive'
        });
        
        // Fallback to basic form if CrewAI agents fail
        setFormData(createFallbackFormData(applicationId));
        
      } finally {
        setIsLoading(false);
      }
    };

    initializeAdaptiveCollection();
    
    // Cleanup: Clear the flow context when leaving the page
    return () => {
      // Only clear if we're on a collection flow
      setCurrentFlow(null);
    };
  }, [applicationId, flowIdFromUrl, checkingFlows, hasIncompleteFlows, setCurrentFlow]);

  // Helper function to convert CrewAI questionnaires to AdaptiveFormData format
  const convertQuestionnairesToFormData = (questionnaire: any, applicationId: string | null): AdaptiveFormData => {
    try {
      const questions = questionnaire.questions || [];
      const sections = [];
      
      // Group questions into logical sections
      const basicQuestions = questions.filter((q: any) => 
        q.category === 'basic' || q.field_type === 'application_name' || q.field_type === 'application_type'
      );
      
      const technicalQuestions = questions.filter((q: any) => 
        q.category === 'technical' || q.field_type === 'technology_stack' || q.field_type === 'database'
      );
      
      if (basicQuestions.length > 0) {
        sections.push({
          id: 'agent-basic-info',
          title: 'Basic Information',
          description: 'Core application details identified by CrewAI gap analysis',
          fields: basicQuestions.map((q: any, index: number) => ({
            id: q.field_id || `basic-${index}`,
            label: q.question_text || q.label || 'Field',
            fieldType: mapQuestionTypeToFieldType(q.field_type || q.question_type),
            criticalAttribute: q.critical_attribute || 'unknown',
            validation: { 
              required: q.required !== false,
              ...(q.validation || {})
            },
            section: 'agent-basic-info',
            order: index + 1,
            businessImpactScore: q.business_impact_score || 0.8,
            options: q.options || (q.field_type === 'select' ? getDefaultOptions(q.field_type) : undefined),
            helpText: q.help_text || q.description
          })),
          order: 1,
          requiredFieldsCount: basicQuestions.filter((q: any) => q.required !== false).length,
          completionWeight: 0.4
        });
      }
      
      if (technicalQuestions.length > 0) {
        sections.push({
          id: 'agent-technical-details',
          title: 'Technical Details',
          description: 'Technical architecture and dependencies from CrewAI analysis',
          fields: technicalQuestions.map((q: any, index: number) => ({
            id: q.field_id || `tech-${index}`,
            label: q.question_text || q.label || 'Field',
            fieldType: mapQuestionTypeToFieldType(q.field_type || q.question_type),
            criticalAttribute: q.critical_attribute || 'unknown',
            validation: { 
              required: q.required !== false,
              ...(q.validation || {})
            },
            section: 'agent-technical-details',
            order: index + 1,
            businessImpactScore: q.business_impact_score || 0.7,
            options: q.options || (q.field_type === 'select' ? getDefaultOptions(q.field_type) : undefined),
            helpText: q.help_text || q.description
          })),
          order: 2,
          requiredFieldsCount: technicalQuestions.filter((q: any) => q.required !== false).length,
          completionWeight: 0.6
        });
      }
      
      const totalFields = questions.length;
      const requiredFields = questions.filter((q: any) => q.required !== false).length;
      
      return {
        formId: questionnaire.id || 'agent-form-001',
        applicationId: applicationId || 'app-new',
        sections,
        totalFields,
        requiredFields,
        estimatedCompletionTime: questionnaire.estimated_completion_time || Math.max(20, totalFields * 2),
        confidenceImpactScore: questionnaire.confidence_impact_score || 0.85
      };
      
    } catch (error) {
      console.error('Error converting questionnaire to form data:', error);
      return createFallbackFormData(applicationId);
    }
  };

  // Helper function to map CrewAI question types to form field types
  const mapQuestionTypeToFieldType = (questionType: string): string => {
    const mappings: Record<string, string> = {
      'text': 'text',
      'textarea': 'textarea',
      'select': 'select',
      'multiselect': 'multiselect',
      'checkbox': 'checkbox',
      'radio': 'radio',
      'number': 'number',
      'email': 'email',
      'url': 'url',
      'date': 'date',
      'file': 'file',
      'application_name': 'text',
      'application_type': 'select',
      'technology_stack': 'multiselect',
      'database': 'select'
    };
    return mappings[questionType] || 'text';
  };

  // Helper function to get default options for certain field types
  const getDefaultOptions = (fieldType: string) => {
    const defaultOptions: Record<string, any[]> = {
      'application_type': [
        { value: 'web', label: 'Web Application' },
        { value: 'desktop', label: 'Desktop Application' },
        { value: 'mobile', label: 'Mobile Application' },
        { value: 'service', label: 'Web Service/API' },
        { value: 'batch', label: 'Batch Processing' }
      ],
      'database': [
        { value: 'mysql', label: 'MySQL' },
        { value: 'postgresql', label: 'PostgreSQL' },
        { value: 'oracle', label: 'Oracle' },
        { value: 'sqlserver', label: 'SQL Server' },
        { value: 'mongodb', label: 'MongoDB' }
      ]
    };
    return defaultOptions[fieldType] || [];
  };

  // Fallback form data if CrewAI agents are not available
  const createFallbackFormData = (applicationId: string | null): AdaptiveFormData => {
    return {
      formId: 'fallback-form-001',
      applicationId: applicationId || 'app-new',
      sections: [
        {
          id: 'basic-info',
          title: 'Basic Information',
          description: 'Core application details (fallback form)',
          fields: [
            {
              id: 'app-name',
              label: 'Application Name',
              fieldType: 'text',
              criticalAttribute: 'name',
              validation: { required: true, minLength: 2 },
              section: 'basic-info',
              order: 1,
              businessImpactScore: 0.9
            },
            {
              id: 'app-type',
              label: 'Application Type',
              fieldType: 'select',
              criticalAttribute: 'type',
              options: getDefaultOptions('application_type'),
              validation: { required: true },
              section: 'basic-info',
              order: 2,
              businessImpactScore: 0.8
            }
          ],
          order: 1,
          requiredFieldsCount: 2,
          completionWeight: 0.5
        }
      ],
      totalFields: 2,
      requiredFields: 2,
      estimatedCompletionTime: 10,
      confidenceImpactScore: 0.6
    };
  };

  // Mock progress milestones
  const progressMilestones: ProgressMilestone[] = [
    {
      id: 'form-start',
      title: 'Form Started',
      description: 'Begin adaptive data collection',
      achieved: true,
      achievedAt: new Date().toISOString(),
      weight: 0.1,
      required: true
    },
    {
      id: 'basic-complete',
      title: 'Basic Information',
      description: 'Complete core application details',
      achieved: false,
      weight: 0.3,
      required: true
    },
    {
      id: 'technical-complete',
      title: 'Technical Details',
      description: 'Complete technical architecture information',
      achieved: false,
      weight: 0.4,
      required: true
    },
    {
      id: 'validation-passed',
      title: 'Validation Passed',
      description: 'All validation checks completed successfully',
      achieved: false,
      weight: 0.2,
      required: true
    }
  ];

  const handleFieldChange = (fieldId: string, value: any) => {
    setFormValues(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  const handleValidationChange = (newValidation: FormValidationResult) => {
    setValidation(newValidation);
  };

  const handleSave = async () => {
    if (!formData) return;

    setIsSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: 'Progress Saved',
        description: 'Your form progress has been saved successfully.'
      });
    } catch (error) {
      toast({
        title: 'Save Failed',
        description: 'Failed to save progress. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = async (data: CollectionFormData) => {
    if (!validation?.isValid) {
      toast({
        title: 'Validation Required',
        description: 'Please complete all required fields and resolve validation errors.',
        variant: 'destructive'
      });
      return;
    }

    if (!flowId || questionnaires.length === 0) {
      toast({
        title: 'Collection Flow Not Ready',
        description: 'CrewAI collection flow is not properly initialized. Please refresh and try again.',
        variant: 'destructive'
      });
      return;
    }

    setIsLoading(true);
    try {
      // Submit responses to the CrewAI-generated questionnaire
      const questionnaireId = questionnaires[0].id;
      const submissionData = {
        responses: data,
        form_metadata: {
          form_id: formData?.formId,
          application_id: applicationId,
          completion_percentage: validation?.completionPercentage,
          confidence_score: validation?.overallConfidenceScore,
          submitted_at: new Date().toISOString()
        },
        validation_results: validation
      };

      console.log(`🚀 Submitting adaptive form responses to CrewAI questionnaire ${questionnaireId}`);
      
      // Submit to CrewAI questionnaire endpoint
      const submissionResponse = await collectionFlowApi.submitQuestionnaireResponse(
        flowId,
        questionnaireId,
        submissionData
      );
      
      toast({
        title: 'Adaptive Form Submitted Successfully',
        description: `CrewAI agents are processing your responses and will continue the collection flow.`
      });

      console.log('✅ Form submitted successfully, CrewAI agents will continue processing');

      // Navigate to the collection flow management page to monitor progress
      navigate(`/collection/progress/${flowId}`);
      
    } catch (error: any) {
      console.error('❌ Adaptive form submission failed:', error);
      
      // More detailed error information
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
      setIsLoading(false);
    }
  };

  // Show loading state while checking for incomplete flows
  if (checkingFlows) {
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
            <div className="flex items-center justify-center min-h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Checking for existing collection flows...</p>
                <p className="text-xs text-muted-foreground mt-2">Validating workflow state</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show blocker if there are incomplete flows
  if (hasIncompleteFlows) {
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
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => navigate('/collection')}
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Collection
                  </Button>
                  <div>
                    <h1 className="text-2xl font-bold">Adaptive Data Collection</h1>
                    <p className="text-muted-foreground">
                      Collection workflow blocked - manage existing flows
                    </p>
                  </div>
                </div>
              </div>

              {/* Collection Upload Blocker */}
              <CollectionUploadBlocker
                incompleteFlows={incompleteFlows}
                onContinueFlow={handleContinueFlow}
                onDeleteFlow={handleDeleteFlow}
                onViewDetails={handleViewFlowDetails}
                onManageFlows={handleManageFlows}
                onRefresh={refetchFlows}
                isLoading={false}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!formData) {
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
            <div className="flex items-center justify-center min-h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">CrewAI agents are generating adaptive questionnaire...</p>
                <p className="text-xs text-muted-foreground mt-2">Analyzing gaps and creating personalized form fields</p>
              </div>
            </div>
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
          <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate('/collection')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Collection
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Adaptive Data Collection</h1>
            <p className="text-muted-foreground">
              {applicationId ? `Collecting data for application ${applicationId}` : 'New application data collection'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={handleSave}
            disabled={isSaving}
          >
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Progress'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Progress Tracker Sidebar */}
        <div className="lg:col-span-1">
          <ProgressTracker
            formId={formData.formId}
            totalSections={formData.sections.length}
            completedSections={0}
            overallCompletion={validation?.completionPercentage || 0}
            confidenceScore={validation?.overallConfidenceScore || 0}
            milestones={progressMilestones}
            timeSpent={0}
            estimatedTimeRemaining={formData.estimatedCompletionTime}
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Validation Display */}
          {validation && validation.fieldResults && Object.keys(validation.fieldResults).length > 0 && (
            <ValidationDisplay 
              validation={validation}
              showWarnings={true}
              onErrorClick={(fieldId) => {
                // Focus the field with error
                const element = document.getElementById(fieldId);
                element?.focus();
              }}
            />
          )}

          {/* Form Tabs */}
          <Tabs defaultValue="single" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="single">Single Application</TabsTrigger>
              <TabsTrigger value="bulk">Bulk Mode</TabsTrigger>
            </TabsList>
            
            <TabsContent value="single" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Application Data Collection</CardTitle>
                </CardHeader>
                <CardContent>
                  <AdaptiveForm
                    formData={formData}
                    initialValues={formValues}
                    onFieldChange={handleFieldChange}
                    onSubmit={handleSubmit}
                    onValidationChange={handleValidationChange}
                    bulkMode={false}
                    className="space-y-6"
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="bulk" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Bulk Application Collection</CardTitle>
                </CardHeader>
                <CardContent>
                  <BulkDataGrid
                    applications={[]}
                    fields={formData.sections.flatMap(section => section.fields)}
                    onDataChange={(appId, fieldId, value) => {
                      console.log('Bulk data change:', { appId, fieldId, value });
                    }}
                    onBulkUpload={async (file) => {
                      toast({
                        title: 'Bulk Upload Started',
                        description: `Processing ${file.name}...`
                      });
                    }}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Submit Actions */}
          <div className="flex justify-end space-x-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/collection')}
            >
              Cancel
            </Button>
            <Button 
              onClick={() => handleSubmit(formValues)}
              disabled={isLoading || !validation?.isValid}
            >
              <Send className="h-4 w-4 mr-2" />
              {isLoading ? 'Submitting...' : 'Submit Collection Data'}
            </Button>
          </div>
        </div>
      </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdaptiveForms;