/**
 * Adaptive Form Container Component
 *
 * Container component that handles form rendering and progress tracking.
 * Extracted from AdaptiveForms.tsx to create a more focused, reusable component.
 */

import React from 'react';
import { Save, Send, ArrowLeft } from 'lucide-react';

// Import collection components
import { AdaptiveForm } from '@/components/collection/AdaptiveForm';
import { ProgressTracker } from '@/components/collection/ProgressTracker';
import { ValidationDisplay } from '@/components/collection/ValidationDisplay';
import { BulkDataGrid } from '@/components/collection/BulkDataGrid';
import { AssetSelectionForm } from '@/components/collection/AssetSelectionForm';

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
  completionStatus?: "pending" | "ready" | "fallback" | "failed" | null;
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
  completionStatus = null,
  onFieldChange,
  onValidationChange,
  onSave,
  onSubmit,
  onCancel,
  className = ''
}) => {
  // CC: Component initialization effect - check if save function is available
  React.useEffect(() => {
    // AdaptiveFormContainer initialized with save functionality
    if (typeof onSave === 'function') {
      // Save functionality is available
    }
  }, [onSave]);
  // Defensive checks
  if (!formData) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-500">No form data available. Please try refreshing the page.</p>
      </div>
    );
  }

  // Check if this is an asset selection bootstrap questionnaire
  // This happens when a collection flow has no assets selected yet
  // The conversion function sets formId to 'bootstrap_asset_selection'
  if (formData.formId === 'bootstrap_asset_selection') {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <AssetSelectionForm
          formData={formData}
          formValues={formValues}
          onFieldChange={onFieldChange}
          onSubmit={onSubmit}
          isSubmitting={isSubmitting}
          className="space-y-6"
        />
      </div>
    );
  }

  // If no sections are available, this likely means no assets have been selected
  // OR questionnaire generation timed out/failed
  // Show asset selection form to allow user to proceed
  // BUT: Don't show this if questionnaire is still being generated (pending status)
  if ((!formData.sections || formData.sections.length === 0) && completionStatus !== 'pending') {
    // Create a bootstrap asset selection form
    const assetSelectionFormData = {
      formId: 'bootstrap_asset_selection',
      title: 'Asset Selection Required',
      description: 'Please select assets to continue with data collection',
      sections: [{
        id: 'asset_selection',
        title: 'Select Applications',
        description: 'Choose which applications to collect data for',
        fields: [{
          id: 'selected_applications',
          name: 'Applications',
          type: 'multi_select',
          required: true,
          options: [],
          helpText: 'Select one or more applications for data collection'
        }]
      }],
      estimatedCompletionTime: 5
    };

    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Asset Selection Required</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-gray-600">
                No assets have been selected for this collection flow.
                Please select assets to continue with data collection.
              </p>
              <AssetSelectionForm
                formData={assetSelectionFormData}
                formValues={formValues}
                onFieldChange={onFieldChange}
                onSubmit={onSubmit}
                isSubmitting={isSubmitting}
                className="space-y-6"
              />
              <div className="text-sm text-gray-500 mt-4">
                Note: If you were expecting questionnaires here, they may still be generating.
                You can refresh the page in a few moments to check again.
              </div>
            </div>
          </CardContent>
        </Card>
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
            <TabsTrigger value="single">Single Asset</TabsTrigger>
            <TabsTrigger value="bulk">Bulk Mode</TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Asset Data Collection</CardTitle>
              </CardHeader>
              <CardContent>
                <AdaptiveForm
                  formData={formData}
                  initialValues={formValues}
                  onFieldChange={onFieldChange}
                  onSubmit={handleFormSubmit}
                  onSave={onSave}
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
                <CardTitle>Bulk Asset Collection</CardTitle>
              </CardHeader>
              <CardContent>
                <BulkDataGrid
                  applications={[]}
                  fields={formData.sections.flatMap(section => section.fields)}
                  onDataChange={(appId, fieldId, value) => {
                    // Handle bulk data changes
                  }}
                  onBulkUpload={async (file) => {
                    // Handle bulk file upload
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
              type="button"
              variant="outline"
              onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.preventDefault();
                e.stopPropagation();

                if (typeof onSave === 'function') {
                  onSave();
                }
              }}
              disabled={isSaving}
              className="border-2 border-blue-500 bg-blue-50 hover:bg-blue-100"
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
