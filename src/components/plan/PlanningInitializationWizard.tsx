/**
 * Planning Flow Initialization Wizard
 *
 * Multi-step wizard for initializing Planning Flow through MFO.
 * All field names use snake_case per CLAUDE.md field naming convention.
 *
 * Flow:
 * 1. Step 1: Select applications from paginated table
 * 2. Step 2: Configure planning settings
 * 3. Step 3: Review and initialize
 *
 * On success, redirects to /plan/waveplanning with planning_flow_id and engagement_id
 *
 * CC Generated Component
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { planningFlowApi } from '@/lib/api/planningFlowService';
import { applicationsApi, type Application } from '@/lib/api/applicationsService';
import { Loader2, CheckCircle, AlertCircle, Search } from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface PlanningInitializationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  engagement_id: number;
  // NEW: Pre-selected applications from Treatment page
  preSelectedApplicationIds?: string[];
  preSelectedApplications?: Application[];
}

interface WizardFormData {
  selected_application_ids: string[];
  selected_applications: Application[]; // Store full application objects for Step 3 display
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
  preSelectedApplicationIds = [],
  preSelectedApplications = [],
}) => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Determine if we should skip Step 1 (applications pre-selected from Treatment page)
  const hasPreSelectedApps = preSelectedApplicationIds.length > 0;

  // Wizard state - Start at Step 2 if apps are pre-selected, otherwise Step 1
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(hasPreSelectedApps ? 2 : 1);
  const [isLoading, setIsLoading] = useState(false);

  // Form data using snake_case per CLAUDE.md
  // Initialize with pre-selected apps if provided
  const [formData, setFormData] = useState<WizardFormData>({
    selected_application_ids: hasPreSelectedApps ? preSelectedApplicationIds : [],
    selected_applications: hasPreSelectedApps ? preSelectedApplications : [],
    max_apps_per_wave: 50,
    wave_duration_limit_days: 90,
    contingency_percentage: 20,
  });

  // Application selection state
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const pageSize = 10;

  // Initialize wizard state when modal opens with pre-selected applications
  React.useEffect(() => {
    if (open && hasPreSelectedApps && preSelectedApplicationIds.length > 0) {
      // Set currentStep to 2 to skip application selection
      setCurrentStep(2);
      // Initialize selectedIds for consistency (though not used when skipping Step 1)
      setSelectedIds(new Set(preSelectedApplicationIds));
      // Ensure formData has the pre-selected apps
      setFormData({
        selected_application_ids: preSelectedApplicationIds,
        selected_applications: preSelectedApplications,
        max_apps_per_wave: 50,
        wave_duration_limit_days: 90,
        contingency_percentage: 20,
      });
    } else if (open && !hasPreSelectedApps) {
      // Reset to Step 1 when opening without pre-selected apps
      setCurrentStep(1);
      setSelectedIds(new Set());
    }
  }, [open, hasPreSelectedApps, preSelectedApplicationIds, preSelectedApplications]);

  // Fetch applications with pagination and search (HTTP polling per CLAUDE.md - NO WebSockets)
  const {
    data: applicationsData,
    isLoading: isLoadingApplications,
    error: applicationsError,
  } = useQuery({
    queryKey: ['applications', currentPage, searchTerm],
    queryFn: () =>
      applicationsApi.getApplications({
        page: currentPage,
        page_size: pageSize,
        search: searchTerm || undefined,
      }),
    enabled: open && currentStep === 1, // Only fetch when dialog is open and on Step 1
    staleTime: 30000, // Cache for 30 seconds
  });

  // =============================================================================
  // Handlers
  // =============================================================================

  /**
   * Reset wizard state when dialog closes
   */
  const handleClose = () => {
    if (!isLoading) {
      // Reset to initial step based on whether apps are pre-selected
      setCurrentStep(hasPreSelectedApps ? 2 : 1);

      // Reset form data, maintaining pre-selected apps if provided
      setFormData({
        selected_application_ids: hasPreSelectedApps ? preSelectedApplicationIds : [],
        selected_applications: hasPreSelectedApps ? preSelectedApplications : [],
        max_apps_per_wave: 50,
        wave_duration_limit_days: 90,
        contingency_percentage: 20,
      });

      setSearchTerm('');
      setCurrentPage(1);
      setSelectedIds(new Set(hasPreSelectedApps ? preSelectedApplicationIds : []));
      onOpenChange(false);
    }
  };

  /**
   * Navigate to next step with validation
   */
  const handleNext = () => {
    if (currentStep === 1) {
      // Validate applications selected
      if (selectedIds.size === 0) {
        toast({
          title: 'Validation Error',
          description: 'Please select at least one application',
          variant: 'destructive',
        });
        return;
      }

      // Update form data with selected applications
      const selectedApps = applicationsData?.applications.filter((app) =>
        selectedIds.has(app.id)
      ) || [];

      setFormData((prev) => ({
        ...prev,
        selected_application_ids: Array.from(selectedIds),
        selected_applications: selectedApps,
      }));
    }

    if (currentStep < 3) {
      setCurrentStep((prev) => (prev + 1) as 1 | 2 | 3);
    }
  };

  /**
   * Navigate to previous step
   */
  const handleBack = () => {
    // If apps are pre-selected, don't go back to Step 1 (app selection)
    const minStep = hasPreSelectedApps ? 2 : 1;

    if (currentStep > minStep) {
      setCurrentStep((prev) => (prev - 1) as 1 | 2 | 3);
    }
  };

  /**
   * Handle individual checkbox toggle
   */
  const handleToggleSelection = (appId: string) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(appId)) {
        newSet.delete(appId);
      } else {
        newSet.add(appId);
      }
      return newSet;
    });
  };

  /**
   * Handle select all / deselect all on current page
   */
  const handleToggleAll = () => {
    if (!applicationsData?.applications) return;

    const currentPageIds = applicationsData.applications.map((app) => app.id);
    const allSelected = currentPageIds.every((id) => selectedIds.has(id));

    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (allSelected) {
        // Deselect all on current page
        currentPageIds.forEach((id) => newSet.delete(id));
      } else {
        // Select all on current page
        currentPageIds.forEach((id) => newSet.add(id));
      }
      return newSet;
    });
  };

  /**
   * Handle search input change with debouncing
   */
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page on search
  };

  /**
   * Handle page navigation
   */
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
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

      // Show success toast with application count
      toast({
        title: 'Planning Flow Initialized',
        description: `Successfully created planning flow for ${formData.selected_application_ids.length} application${formData.selected_application_ids.length !== 1 ? 's' : ''}`,
        variant: 'default',
      });

      // Close dialog
      handleClose();

      // Redirect to wave planning page with planning_flow_id and engagement_id
      navigate(
        `/plan/waveplanning?planning_flow_id=${response.planning_flow_id}&engagement_id=${engagement_id}`
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
  const renderStep1 = () => {
    const applications = applicationsData?.applications || [];
    const totalPages = applicationsData?.total_pages || 0;
    const currentPageIds = applications.map((app) => app.id);
    const allCurrentPageSelected = currentPageIds.length > 0 && currentPageIds.every((id) => selectedIds.has(id));

    return (
      <div className="space-y-4">
        {/* Search Box */}
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search applications..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleAll}
            disabled={isLoadingApplications || applications.length === 0}
          >
            {allCurrentPageSelected ? 'Deselect All' : 'Select All'}
          </Button>
        </div>

        {/* Selection Count */}
        {selectedIds.size > 0 && (
          <p className="text-sm text-green-600 flex items-center">
            <CheckCircle className="h-4 w-4 mr-1" />
            {selectedIds.size} application(s) selected
          </p>
        )}

        {/* Loading State */}
        {isLoadingApplications && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </div>
        )}

        {/* Error State */}
        {applicationsError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">
              Failed to load applications. Please try again.
            </p>
          </div>
        )}

        {/* Applications Table */}
        {!isLoadingApplications && !applicationsError && (
          <>
            {applications.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  No applications found. {searchTerm && 'Try adjusting your search criteria.'}
                </p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">Select</TableHead>
                      <TableHead>Application Name</TableHead>
                      <TableHead>6R Strategy</TableHead>
                      <TableHead>Tech Stack</TableHead>
                      <TableHead className="text-right">Complexity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {applications.map((app) => (
                      <TableRow key={app.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedIds.has(app.id)}
                            onCheckedChange={() => handleToggleSelection(app.id)}
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {app.application_name || app.asset_name || 'Unnamed'}
                        </TableCell>
                        <TableCell>
                          {app.six_r_strategy ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {app.six_r_strategy}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">Not assessed</span>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {app.tech_stack || <span className="text-gray-400">N/A</span>}
                        </TableCell>
                        <TableCell className="text-right">
                          {app.complexity_score !== null ? (
                            <span className="text-sm font-medium">
                              {app.complexity_score.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">N/A</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

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
      {/* Selected Applications List */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3">
          Selected Applications ({formData.selected_applications.length})
        </h3>

        <div className="max-h-48 overflow-y-auto space-y-2">
          {formData.selected_applications.map((app) => (
            <div
              key={app.id}
              className="bg-white rounded px-3 py-2 text-sm flex justify-between items-center"
            >
              <div>
                <p className="font-medium text-gray-900">
                  {app.application_name || app.asset_name || 'Unnamed'}
                </p>
                {app.six_r_strategy && (
                  <p className="text-xs text-gray-500">Strategy: {app.six_r_strategy}</p>
                )}
              </div>
              {app.complexity_score !== null && (
                <span className="text-xs text-gray-600">
                  Complexity: {app.complexity_score.toFixed(1)}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Configuration Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3">Planning Configuration</h3>

        <div className="space-y-2 text-sm">
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

      {/* Ready to Initialize Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Ready to Initialize</p>
            <p>
              This will create a new planning flow and begin AI-powered wave planning analysis
              for {formData.selected_applications.length} application(s).
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

  // Calculate display step (for UI) - If pre-selected, we're on "Step 1 of 2" (skipping app selection)
  const displayStep = hasPreSelectedApps ? currentStep - 1 : currentStep;
  const totalSteps = hasPreSelectedApps ? 2 : 3;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl" hideCloseButton={isLoading}>
        <DialogHeader>
          <DialogTitle>Initialize Planning Flow</DialogTitle>
          <DialogDescription>
            {hasPreSelectedApps && (
              <span className="text-green-600 font-medium">
                {preSelectedApplicationIds.length} application{preSelectedApplicationIds.length !== 1 ? 's' : ''} pre-selected
                {' • '}
              </span>
            )}
            Step {displayStep} of {totalSteps}: {
              currentStep === 1 ? 'Select Applications' :
              currentStep === 2 ? 'Configure Planning' :
              'Review and Initialize'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Step Content */}
        <div className="py-4">
          {currentStep === 1 && !hasPreSelectedApps && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </div>

        {/* Step Progress Indicator */}
        <div className="flex justify-center space-x-2 mb-4">
          {hasPreSelectedApps ? (
            // 2-step indicator when apps are pre-selected
            [2, 3].map((step) => (
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
            ))
          ) : (
            // 3-step indicator when selecting apps in wizard
            [1, 2, 3].map((step) => (
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
            ))
          )}
        </div>

        {/* Footer Actions */}
        <DialogFooter>
          <div className="flex justify-between w-full">
            <div>
              {/* Show Back button only if we can go back (not on first step) */}
              {currentStep > (hasPreSelectedApps ? 2 : 1) && (
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
