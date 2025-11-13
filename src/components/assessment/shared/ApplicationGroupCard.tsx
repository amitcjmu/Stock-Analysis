/**
 * ApplicationGroupCard - Individual application group card with assets
 *
 * Phase 4 Days 17-18: Assessment Architecture Enhancement
 *
 * Features:
 * - Collapsible card showing application and its assets
 * - Readiness indicators
 * - Asset type icons
 * - Click handling for asset navigation
 */

import React from 'react';
import {
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Package,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
}

export const ApplicationGroupCard: React.FC<ApplicationGroupCardProps> = ({
  group,
  isExpanded,
  onToggle,
  onAssetClick,
}) => {
  const isUnmapped = group.canonical_application_id === null;

  return (
    <Card className="transition-shadow hover:shadow-md">
      <Collapsible open={isExpanded} onOpenChange={onToggle}>
        <CardHeader>
          <CollapsibleTrigger className="w-full">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 flex-1">
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                )}
                <div className="flex-1 text-left">
                  <CardTitle className="text-xl flex items-center gap-2">
                    {group.canonical_application_name}
                    {isUnmapped && (
                      <Badge variant="secondary">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Unmapped
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1 flex items-center gap-3 flex-wrap">
                    <span>{group.asset_count} assets</span>
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
        </CardHeader>

        <CollapsibleContent>
          <CardContent>
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-muted-foreground mb-3">Assets in this group:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {group.asset_ids && group.asset_ids.length > 0 ? (
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
