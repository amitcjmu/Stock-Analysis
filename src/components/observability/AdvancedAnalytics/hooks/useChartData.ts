/**
 * Custom Hook for Chart Data Transformation
 * Handles data transformation for chart visualization
 */

import { useMemo } from 'react';
import { AnalyticsData } from '../types';

interface UseChartDataProps {
  analyticsData: AnalyticsData | null;
  agentNames: string[];
  selectedMetrics: string[];
}

export const useChartData = ({ 
  analyticsData, 
  agentNames, 
  selectedMetrics 
}: UseChartDataProps) => {
  const chartData = useMemo(() => {
    if (!analyticsData?.timeSeriesData) return [];
    
    // Limit data points to prevent performance issues
    const maxDataPoints = 100;
    const data = analyticsData.timeSeriesData.length > maxDataPoints 
      ? analyticsData.timeSeriesData.slice(-maxDataPoints) 
      : analyticsData.timeSeriesData;
    
    return data.map(item => {
      const transformed: Record<string, string | number> = { timestamp: item.timestamp };
      
      agentNames.forEach(agent => {
        selectedMetrics.forEach(metric => {
          const key = `${agent}_${metric}`;
          if (item[key] !== undefined) {
            transformed[`${agent}_${metric}`] = item[key];
          }
        });
      });
      
      return transformed;
    });
  }, [analyticsData?.timeSeriesData, agentNames, selectedMetrics]);

  return chartData;
};