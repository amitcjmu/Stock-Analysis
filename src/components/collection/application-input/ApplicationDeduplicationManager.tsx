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
  DEFAULT_DEDUPLICATION_CONFIG,
  CreateCanonicalApplicationRequest,
  LinkToCanonicalApplicationRequest,
} from '@/types/collection/canonical-applications';

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
  confidenceConfig = DEFAULT_DEDUPLICATION_CONFIG,
}) => {
  const { client, engagement } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

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

  // Fetch canonical applications for the tenant
  const {
    data: canonicalApplications = [],
    isLoading: isLoadingApplications,
    error: applicationsError,
    refetch: refetchApplications,
  } = useQuery({
    queryKey: ['canonical-applications', client?.id, engagement?.id],
    queryFn: async () => {
      if (!client || !engagement) return [];
      const response = await canonicalApplicationsApi.getCanonicalApplications({
        limit: 1000,
        include_variants: true,
        include_history: true,
      });
      return response.applications;
    },
    enabled: !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update parent when applications change
  useEffect(() => {
    onApplicationsChange(selectedApplications);
  }, [selectedApplications, onApplicationsChange]);

  // Handle application selection from input field
  const handleApplicationSelected = useCallback(async (
    suggestion: ApplicationSuggestion | null,
    userInput: string
  ) => {
    if (!userInput.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      if (suggestion) {
        // User selected an existing suggestion
        const newSelection: CanonicalApplicationSelection = {
          canonical_application_id: suggestion.canonical_application.id,
          canonical_name: suggestion.canonical_application.canonical_name,
          variant_name: userInput.trim(),
          selection_method: 'autocomplete',
        };

        // Check if already selected
        const alreadySelected = selectedApplications.some(
          app => app.canonical_application_id === suggestion.canonical_application.id
        );

        if (alreadySelected) {
          toast({
            title: 'Application Already Selected',
            description: `"${suggestion.canonical_application.canonical_name}" is already in your collection.`,
            variant: 'destructive',
          });
          setCurrentInput('');
          return;
        }

        // Link the variant to the canonical application
        const linkRequest: LinkToCanonicalApplicationRequest = {
          canonical_application_id: suggestion.canonical_application.id,
          variant_name: userInput.trim(),
          source: 'collection_manual',
          collection_flow_id: collectionFlowId,
        };

        await canonicalApplicationsApi.linkToCanonicalApplication(linkRequest);

        setSelectedApplications(prev => [...prev, newSelection]);
        setCurrentInput('');

        // Refresh canonical applications data
        queryClient.invalidateQueries({
          queryKey: ['canonical-applications', client?.id, engagement?.id],
        });

        toast({
          title: 'Application Added',
          description: `"${userInput}" has been linked to "${suggestion.canonical_application.canonical_name}".`,
        });
      } else {
        // Manual entry - check for duplicates first
        await checkForDuplicatesAndHandle(userInput.trim());
      }
    } catch (error: any) {
      console.error('Error handling application selection:', error);
      setError(error.message || 'Failed to process application selection');
      toast({
        title: 'Error',
        description: error.message || 'Failed to add application to collection.',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [selectedApplications, collectionFlowId, client, engagement, queryClient, toast]);

  // Check for duplicates and show modal if needed
  const checkForDuplicatesAndHandle = useCallback(async (userInput: string) => {
    try {
      const searchResponse = await canonicalApplicationsApi.searchSimilar({
        query: userInput,
        client_account_id: client!.id,
        engagement_id: engagement!.id,
        min_confidence: confidenceConfig.confidence_thresholds.duplicate_warning,
        max_results: 5,
        include_variants: true,
      });

      const potentialDuplicates = searchResponse.matches.filter(
        match => match.confidence_score >= confidenceConfig.confidence_thresholds.duplicate_warning
      );

      if (potentialDuplicates.length > 0) {
        // Show duplicate detection modal
        setDuplicateModalState({
          isOpen: true,
          userInput,
          detectedMatches: potentialDuplicates,
        });
      } else {
        // No duplicates detected, create new application
        await createNewCanonicalApplication(userInput);
      }
    } catch (error: any) {
      console.error('Error checking for duplicates:', error);
      throw error;
    }
  }, [client, engagement, confidenceConfig]);

  // Create a new canonical application
  const createNewCanonicalApplication = useCallback(async (applicationName: string) => {
    const createRequest: CreateCanonicalApplicationRequest = {
      canonical_name: applicationName,
      initial_variant_name: applicationName,
      source: 'collection_manual',
      metadata: {
        total_variants: 1,
        collection_count: 0,
      },
    };

    const newCanonicalApp = await canonicalApplicationsApi.createCanonicalApplication(createRequest);

    const newSelection: CanonicalApplicationSelection = {
      canonical_application_id: newCanonicalApp.id,
      canonical_name: newCanonicalApp.canonical_name,
      variant_name: applicationName,
      selection_method: 'manual_entry',
    };

    setSelectedApplications(prev => [...prev, newSelection]);
    setCurrentInput('');

    // Refresh canonical applications data
    queryClient.invalidateQueries({
      queryKey: ['canonical-applications', client?.id, engagement?.id],
    });

    toast({
      title: 'New Application Created',
      description: `"${applicationName}" has been added as a new application.`,
    });
  }, [collectionFlowId, queryClient, client, engagement, toast]);

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

      // Refresh data
      queryClient.invalidateQueries({
        queryKey: ['canonical-applications', client?.id, engagement?.id],
      });
    } catch (error: any) {
      console.error('Error processing duplicate decision:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to process duplicate decision.',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [duplicateModalState.userInput, collectionFlowId, queryClient, client, engagement, toast, createNewCanonicalApplication]);

  // Remove application from selection
  const handleRemoveApplication = useCallback((canonicalApplicationId: string) => {
    setSelectedApplications(prev =>
      prev.filter(app => app.canonical_application_id !== canonicalApplicationId)
    );

    toast({
      title: 'Application Removed',
      description: 'The application has been removed from this collection.',
    });
  }, [toast]);

  // Get statistics for display
  const stats = {
    totalApplications: selectedApplications.length,
    totalVariants: canonicalApplications
      .filter(app => selectedApplications.some(sel => sel.canonical_application_id === app.id))
      .reduce((sum, app) => sum + app.variants.length, 0),
    newApplications: selectedApplications.filter(app => app.selection_method === 'manual_entry').length,
    linkedApplications: selectedApplications.filter(app => app.selection_method !== 'manual_entry').length,
  };

  // Check if at capacity
  const atCapacity = selectedApplications.length >= maxApplications;

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
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <ApplicationInputField
            value={currentInput}
            onChange={setCurrentInput}
            onApplicationSelected={handleApplicationSelected}
            disabled={disabled || isProcessing || atCapacity}
            placeholder={atCapacity ? `Maximum ${maxApplications} applications reached` : "Enter application name..."}
            showConfidenceScores={true}
            maxSuggestions={8}
            confidenceThresholds={confidenceConfig.confidence_thresholds}
          />

          {atCapacity && (
            <Alert>
              <AlertDescription>
                You've reached the maximum of {maxApplications} applications for this collection.
                Remove some applications to add new ones.
              </AlertDescription>
            </Alert>
          )}

          {/* Statistics */}
          {selectedApplications.length > 0 && (
            <div className="flex flex-wrap gap-4 pt-4 border-t text-sm text-gray-600">
              <span>📊 {stats.totalApplications} applications selected</span>
              <span>🔗 {stats.linkedApplications} linked to existing</span>
              <span>✨ {stats.newApplications} new applications created</span>
              <span>📝 {stats.totalVariants} total variants</span>
            </div>
          )}

          {/* Bulk Actions */}
          {(showBulkImport || showExportOptions) && (
            <div className="flex flex-wrap gap-2 pt-4 border-t">
              {showBulkImport && (
                <Button variant="outline" size="sm" disabled={disabled}>
                  <Upload className="h-4 w-4 mr-2" />
                  Bulk Import
                </Button>
              )}
              {showExportOptions && selectedApplications.length > 0 && (
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
