/**
 * Correlation Heatmap Component
 * Visualizes correlations between different metrics
 */

import React from 'react';
import { AnalyticsData } from '../types';

interface CorrelationHeatmapProps {
  correlationMatrix: AnalyticsData['correlationMatrix'];
}

const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({ correlationMatrix }) => {
  const metrics = Object.keys(correlationMatrix);
  
  const getCorrelationColor = (value: number): string => {
    const intensity = Math.abs(value);
    if (value > 0) {
      return `rgba(34, 197, 94, ${intensity})`; // Green for positive correlation
    } else {
      return `rgba(239, 68, 68, ${intensity})`; // Red for negative correlation
    }
  };

  return (
    <div className="grid grid-cols-5 gap-1 p-4">
      {metrics.map((metric1) =>
        metrics.map((metric2) => {
          const correlation = correlationMatrix[metric1]?.[metric2] || 0;
          return (
            <div
              key={`${metric1}-${metric2}`}
              className="aspect-square flex items-center justify-center text-xs font-medium text-white rounded"
              style={{ backgroundColor: getCorrelationColor(correlation) }}
              title={`${metric1} vs ${metric2}: ${correlation.toFixed(2)}`}
            >
              {correlation.toFixed(1)}
            </div>
          );
        })
      )}
    </div>
  );
};

export default CorrelationHeatmap;