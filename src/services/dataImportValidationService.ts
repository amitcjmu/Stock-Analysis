import { apiCall } from '@/config/api';

export interface ValidationAgentResult {
  agent_id: string;
  agent_name: string;
  validation: 'passed' | 'failed' | 'warning';
  confidence: number;
  message: string;
  details: string[];
  processing_time_seconds?: number;
}

export interface ValidationResponse {
  success: boolean;
  validation_session: {
    file_id: string;
    filename: string;
    size_mb: number;
    content_type: string;
    category: string;
    uploaded_by: number;
    uploaded_at: string;
    status: 'validating' | 'approved' | 'rejected' | 'approved_with_warnings';
    agent_results: ValidationAgentResult[];
  };
  file_status: 'approved' | 'rejected' | 'approved_with_warnings';
  agent_results: ValidationAgentResult[];
  security_clearances: {
    format_validation: boolean;
    security_clearance: boolean;
    privacy_clearance: boolean;
  };
  next_step: string;
}

export interface ValidationAgentsResponse {
  agents: Record<string, any>;
  categories: {
    cmdb: string[];
    'app-discovery': string[];
    infrastructure: string[];
    sensitive: string[];
  };
}

export class DataImportValidationService {
  /**
   * Validate uploaded file using backend validation agents
   */
  static async validateFile(file: File, category: string): Promise<ValidationResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    try {
      const response = await apiCall('/data-import/validate-upload', {
        method: 'POST',
        body: formData,
      }, true);

      return response;
    } catch (error) {
      console.error('File validation failed:', error);
      throw new Error(`Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get available validation agents and their configurations
   */
  static async getValidationAgents(): Promise<ValidationAgentsResponse> {
    try {
      const response = await apiCall('/data-import/validation-agents', {
        method: 'GET',
      }, true);

      return response;
    } catch (error) {
      console.error('Failed to get validation agents:', error);
      throw new Error(`Failed to get validation agents: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get validation session by ID
   */
  static async getValidationSession(sessionId: string): Promise<any> {
    try {
      const response = await apiCall(`/data-import/validation-session/${sessionId}`, {
        method: 'GET',
      }, true);

      return response;
    } catch (error) {
      console.error('Failed to get validation session:', error);
      throw new Error(`Failed to get validation session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
} 