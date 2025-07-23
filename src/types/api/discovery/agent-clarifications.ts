/**
 * Discovery Agent Clarifications API Types
 * 
 * Type definitions for agent clarification operations including creation,
 * responses, escalation, and resolution workflows.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  GetRequest,
  ListResponse,
  CreateRequest,
  CreateResponse,
  MultiTenantContext
} from '../shared';

// Agent Clarifications APIs
export interface GetAgentClarificationsRequest extends GetRequest {
  flowId: string;
  agentId?: string;
  status?: ClarificationStatus[];
  priority?: ClarificationPriority[];
  category?: ClarificationCategory[];
}

export interface GetAgentClarificationsResponse extends ListResponse<AgentClarification> {
  data: AgentClarification[];
  pendingCount: number;
  highPriorityCount: number;
  overdueCount: number;
}

export interface CreateClarificationRequest extends CreateRequest<ClarificationInput> {
  flowId: string;
  data: ClarificationInput;
  notifyUser?: boolean;
  escalationLevel?: EscalationLevel;
}

export interface CreateClarificationResponse extends CreateResponse<AgentClarification> {
  data: AgentClarification;
  notificationSent: boolean;
  escalated: boolean;
}

export interface RespondToClarificationRequest extends BaseApiRequest {
  clarificationId: string;
  context: MultiTenantContext;
  response: string;
  attachments?: string[];
  markAsResolved?: boolean;
}

export interface RespondToClarificationResponse extends BaseApiResponse<AgentClarification> {
  data: AgentClarification;
  resolved: boolean;
  followUpActions?: FollowUpAction[];
}

// Agent Clarification Models
export interface AgentClarification {
  id: string;
  flowId: string;
  agentId: string;
  category: ClarificationCategory;
  priority: ClarificationPriority;
  status: ClarificationStatus;
  question: string;
  context: string;
  suggestedActions: string[];
  response?: string;
  attachments: string[];
  createdAt: string;
  respondedAt?: string;
  resolvedAt?: string;
  escalationLevel: EscalationLevel;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface ClarificationInput {
  agentId: string;
  category: ClarificationCategory;
  priority: ClarificationPriority;
  question: string;
  context: string;
  suggestedActions?: string[];
  attachments?: string[];
  escalationLevel?: EscalationLevel;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface FollowUpAction {
  type: 'task' | 'reminder' | 'escalation' | 'review';
  description: string;
  assignee?: string;
  dueDate?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  automated: boolean;
}

// Enums and Types
export type ClarificationStatus = 'pending' | 'in_progress' | 'answered' | 'resolved' | 'dismissed' | 'escalated';
export type ClarificationPriority = 'urgent' | 'high' | 'medium' | 'low';
export type ClarificationCategory = 'mapping' | 'validation' | 'business_rule' | 'data_quality' | 'workflow' | 'technical';
export type EscalationLevel = 'none' | 'supervisor' | 'expert' | 'administrator';