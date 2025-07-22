import { ValidationAgentResult } from '@/services/dataImportValidationService';

export interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'validating' | 'processing' | 'approved' | 'approved_with_warnings' | 'rejected' | 'error';
  agentResults: ValidationAgentResult[];
  flow_id?: string;  // ✅ CrewAI-generated flow ID
  // Additional progress tracking properties
  upload_progress?: number;
  validation_progress?: number;
  discovery_progress?: number;  // NEW: Track CrewAI flow progress
  agents_completed?: number;
  total_agents?: number;
  // Security clearance properties
  security_clearance?: boolean;
  privacy_clearance?: boolean;
  format_validation?: boolean;
  agent_results?: ValidationAgentResult[];
  // Error handling
  error_message?: string;
  // NEW: Flow tracking properties
  current_phase?: string;
  flow_status?: 'running' | 'completed' | 'failed' | 'paused';
  flow_summary?: {
    total_assets: number;
    errors: number;
    warnings: number;
    phases_completed: string[];
    agent_insights?: unknown[];
  };
}

export interface UploadCategory {
  id: string;
  title: string;
  description: string;
  icon: unknown;
  color: string;
  acceptedTypes: string[];
  examples: string[];
  securityLevel: string;
  agents: string[];
}

export interface FlowManagementState {
  showFlowManager: boolean;
  conflictFlows: unknown[];
  isLoadingFlowDetails: boolean;
}

export interface CMDBImportState {
  uploadedFiles: UploadFile[];
  flowManagement: FlowManagementState;
}