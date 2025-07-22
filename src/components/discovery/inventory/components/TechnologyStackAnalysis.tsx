/**
 * TechnologyStackAnalysis Component
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Badge } from '../../../ui/badge';
import { ProcessedInsights } from '../types/InventoryInsightsTypes';

interface TechnologyStackAnalysisProps {
  analysis: ProcessedInsights['technology_analysis'];
}

export const TechnologyStackAnalysis: React.FC<TechnologyStackAnalysisProps> = ({ analysis }) => {
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  return (
    <div>
      <h4 className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-3">
        <BarChart3 className="h-4 w-4 text-indigo-500" />
        Technology Stack Analysis
      </h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Stack Diversity:</span>
          <Badge variant="outline" className="ml-2 capitalize">
            {analysis.stack_diversity}
          </Badge>
        </div>
        <div>
          <span className="text-gray-600">Integration Complexity:</span>
          <Badge 
            variant={getComplexityColor(analysis.integration_complexity) as unknown}
            className="ml-2 capitalize"
          >
            {analysis.integration_complexity}
          </Badge>
        </div>
      </div>
    </div>
  );
};