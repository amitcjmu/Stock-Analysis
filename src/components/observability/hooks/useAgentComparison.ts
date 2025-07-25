/**
 * Hook for agent comparison functionality
 * Extracted from AgentComparison component
 */

import { useState } from 'react'
import { useEffect, useCallback, useMemo } from 'react'
import { agentObservabilityService } from '../../../services/api/agentObservabilityService';

export interface AgentComparisonData {
  agentName: string;
  metrics: {
    successRate: number;
    totalTasks: number;
    avgDuration: number;
    avgConfidence: number;
    memoryUsage: number;
    llmCalls: number;
    errorRate: number;
    throughput: number;
  };
  trends: {
    successRateHistory: number[];
    durationHistory: number[];
    confidenceHistory: number[];
    timestamps: string[];
  };
  ranking: {
    overall: number;
    successRate: number;
    performance: number;
    reliability: number;
  };
}

export interface UseAgentComparisonOptions {
  selectedAgents: string[];
  period?: number;
  autoRefresh?: boolean;
}

export const useAgentComparison = (options: UseAgentComparisonOptions) => {
  const { selectedAgents, period = 7, autoRefresh = false } = options;

  const [comparisonData, setComparisonData] = useState<AgentComparisonData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadComparisonData = useCallback(async () => {
    if (selectedAgents.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const agentDataPromises = selectedAgents.map(async (agentName) => {
        const [performance, analytics] = await Promise.all([
          agentObservabilityService.getAgentPerformance(agentName, period),
          agentObservabilityService.getAgentAnalytics(agentName, period)
        ]);

        if (!performance.success || !analytics.success) {
          throw new Error(`Failed to load data for ${agentName}`);
        }

        const perfData = performance.data;
        const analyticsData = analytics.data;

        const errorRate = perfData.summary.total_tasks > 0 ?
          perfData.summary.failed_tasks / perfData.summary.total_tasks : 0;

        const throughput = perfData.summary.total_tasks / (period * 24);

        return {
          agentName,
          metrics: {
            successRate: perfData.summary.success_rate,
            totalTasks: perfData.summary.total_tasks,
            avgDuration: perfData.summary.avg_duration_seconds,
            avgConfidence: perfData.summary.avg_confidence_score,
            memoryUsage: analyticsData.analytics.resource_usage.avg_memory_usage_mb,
            llmCalls: perfData.summary.total_llm_calls,
            errorRate,
            throughput
          },
          trends: {
            successRateHistory: perfData.trends.success_rates,
            durationHistory: perfData.trends.avg_durations,
            confidenceHistory: perfData.trends.confidence_scores || Array(perfData.trends.success_rates.length).fill(0),
            timestamps: perfData.trends.dates
          },
          ranking: {
            overall: 0,
            successRate: 0,
            performance: 0,
            reliability: 0
          }
        } as AgentComparisonData;
      });

      const agentData = await Promise.all(agentDataPromises);
      const dataWithRankings = calculateRankings(agentData);

      setComparisonData(dataWithRankings);
    } catch (err) {
      console.error('Failed to load comparison data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  }, [selectedAgents, period]);

  const calculateRankings = (data: AgentComparisonData[]): AgentComparisonData[] => {
    const scoredData = data.map(agent => {
      const performanceScore =
        (agent.metrics.successRate * 0.3) +
        ((1 - agent.metrics.errorRate) * 0.2) +
        (agent.metrics.avgConfidence * 0.2) +
        (Math.min(agent.metrics.throughput / 10, 1) * 0.15) +
        (Math.max(0, 1 - agent.metrics.avgDuration / 60) * 0.15);

      return { ...agent, performanceScore };
    });

    scoredData.sort((a, b) => b.performanceScore - a.performanceScore);

    return scoredData.map((agent, index) => ({
      ...agent,
      ranking: {
        overall: index + 1,
        successRate: getRankByMetric(data, 'successRate', agent.agentName, true),
        performance: getRankByMetric(data, 'avgDuration', agent.agentName, false),
        reliability: getRankByMetric(data, 'errorRate', agent.agentName, false)
      }
    }));
  };

  const getRankByMetric = (
    data: AgentComparisonData[],
    metric: keyof AgentComparisonData['metrics'],
    agentName: string,
    higherIsBetter: boolean
  ): number => {
    const sorted = [...data].sort((a, b) =>
      higherIsBetter ? b.metrics[metric] - a.metrics[metric] : a.metrics[metric] - b.metrics[metric]
    );
    return sorted.findIndex(agent => agent.agentName === agentName) + 1;
  };

  useEffect(() => {
    loadComparisonData();
  }, [loadComparisonData]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadComparisonData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, loadComparisonData]);

  return {
    comparisonData,
    loading,
    error,
    refresh: loadComparisonData
  };
};
