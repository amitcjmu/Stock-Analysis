/**
 * SixRRecommendations Component
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import React from 'react';
import { GitBranch } from 'lucide-react';
import type { SixRRecommendationsProps } from '../types/InventoryInsightsTypes';

export const SixRRecommendations: React.FC<SixRRecommendationsProps> = ({ recommendations }) => {
  const getStrategyColor = (strategy: string): unknown => {
    switch (strategy) {
      case 'Rehost': return 'bg-blue-500';
      case 'Replatform': return 'bg-green-500';
      case 'Refactor': return 'bg-orange-500';
      case 'Rearchitect': return 'bg-purple-500';
      case 'Retire': return 'bg-gray-500';
      default: return 'bg-red-500';
    }
  };

  return (
    <div>
      <h4 className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-3">
        <GitBranch className="h-4 w-4 text-purple-500" />
        6R Strategy Recommendations
      </h4>
      <div className="space-y-2">
        {Object.entries(recommendations).map(([strategy, percentage]) => (
          <div key={strategy} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getStrategyColor(strategy)}`} />
              {strategy}
            </span>
            <span className="font-medium">{percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};
