/**
 * Custom hook for Agent Metrics calculations
 * Extracted from AgentDetailPage.tsx for modularization
 */

import { useMemo } from 'react';
import type { AgentDetailData, PerformanceMetrics } from '../types/AgentDetailTypes';

interface UseAgentMetricsResult {
  performanceMetrics: PerformanceMetrics | null;
}

export const useAgentMetrics = (agentData: AgentDetailData | null): UseAgentMetricsResult => {
  // Performance metrics calculations
  const performanceMetrics = useMemo((): PerformanceMetrics | null => {
    if (!agentData) return null;

    const { performance, trends } = agentData;
    
    return {
      efficiency: (performance.successRate * 100).toFixed(1),
      reliability: performance.totalTasks > 0 ? 
        ((performance.totalTasks - performance.failedTasks) / performance.totalTasks * 100).toFixed(1) : '0',
      speed: performance.avgDuration.toFixed(1),
      confidence: (performance.avgConfidence * 100).toFixed(1),
      trend: trends.successRateHistory.length > 1 ? 
        (trends.successRateHistory[trends.successRateHistory.length - 1] > trends.successRateHistory[0] ? 'up' : 'down') : 'stable'
    };
  }, [agentData]);

  return {
    performanceMetrics
  };
};