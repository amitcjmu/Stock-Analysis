/**
 * Planning Flow Initialization Wizard
 *
 * Multi-step wizard for initializing Planning Flow through MFO.
 * All field names use snake_case per CLAUDE.md field naming convention.
 *
 * Flow:
 * 1. Step 1: Select applications (manual UUID entry for MVP)
 * 2. Step 2: Configure planning settings
 * 3. Step 3: Review and initialize
 *
 * On success, redirects to /plan/wave-planning with planning_flow_id and engagement_id
 *
 * CC Generated Component
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { planningFlowApi } from '@/lib/api/planningFlowService';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface PlanningInitializationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  engagement_id: number;
}

interface WizardFormData {
  selected_application_ids: string[];
  max_apps_per_wave: number;
  wave_duration_limit_days: number;
  contingency_percentage: number;
}

// =============================================================================
// Component
// =============================================================================

export const PlanningInitializationWizard: React.FC<PlanningInitializationWizardProps> = ({
  open,
  onOpenChange,
  engagement_id,
}) => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Wizard state
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  const [isLoading, setIsLoading] = useState(false);

  // Form data using snake_case per CLAUDE.md
  const [formData, setFormData] = useState<WizardFormData>({
    selected_application_ids: [],
    max_apps_per_wave: 50,
    wave_duration_limit_days: 90,
    contingency_percentage: 20,
  });

  // Application UUIDs input (comma-separated)
  const [applicationIdsInput, setApplicationIdsInput] = useState('');

  // =============================================================================
  // Handlers
  // =============================================================================

  /**
   * Reset wizard state when dialog closes
   */
  const handleClose = () => {
    if (!isLoading) {
      setCurrentStep(1);
      setFormData({
        selected_application_ids: [],
        max_apps_per_wave: 50,
        wave_duration_limit_days: 90,
        contingency_percentage: 20,
      });
      setApplicationIdsInput('');
      onOpenChange(false);
    }
  };

  /**
   * Navigate to next step with validation
   */
  const handleNext = () => {
    if (currentStep === 1) {
      // Validate applications selected
      if (formData.selected_application_ids.length === 0) {
        toast({
          title: 'Validation Error',
          description: 'Please enter at least one application UUID',
          variant: 'destructive',
        });
        return;
      }
    }

    if (currentStep < 3) {
      setCurrentStep((prev) => (prev + 1) as 1 | 2 | 3);
    }
  };

  /**
   * Navigate to previous step
   */
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as 1 | 2 | 3);
    }
  };

  /**
   * Parse comma-separated UUIDs and update form data
   */
  const handleApplicationIdsChange = (value: string) => {
    setApplicationIdsInput(value);

    // Parse comma-separated UUIDs and trim whitespace
    const uuids = value
      .split(',')
      .map((uuid) => uuid.trim())
      .filter((uuid) => uuid.length > 0);

    setFormData((prev) => ({
      ...prev,
      selected_application_ids: uuids,
    }));
  };

  /**
   * Initialize planning flow and redirect on success
   */
  const handleInitialize = async () => {
    try {
      setIsLoading(true);

      // CRITICAL: Use request body with snake_case fields per CLAUDE.md
      const response = await planningFlowApi.initializePlanningFlow({
        engagement_id,
        selected_application_ids: formData.selected_application_ids,
        planning_config: {
          max_apps_per_wave: formData.max_apps_per_wave,
          wave_duration_limit_days: formData.wave_duration_limit_days,
          contingency_percentage: formData.contingency_percentage,
        },
      });

      // Show success toast
      toast({
        title: 'Planning Flow Initialized',
        description: `Successfully created planning flow ${response.planning_flow_id}`,
        variant: 'default',
      });

      // Close dialog
      handleClose();

      // Redirect to wave planning page with planning_flow_id and engagement_id
      navigate(
        `/plan/wave-planning?planning_flow_id=${response.planning_flow_id}&engagement_id=${engagement_id}`
      );
    } catch (error) {
      console.error('Failed to initialize planning flow:', error);

      toast({
        title: 'Initialization Failed',
        description: error instanceof Error ? error.message : 'Failed to initialize planning flow',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // =============================================================================
  // Step Content Renderers
  // =============================================================================

  /**
   * Step 1: Application Selection
   */
  const renderStep1 = () => (
    <div className="space-y-4">
      <div>
        <Label htmlFor="application_ids">Application UUIDs</Label>
        <p className="text-sm text-gray-500 mb-2">
          Enter application UUIDs separated by commas (e.g., uuid1, uuid2, uuid3)
        </p>
        <Input
          id="application_ids"
          placeholder="uuid1, uuid2, uuid3"
          value={applicationIdsInput}
          onChange={(e) => handleApplicationIdsChange(e.target.value)}
          className="font-mono text-sm"
        />
        {formData.selected_application_ids.length > 0 && (
          <p className="text-sm text-green-600 mt-2 flex items-center">
            <CheckCircle className="h-4 w-4 mr-1" />
            {formData.selected_application_ids.length} application(s) selected
          </p>
        )}
      </div>
    </div>
  );

  /**
   * Step 2: Planning Configuration
   */
  const renderStep2 = () => (
    <div className="space-y-4">
      <div>
        <Label htmlFor="max_apps_per_wave">Max Applications per Wave</Label>
        <p className="text-sm text-gray-500 mb-2">
          Maximum number of applications to include in each wave
        </p>
        <Input
          id="max_apps_per_wave"
          type="number"
          min={1}
          value={formData.max_apps_per_wave}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              max_apps_per_wave: parseInt(e.target.value) || 50,
            }))
          }
        />
      </div>

      <div>
        <Label htmlFor="wave_duration_limit_days">Wave Duration Limit (Days)</Label>
        <p className="text-sm text-gray-500 mb-2">
          Maximum duration for each migration wave
        </p>
        <Input
          id="wave_duration_limit_days"
          type="number"
          min={1}
          value={formData.wave_duration_limit_days}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              wave_duration_limit_days: parseInt(e.target.value) || 90,
            }))
          }
        />
      </div>

      <div>
        <Label htmlFor="contingency_percentage">Contingency Percentage</Label>
        <p className="text-sm text-gray-500 mb-2">
          Buffer percentage for risk and delays (e.g., 20 for 20%)
        </p>
        <Input
          id="contingency_percentage"
          type="number"
          min={0}
          max={100}
          value={formData.contingency_percentage}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              contingency_percentage: parseInt(e.target.value) || 20,
            }))
          }
        />
      </div>
    </div>
  );

  /**
   * Step 3: Review and Confirmation
   */
  const renderStep3 = () => (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3">Review Planning Configuration</h3>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Applications:</span>
            <span className="font-medium">{formData.selected_application_ids.length}</span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-600">Max Apps per Wave:</span>
            <span className="font-medium">{formData.max_apps_per_wave}</span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-600">Wave Duration Limit:</span>
            <span className="font-medium">{formData.wave_duration_limit_days} days</span>
          </div>

          <div className="flex justify-between">
            <span className="text-gray-600">Contingency Buffer:</span>
            <span className="font-medium">{formData.contingency_percentage}%</span>
          </div>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Ready to Initialize</p>
            <p>
              This will create a new planning flow and begin AI-powered wave planning analysis.
              You can modify wave assignments later.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  // =============================================================================
  // Render
  // =============================================================================

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl" hideCloseButton={isLoading}>
        <DialogHeader>
          <DialogTitle>Initialize Planning Flow</DialogTitle>
          <DialogDescription>
            Step {currentStep} of 3: {
              currentStep === 1 ? 'Select Applications' :
              currentStep === 2 ? 'Configure Planning' :
              'Review and Initialize'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Step Content */}
        <div className="py-4">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </div>

        {/* Step Progress Indicator */}
        <div className="flex justify-center space-x-2 mb-4">
          {[1, 2, 3].map((step) => (
            <div
              key={step}
              className={`h-2 w-12 rounded-full transition-colors ${
                step === currentStep
                  ? 'bg-blue-600'
                  : step < currentStep
                  ? 'bg-green-500'
                  : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Footer Actions */}
        <DialogFooter>
          <div className="flex justify-between w-full">
            <div>
              {currentStep > 1 && (
                <Button
                  variant="outline"
                  onClick={handleBack}
                  disabled={isLoading}
                >
                  Back
                </Button>
              )}
            </div>

            <div className="flex space-x-2">
              <Button
                variant="outline"
                onClick={handleClose}
                disabled={isLoading}
              >
                Cancel
              </Button>

              {currentStep < 3 ? (
                <Button onClick={handleNext} disabled={isLoading}>
                  Next
                </Button>
              ) : (
                <Button onClick={handleInitialize} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Initializing...
                    </>
                  ) : (
                    'Initialize Planning Flow'
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
