/**
 * Agent Clarification Panel Types
 * 
 * Type definitions for agent questions, responses, and asset details.
 */

export interface AgentQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  context: unknown;
  options?: string[];
  confidence: string;
  priority: string;
  created_at: string;
  answered_at?: string;
  user_response?: unknown;
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
  onQuestionAnswered?: (questionId: string, response: unknown) => void;
  className?: string;
  refreshTrigger?: number; // Increment this to trigger a refresh
  isProcessing?: boolean; // Set to true when background processing is happening
}