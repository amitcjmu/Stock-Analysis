/**
 * Agent Observability Service
 * API service layer for agent observability dashboard
 * Part of the Agent Observability Enhancement Phase 4A
 */

import { apiCall } from '../../config/api';
import type {
  AgentPerformanceResponse,
  AgentTaskHistoryResponse,
  AgentAnalyticsResponse,
  AgentActivityFeedResponse,
  AllAgentsSummaryResponse,
  EnhancedMonitoringStatus,
  AgentCardData,
  AgentMetricsData
} from '../../types/api/observability/agent-performance';

export class AgentObservabilityService {
  constructor() {
    // Using the main API client with multi-tenant header support
  }

  /**
   * Get performance metrics for a specific agent
   */
  async getAgentPerformance(agentName: string, periodDays: number = 7): Promise<AgentPerformanceResponse> {
    const endpoint = `/monitoring/agents/${encodeURIComponent(agentName)}/performance`;
    const params = new URLSearchParams({ period_days: periodDays.toString() });
    
    return apiCall(`${endpoint}?${params}`, { method: 'GET' });
  }

  /**
   * Get task history for a specific agent
   */
  async getAgentTaskHistory(
    agentName: string, 
    limit: number = 10, 
    offset: number = 0
  ): Promise<AgentTaskHistoryResponse> {
    const endpoint = `/monitoring/agents/${encodeURIComponent(agentName)}/history`;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    return apiCall(`${endpoint}?${params}`, { method: 'GET' });
  }

  /**
   * Get detailed analytics for a specific agent
   */
  async getAgentAnalytics(agentName: string, periodDays: number = 7): Promise<AgentAnalyticsResponse> {
    const endpoint = `/monitoring/agents/${encodeURIComponent(agentName)}/analytics`;
    const params = new URLSearchParams({ period_days: periodDays.toString() });
    
    return apiCall(`${endpoint}?${params}`, { method: 'GET' });
  }

  /**
   * Get real-time agent activity feed
   */
  async getAgentActivityFeed(
    agentName?: string,
    includeCompleted: boolean = false,
    limit: number = 50
  ): Promise<AgentActivityFeedResponse> {
    // Use the existing /monitoring/tasks endpoint for activity feed
    const endpoint = '/monitoring/tasks';
    const params = new URLSearchParams({
      include_performance_data: includeCompleted.toString(),
      limit: limit.toString()
    });
    
    if (agentName) {
      params.append('agent_id', agentName);
    }
    
    return apiCall(`${endpoint}?${params}`, { method: 'GET' });
  }

  /**
   * Get summary of all agents
   */
  async getAllAgentsSummary(periodDays: number = 7): Promise<AllAgentsSummaryResponse> {
    // Use the existing /monitoring/agents endpoint instead of /monitoring/agents/summary
    const endpoint = '/monitoring/agents';
    
    return apiCall(endpoint, { method: 'GET' });
  }

  /**
   * Get enhanced monitoring status with individual agent data
   */
  async getEnhancedMonitoringStatus(): Promise<EnhancedMonitoringStatus> {
    const endpoint = '/monitoring/status';
    return apiCall(endpoint, { method: 'GET' });
  }

  /**
   * Transform API response to UI-friendly agent card data
   */
  transformToAgentCardData(response: unknown): AgentCardData[] {
    if (!response.success || !response.agents_by_phase) {
      return [];
    }

    const agents: AgentCardData[] = [];
    
    // Iterate through all phases and extract agent data
    for (const [phaseName, phaseData] of Object.entries(response.agents_by_phase)) {
      if (phaseData && typeof phaseData === 'object' && 'agents' in phaseData) {
        const phaseAgents = (phaseData as unknown).agents;
        
        phaseAgents.forEach((agent: unknown) => {
          agents.push({
            id: agent.agent_id || agent.name,
            name: agent.name,
            status: agent.status?.current_status || 'unknown',
            lastActive: agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleDateString() : 'Unknown',
            successRate: this.parseSuccessRate(agent.performance?.success_rate),
            totalTasks: this.parseTaskCount(agent.performance?.tasks_completed),
            avgDuration: this.parseAvgDuration(agent.performance?.avg_execution_time),
            isOnline: agent.status?.current_status === 'active'
          });
        });
      }
    }

    return agents;
  }

  /**
   * Parse success rate from different formats
   */
  private parseSuccessRate(successRate: unknown): number {
    if (typeof successRate === 'number') {
      return successRate;
    }
    if (typeof successRate === 'string') {
      // Handle percentage strings like "85.0%" or "N/A"
      if (successRate === 'N/A') return 0;
      const match = successRate.match(/(\d+\.?\d*)/);
      if (match) {
        const value = parseFloat(match[1]);
        return successRate.includes('%') ? value / 100 : value;
      }
    }
    return 0;
  }

  /**
   * Parse task count from different formats
   */
  private parseTaskCount(taskCount: unknown): number {
    if (typeof taskCount === 'number') {
      return taskCount;
    }
    if (typeof taskCount === 'string') {
      // Handle "N/A" or numeric strings
      if (taskCount === 'N/A') return 0;
      const parsed = parseInt(taskCount, 10);
      return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
  }

  /**
   * Parse average duration from different formats
   */
  private parseAvgDuration(avgDuration: unknown): number {
    if (typeof avgDuration === 'number') {
      return avgDuration;
    }
    if (typeof avgDuration === 'string') {
      // Handle duration strings like "5.2s" or "N/A"
      if (avgDuration === 'N/A') return 0;
      const match = avgDuration.match(/(\d+\.?\d*)/);
      if (match) {
        return parseFloat(match[1]);
      }
    }
    return 0;
  }

  /**
   * Transform performance data to metrics format
   */
  async transformToAgentMetricsData(agentName: string): Promise<AgentMetricsData | null> {
    try {
      const [performance, analytics] = await Promise.all([
        this.getAgentPerformance(agentName),
        this.getAgentAnalytics(agentName)
      ]);

      if (!performance.success || !analytics.success) {
        return null;
      }

      const perfData = performance.data;
      const analyticsData = analytics.data;

      return {
        agentName,
        metrics: {
          successRate: perfData.summary.success_rate,
          totalTasks: perfData.summary.total_tasks,
          completedTasks: perfData.summary.successful_tasks,
          failedTasks: perfData.summary.failed_tasks,
          avgDuration: perfData.summary.avg_duration_seconds,
          lastActive: perfData.current_status?.last_activity || 'Unknown',
          confidence: perfData.summary.avg_confidence_score,
          memoryUsage: analyticsData.analytics.resource_usage.avg_memory_usage_mb,
          llmCalls: perfData.summary.total_llm_calls
        },
        trends: {
          successRateHistory: perfData.trends.success_rates,
          durationHistory: perfData.trends.avg_durations,
          taskCountHistory: perfData.trends.task_counts,
          timestamps: perfData.trends.dates
        },
        status: {
          current: perfData.current_status?.is_active ? 'active' : 'idle',
          isHealthy: perfData.summary.success_rate > 0.8, // Basic health check
          lastHealthCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error(`Failed to transform metrics data for agent ${agentName}:`, error);
      return null;
    }
  }

  /**
   * Check if an agent is currently active
   */
  async isAgentActive(agentName: string): Promise<boolean> {
    try {
      const performance = await this.getAgentPerformance(agentName, 1);
      return performance.success && 
             performance.data.current_status?.is_active === true;
    } catch (error) {
      console.error(`Failed to check agent status for ${agentName}:`, error);
      return false;
    }
  }

  /**
   * Get agent names list from monitoring status
   */
  async getAgentNames(): Promise<string[]> {
    try {
      const summary = await this.getAllAgentsSummary();
      if (summary.success && summary.data?.agents) {
        return summary.data.agents.map(agent => agent.agent_name);
      }
      return [];
    } catch (error) {
      console.error('Failed to get agent names:', error);
      return [];
    }
  }

  /**
   * Bulk fetch agent data for dashboard
   */
  async getBulkAgentData(agentNames: string[]): Promise<AgentCardData[]> {
    try {
      const summary = await this.getAllAgentsSummary();
      return this.transformToAgentCardData(summary);
    } catch (error) {
      console.error('Failed to get bulk agent data:', error);
      return [];
    }
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<boolean> {
    try {
      const status = await this.getEnhancedMonitoringStatus();
      return status.success;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const agentObservabilityService = new AgentObservabilityService();