import React from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { FileSpreadsheet } from 'lucide-react'
import { ArrowLeft, Download, Upload, AlertCircle, CheckCircle } from 'lucide-react'

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Import existing collection components
import { BulkDataGrid } from '@/components/collection/BulkDataGrid';
import { ValidationDisplay } from '@/components/collection/ValidationDisplay';
import { ProgressTracker } from '@/components/collection/ProgressTracker';

// Import types
import type { 
  ApplicationSummary, 
  FormField, 
  BulkUploadResult,
  FormValidationResult,
  ProgressMilestone 
} from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';

/**
 * Bulk Upload collection page
 * Handles large-scale data collection via file uploads and bulk processing
 */
const BulkUpload: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State management
  const [uploadResults, setUploadResults] = useState<BulkUploadResult[]>([]);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Mock field definitions for bulk collection
  const bulkFields: FormField[] = [
    {
      id: 'name',
      label: 'Application Name',
      fieldType: 'text',
      criticalAttribute: 'name',
      validation: { required: true },
      section: 'basic',
      order: 1,
      businessImpactScore: 0.9
    },
    {
      id: 'type',
      label: 'Application Type',
      fieldType: 'select',
      criticalAttribute: 'type',
      options: [
        { value: 'web', label: 'Web Application' },
        { value: 'desktop', label: 'Desktop Application' },
        { value: 'mobile', label: 'Mobile Application' },
        { value: 'service', label: 'Web Service/API' }
      ],
      validation: { required: true },
      section: 'basic',
      order: 2,
      businessImpactScore: 0.8
    },
    {
      id: 'technology',
      label: 'Primary Technology',
      fieldType: 'select',
      criticalAttribute: 'technology',
      options: [
        { value: 'java', label: 'Java' },
        { value: 'dotnet', label: '.NET' },
        { value: 'python', label: 'Python' },
        { value: 'nodejs', label: 'Node.js' }
      ],
      section: 'technical',
      order: 1,
      businessImpactScore: 0.75
    },
    {
      id: 'criticality',
      label: 'Business Criticality',
      fieldType: 'select',
      criticalAttribute: 'criticality',
      options: [
        { value: 'critical', label: 'Mission Critical' },
        { value: 'important', label: 'Important' },
        { value: 'moderate', label: 'Moderate' },
        { value: 'low', label: 'Low Impact' }
      ],
      section: 'business',
      order: 1,
      businessImpactScore: 0.85
    }
  ];

  // Progress milestones for bulk upload
  const progressMilestones: ProgressMilestone[] = [
    {
      id: 'upload-start',
      title: 'Upload Started',
      description: 'File upload initiated',
      achieved: uploadResults.length > 0,
      achievedAt: uploadResults.length > 0 ? new Date().toISOString() : undefined,
      weight: 0.2,
      required: true
    },
    {
      id: 'data-parsed',
      title: 'Data Parsed',
      description: 'File data successfully parsed',
      achieved: applications.length > 0,
      weight: 0.3,
      required: true
    },
    {
      id: 'validation-complete',
      title: 'Validation Complete',
      description: 'Data validation and quality checks completed',
      achieved: validation !== null,
      weight: 0.3,
      required: true
    },
    {
      id: 'processing-complete',
      title: 'Processing Complete',
      description: 'All data processed and ready for next phase',
      achieved: false,
      weight: 0.2,
      required: true
    }
  ];

  const handleBulkUpload = async (file: File) => {
    setIsProcessing(true);
    setUploadProgress(0);

    try {
      // Simulate file processing with progress updates
      const totalSteps = 100;
      for (let i = 0; i <= totalSteps; i += 10) {
        setUploadProgress(i);
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Mock processing results
      const mockResult: BulkUploadResult = {
        uploadId: `upload-${Date.now()}`,
        status: 'completed',
        totalRows: 150,
        successfulRows: 142,
        failedRows: 8,
        validationIssues: [
          {
            fieldId: 'name',
            fieldLabel: 'Application Name',
            errorCode: 'REQUIRED_FIELD_MISSING',
            errorMessage: 'Application name is required',
            severity: 'error'
          },
          {
            fieldId: 'type',
            fieldLabel: 'Application Type',
            errorCode: 'INVALID_VALUE',
            errorMessage: 'Invalid application type specified',
            severity: 'warning'
          }
        ],
        processingTime: 45000,
        dataQualityScore: 94.7
      };

      // Mock applications data
      const mockApplications: ApplicationSummary[] = Array.from({ length: 142 }, (_, i) => ({
        id: `app-${i + 1}`,
        name: `Application ${i + 1}`,
        technology: ['Java', '.NET', 'Python', 'Node.js'][i % 4],
        architecturePattern: ['Monolithic', 'Microservices', 'SOA'][i % 3],
        businessCriticality: ['Critical', 'Important', 'Moderate', 'Low'][i % 4]
      }));

      setUploadResults([mockResult]);
      setApplications(mockApplications);

      toast({
        title: 'Upload Successful',
        description: `Processed ${mockResult.successfulRows} of ${mockResult.totalRows} applications successfully.`
      });

    } catch (error) {
      toast({
        title: 'Upload Failed',
        description: 'Failed to process the uploaded file. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  };

  const handleDataChange = (applicationId: string, fieldId: string, value: unknown) => {
    setApplications(prev => prev.map(app => 
      app.id === applicationId 
        ? { ...app, [fieldId]: value }
        : app
    ));
  };

  const handleDownloadTemplate = () => {
    // Create a mock CSV template
    const headers = bulkFields.map(field => field.label).join(',');
    const sampleRow = bulkFields.map(field => {
      switch (field.fieldType) {
        case 'select':
          return field.options?.[0]?.value || '';
        case 'text':
          return `Sample ${field.label}`;
        default:
          return '';
      }
    }).join(',');

    const csvContent = `${headers}\n${sampleRow}`;
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'bulk-collection-template.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const completedMilestones = progressMilestones.filter(m => m.achieved).length;
  const overallProgress = (completedMilestones / progressMilestones.length) * 100;

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
            <h1 className="text-2xl font-bold">Bulk Data Upload</h1>
            <p className="text-muted-foreground">
              Upload and process multiple applications efficiently
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={handleDownloadTemplate}
          >
            <Download className="h-4 w-4 mr-2" />
            Download Template
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Progress Tracker Sidebar */}
        <div className="lg:col-span-1">
          <ProgressTracker
            formId="bulk-upload"
            totalSections={4}
            completedSections={completedMilestones}
            overallCompletion={overallProgress}
            confidenceScore={uploadResults[0]?.dataQualityScore || 0}
            milestones={progressMilestones}
            timeSpent={uploadResults[0]?.processingTime || 0}
            estimatedTimeRemaining={isProcessing ? 60000 : 0}
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Upload Status */}
          {uploadResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Upload Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {uploadResults.map((result, index) => (
                    <React.Fragment key={result.uploadId}>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">{result.successfulRows}</p>
                        <p className="text-sm text-muted-foreground">Successful</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-600">{result.failedRows}</p>
                        <p className="text-sm text-muted-foreground">Failed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold">{result.totalRows}</p>
                        <p className="text-sm text-muted-foreground">Total Rows</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">{result.dataQualityScore}%</p>
                        <p className="text-sm text-muted-foreground">Quality Score</p>
                      </div>
                    </React.Fragment>
                  ))}
                </div>
                
                {uploadResults[0]?.validationIssues.length > 0 && (
                  <Alert className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {uploadResults[0].validationIssues.length} validation issues found. 
                      Review the data grid below to address these issues.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {/* Processing Progress */}
          {isProcessing && (
            <Card>
              <CardHeader>
                <CardTitle>Processing Upload</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Processing...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Bulk Data Grid */}
          <Card>
            <CardHeader>
              <CardTitle>Bulk Application Data</CardTitle>
            </CardHeader>
            <CardContent>
              <BulkDataGrid
                applications={applications}
                fields={bulkFields}
                onDataChange={handleDataChange}
                onBulkUpload={handleBulkUpload}
                templateOptions={[
                  {
                    id: 'standard',
                    name: 'Standard Application Template',
                    description: 'Basic application information template',
                    applicableTypes: ['web', 'desktop', 'mobile'],
                    fieldCount: bulkFields.length,
                    effectivenessScore: 85
                  },
                  {
                    id: 'detailed',
                    name: 'Detailed Technical Template',
                    description: 'Comprehensive technical assessment template',
                    applicableTypes: ['web', 'service'],
                    fieldCount: bulkFields.length + 5,
                    effectivenessScore: 95
                  }
                ]}
              />
            </CardContent>
          </Card>

          {/* Validation Results */}
          {validation && (
            <ValidationDisplay 
              validation={validation}
              showWarnings={true}
              onErrorClick={(fieldId) => {
                console.log('Navigate to field:', fieldId);
              }}
            />
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/collection')}
            >
              Save and Continue Later
            </Button>
            <Button 
              onClick={() => navigate('/collection/data-integration')}
              disabled={applications.length === 0}
            >
              Proceed to Data Integration
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

export default BulkUpload;