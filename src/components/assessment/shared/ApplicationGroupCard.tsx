/**
 * ApplicationGroupCard - Individual application group card with assets
 *
 * Phase 4 Days 17-18: Assessment Architecture Enhancement
 * Updated December 2025: Enhanced with asset names and readiness status
 *
 * Features:
 * - Collapsible card showing application and its assets
 * - Readiness indicators with progress bar
 * - Individual asset readiness status (ready/blocked)
 * - Asset type icons
 * - Click handling for asset navigation
 */

import React from 'react';
import {
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  FileSearch,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { AssetTypeIcon } from './AssetTypeIcon';
import { ReadinessBadge } from './ReadinessBadge';
import type { ApplicationAssetGroup } from '@/types/assessment';

export interface ApplicationGroupCardProps {
  group: ApplicationAssetGroup;
  isExpanded: boolean;
  onToggle: () => void;
  onAssetClick?: (asset_id: string) => void;
  onCollectData?: (application_id: string | null, asset_ids: string[]) => void;
}

export const ApplicationGroupCard: React.FC<ApplicationGroupCardProps> = ({
  group,
  isExpanded,
  onToggle,
  onAssetClick,
  onCollectData,
}) => {
  const isUnmapped = group.canonical_application_id === null;

  // Calculate readiness percentage for progress bar
  const total = (group.readiness_summary?.ready || 0) +
                (group.readiness_summary?.not_ready || 0) +
                (group.readiness_summary?.in_progress || 0);
  const readinessPercentage = total > 0
    ? Math.round((group.readiness_summary?.ready || 0) / total * 100)
    : 0;

  // Determine progress bar color based on readiness
  const progressColor = readinessPercentage === 100
    ? 'bg-green-500'
    : readinessPercentage >= 50
      ? 'bg-yellow-500'
      : 'bg-red-500';

  // Get asset readiness icon
  const getAssetReadinessIcon = (readiness: string) => {
    switch (readiness) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-yellow-600 flex-shrink-0" />;
      default:
        return <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />;
    }
  };

  return (
    <Card className="transition-shadow hover:shadow-md">
      <Collapsible open={isExpanded} onOpenChange={onToggle}>
        <CardHeader className="pb-3">
          <CollapsibleTrigger className="w-full">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 flex-1">
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                )}
                <div className="flex-1 text-left">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {group.canonical_application_name}
                    {isUnmapped && (
                      <Badge variant="secondary" className="text-xs">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Unmapped
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1 flex items-center gap-3 flex-wrap">
                    {group.asset_types && group.asset_types.length > 0 && (
                      <span className="flex items-center gap-1">
                        {group.asset_types.map((type, idx) => (
                          <React.Fragment key={type}>
                            <AssetTypeIcon type={type} className="text-muted-foreground" />
                            {idx < group.asset_types.length - 1 && <span className="text-xs">,</span>}
                          </React.Fragment>
                        ))}
                      </span>
                    )}
                  </CardDescription>
                </div>
              </div>
              <div className="flex-shrink-0">
                <ReadinessBadge readiness_summary={group.readiness_summary} />
              </div>
            </div>
          </CollapsibleTrigger>

          {/* Progress bar showing readiness at a glance */}
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{group.readiness_summary?.ready || 0} ready</span>
              <span>{group.readiness_summary?.not_ready || 0} blocked</span>
            </div>
            <Progress value={readinessPercentage} className={cn("h-2", progressColor)} />
          </div>

          {/* Collect Missing Data button - shows when there are blocked assets */}
          {(group.readiness_summary?.not_ready || 0) > 0 && onCollectData && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3 w-full text-blue-600 border-blue-300 hover:bg-blue-50 dark:text-blue-400 dark:border-blue-600 dark:hover:bg-blue-950"
              onClick={(e) => {
                e.stopPropagation(); // Prevent triggering collapse toggle
                // Filter for assets that explicitly need data collection
                const nonReadyAssetIds = (group.assets || [])
                  .filter(
                    (a) =>
                      a.assessment_readiness === 'not_ready' ||
                      a.assessment_readiness === 'in_progress'
                  )
                  .map((a) => a.asset_id);
                onCollectData(
                  group.canonical_application_id?.toString() || null,
                  nonReadyAssetIds
                );
              }}
            >
              <FileSearch className="h-4 w-4 mr-2" />
              Collect Missing Data ({group.readiness_summary?.not_ready || 0} assets)
            </Button>
          )}
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">
                Assets ({group.asset_count}):
              </h4>
              <div className="space-y-2">
                {/* Use detailed assets if available, fallback to asset_ids */}
                {group.assets && group.assets.length > 0 ? (
                  group.assets.map((asset) => (
                    <div
                      key={asset.asset_id}
                      className={cn(
                        'flex items-center gap-3 p-3 rounded-md border transition-colors',
                        asset.assessment_readiness === 'ready'
                          ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                          : asset.assessment_readiness === 'in_progress'
                            ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800'
                            : 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800',
                        onAssetClick && 'cursor-pointer hover:shadow-sm'
                      )}
                      onClick={() => onAssetClick?.(asset.asset_id)}
                      role={onAssetClick ? 'button' : undefined}
                      tabIndex={onAssetClick ? 0 : undefined}
                      onKeyDown={(e) => {
                        if (onAssetClick && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault();
                          onAssetClick(asset.asset_id);
                        }
                      }}
                      aria-label={`Asset ${asset.asset_name}`}
                    >
                      {getAssetReadinessIcon(asset.assessment_readiness)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium truncate">
                            {asset.asset_name}
                          </span>
                          {asset.asset_type && (
                            <Badge variant="outline" className="text-xs">
                              {asset.asset_type}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={cn(
                            'text-xs',
                            asset.assessment_readiness === 'ready'
                              ? 'text-green-700 dark:text-green-300'
                              : asset.assessment_readiness === 'in_progress'
                                ? 'text-yellow-700 dark:text-yellow-300'
                                : 'text-red-700 dark:text-red-300'
                          )}>
                            {asset.assessment_readiness === 'ready'
                              ? 'Ready for assessment'
                              : asset.assessment_readiness === 'in_progress'
                                ? 'Data collection in progress'
                                : 'Needs data collection'}
                          </span>
                        </div>
                      </div>
                      {asset.assessment_readiness_score !== undefined && (
                        <div className="text-xs text-muted-foreground">
                          {Math.round((asset.assessment_readiness_score || 0) * 100)}%
                        </div>
                      )}
                    </div>
                  ))
                ) : group.asset_ids && group.asset_ids.length > 0 ? (
                  // Fallback to showing asset IDs if no detailed info
                  group.asset_ids.map((asset_id) => (
                    <div
                      key={asset_id}
                      className={cn(
                        'flex items-center gap-2 p-2 rounded-md border bg-card transition-colors',
                        onAssetClick && 'cursor-pointer hover:bg-accent hover:border-accent-foreground/20'
                      )}
                      onClick={() => onAssetClick?.(asset_id)}
                      role={onAssetClick ? 'button' : undefined}
                      tabIndex={onAssetClick ? 0 : undefined}
                      onKeyDown={(e) => {
                        if (onAssetClick && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault();
                          onAssetClick(asset_id);
                        }
                      }}
                      aria-label={`Asset ${asset_id.substring(0, 8)}`}
                    >
                      <Package className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-sm font-mono truncate">{asset_id.substring(0, 8)}...</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No assets in this group</p>
                )}
              </div>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

export default ApplicationGroupCard;
