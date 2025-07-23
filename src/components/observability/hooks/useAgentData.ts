/**
 * Shared hook for fetching and managing agent data
 * Extracted from observability components for reuse
 */

import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { agentObservabilityService } from '../../../services/api/agentObservabilityService';
import type { AgentCardData, AgentMetricsData } from '../../../types/api/observability/agent-performance';

export interface UseAgentDataOptions {
  agentName?: string;
  period?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface UseAgentDataReturn {
  agents: AgentCardData[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: Date | null;
}

export const useAgentData = (options: UseAgentDataOptions = {}): UseAgentDataReturn => {
  const { agentName, period = 7, autoRefresh = false, refreshInterval = 30000 } = options;
  
  const [agents, setAgents] = useState<AgentCardData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (agentName) {
        // Fetch specific agent data
        const [performance, analytics] = await Promise.all([
          agentObservabilityService.getAgentPerformance(agentName, period),
          agentObservabilityService.getAgentAnalytics(agentName, period)
        ]);

        if (performance.success && analytics.success) {
          // Transform to AgentCardData format
          const agentCard: AgentCardData = {
            id: agentName,
            name: agentName,
            status: 'active', // Would need to determine from data
            successRate: performance.data.summary.success_rate,
            totalTasks: performance.data.summary.total_tasks,
            avgDuration: performance.data.summary.avg_duration_seconds,
            lastActive: new Date().toISOString(),
            confidence: performance.data.summary.avg_confidence_score,
            metrics: {
              cpu: 0, // Not available in current API
              memory: analytics.data.analytics.resource_usage.avg_memory_usage_mb,
              latency: performance.data.summary.avg_duration_seconds * 1000
            }
          };
          setAgents([agentCard]);
        }
      } else {
        // Fetch all agents
        const summary = await agentObservabilityService.getAllAgentsSummary();
        const agentCards = agentObservabilityService.transformToAgentCardData(summary);
        setAgents(agentCards);
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch agent data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch agent data');
    } finally {
      setLoading(false);
    }
  }, [agentName, period]);

  // Initial fetch
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchAgents, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchAgents]);

  return {
    agents,
    loading,
    error,
    refresh: fetchAgents,
    lastUpdated
  };
};

export const useAgentPerformance = (agentName: string, period: number = 7) => {
  const [data, setData] = useState<AgentMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPerformance = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await agentObservabilityService.getAgentPerformance(agentName, period);
      
      if (response.success) {
        setData(response.data);
      } else {
        throw new Error('Failed to fetch performance data');
      }
    } catch (err) {
      console.error('Failed to fetch agent performance:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch performance data');
    } finally {
      setLoading(false);
    }
  }, [agentName, period]);

  useEffect(() => {
    if (agentName) {
      fetchPerformance();
    }
  }, [agentName, fetchPerformance]);

  return { data, loading, error, refresh: fetchPerformance };
};

export const useAgentAnalytics = (agentName: string, period: number = 7) => {
  const [data, setData] = useState<AgentMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await agentObservabilityService.getAgentAnalytics(agentName, period);
      
      if (response.success) {
        setData(response.data);
      } else {
        throw new Error('Failed to fetch analytics data');
      }
    } catch (err) {
      console.error('Failed to fetch agent analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics data');
    } finally {
      setLoading(false);
    }
  }, [agentName, period]);

  useEffect(() => {
    if (agentName) {
      fetchAnalytics();
    }
  }, [agentName, fetchAnalytics]);

  return { data, loading, error, refresh: fetchAnalytics };
};