/**
 * ReadinessDashboardWidget - Assessment readiness visualization and blocker tracking
 *
 * Phase 4 Days 19-20: Assessment Architecture Enhancement
 *
 * Features:
 * - Summary cards (Ready, Not Ready, In Progress, Avg Completeness)
 * - Assessment blockers per-asset with missing attributes
 * - Critical attributes reference (22 attributes grouped by category)
 * - Progress bars and completeness visualization
 * - "Collect Missing Data" button to navigate to Collection flow
 *
 * Backend Integration:
 * - Fetches from: GET /api/v1/master-flows/{flow_id}/assessment-readiness
 * - Uses snake_case for ALL field names (ADR compliance)
 * - Follows TanStack Query patterns for data fetching
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { SummaryCard } from './shared/SummaryCard';
import { AssetBlockerAccordion } from './shared/AssetBlockerAccordion';
import {
  type AssessmentReadinessResponse,
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
  onCollectDataClick?: () => void;
}

// ============================================================================
// Main Component
// ============================================================================

export const ReadinessDashboardWidget: React.FC<ReadinessDashboardWidgetProps> = ({
  flow_id,
  client_account_id,
  engagement_id,
  onCollectDataClick,
}) => {
  const { getAuthHeaders } = useAuth();
  const [expandedAssets, setExpandedAssets] = useState<Set<string>>(new Set());
  const [showAttributesReference, setShowAttributesReference] = useState(false);

  // ============================================================================
  // Data Fetching
  // ============================================================================

  const {
    data: readinessData,
    isLoading,
    isError,
    error,
  } = useQuery<AssessmentReadinessResponse>({
    queryKey: ['assessment-readiness', flow_id, client_account_id, engagement_id],
    queryFn: async () => {
      const headers = {
        ...getAuthHeaders(),
        'X-Client-Account-ID': client_account_id,
        ...(engagement_id && { 'X-Engagement-ID': engagement_id }), // Conditionally include
      };

      const response = await apiCall(`/master-flows/${flow_id}/assessment-readiness`, {
        method: 'GET',
        headers,
      });

      return response as AssessmentReadinessResponse;
    },
    enabled: !!flow_id && !!client_account_id, // engagement_id is optional
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refresh every minute
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

  // ============================================================================
  // Computed Values
  // ============================================================================

  const avgCompleteness = useMemo(() => {
    if (!readinessData) return 0;
    return Math.round(readinessData.readiness_summary.avg_completeness_score * 100);
  }, [readinessData]);

  const blockersAssets = useMemo(() => {
    if (!readinessData) return [];
    return readinessData.asset_details.filter((asset) => asset.assessment_blockers.length > 0);
  }, [readinessData]);

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

  if (!readinessData || readinessData.total_assets === 0) {
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

  const { readiness_summary } = readinessData;
  const allReady = readiness_summary.ready === readinessData.total_assets;

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Ready Assets"
          value={readiness_summary.ready}
          icon={<CheckCircle />}
          color="text-green-600"
          description={`${Math.round((readiness_summary.ready / readinessData.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="Not Ready Assets"
          value={readiness_summary.not_ready}
          icon={<AlertTriangle />}
          color="text-red-600"
          description={`${Math.round((readiness_summary.not_ready / readinessData.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="In Progress Assets"
          value={readiness_summary.in_progress}
          icon={<Clock />}
          color="text-yellow-600"
          description={`${Math.round((readiness_summary.in_progress / readinessData.total_assets) * 100)}% of total`}
        />
        <SummaryCard
          title="Avg Completeness"
          value={`${avgCompleteness}%`}
          icon={<FileText />}
          color={avgCompleteness >= 75 ? 'text-green-600' : avgCompleteness >= 50 ? 'text-yellow-600' : 'text-red-600'}
          description={`Across ${readinessData.total_assets} assets`}
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

      {/* Assessment Blockers */}
      {blockersAssets.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Assessment Blockers</h3>
              <p className="text-sm text-muted-foreground">{blockersAssets.length} assets need attention</p>
            </div>
            <div className="flex gap-2">
              {onCollectDataClick && (
                <Button onClick={onCollectDataClick} variant="default">
                  <ArrowRight className="h-4 w-4 mr-2" />
                  Collect Missing Data
                </Button>
              )}
              <Button onClick={handleExportReport} variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {blockersAssets.map((asset) => (
              <AssetBlockerAccordion
                key={asset.asset_id}
                asset={asset}
                isExpanded={expandedAssets.has(asset.asset_id)}
                onToggle={() => toggleAsset(asset.asset_id)}
              />
            ))}
          </div>
        </div>
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
