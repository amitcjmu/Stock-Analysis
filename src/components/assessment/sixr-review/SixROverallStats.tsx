import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { SIX_R_STRATEGIES } from '@/utils/assessment/sixrHelpers';

interface SixRStatistics {
  totalApps: number;
  assessed: number;
  avgConfidence: number;
  needsReview: number;
  hasIssues: number;
  strategyCount: Record<string, number>;
}

interface SixROverallStatsProps {
  statistics: SixRStatistics;
}

export const SixROverallStats: React.FC<SixROverallStatsProps> = ({ statistics }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>6R Strategy Overview</span>
        </CardTitle>
        <CardDescription>
          Summary of modernization strategies across all applications
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {statistics.assessed}/{statistics.totalApps}
            </div>
            <div className="text-sm text-gray-600">Applications Assessed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {Math.round(statistics.avgConfidence * 100)}%
            </div>
            <div className="text-sm text-gray-600">Avg Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{statistics.needsReview}</div>
            <div className="text-sm text-gray-600">Need Review</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{statistics.hasIssues}</div>
            <div className="text-sm text-gray-600">Have Issues</div>
          </div>
        </div>

        {/* Strategy Distribution */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Strategy Distribution</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {SIX_R_STRATEGIES.map(strategy => (
              <div key={strategy.value} className={cn("p-2 rounded-lg border", strategy.color)}>
                <div className="font-semibold">{statistics.strategyCount[strategy.value] || 0}</div>
                <div className="text-xs">{strategy.label}</div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};