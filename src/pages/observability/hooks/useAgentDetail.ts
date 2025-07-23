/**
 * Custom hook for Agent Detail data management
 * Extracted from AgentDetailPage.tsx for modularization
 */

import { useState } from 'react'
import { useEffect } from 'react'
import { agentObservabilityService } from '../../../services/api/agentObservabilityService';
import type { AgentDetailData } from '../types/AgentDetailTypes';
import { getAgentMetadataHelpers } from '../utils/agentMetadataHelpers';

interface UseAgentDetailResult {
  agentData: AgentDetailData | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  loadAgentData: () => Promise<void>;
  handleRefresh: () => Promise<void>;
}

export const useAgentDetail = (agentName: string | undefined, taskHistoryPage: number = 0): UseAgentDetailResult => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentData, setAgentData] = useState<AgentDetailData | null>(null);

  const { getAgentRole, getAgentSpecialization, getAgentCapabilities, getAgentEndpoints } = getAgentMetadataHelpers();

  const loadAgentData = async () => {
    if (!agentName) return;

    try {
      setLoading(true);
      setError(null);

      // Simulate comprehensive agent data loading
      // In a real implementation, this would call multiple API endpoints
      const [performance, analytics, taskHistory] = await Promise.all([
        agentObservabilityService.getAgentPerformance(agentName, 30),
        agentObservabilityService.getAgentAnalytics(agentName, 30),
        agentObservabilityService.getAgentTaskHistory(agentName, 20, taskHistoryPage * 20)
      ]);

      if (!performance.success || !analytics.success || !taskHistory.success) {
        throw new Error('Failed to load agent data');
      }

      // Transform the data into the detailed format
      const detailData: AgentDetailData = {
        agentName,
        profile: {
          role: getAgentRole(agentName),
          specialization: getAgentSpecialization(agentName),
          capabilities: getAgentCapabilities(agentName),
          endpoints: getAgentEndpoints(agentName),
          configuration: {}
        },
        performance: {
          successRate: performance.data.summary.success_rate,
          totalTasks: performance.data.summary.total_tasks,
          completedTasks: performance.data.summary.successful_tasks,
          failedTasks: performance.data.summary.failed_tasks,
          avgDuration: performance.data.summary.avg_duration_seconds,
          avgConfidence: performance.data.summary.avg_confidence_score,
          memoryUsage: analytics.data.analytics.resource_usage.avg_memory_usage_mb,
          llmCalls: performance.data.summary.total_llm_calls,
          lastActive: performance.data.current_status?.last_activity || 'Unknown'
        },
        trends: {
          successRateHistory: performance.data.trends.success_rates,
          durationHistory: performance.data.trends.avg_durations,
          confidenceHistory: Array.from({ length: 7 }, () => Math.random() * 0.2 + 0.8),
          taskCountHistory: performance.data.trends.task_counts,
          memoryUsageHistory: Array.from({ length: 7 }, () => Math.random() * 50 + 100),
          timestamps: performance.data.trends.dates
        },
        taskHistory: {
          tasks: taskHistory.data.tasks.map(task => ({
            taskId: task.task_id,
            flowId: task.flow_id,
            taskName: task.task_name,
            startedAt: task.started_at,
            completedAt: task.completed_at,
            duration: task.duration_seconds,
            status: task.status,
            success: task.success,
            confidenceScore: task.confidence_score,
            resultPreview: task.result_preview,
            errorMessage: task.error_message,
            llmCallsCount: task.llm_calls_count,
            tokenUsage: {
              inputTokens: task.token_usage?.input_tokens || 0,
              outputTokens: task.token_usage?.output_tokens || 0
            }
          })),
          totalTasks: taskHistory.data.total_tasks,
          hasMore: taskHistory.data.tasks.length === 20
        },
        llmAnalytics: {
          totalTokens: analytics.data.analytics.resource_usage.total_tokens_used,
          avgTokensPerTask: Math.round(analytics.data.analytics.resource_usage.total_tokens_used / performance.data.summary.total_tasks),
          tokenTrends: Array.from({ length: 7 }, () => Math.random() * 1000 + 500),
          costEstimate: (analytics.data.analytics.resource_usage.total_tokens_used * 0.00002), // Rough estimate
          topModelsUsed: [
            { model: 'claude-3-haiku', usage: 80 },
            { model: 'gpt-4o-mini', usage: 20 }
          ]
        }
      };

      setAgentData(detailData);
    } catch (err) {
      console.error('Failed to load agent data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load agent data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAgentData();
  };

  useEffect(() => {
    if (!agentName) {
      setError('Agent name is required');
      return;
    }

    loadAgentData();
  }, [agentName]);

  return {
    agentData,
    loading,
    refreshing,
    error,
    loadAgentData,
    handleRefresh
  };
};