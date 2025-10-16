/**
 * AssetBlockerAccordion - Collapsible asset blocker details component
 *
 * Phase 4: Assessment Architecture Enhancement
 *
 * Displays assessment blockers for a single asset with:
 * - Asset name, type, and readiness percentage
 * - Collapsible section showing missing attributes by category
 * - Color-coded severity (required vs. recommended)
 * - Progress bar visualization
 */

import React from 'react';
import { CheckCircle, Clock, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { AssetTypeIcon } from './AssetTypeIcon';
import { type AssetReadinessDetail, CRITICAL_ATTRIBUTES, getReadinessPercentage } from '@/types/assessment';

export interface AssetBlockerAccordionProps {
  asset: AssetReadinessDetail;
  isExpanded: boolean;
  onToggle: () => void;
}

export const AssetBlockerAccordion: React.FC<AssetBlockerAccordionProps> = ({ asset, isExpanded, onToggle }) => {
  const percentage = getReadinessPercentage(asset.assessment_readiness_score);
  const statusIcon =
    percentage >= 75 ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : percentage >= 50 ? (
      <Clock className="h-4 w-4 text-yellow-600" />
    ) : (
      <AlertTriangle className="h-4 w-4 text-red-600" />
    );

  const categories = [
    { key: 'infrastructure', label: 'Infrastructure', color: 'text-blue-600' },
    { key: 'application', label: 'Application', color: 'text-purple-600' },
    { key: 'business', label: 'Business', color: 'text-green-600' },
    { key: 'technical_debt', label: 'Technical Debt', color: 'text-orange-600' },
  ] as const;

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
                <AssetTypeIcon type={asset.asset_type} className="text-muted-foreground" />
                <div className="flex-1 text-left">
                  <CardTitle className="text-lg">{asset.asset_name}</CardTitle>
                  <CardDescription className="mt-1">
                    {asset.assessment_blockers.length} missing attributes
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {statusIcon}
                <span className="text-sm font-medium">{percentage}%</span>
              </div>
            </div>
          </CollapsibleTrigger>
        </CardHeader>

        <CollapsibleContent>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Progress value={percentage} className="h-2" />
              </div>

              {categories.map(({ key, label, color }) => {
                const missing = asset.missing_attributes[key as keyof typeof asset.missing_attributes];
                if (missing.length === 0) return null;

                return (
                  <div key={key} className="space-y-2">
                    <h4 className={cn('text-sm font-semibold', color)}>{label}</h4>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {missing.map((attr) => {
                        const attributeDef = CRITICAL_ATTRIBUTES.find((a) => a.name === attr);
                        return (
                          <li key={attr} className="flex items-start gap-2 text-sm">
                            <AlertTriangle
                              className={cn(
                                'h-4 w-4 flex-shrink-0 mt-0.5',
                                attributeDef?.required ? 'text-red-500' : 'text-yellow-500'
                              )}
                            />
                            <div className="flex-1">
                              <span className="font-medium">{attr.replace(/_/g, ' ')}</span>
                              {attributeDef?.required && (
                                <Badge variant="destructive" className="ml-2 text-xs">
                                  Required
                                </Badge>
                              )}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

export default AssetBlockerAccordion;
