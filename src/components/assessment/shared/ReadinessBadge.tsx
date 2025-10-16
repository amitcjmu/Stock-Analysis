/**
 * ReadinessBadge - Reusable readiness status badge component
 *
 * Phase 4: Assessment Architecture Enhancement
 *
 * Displays readiness status with color coding:
 * - Green (≥75%): Ready for automated 6R analysis
 * - Yellow (50-74%): Manual review required
 * - Red (<50%): Cannot proceed, data gaps exist
 *
 * Used across ApplicationGroupsWidget and ReadinessDashboardWidget for consistent visualization.
 *
 * @example
 * ```tsx
 * <ReadinessBadge readiness_summary={{ ready: 8, not_ready: 2, in_progress: 0, avg_completeness_score: 0.8 }} />
 * <ReadinessBadge readiness_summary={{ ready: 3, not_ready: 5, in_progress: 2, avg_completeness_score: 0.45 }} />
 * ```
 */

import React from 'react';
import { CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { ReadinessSummary } from '@/types/assessment';

export interface ReadinessBadgeProps {
  readiness_summary: ReadinessSummary;
  className?: string;
}

/**
 * Readiness Badge Component
 *
 * Calculates readiness percentage from summary and displays:
 * - Icon: CheckCircle (green), Clock (yellow), or AlertTriangle (red)
 * - Badge: Percentage with color variant
 * - Text: Count of ready assets vs. total
 *
 * Color thresholds based on 22 Critical Attributes framework:
 * - ≥75%: Default variant (green) - Ready
 * - 50-74%: Secondary variant (yellow) - In Progress
 * - <50%: Destructive variant (red) - Not Ready
 */
export const ReadinessBadge: React.FC<ReadinessBadgeProps> = ({ readiness_summary, className }) => {
  const total = readiness_summary.ready + readiness_summary.not_ready + readiness_summary.in_progress;
  const percentage = total > 0 ? Math.round((readiness_summary.ready / total) * 100) : 0;

  const variant = percentage >= 75 ? 'default' : percentage >= 50 ? 'secondary' : 'destructive';
  const color = percentage >= 75 ? 'text-green-600' : percentage >= 50 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className={`flex items-center gap-2 ${className || ''}`}>
      {percentage >= 75 && <CheckCircle className="h-4 w-4 text-green-600" />}
      {percentage >= 50 && percentage < 75 && <Clock className="h-4 w-4 text-yellow-600" />}
      {percentage < 50 && <AlertTriangle className="h-4 w-4 text-red-600" />}
      <Badge variant={variant}>
        <span className={color}>{percentage}% ready</span>
      </Badge>
      <span className="text-sm text-muted-foreground">
        ({readiness_summary.ready}/{total} assets)
      </span>
    </div>
  );
};

export default ReadinessBadge;
