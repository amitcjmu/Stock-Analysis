/**
 * Adaptive Form Container Component
 *
 * Container component that handles form rendering and progress tracking.
 * Extracted from AdaptiveForms.tsx to create a more focused, reusable component.
 */

import React from 'react';
import { Save, Send } from 'lucide-react';

// Import collection components
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

export interface AdaptiveFormContainerProps {
  formData: AdaptiveFormData;
  formValues: CollectionFormData;
  validation: FormValidationResult | null;
  milestones: ProgressMilestone[];
  isSaving?: boolean;
  isSubmitting?: boolean;
  onFieldChange: (fieldId: string, value: unknown) => void;
  onValidationChange: (validation: FormValidationResult) => void;
  onSave: () => void;
  onSubmit: (data: CollectionFormData) => void;
  onCancel: () => void;
  className?: string;
}

export const AdaptiveFormContainer: React.FC<AdaptiveFormContainerProps> = ({
  formData,
  formValues,
  validation,
  milestones,
  isSaving = false,
  isSubmitting = false,
  onFieldChange,
  onValidationChange,
  onSave,
  onSubmit,
  onCancel,
  className = ''
}) => {
  // Defensive checks
  if (!formData) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-500">No form data available. Please try refreshing the page.</p>
      </div>
    );
  }

  if (!formData.sections || formData.sections.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-500">Form sections are not available. Please contact support if this issue persists.</p>
      </div>
    );
  }

  const handleFormSubmit = (): void => {
    if (onSubmit && formValues) {
      onSubmit(formValues);
    }
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-4 gap-6 ${className}`}>
      {/* Progress Tracker Sidebar */}
      <div className="lg:col-span-1">
        <ProgressTracker
          formId={formData.formId}
          totalSections={formData.sections.length}
          completedSections={0}
          overallCompletion={validation?.completionPercentage || 0}
          confidenceScore={validation?.overallConfidenceScore || 0}
          milestones={milestones}
          timeSpent={0}
          estimatedTimeRemaining={formData.estimatedCompletionTime}
        />
      </div>

      {/* Main Content */}
      <div className="lg:col-span-3 space-y-6">
        {/* Validation Display is now handled inside AdaptiveForm component */}

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
                  onFieldChange={onFieldChange}
                  onSubmit={handleFormSubmit}
                  onValidationChange={onValidationChange}
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
                    console.log('Bulk upload:', file.name);
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save and Cancel Actions */}
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={onSave}
              disabled={isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Progress'}
            </Button>
          </div>

          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={onCancel}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdaptiveFormContainer;
