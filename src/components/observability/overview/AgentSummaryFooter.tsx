/**
 * Agent summary footer component extracted from ResponsiveAgentListOverview
 * Shows summary statistics and last updated time
 */

import React from 'react';
import { TrendingUp } from 'lucide-react';
import { Card, CardContent } from '../../ui/card';
import { cn } from '../../../lib/utils';

interface AgentSummaryFooterProps {
  displayedCount: number;
  filteredCount: number;
  totalCount: number;
  maxAgents?: number;
  activeCount: number;
  lastUpdated?: Date | null;
  isMobile?: boolean;
}

export const AgentSummaryFooter: React.FC<AgentSummaryFooterProps> = ({
  displayedCount,
  filteredCount,
  totalCount,
  maxAgents,
  activeCount,
  lastUpdated,
  isMobile = false
}) => {
  const uptimePercentage = totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0;

  return (
    <Card>
      <CardContent className="py-4">
        <div className={cn(
          'flex items-center justify-between text-sm text-gray-600',
          isMobile && 'flex-col space-y-2 items-start'
        )}>
          <span>
            Showing {displayedCount} of {filteredCount} agents
            {maxAgents && filteredCount > maxAgents && ` (${maxAgents} max)`}
          </span>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span>
                {uptimePercentage}% uptime
              </span>
            </div>

            {lastUpdated && (
              <div className="text-xs text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
