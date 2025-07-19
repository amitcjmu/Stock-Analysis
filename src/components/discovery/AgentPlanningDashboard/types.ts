/**
 * Agent Planning Dashboard Types
 * 
 * Type definitions for agent planning, tasks, and dashboard components.
 */

export interface AgentTask {
  id: string;
  agent_name: string;
  task_description: string;
  status: 'planned' | 'in_progress' | 'completed' | 'blocked' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  dependencies: string[];
  estimated_duration: number;
  progress: number;
  started_at?: string;
  completed_at?: string;
  requires_human_input?: boolean;
  human_feedback?: any;
}

export interface AgentPlan {
  plan_id: string;
  plan_name: string;
  description: string;
  total_tasks: number;
  completed_tasks: number;
  overall_progress: number;
  estimated_completion: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  tasks: AgentTask[];
  next_actions: string[];
  blocking_issues: string[];
  human_input_required: AgentTask[];
}

export interface AgentPlanningDashboardProps {
  pageContext: string;
  onPlanApproval?: (planId: string, approved: boolean) => void;
  onTaskFeedback?: (taskId: string, feedback: any) => void;
  onHumanInput?: (taskId: string, input: any) => void;
  isOpen?: boolean;
  onClose?: () => void;
  triggerElement?: React.ReactNode;
}

export type FeedbackType = 'suggestion' | 'concern' | 'approval' | 'correction';