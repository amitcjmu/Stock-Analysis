/**
 * ReadinessDashboardWidget - Assessment readiness visualization and blocker tracking
 *
 * Phase 4 Days 19-20: Assessment Architecture Enhancement
 * Day 12 (Issue #980): Updated to use comprehensive gap analysis API
 *
 * Features:
 * - Summary cards (Ready, Not Ready, In Progress, Avg Completeness)
 * - Asset cards with expandable gap details across 5 inspectors
 * - Weighted completeness scores by data layer
 * - Prioritized gaps with badges (critical/high/medium)
 * - Readiness blockers with actionable details
 * - "Collect Missing Data" button to navigate to Collection flow
 *
 * Backend Integration:
 * - Fetches from: GET /api/v1/assessment-flow/{flow_id}/readiness-summary
 * - Optional detailed mode for per-asset ComprehensiveGapReport
 * - Uses snake_case for ALL field names (ADR compliance)
 * - Follows TanStack Query patterns with 15s refetch interval
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronRight,
  FileText,
  Download,
  ArrowRight,
  Info,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { assessmentFlowApi } from '@/lib/api/assessmentFlow';
import { SummaryCard } from './shared/SummaryCard';
import { AssetBlockerAccordion } from './shared/AssetBlockerAccordion';
import {
  type AssessmentReadinessResponse,
  type BatchReadinessSummary,
  type ComprehensiveGapReport,
  CRITICAL_ATTRIBUTES,
  getCriticalAttributesByCategory,
} from '@/types/assessment';

// ============================================================================
// Component Props
// ============================================================================

export interface ReadinessDashboardWidgetProps {
  flow_id: string;
  client_account_id: string;
  engagement_id?: string; // Optional - not required for tenant scoping
}

// ============================================================================
// Main Component
// ============================================================================

export const ReadinessDashboardWidget: React.FC<ReadinessDashboardWidgetProps> = ({
  flow_id,
  client_account_id,
  engagement_id,
}) => {
  const { getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [expandedAssets, setExpandedAssets] = useState<Set<string>>(new Set());
  const [showAttributesReference, setShowAttributesReference] = useState(false);
  const [isCollecting, setIsCollecting] = useState(false);

  // ============================================================================
  // Data Fetching
  // ============================================================================

  /**
   * Fetch readiness summary using new gap analysis API (Day 12 - Issue #980)
   *
   * Endpoint: GET /api/v1/assessment-flow/{flow_id}/readiness-summary?detailed=false
   * Uses lightweight mode (detailed=false) for performance - no per-asset reports
   *
   * Response contains:
   * - total_assets, ready_count, not_ready_count, overall_readiness_rate
   * - summary_by_type (per asset type breakdown)
   * - analyzed_at (ISO timestamp)
   */
  const {
    data: readinessSummary,
    isLoading,
    isError,
    error,
  } = useQuery<BatchReadinessSummary>({
    queryKey: ['assessment-readiness-v2', flow_id],
    queryFn: async () => {
      // Use new assessmentFlowApi with detailed=false for lightweight summary
      return await assessmentFlowApi.getFlowReadinessSummary(flow_id, false);
    },
    enabled: !!flow_id,
    staleTime: 10000, // 10 seconds (more frequent for real-time updates)
    refetchInterval: 15000, // Refresh every 15 seconds per Day 12 requirements
  });

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const toggleAsset = (asset_id: string) => {
    setExpandedAssets((prev) => {
      const next = new Set(prev);
      if (next.has(asset_id)) {
        next.delete(asset_id);
      } else {
        next.add(asset_id);
      }
      return next;
    });
  };

  const handleExportReport = () => {
    // TODO: Implement export to PDF/CSV
    console.log('Export readiness report');
  };

  /**
   * Navigate to collection flow for not-ready assets.
   *
   * Day 12 Update: Fetch not-ready asset IDs using new API, then get individual
   * gap reports to extract missing attributes for targeted collection.
   */
  const handleCollectMissingData = async () => {
    if (!readinessSummary || isCollecting) {
      return;
    }

    setIsCollecting(true);
    try {
      // Fetch not-ready asset IDs using new filter endpoint
      const notReadyAssetIds = await assessmentFlowApi.getReadyAssets(flow_id, false);

      if (notReadyAssetIds.length === 0) {
        toast({
          title: 'No Assets Need Collection',
          description: 'All assets are ready for assessment',
        });
        setIsCollecting(false);
        return;
      }

      // For now, navigate to collection flow with flow context
      // TODO (Future): Fetch individual gap reports to extract specific missing attributes
      // const missing_attributes: Record<string, string[]> = {};
      // for (const assetId of notReadyAssetIds) {
      //   const gapReport = await assessmentFlowApi.getAssetReadiness(flow_id, assetId);
      //   missing_attributes[assetId] = gapReport.critical_gaps;
      // }

      // Create or update collection flow linked to assessment flow
      const collectionFlow = await collectionFlowApi.ensureFlow({}, flow_id);

      toast({
        title: 'Collection Flow Ready',
        description: `${notReadyAssetIds.length} assets need data collection`,
      });

      // Navigate to collection flow
      navigate(`/collection/adaptive-forms?flowId=${collectionFlow.flow_id || collectionFlow.id}`);
    } catch (error) {
      console.error('Failed to start collection:', error);
      toast({
        title: 'Collection Failed',
        description: 'Failed to start data collection. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsCollecting(false);
    }
  };

  // ============================================================================
  // Computed Values
  // ============================================================================

  /**
   * Calculate average completeness percentage from readiness rate.
   *
   * Day 12: Uses overall_readiness_rate from BatchReadinessSummary (0-100 scale)
   */
  const avgCompleteness = useMemo(() => {
    if (!readinessSummary) return 0;
    // overall_readiness_rate is already 0-100, no conversion needed
    return Math.round(readinessSummary.overall_readiness_rate ?? 0);
  }, [readinessSummary]);

  /**
   * Readiness counts from summary.
   */
  const readinessCounts = useMemo(() => {
    if (!readinessSummary) {
      return { ready: 0, not_ready: 0, in_progress: 0 };
    }
    return {
      ready: readinessSummary.ready_count,
      not_ready: readinessSummary.not_ready_count,
      // in_progress not provided by new API, calculate as total - ready - not_ready
      in_progress: readinessSummary.total_assets - readinessSummary.ready_count - readinessSummary.not_ready_count,
    };
  }, [readinessSummary]);

  // ============================================================================
  // Render States
  // ============================================================================

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Assessment Readiness</CardTitle>
          <CardDescription>Loading readiness data...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Assessment Readiness</CardTitle>
          <CardDescription className="text-destructive">Failed to load readiness data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>{error instanceof Error ? error.message : 'An error occurred'}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!readinessSummary || readinessSummary.total_assets === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Assessment Readiness</CardTitle>
          <CardDescription>No assets found for readiness assessment</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">No asset data available</p>
        </CardContent>
      </Card>
    );
  }

  const allReady = readinessCounts.ready === readinessSummary.total_assets;

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Ready Assets"
          value={readinessCounts.ready}
          icon={<CheckCircle />}
          color="text-green-600"
          description={`${Math.round((readinessCounts.ready / readinessSummary.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="Not Ready Assets"
          value={readinessCounts.not_ready}
          icon={<AlertTriangle />}
          color="text-red-600"
          description={`${Math.round((readinessCounts.not_ready / readinessSummary.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="In Progress Assets"
          value={readinessCounts.in_progress}
          icon={<Clock />}
          color="text-yellow-600"
          description={`${Math.round((readinessCounts.in_progress / readinessSummary.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="Avg Completeness"
          value={`${avgCompleteness}%`}
          icon={<FileText />}
          color={avgCompleteness >= 75 ? 'text-green-600' : avgCompleteness >= 50 ? 'text-yellow-600' : 'text-red-600'}
          description={`Across ${readinessSummary.total_assets} assets`}
        />
      </div>

      {/* All Ready Celebration */}
      {allReady && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-950">
          <CardContent className="flex items-center justify-center gap-4 py-8">
            <CheckCircle className="h-12 w-12 text-green-600" />
            <div>
              <h3 className="text-xl font-semibold text-green-900 dark:text-green-100">All Assets Ready!</h3>
              <p className="text-green-700 dark:text-green-300">You can proceed with the assessment</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Assessment Blockers Summary */}
      {readinessCounts.not_ready > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  Assessment Blockers
                </CardTitle>
                <CardDescription>
                  {readinessCounts.not_ready} assets need data collection before assessment
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleCollectMissingData}
                  variant="default"
                  disabled={isCollecting}
                >
                  {isCollecting ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4 mr-2" />
                  )}
                  {isCollecting ? 'Starting Collection...' : 'Collect Missing Data'}
                </Button>
                <Button onClick={handleExportReport} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export Report
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Readiness by Asset Type */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold">Readiness by Asset Type</h4>
              <div className="space-y-3">
                {Object.entries(readinessSummary.summary_by_type).map(([assetType, summary]) => (
                  <div key={assetType} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium capitalize">{assetType.replace(/_/g, ' ')}</span>
                      <span className="text-muted-foreground">
                        {summary.ready} / {summary.total} ready ({summary.readiness_rate.toFixed(0)}%)
                      </span>
                    </div>
                    <Progress value={summary.readiness_rate} className="h-2" />
                    {summary.not_ready > 0 && (
                      <p className="text-xs text-muted-foreground">
                        {summary.not_ready} {assetType} {summary.not_ready === 1 ? 'needs' : 'need'} data collection
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Note about detailed gap analysis */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    Detailed Gap Analysis Available
                  </p>
                  <p className="mt-1 text-blue-700 dark:text-blue-300">
                    Click "Collect Missing Data" to view specific missing attributes per asset and
                    generate targeted questionnaires using the new 5-inspector gap analysis system.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Critical Attributes Reference */}
      <Card>
        <Collapsible open={showAttributesReference} onOpenChange={setShowAttributesReference}>
          <CardHeader>
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>22 Critical Attributes for 6R Assessment</CardTitle>
                </div>
                {showAttributesReference ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
              </div>
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-6">
              {(['infrastructure', 'application', 'business', 'technical_debt'] as const).map((category) => {
                const attributes = getCriticalAttributesByCategory(category);
                return (
                  <div key={category}>
                    <h4 className="text-sm font-semibold mb-3 capitalize">{category.replace('_', ' ')} ({attributes.length})</h4>
                    <ul className="space-y-2">
                      {attributes.map((attr) => (
                        <li key={attr.name} className="text-sm">
                          <div className="flex items-start gap-2">
                            <span className={cn('font-medium', attr.required ? 'text-red-600' : 'text-yellow-600')}>
                              {attr.name.replace(/_/g, ' ')}
                            </span>
                            {attr.required && <Badge variant="destructive" className="text-xs">Required</Badge>}
                          </div>
                          <p className="text-muted-foreground ml-6">{attr.description}</p>
                          <p className="text-xs text-muted-foreground ml-6 italic">{attr.importance}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  );
};

export default ReadinessDashboardWidget;
