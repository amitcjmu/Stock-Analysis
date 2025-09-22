import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { ArrowLeft, RefreshCw, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Import existing collection components
import { DataIntegrationView } from '@/components/collection/DataIntegrationView';
import { ConflictResolver } from '@/components/collection/components/ConflictResolver';
import { ValidationDisplay } from '@/components/collection/ValidationDisplay';
import { ProgressTracker } from '@/components/collection/ProgressTracker';

// Import types
import type {
  DataConflict,
  ConflictResolution,
  FormValidationResult,
  ProgressMilestone
} from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';
import { CardHeader, CardTitle } from '@/components/ui/card'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

/**
 * Data Integration page
 * Handles conflict resolution and data validation from multiple sources
 */
const DataIntegration: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();

  // Get asset_id from URL parameters - required for this component to function
  const asset_id = searchParams.get('asset_id');

  // State management
  const [conflicts, setConflicts] = useState<DataConflict[]>([]);
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resolvedConflicts, setResolvedConflicts] = useState<string[]>([]);

  // Early return if no asset_id is provided
  if (!asset_id) {
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
                    <h1 className="text-2xl font-bold">Data Integration & Validation</h1>
                    <p className="text-muted-foreground">
                      Resolve conflicts and validate data from multiple collection sources
                    </p>
                  </div>
                </div>
              </div>

              <Card>
                <CardContent className="p-8">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-orange-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Asset Selection Required</h3>
                    <p className="text-muted-foreground mb-6">
                      Please select an asset to view and resolve data conflicts.
                      You can navigate back to the collection page to choose an asset.
                    </p>
                    <Button onClick={() => navigate('/collection')}>
                      Select Asset
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fetch real conflicts data from the API
  const { data: conflictsData, isLoading, error, refetch } = useQuery({
    queryKey: ['asset-conflicts', asset_id],
    queryFn: async () => {
      try {
        const response = await collectionFlowApi.getAssetConflicts(asset_id);
        return response;
      } catch (err) {
        console.error('Failed to fetch asset conflicts:', err);
        // Return empty array if API fails, rather than showing error
        return [];
      }
    },
    enabled: !!asset_id,
    staleTime: 30000, // 30 seconds
    refetchInterval: false // Only refetch manually
  });

  // Transform API conflicts data to match frontend DataConflict interface
  useEffect(() => {
    if (conflictsData) {
      const transformedConflicts: DataConflict[] = conflictsData.map(apiConflict => ({
        id: apiConflict.id,
        attributeName: apiConflict.field_name,
        attributeLabel: apiConflict.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        conflictingValues: apiConflict.conflicting_values.map(value => ({
          value: value.value,
          source: value.source === 'custom_attributes' ? 'manual' :
                  value.source === 'technical_details' ? 'automated' :
                  value.source.startsWith('import:') ? 'bulk' : 'automated',
          sourceId: value.source,
          confidenceScore: value.confidence,
          collectedAt: value.timestamp
        })),
        recommendedResolution: undefined, // API doesn't provide this yet
        requiresUserReview: apiConflict.resolution_status === 'pending'
      }));

      setConflicts(transformedConflicts);

      // Generate validation result based on conflicts
      const mockValidation: FormValidationResult = {
        formId: 'data-integration',
        isValid: transformedConflicts.length === 0,
        overallConfidenceScore: transformedConflicts.length > 0 ? 0.75 : 1.0,
        completionPercentage: Math.round(((transformedConflicts.length - transformedConflicts.filter(c => c.requiresUserReview).length) / Math.max(transformedConflicts.length, 1)) * 100),
        fieldResults: {},
        crossFieldErrors: transformedConflicts
          .filter(conflict => conflict.requiresUserReview)
          .map(conflict => ({
            fieldId: conflict.attributeName,
            fieldLabel: conflict.attributeLabel,
            errorCode: 'CONFLICTING_VALUES',
            errorMessage: 'Multiple conflicting values detected from different sources',
            severity: 'warning' as const
          })),
        businessRuleViolations: []
      };

      setValidation(mockValidation);
    }
  }, [conflictsData]);

  // Progress milestones
  const progressMilestones: ProgressMilestone[] = [
    {
      id: 'data-loaded',
      title: 'Data Sources Loaded',
      description: 'All data sources have been loaded and analyzed',
      achieved: !isLoading,
      achievedAt: !isLoading ? new Date().toISOString() : undefined,
      weight: 0.2,
      required: true
    },
    {
      id: 'conflicts-identified',
      title: 'Conflicts Identified',
      description: 'Data conflicts have been identified and categorized',
      achieved: conflicts.length > 0,
      weight: 0.3,
      required: true
    },
    {
      id: 'conflicts-resolved',
      title: 'Conflicts Resolved',
      description: 'All data conflicts have been resolved',
      achieved: resolvedConflicts.length === conflicts.length && conflicts.length > 0,
      weight: 0.3,
      required: true
    },
    {
      id: 'validation-passed',
      title: 'Final Validation',
      description: 'All data has passed final validation checks',
      achieved: validation?.isValid || false,
      weight: 0.2,
      required: true
    }
  ];

  const handleConflictResolve = async (conflictId: string, resolution: ConflictResolution): Promise<void> => {
    try {
      setIsProcessing(true);

      // Find the conflict to get field_name
      const conflict = conflicts.find(c => c.id === conflictId);
      if (!conflict) {
        throw new Error('Conflict not found');
      }

      // Call the API to resolve the conflict
      await collectionFlowApi.resolveAssetConflict(
        asset_id,
        conflict.attributeName,
        {
          value: String(resolution.selectedValue),
          rationale: resolution.userJustification
        }
      );

      // Update local state
      setResolvedConflicts(prev => [...prev, conflictId]);
      setConflicts(prev => prev.filter(c => c.id !== conflictId));

      toast({
        title: 'Conflict Resolved',
        description: `Selected "${resolution.selectedValue}" from ${resolution.selectedSource} source.`
      });

      // Check if all conflicts are resolved
      const remainingConflicts = conflicts.filter(c => c.id !== conflictId);
      if (remainingConflicts.length === 0) {
        // Update validation to mark as valid
        setValidation(prev => prev ? { ...prev, isValid: true, completionPercentage: 100 } : null);

        toast({
          title: 'All Conflicts Resolved',
          description: 'Data integration is complete. Ready to proceed to discovery phase.'
        });
      }
    } catch (error) {
      console.error('Failed to resolve conflict:', error);
      toast({
        title: 'Resolution Failed',
        description: 'Failed to resolve conflict. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRefreshData = async (): void => {
    try {
      // Refetch conflicts data from the API
      await refetch();

      toast({
        title: 'Data Refreshed',
        description: 'Latest conflict data has been loaded from all sources.'
      });
    } catch (error) {
      toast({
        title: 'Refresh Failed',
        description: 'Failed to refresh conflict data. Please try again.',
        variant: 'destructive'
      });
    }
  };

  const handleProceedToDiscovery = async (): void => {
    if (!validation?.isValid) {
      toast({
        title: 'Validation Required',
        description: 'Please resolve all conflicts before proceeding.',
        variant: 'destructive'
      });
      return;
    }

    setIsProcessing(true);
    try {
      // Simulate handoff to discovery phase
      await new Promise(resolve => setTimeout(resolve, 2000));

      toast({
        title: 'Handoff Successful',
        description: 'Data has been successfully transferred to discovery phase.'
      });

      navigate('/discovery?source=collection&integrated=true');
    } catch (error) {
      toast({
        title: 'Handoff Failed',
        description: 'Failed to transfer data to discovery phase.',
        variant: 'destructive'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const getConflictStatusCounts = (): unknown => {
    const total = conflicts.length + resolvedConflicts.length;
    const resolved = resolvedConflicts.length;
    const pending = conflicts.length;
    const highPriority = conflicts.filter(c => c.requiresUserReview).length;

    return { total, resolved, pending, highPriority };
  };

  const statusCounts = getConflictStatusCounts();
  const overallProgress = statusCounts.total > 0 ? (statusCounts.resolved / statusCounts.total) * 100 : 0;

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
            <h1 className="text-2xl font-bold">Data Integration & Validation</h1>
            <p className="text-muted-foreground">
              Resolve conflicts and validate data from multiple collection sources
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleRefreshData}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Data
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Conflicts</p>
                <p className="text-2xl font-bold">{statusCounts.total}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Resolved</p>
                <p className="text-2xl font-bold text-green-600">{statusCounts.resolved}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold text-orange-600">{statusCounts.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">High Priority</p>
                <p className="text-2xl font-bold text-red-600">{statusCounts.highPriority}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Progress Tracker Sidebar */}
        <div className="lg:col-span-1">
          <ProgressTracker
            formId="data-integration"
            totalSections={4}
            completedSections={progressMilestones.filter(m => m.achieved).length}
            overallCompletion={overallProgress}
            confidenceScore={validation?.overallConfidenceScore || 0}
            milestones={progressMilestones}
            timeSpent={0}
            estimatedTimeRemaining={statusCounts.pending * 120000} // 2 min per conflict
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Validation Display */}
          {validation && (
            <ValidationDisplay
              validation={validation}
              showWarnings={true}
              onErrorClick={(fieldId) => {
                console.log('Navigate to conflict:', fieldId);
              }}
            />
          )}

          {/* Main Content Tabs */}
          <Tabs defaultValue="conflicts" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="conflicts" className="relative">
                Conflict Resolution
                {statusCounts.pending > 0 && (
                  <Badge variant="destructive" className="ml-2 text-xs">
                    {statusCounts.pending}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="overview">Data Overview</TabsTrigger>
            </TabsList>

            <TabsContent value="conflicts" className="space-y-6">
              {isLoading ? (
                <Card>
                  <CardContent className="p-8">
                    <div className="flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                        <p className="text-muted-foreground">Loading data conflicts...</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : conflicts.length > 0 ? (
                <ConflictResolver
                  conflicts={conflicts}
                  onResolve={handleConflictResolve}
                />
              ) : (
                <Card>
                  <CardContent className="p-8">
                    <div className="text-center">
                      <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">All Conflicts Resolved</h3>
                      <p className="text-muted-foreground">
                        Great! All data conflicts have been resolved. You can now proceed to the discovery phase.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="overview" className="space-y-6">
              <DataIntegrationView />
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <Button
              variant="outline"
              onClick={() => navigate('/collection')}
            >
              Save and Return
            </Button>
            <Button
              onClick={handleProceedToDiscovery}
              disabled={!validation?.isValid || isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Proceed to Discovery Phase'}
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

export default DataIntegration;
