/**
 * Types for Agent Detail functionality
 * Extracted from AgentDetailPage.tsx for modularization
 */

export interface AgentDetailData {
  agentName: string;
  profile: {
    role: string;
    specialization: string;
    capabilities: string[];
    endpoints: string[];
    configuration: Record<string, any>;
  };
  performance: {
    successRate: number;
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    avgDuration: number;
    avgConfidence: number;
    memoryUsage: number;
    llmCalls: number;
    lastActive: string;
  };
  trends: {
    successRateHistory: number[];
    durationHistory: number[];
    confidenceHistory: number[];
    taskCountHistory: number[];
    memoryUsageHistory: number[];
    timestamps: string[];
  };
  taskHistory: {
    tasks: Array<{
      taskId: string;
      flowId: string;
      taskName: string;
      startedAt: string;
      completedAt: string;
      duration: number;
      status: 'completed' | 'failed' | 'timeout';
      success: boolean;
      confidenceScore: number;
      resultPreview: string;
      errorMessage?: string;
      llmCallsCount: number;
      tokenUsage: { inputTokens: number; outputTokens: number };
    }>;
    totalTasks: number;
    hasMore: boolean;
  };
  llmAnalytics: {
    totalTokens: number;
    avgTokensPerTask: number;
    tokenTrends: number[];
    costEstimate: number;
    topModelsUsed: Array<{ model: string; usage: number }>;
  };
}

export interface TaskHistoryRowProps {
  task: AgentDetailData['taskHistory']['tasks'][0];
  onViewDetails: (taskId: string) => void;
}

export interface PerformanceMetrics {
  efficiency: string;
  reliability: string;
  speed: string;
  confidence: string;
  trend: 'up' | 'down' | 'stable';
}

export interface AgentMetadataHelpers {
  getAgentRole: (name: string) => string;
  getAgentSpecialization: (name: string) => string;
  getAgentCapabilities: (name: string) => string[];
  getAgentEndpoints: (name: string) => string[];
}