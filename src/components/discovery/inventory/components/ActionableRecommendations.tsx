/**
 * ActionableRecommendations Component
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import React from 'react';
import { Target, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { ActionableRecommendationsProps } from '../types/InventoryInsightsTypes';

export const ActionableRecommendations: React.FC<ActionableRecommendationsProps> = ({ recommendations }) => {
  return (
    <div>
      <h4 className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-3">
        <Target className="h-4 w-4 text-emerald-500" />
        Actionable Recommendations
      </h4>
      
      <div className="space-y-4">
        {recommendations.immediate_actions.length > 0 && (
          <div>
            <h5 className="text-sm font-medium text-red-700 mb-2">Immediate Actions</h5>
            <ul className="space-y-1">
              {recommendations.immediate_actions.slice(0, 3).map((action, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <AlertTriangle className="h-3 w-3 text-red-500 mt-0.5 flex-shrink-0" />
                  {action}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendations.quick_wins.length > 0 && (
          <div>
            <h5 className="text-sm font-medium text-green-700 mb-2">Quick Wins</h5>
            <ul className="space-y-1">
              {recommendations.quick_wins.slice(0, 3).map((win, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                  {win}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendations.strategic_initiatives.length > 0 && (
          <div>
            <h5 className="text-sm font-medium text-blue-700 mb-2">Strategic Initiatives</h5>
            <ul className="space-y-1">
              {recommendations.strategic_initiatives.slice(0, 2).map((initiative, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <TrendingUp className="h-3 w-3 text-blue-500 mt-0.5 flex-shrink-0" />
                  {initiative}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};