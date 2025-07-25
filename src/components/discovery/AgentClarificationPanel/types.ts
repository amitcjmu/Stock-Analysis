/**
 * Agent Clarification Panel Types
 *
 * Type definitions for agent questions, responses, and asset details.
 */

// Agent clarification context interface
export interface AgentQuestionContext {
  assetId?: string;
  sessionId?: string;
  flowId?: string;
  metadata: Record<string, unknown>;
}

// User response interface
export interface UserResponse {
  answer: string | string[] | boolean | number;
  confidence?: number;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface AgentQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  context: AgentQuestionContext;
  options?: string[];
  confidence: string;
  priority: string;
  created_at: string;
  answered_at?: string;
  user_response?: UserResponse;
  is_resolved: boolean;
}

export interface AssetDetails {
  id?: string;
  name: string;
  asset_type: string;
  hostname?: string;
  ip_address?: string;
  operating_system?: string;
  environment?: string;
  business_criticality?: string;
  department?: string;
  business_owner?: string;
  technical_owner?: string;
  description?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;
  location?: string;
  datacenter?: string;
}

export interface AgentClarificationPanelProps {
  pageContext: string;
  onQuestionAnswered?: (questionId: string, response: UserResponse) => void;
  className?: string;
  refreshTrigger?: number; // Increment this to trigger a refresh
  isProcessing?: boolean; // Set to true when background processing is happening
}
