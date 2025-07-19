import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save, Send } from 'lucide-react';

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

  // State management
  const [formData, setFormData] = useState<AdaptiveFormData | null>(null);
  const [formValues, setFormValues] = useState<CollectionFormData>({});
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [bulkMode, setBulkMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Get application ID from URL params if provided
  const applicationId = searchParams.get('applicationId');

  // Mock data for demonstration - in real implementation this would come from API
  useEffect(() => {
    const mockFormData: AdaptiveFormData = {
      formId: 'adaptive-form-001',
      applicationId: applicationId || 'app-new',
      sections: [
        {
          id: 'basic-info',
          title: 'Basic Information',
          description: 'Core application details',
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
              options: [
                { value: 'web', label: 'Web Application' },
                { value: 'desktop', label: 'Desktop Application' },
                { value: 'mobile', label: 'Mobile Application' },
                { value: 'service', label: 'Web Service/API' },
                { value: 'batch', label: 'Batch Processing' }
              ],
              validation: { required: true },
              section: 'basic-info',
              order: 2,
              businessImpactScore: 0.8
            }
          ],
          order: 1,
          requiredFieldsCount: 2,
          completionWeight: 0.3
        },
        {
          id: 'technical-details',
          title: 'Technical Details',
          description: 'Technical architecture and dependencies',
          fields: [
            {
              id: 'tech-stack',
              label: 'Technology Stack',
              fieldType: 'multiselect',
              criticalAttribute: 'technologies',
              options: [
                { value: 'java', label: 'Java' },
                { value: 'dotnet', label: '.NET' },
                { value: 'python', label: 'Python' },
                { value: 'nodejs', label: 'Node.js' },
                { value: 'php', label: 'PHP' }
              ],
              validation: { required: true },
              section: 'technical-details',
              order: 1,
              businessImpactScore: 0.85
            },
            {
              id: 'database-type',
              label: 'Primary Database',
              fieldType: 'select',
              criticalAttribute: 'database',
              options: [
                { value: 'mysql', label: 'MySQL' },
                { value: 'postgresql', label: 'PostgreSQL' },
                { value: 'oracle', label: 'Oracle' },
                { value: 'sqlserver', label: 'SQL Server' },
                { value: 'mongodb', label: 'MongoDB' }
              ],
              section: 'technical-details',
              order: 2,
              businessImpactScore: 0.7
            }
          ],
          order: 2,
          requiredFieldsCount: 1,
          completionWeight: 0.4
        }
      ],
      totalFields: 4,
      requiredFields: 3,
      estimatedCompletionTime: 20,
      confidenceImpactScore: 0.85
    };

    setFormData(mockFormData);
  }, [applicationId]);

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

    setIsLoading(true);
    try {
      // Simulate API submission
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: 'Data Submitted Successfully',
        description: 'Your application data has been collected and processed.'
      });

      // Navigate to the next step or back to collection index
      navigate('/collection?success=adaptive-form');
    } catch (error) {
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit data. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!formData) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading adaptive form...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
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
  );
};

export default AdaptiveForms;