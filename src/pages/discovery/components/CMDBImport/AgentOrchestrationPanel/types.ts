import type { ReactNode } from 'react';

export interface AgentInfo {
  name: string;
  role: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  isManager?: boolean;
  collaborations?: string[];
  currentTask?: string;
  performance?: {
    tasks_completed: number;
    success_rate: number;
    avg_duration: number;
  };
}

export interface CrewProgress {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  agents: AgentInfo[];
  description: string;
  icon: ReactNode;
  results?: unknown;
  currentTask?: string;
  manager?: string;
  collaboration_status?: {
    intra_crew: number;
    cross_crew: number;
    memory_sharing: boolean;
    knowledge_utilization: number;
  };
  planning_status?: {
    strategy: string;
    coordination_score: number;
    adaptive_triggers: string[];
  };
}

export interface CollaborationData {
  total_collaborations: number;
  active_collaborations: number;
  cross_crew_insights: number;
  memory_utilization: number;
  knowledge_sharing_score: number;
}

export interface PlanningData {
  coordination_strategy: string;
  success_criteria_met: number;
  adaptive_adjustments: number;
  optimization_score: number;
  predicted_completion: string;
}

export interface AgentOrchestrationPanelProps {
  flowId: string;
  flowState: unknown;
  onStatusUpdate?: (status: unknown) => void;
}

export type CrewStatus = 'pending' | 'running' | 'completed' | 'failed';

export type BadgeVariant = 'secondary' | 'default' | 'success' | 'destructive';