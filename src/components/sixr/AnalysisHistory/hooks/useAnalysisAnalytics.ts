import { useMemo } from 'react';
import { AnalysisHistoryItem, AnalyticsData } from '../types';

export const useAnalysisAnalytics = (analyses: AnalysisHistoryItem[]): AnalyticsData => {
  return useMemo(() => {
    const total = analyses.length;
    const completed = analyses.filter(a => a.status === 'completed').length;
    const completedRate = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    const avgConfidence = total > 0
      ? Math.round(analyses.reduce((sum, a) => sum + a.confidence_score, 0) / total)
      : 0;

    const strategyDistribution = analyses.reduce((acc, analysis) => {
      acc[analysis.recommended_strategy] = (acc[analysis.recommended_strategy] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const effortDistribution = analyses.reduce((acc, analysis) => {
      acc[analysis.estimated_effort] = (acc[analysis.estimated_effort] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const departmentDistribution = analyses.reduce((acc, analysis) => {
      acc[analysis.department] = (acc[analysis.department] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total,
      completedRate,
      avgConfidence,
      strategyDistribution,
      effortDistribution,
      departmentDistribution
    };
  }, [analyses]);
};