import { useMemo } from 'react';
import type { FlowSummary, SystemMetrics } from '../types';

export interface FlowMetrics {
  totalFlows: number;
  runningFlows: number;
  completedFlows: number;
  failedFlows: number;
  pausedFlows: number;
  successRate: number;
  averageProgress: number;
  mostActivePhase: string;
  totalAgents: number;
  estimatedCompletionTime: string;
}

export const useFlowMetrics = (
  flows: FlowSummary[] | undefined,
  systemMetrics: SystemMetrics | null
): FlowMetrics => {

  return useMemo(() => {
    // Defensive check: Handle undefined/null flows
    if (!flows || !Array.isArray(flows) || !flows.length) {
      return {
        totalFlows: 0,
        runningFlows: 0,
        completedFlows: 0,
        failedFlows: 0,
        pausedFlows: 0,
        successRate: 0,
        averageProgress: 0,
        mostActivePhase: 'N/A',
        totalAgents: 0,
        estimatedCompletionTime: 'N/A'
      };
    }

    const runningFlows = flows.filter(f => f.status === 'running' || f.status === 'active');
    const completedFlows = flows.filter(f => f.status === 'completed');
    const failedFlows = flows.filter(f => f.status === 'failed');
    const pausedFlows = flows.filter(f => f.status === 'paused');

    // Calculate success rate
    const successRate = flows.length > 0 ? completedFlows.length / flows.length : 0;

    // Calculate average progress
    const totalProgress = flows.reduce((sum, flow) => sum + flow.progress, 0);
    const averageProgress = totalProgress / flows.length;

    // Find most active phase
    const phaseCount = flows.reduce((acc, flow) => {
      acc[flow.current_phase] = (acc[flow.current_phase] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const mostActivePhase = Object.entries(phaseCount)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';

    // Calculate total active agents
    const totalAgents = runningFlows.reduce((sum, flow) => sum + flow.active_agents, 0);

    // Estimate completion time based on running flows
    const runningFlowsWithEstimates = runningFlows.filter(f => f.estimated_completion);
    let estimatedCompletionTime = 'N/A';

    if (runningFlowsWithEstimates.length > 0) {
      const avgCompletion = systemMetrics?.avg_completion_time_hours || 3.2;
      estimatedCompletionTime = `~${avgCompletion.toFixed(1)}h`;
    }

    return {
      totalFlows: flows.length,
      runningFlows: runningFlows.length,
      completedFlows: completedFlows.length,
      failedFlows: failedFlows.length,
      pausedFlows: pausedFlows.length,
      successRate,
      averageProgress,
      mostActivePhase,
      totalAgents,
      estimatedCompletionTime
    };
  }, [flows, systemMetrics]);
};
