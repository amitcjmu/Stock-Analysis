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
  // CC: Debugging - Log props only when onSave changes to avoid infinite re-renders
  React.useEffect(() => {
    console.log('🔍 AdaptiveFormContainer initialized with save handler:', typeof onSave === 'function');
  }, [typeof onSave]); // Only log when onSave type changes
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
        {/* CC: Debug Test Button to verify event handling */}
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800 mb-2">Debug: Click to test if buttons work</p>
          <button
            type="button"
            onClick={() => {
              console.log('🟡 TEST: Plain HTML button clicked!');
              alert('Plain HTML button works!');
            }}
            className="px-4 py-2 bg-yellow-500 text-white rounded mr-2"
          >
            Test HTML Button
          </button>
          <Button
            type="button"
            onClick={() => {
              console.log('🟡 TEST: UI Button component clicked!');
              alert('UI Button component works!');
            }}
            variant="default"
          >
            Test UI Button
          </Button>
          <Button
            type="button"
            onClick={() => {
              console.log('🔵 TEST: Direct onSave call!');
              if (typeof onSave === 'function') {
                console.log('🔵 Calling onSave directly from test button');
                onSave();
              } else {
                console.log('🔴 onSave is not a function in test button');
              }
            }}
            variant="destructive"
          >
            Test Direct Save Call
          </Button>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                console.log('🔴 Save Progress button clicked - Event fired!');
                console.log('🔍 Button event:', e);
                console.log('🔍 onSave type:', typeof onSave);
                console.log('🔍 onSave value:', onSave);

                // CC: Prevent any form submission or event bubbling
                e.preventDefault();
                e.stopPropagation();

                if (typeof onSave === 'function') {
                  console.log('✅ Calling onSave function NOW...');
                  try {
                    // Call onSave directly
                    const result = onSave();
                    console.log('✅ onSave called successfully, result:', result);
                  } catch (error) {
                    console.error('❌ Error calling onSave:', error);
                  }
                } else {
                  console.error('❌ onSave prop is not a function!', {
                    onSave,
                    typeOf: typeof onSave,
                    isNull: onSave === null,
                    isUndefined: onSave === undefined
                  });
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
