import React, { useState, useCallback, useEffect } from 'react';
import { Plus, Upload, Download, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { ApplicationInputField } from './ApplicationInputField';
import { DuplicateDetectionModal } from './DuplicateDetectionModal';
import { CanonicalApplicationView } from './CanonicalApplicationView';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { canonicalApplicationsApi } from '@/services/api/canonical-applications';
import { useAuth } from '@/contexts/AuthContext';
import type {
  ApplicationSuggestion,
  CanonicalApplication,
  CanonicalApplicationSelection,
  SimilarityMatch,
  DuplicateDecision,
  CreateCanonicalApplicationRequest,
  LinkToCanonicalApplicationRequest,
} from '@/types/collection/canonical-applications';
import { DEFAULT_DEDUPLICATION_CONFIG } from '@/types/collection/canonical-applications';

interface ApplicationDeduplicationManagerProps {
  collectionFlowId: string;
  initialApplications?: CanonicalApplicationSelection[];
  onApplicationsChange: (applications: CanonicalApplicationSelection[]) => void;
  disabled?: boolean;
  maxApplications?: number;
  showBulkImport?: boolean;
  showExportOptions?: boolean;
  confidenceConfig?: typeof DEFAULT_DEDUPLICATION_CONFIG;
}

/**
 * ApplicationDeduplicationManager Component
 *
 * The main orchestration component for application deduplication. Manages the entire
 * workflow from input to duplicate detection to final application selection. Integrates
 * all the deduplication components and provides bulk operations.
 */
export const ApplicationDeduplicationManager: React.FC<ApplicationDeduplicationManagerProps> = ({
  collectionFlowId,
  initialApplications = [],
  onApplicationsChange,
  disabled = false,
  maxApplications = 100,
  showBulkImport = true,
  showExportOptions = false,
  confidenceConfig,
}) => {
  // All hooks must be called at the top level before any conditional logic
  const { client, engagement } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Use default config if not provided
  const effectiveConfig = confidenceConfig || DEFAULT_DEDUPLICATION_CONFIG;

  // Local state
  const [selectedApplications, setSelectedApplications] = useState<CanonicalApplicationSelection[]>(
    initialApplications
  );
  const [currentInput, setCurrentInput] = useState('');
  const [duplicateModalState, setDuplicateModalState] = useState({
    isOpen: false,
    userInput: '',
    detectedMatches: [] as SimilarityMatch[],
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch canonical applications for the tenant with error handling
  const {
    data: canonicalApplications = [],
    isLoading: isLoadingApplications,
    error: applicationsError,
    refetch: refetchApplications,
  } = useQuery({
    queryKey: ['canonical-applications', client?.id, engagement?.id],
    queryFn: async () => {
      if (!client?.id || !engagement?.id) {
        console.warn('Canonical applications query called without client/engagement context');
        return [];
      }
      try {
        const response = await canonicalApplicationsApi.getCanonicalApplications({
          limit: 1000,
          include_variants: true,
          include_history: true,
        });
        return Array.isArray(response?.applications) ? response.applications : [];
      } catch (error: unknown) {
        console.error('Failed to fetch canonical applications:', error);
        const errorMessage = error instanceof Error ? error.message : 'Failed to load canonical applications';
        throw new Error(errorMessage);
      }
    },
    enabled: !!client?.id && !!engagement?.id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Retry up to 2 times for network errors, but not for auth errors
      if (failureCount >= 2) return false;
      return !error?.message?.toLowerCase().includes('unauthorized');
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Update parent when applications change - with proper cleanup
  useEffect(() => {
    // Only call if we have valid applications array
    if (Array.isArray(selectedApplications)) {
      onApplicationsChange(selectedApplications);
    }
  }, [selectedApplications, onApplicationsChange]);

  // Cleanup effect for component unmount with comprehensive cleanup
  useEffect(() => {
    return () => {
      // Clear any pending states on unmount
      setIsProcessing(false);
      setError(null);

      // Reset modal state to prevent memory leaks
      setDuplicateModalState({
        isOpen: false,
        userInput: '',
        detectedMatches: [],
      });

      // Clear input state
      setCurrentInput('');
    };
  }, []);

  // Cleanup when auth context changes to prevent stale data
  useEffect(() => {
    // Reset component state when client/engagement changes
    setSelectedApplications(initialApplications);
    setError(null);
    setIsProcessing(false);
  }, [client?.id, engagement?.id, initialApplications]);

  // Create a new canonical application
  const createNewCanonicalApplication = useCallback(async (applicationName: string) => {
    // Validate authentication context first
    if (!client?.id || !engagement?.id) {
      throw new Error('Authentication context is required. Please ensure you are logged in and try again.');
    }

    if (!applicationName || typeof applicationName !== 'string' || !applicationName.trim()) {
      throw new Error('Valid application name is required to create canonical application');
    }

    const trimmedName = applicationName.trim();
    const createRequest: CreateCanonicalApplicationRequest = {
      canonical_name: trimmedName,
      initial_variant_name: trimmedName,
      source: 'collection_manual',
      metadata: {
        total_variants: 1,
        collection_count: 0,
      },
    };

    const newCanonicalApp = await canonicalApplicationsApi.createCanonicalApplication(createRequest);

    if (!newCanonicalApp?.id || !newCanonicalApp?.canonical_name) {
      throw new Error('Failed to create canonical application: Invalid response from API');
    }

    const newSelection: CanonicalApplicationSelection = {
      canonical_application_id: newCanonicalApp.id,
      canonical_name: newCanonicalApp.canonical_name,
      variant_name: trimmedName,
      selection_method: 'manual_entry',
    };

    setSelectedApplications(prev => [...prev, newSelection]);
    setCurrentInput('');

    // Refresh canonical applications data - only if client and engagement are available
    if (client?.id && engagement?.id) {
      queryClient.invalidateQueries({
        queryKey: ['canonical-applications', client.id, engagement.id],
      });
    }

    toast({
      title: 'New Application Created',
      description: `"${trimmedName}" has been added as a new application.`,
    });
  }, [queryClient, client, engagement, toast]);

  // Check for duplicates and show modal if needed
  const checkForDuplicatesAndHandle = useCallback(async (userInput: string) => {
    if (!client?.id || !engagement?.id) {
      throw new Error('Client and engagement must be available to check for duplicates');
    }

    if (!userInput || typeof userInput !== 'string' || !userInput.trim()) {
      throw new Error('Valid user input is required to check for duplicates');
    }

    try {
      const searchResponse = await canonicalApplicationsApi.searchSimilar({
        query: userInput.trim(),
        client_account_id: client.id,
        engagement_id: engagement.id,
        min_confidence: effectiveConfig?.confidence_thresholds?.duplicate_warning || 0.8,
        max_results: 5,
        include_variants: true,
      });

      const duplicateWarningThreshold = effectiveConfig?.confidence_thresholds?.duplicate_warning || 0.8;
      const potentialDuplicates = (searchResponse?.matches || []).filter(
        match => match?.confidence_score >= duplicateWarningThreshold
      );

      if (Array.isArray(potentialDuplicates) && potentialDuplicates.length > 0) {
        // Show duplicate detection modal
        setDuplicateModalState({
          isOpen: true,
          userInput: userInput.trim(),
          detectedMatches: potentialDuplicates,
        });
      } else {
        // No duplicates detected, create new application
        await createNewCanonicalApplication(userInput.trim());
      }
    } catch (error: unknown) {
      console.error('Error checking for duplicates:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to check for duplicate applications';
      throw new Error(errorMessage);
    }
  }, [client, engagement, effectiveConfig, createNewCanonicalApplication]);

  // Handle application selection from input field
  const handleApplicationSelected = useCallback(async (
    suggestion: ApplicationSuggestion | null,
    userInput: string
  ) => {
    // Type safety checks
    if (!userInput || typeof userInput !== 'string' || !userInput.trim()) {
      console.warn('ApplicationDeduplicationManager: Invalid user input provided');
      return;
    }

    // Check if we have required auth context
    if (!client?.id || !engagement?.id) {
      setError('Authentication context is required. Please ensure you are logged in.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      if (suggestion) {
        // User selected an existing suggestion
        const newSelection: CanonicalApplicationSelection = {
          canonical_application_id: suggestion.canonical_application.id,
          canonical_name: suggestion.canonical_application.canonical_name || 'Unknown Application',
          variant_name: userInput.trim(),
          selection_method: 'autocomplete',
        };

        // Check if already selected with proper null checks
        const alreadySelected = selectedApplications.some(
          app => app?.canonical_application_id === suggestion?.canonical_application?.id
        );

        if (alreadySelected) {
          toast({
            title: 'Application Already Selected',
            description: `"${suggestion?.canonical_application?.canonical_name || 'Unknown application'}" is already in your collection.`,
            variant: 'destructive',
          });
          setCurrentInput('');
          return;
        }

        // Link the variant to the canonical application with null checks
        if (!suggestion?.canonical_application?.id) {
          throw new Error('Invalid suggestion: Missing canonical application ID');
        }

        const linkRequest: LinkToCanonicalApplicationRequest = {
          canonical_application_id: suggestion.canonical_application.id,
          variant_name: userInput.trim(),
          source: 'collection_manual',
          collection_flow_id: collectionFlowId,
        };

        await canonicalApplicationsApi.linkToCanonicalApplication(linkRequest);

        setSelectedApplications(prev => [...prev, newSelection]);
        setCurrentInput('');

        // Refresh canonical applications data - only if client and engagement are available
        if (client?.id && engagement?.id) {
          queryClient.invalidateQueries({
            queryKey: ['canonical-applications', client.id, engagement.id],
          });
        }

        toast({
          title: 'Application Added',
          description: `"${userInput}" has been linked to "${suggestion?.canonical_application?.canonical_name || 'Unknown Application'}".`,
        });
      } else {
        // Manual entry - check for duplicates first
        await checkForDuplicatesAndHandle(userInput.trim());
      }
    } catch (error: unknown) {
      console.error('Error handling application selection:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to process application selection';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [selectedApplications, collectionFlowId, client, engagement, queryClient, toast, checkForDuplicatesAndHandle]);

  // Handle duplicate detection modal decision
  const handleDuplicateDecision = useCallback(async (
    decision: DuplicateDecision,
    selectedMatch?: SimilarityMatch
  ) => {
    const userInput = duplicateModalState.userInput;

    try {
      setIsProcessing(true);

      if (decision === 'use_existing' && selectedMatch) {
        // Link to existing canonical application
        const linkRequest: LinkToCanonicalApplicationRequest = {
          canonical_application_id: selectedMatch.canonical_application.id,
          variant_name: userInput,
          source: 'collection_manual',
          collection_flow_id: collectionFlowId,
        };

        await canonicalApplicationsApi.linkToCanonicalApplication(linkRequest);

        const newSelection: CanonicalApplicationSelection = {
          canonical_application_id: selectedMatch.canonical_application.id,
          canonical_name: selectedMatch.canonical_application.canonical_name,
          variant_name: userInput,
          selection_method: 'duplicate_resolution',
        };

        setSelectedApplications(prev => [...prev, newSelection]);
        setCurrentInput('');

        toast({
          title: 'Application Linked',
          description: `"${userInput}" has been linked to "${selectedMatch.canonical_application.canonical_name}".`,
        });
      } else if (decision === 'create_new') {
        // Create new canonical application
        await createNewCanonicalApplication(userInput);
      }

      // Close modal
      setDuplicateModalState({
        isOpen: false,
        userInput: '',
        detectedMatches: [],
      });

      // Refresh data - only if client and engagement are available
      if (client?.id && engagement?.id) {
        queryClient.invalidateQueries({
          queryKey: ['canonical-applications', client.id, engagement.id],
        });
      }
    } catch (error: unknown) {
      console.error('Error processing duplicate decision:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to process duplicate decision.';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [duplicateModalState.userInput, collectionFlowId, queryClient, client, engagement, toast, createNewCanonicalApplication]);

  // Remove application from selection
  const handleRemoveApplication = useCallback((canonicalApplicationId: string) => {
    if (!canonicalApplicationId || typeof canonicalApplicationId !== 'string') {
      console.warn('ApplicationDeduplicationManager: Invalid canonical application ID provided for removal');
      return;
    }

    setSelectedApplications(prev =>
      Array.isArray(prev) ? prev.filter(app => app?.canonical_application_id !== canonicalApplicationId) : []
    );

    toast({
      title: 'Application Removed',
      description: 'The application has been removed from this collection.',
    });
  }, [toast]);

  // Type safety check for required props (after all hooks)
  if (!collectionFlowId || typeof collectionFlowId !== 'string') {
    console.error('ApplicationDeduplicationManager: collectionFlowId is required and must be a string');
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-red-700 text-sm">Error: Invalid collection flow ID. Cannot initialize application deduplication.</p>
      </div>
    );
  }

  if (!onApplicationsChange || typeof onApplicationsChange !== 'function') {
    console.error('ApplicationDeduplicationManager: onApplicationsChange callback is required');
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-red-700 text-sm">Error: Missing required callback function. Cannot initialize component.</p>
      </div>
    );
  }

  // Get statistics for display with proper null checks
  const stats = {
    totalApplications: Array.isArray(selectedApplications) ? selectedApplications.length : 0,
    totalVariants: Array.isArray(canonicalApplications) && Array.isArray(selectedApplications)
      ? canonicalApplications
          .filter(app => app?.id && selectedApplications.some(sel => sel?.canonical_application_id === app.id))
          .reduce((sum, app) => sum + (Array.isArray(app?.variants) ? app.variants.length : 0), 0)
      : 0,
    newApplications: Array.isArray(selectedApplications)
      ? selectedApplications.filter(app => app?.selection_method === 'manual_entry').length
      : 0,
    linkedApplications: Array.isArray(selectedApplications)
      ? selectedApplications.filter(app => app?.selection_method !== 'manual_entry').length
      : 0,
  };

  // Check if at capacity with safe number check
  const safeMaxApplications = typeof maxApplications === 'number' && isFinite(maxApplications) ? maxApplications : 100;
  const atCapacity = (Array.isArray(selectedApplications) ? selectedApplications.length : 0) >= safeMaxApplications;

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Applications
          </CardTitle>
          <CardDescription>
            Enter application names to add them to your collection. The system will suggest existing applications and detect potential duplicates.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Loading State */}
          {isLoadingApplications && (
            <Alert>
              <AlertDescription className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                Loading application data...
              </AlertDescription>
            </Alert>
          )}

          {/* Error States */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {applicationsError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to load existing applications: {applicationsError?.message || 'Unknown error'}
                <Button variant="link" className="ml-2 p-0 h-auto" onClick={() => refetchApplications()}>
                  Try Again
                </Button>
              </AlertDescription>
            </Alert>
          )}

          <ApplicationInputField
            value={currentInput}
            onChange={setCurrentInput}
            onApplicationSelected={handleApplicationSelected}
            disabled={disabled || isProcessing || atCapacity}
            placeholder={atCapacity ? `Maximum ${safeMaxApplications} applications reached` : "Enter application name..."}
            showConfidenceScores={true}
            maxSuggestions={8}
            confidenceThresholds={effectiveConfig.confidence_thresholds}
          />

          {atCapacity && (
            <Alert>
              <AlertDescription>
                You've reached the maximum of {safeMaxApplications} applications for this collection.
                Remove some applications to add new ones.
              </AlertDescription>
            </Alert>
          )}

          {/* Statistics - Responsive Grid Layout */}
          {stats.totalApplications > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 pt-4 border-t text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <span>📊</span>
                <span className="truncate">{stats.totalApplications} applications</span>
              </span>
              <span className="flex items-center gap-1">
                <span>🔗</span>
                <span className="truncate">{stats.linkedApplications} linked</span>
              </span>
              <span className="flex items-center gap-1">
                <span>✨</span>
                <span className="truncate">{stats.newApplications} new created</span>
              </span>
              <span className="flex items-center gap-1">
                <span>📝</span>
                <span className="truncate">{stats.totalVariants} variants</span>
              </span>
            </div>
          )}

          {/* Bulk Actions - Responsive Button Layout */}
          {(showBulkImport || showExportOptions) && (
            <div className="flex flex-col sm:flex-row gap-2 pt-4 border-t">
              {showBulkImport && (
                <Button variant="outline" size="sm" disabled={disabled}>
                  <Upload className="h-4 w-4 mr-2" />
                  Bulk Import
                </Button>
              )}
              {showExportOptions && stats.totalApplications > 0 && (
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export List
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchApplications()}
                disabled={isLoadingApplications}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Selected Applications View */}
      <CanonicalApplicationView
        applications={selectedApplications}
        canonicalApplications={canonicalApplications}
        onRemoveApplication={handleRemoveApplication}
        showVariantDetails={true}
        showCollectionHistory={false}
      />

      {/* Duplicate Detection Modal */}
      <DuplicateDetectionModal
        isOpen={duplicateModalState.isOpen}
        onClose={() => setDuplicateModalState(prev => ({ ...prev, isOpen: false }))}
        userInput={duplicateModalState.userInput}
        detectedMatches={duplicateModalState.detectedMatches}
        onDecision={handleDuplicateDecision}
        isProcessing={isProcessing}
      />
    </div>
  );
};
