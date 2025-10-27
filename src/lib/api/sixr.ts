import { apiCall } from '@/config/api';
import { apiClient } from '@/lib/api/apiClient';
import type { QuestionResponse, AnalysisProgressType, BulkAnalysisResult, BulkAnalysisSummary } from '../../components/sixr'
import { SixRParameters, QualifyingQuestion, SixRRecommendation, AnalysisHistoryItem, BulkAnalysisJob } from '../../components/sixr'

// Custom API Error class for SixR
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public type: 'network' | 'server' | 'client' | 'unknown',
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// API Configuration
const getWsBaseUrl = (): string => {
  // Force relative WebSocket URL for Docker development on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }

  // First, check for WebSocket-specific environment variable
  const wsUrl = import.meta.env.VITE_WS_BASE_URL || import.meta.env.VITE_WS_URL;

  if (wsUrl) {
    return wsUrl;
  }

  // If no WebSocket URL specified, derive from backend URL
  const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL;

  if (backendUrl) {
    const baseUrl = backendUrl.replace(/\/api\/v1$/, '');
    // Convert HTTP(S) to WS(S)
    const wsBaseUrl = baseUrl.replace(/^https?:/, (match) =>
      match === 'https:' ? 'wss:' : 'ws:'
    );
    return `${wsBaseUrl}/ws`;
  }

  // In development mode, use localhost
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return 'ws://localhost:8000/ws';
  }

  // For production without explicit backend URL, use same origin
  console.warn('No VITE_WS_BASE_URL environment variable found. Deriving from current location.');
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
};

const WS_BASE_URL = getWsBaseUrl();

// Request/Response Types
export interface SixRAnalysisResponse {
  analysis_id: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'requires_input';
  current_iteration: number;
  applications: Array<{id: number}>;
  parameters: SixRParameters;
  qualifying_questions: QualifyingQuestion[];
  recommendation?: SixRRecommendation;
  progress_percentage: number;
  estimated_completion?: string;
  created_at: string;
  updated_at: string;
}

// Bug #813 fix: Changed application_ids from number[] to string[] (UUIDs)
export interface CreateAnalysisRequest {
  application_ids: string[]; // UUID strings from assets table
  parameters?: Partial<SixRParameters>;
  queue_name?: string;
}

export interface CreateAnalysisResponse {
  analysis_id: number;
  status: 'created' | 'queued';
  estimated_duration: number;
  queue_position?: number;
}

export interface UpdateParametersRequest {
  parameters: SixRParameters;
  trigger_reanalysis?: boolean;
}

export interface SubmitQuestionsRequest {
  responses: QuestionResponse[];
  is_partial?: boolean;
}

export interface IterateAnalysisRequest {
  parameters?: Partial<SixRParameters>;
  additional_responses?: QuestionResponse[];
  iteration_notes?: string;
}

// Bug #813 fix: Changed application_ids from number[] to string[] (UUIDs)
export interface BulkAnalysisRequest {
  name: string;
  description?: string;
  application_ids: string[]; // UUID strings from assets table
  priority: 'low' | 'medium' | 'high' | 'urgent';
  parameters?: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

// Bug #813 fix: Changed application_id from number to string (UUID)
export interface AnalysisFilters {
  status?: string;
  application_id?: string; // UUID string
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

export interface SixRAnalysisListResponse {
  analyses: SixRAnalysisResponse[];
  total_count: number;
  page: number;
  page_size: number;
}

// WebSocket Manager
class WebSocketManager {
  private connections = new Map<string, WebSocket>();
  private reconnectAttempts = new Map<string, number>();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  connect(
    endpoint: string,
    onMessage?: (data: Record<string, unknown>) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    const url = `${WS_BASE_URL}${endpoint}`;

    if (this.connections.has(endpoint)) {
      return this.connections.get(endpoint)!;
    }

    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
        onError?.(error as Event);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    ws.onopen = () => {
      console.log('WebSocket connected:', url);
      this.reconnectAttempts.set(endpoint, 0);
      onOpen?.();
    };

    ws.onclose = () => {
      console.log('WebSocket closed:', url);
      this.connections.delete(endpoint);

      const attempts = this.reconnectAttempts.get(endpoint) || 0;
      if (attempts < this.maxReconnectAttempts) {
        console.log(`Attempting to reconnect (${attempts + 1}/${this.maxReconnectAttempts})...`);
        this.reconnectAttempts.set(endpoint, attempts + 1);
        setTimeout(() => {
          this.connect(endpoint, onMessage, onError, onOpen, onClose);
        }, this.reconnectDelay * Math.pow(2, attempts));
      } else {
        console.error('Max reconnection attempts reached');
        this.reconnectAttempts.delete(endpoint);
      }

      onClose?.();
    };

    this.connections.set(endpoint, ws);
    return ws;
  }

  disconnect(endpoint: string): void {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close();
      this.connections.delete(endpoint);
      this.reconnectAttempts.delete(endpoint);
    }
  }

  send(endpoint: string, data: Record<string, unknown>): boolean {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  disconnectAll(): void {
    for (const [endpoint] of this.connections) {
      this.disconnect(endpoint);
    }
  }
}

// Main API Client
export class SixRApiClient {
  private ws = new WebSocketManager();

  // Analysis Management
  async createAnalysis(request: CreateAnalysisRequest): Promise<number> {
    try {
      console.log('🔍 API createAnalysis called with:', request);
      const response = await apiClient.post<{ analysis_id: number }>('/6r/analyze', {
        application_ids: request.application_ids,
        initial_parameters: request.parameters,
        analysis_name: request.queue_name || `Analysis ${Date.now()}`
      });

      return response.analysis_id;
    } catch (error) {
      this.handleError('Failed to create analysis', error);
      throw error;
    }
  }

  async getAnalysis(analysisId: number): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiClient.get<SixRAnalysisResponse>(`/6r/${analysisId}`);
      return response;
    } catch (error) {
      this.handleError('Failed to get analysis', error);
      throw error;
    }
  }

  async updateParameters(analysisId: number, parameters: SixRParameters): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiClient.put<SixRAnalysisResponse>(`/6r/${analysisId}/parameters`, {
        parameters,
        trigger_reanalysis: true
      });

      return response;
    } catch (error) {
      this.handleError('Failed to update parameters', error);
      throw error;
    }
  }

  async submitQuestions(analysisId: number, responses: QuestionResponse[], isPartial: boolean = false): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiClient.post<SixRAnalysisResponse>(`/6r/${analysisId}/questions`, {
        responses,
        is_partial: isPartial
      });

      return response;
    } catch (error) {
      this.handleError('Failed to submit questions', error);
      throw error;
    }
  }

  async iterateAnalysis(analysisId: number, iterationNotes: string): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiClient.post<SixRAnalysisResponse>(`/6r/${analysisId}/iterate`, {
        iteration_reason: 'User-initiated iteration',
        stakeholder_feedback: iterationNotes
      });

      return response;
    } catch (error) {
      this.handleError('Failed to iterate analysis', error);
      throw error;
    }
  }

  async getRecommendation(analysisId: number): Promise<SixRRecommendation> {
    try {
      const response = await apiClient.get<SixRRecommendation>(`/6r/${analysisId}/recommendation`);
      return response;
    } catch (error) {
      this.handleError('Failed to get recommendation', error);
      throw error;
    }
  }

  async getQualifyingQuestions(analysisId: number): Promise<QualifyingQuestion[]> {
    try {
      const response = await apiClient.get<QualifyingQuestion[]>(`/6r/${analysisId}/questions`);
      return response;
    } catch (error) {
      this.handleError('Failed to get qualifying questions', error);
      throw error;
    }
  }

  async getAnalysisHistory(
    filters?: {
      status?: string;
      strategy?: string;
      department?: string;
      date_range?: string;
      search?: string;
    }
  ): Promise<AnalysisHistoryItem[]> {
    try {
      const queryParams = new URLSearchParams();

      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) queryParams.append(key, value);
        });
      }

      // Bug #814: Backend serves GET /6r/ with pagination, not /6r/history
      const endpoint = `/6r/${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await apiClient.get<AnalysisHistoryItem[]>(endpoint);
      return response;
    } catch (error) {
      this.handleError('Failed to get analysis history', error);
      throw error;
    }
  }

  async deleteAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    try {
      return await apiClient.delete<{ success: boolean; message: string }>(`/6r/${analysisId}`);
    } catch (error) {
      this.handleError('Failed to delete analysis', error);
      throw error;
    }
  }

  async archiveAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    try {
      return await apiClient.post<{ success: boolean; message: string }>(`/6r/${analysisId}/archive`, {});
    } catch (error) {
      this.handleError('Failed to archive analysis', error);
      throw error;
    }
  }

  async createBulkAnalysis(request: BulkAnalysisRequest): Promise<string> {
    try {
      const response = await apiClient.post<{ job_id: string }>('/6r/bulk', request);
      return response.job_id;
    } catch (error) {
      this.handleError('Failed to create bulk analysis', error);
      throw error;
    }
  }

  async getBulkJobs(): Promise<BulkAnalysisJob[]> {
    try {
      return await apiClient.get<BulkAnalysisJob[]>('/6r/bulk');
    } catch (error) {
      this.handleError('Failed to get bulk jobs', error);
      throw error;
    }
  }

  async getBulkJobResults(jobId: string): Promise<BulkAnalysisResult[]> {
    try {
      return await apiClient.get<BulkAnalysisResult[]>(`/6r/bulk/${jobId}/results`);
    } catch (error) {
      this.handleError('Failed to get bulk job results', error);
      throw error;
    }
  }

  async getBulkSummary(): Promise<BulkAnalysisSummary> {
    try {
      return await apiClient.get<BulkAnalysisSummary>('/6r/bulk/summary');
    } catch (error) {
      this.handleError('Failed to get bulk summary', error);
      throw error;
    }
  }

  async controlBulkJob(
    jobId: string,
    action: 'start' | 'pause' | 'cancel' | 'retry'
  ): Promise<{ success: boolean; message: string }> {
    try {
      return await apiClient.post<{ success: boolean; message: string }>(`/6r/bulk/${jobId}/${action}`, {});
    } catch (error) {
      this.handleError('Failed to control bulk job', error);
      throw error;
    }
  }

  async deleteBulkJob(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      return await apiClient.delete<{ success: boolean; message: string }>(`/6r/bulk/${jobId}`);
    } catch (error) {
      this.handleError('Failed to delete bulk job', error);
      throw error;
    }
  }

  async exportAnalysis(
    analysisIds: number[],
    format: 'csv' | 'pdf' | 'json'
  ): Promise<Blob> {
    try {
      // Use direct fetch with proper URL construction for file downloads
      // The apiClient doesn't handle blob responses well, so we construct the URL manually
      let url: string;

      // CRITICAL FIX: Always use relative URLs when running on port 8081 (Docker development)
      if (typeof window !== 'undefined' && window.location.port === '8081') {
        // Force relative URL for Docker development to use Vite proxy
        url = '/api/v1/6r/export';
      } else {
        // For other environments, use the proper base URL
        const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL || '';
        url = `${backendUrl}/api/v1/6r/export`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_ids: analysisIds,
          format
        })
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      this.handleError('Failed to export analysis', error);
      throw error;
    }
  }

  async exportBulkResults(
    jobId: string,
    format: 'csv' | 'pdf' | 'json'
  ): Promise<Blob> {
    try {
      // Use direct fetch with proper URL construction for file downloads
      // The apiClient doesn't handle blob responses well, so we construct the URL manually
      let url: string;

      // CRITICAL FIX: Always use relative URLs when running on port 8081 (Docker development)
      if (typeof window !== 'undefined' && window.location.port === '8081') {
        // Force relative URL for Docker development to use Vite proxy
        url = `/api/v1/6r/bulk/${jobId}/export`;
      } else {
        // For other environments, use the proper base URL
        const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL || '';
        url = `${backendUrl}/api/v1/6r/bulk/${jobId}/export`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ format })
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      this.handleError('Failed to export bulk results', error);
      throw error;
    }
  }

  // WebSocket Methods
  connectToAnalysis(
    analysisId: number,
    onMessage?: (data: Record<string, unknown>) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    return this.ws.connect(
      `/6r/${analysisId}`,
      onMessage,
      onError,
      onOpen,
      onClose
    );
  }

  connectToBulkJob(
    jobId: string,
    onMessage?: (data: Record<string, unknown>) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    return this.ws.connect(
      `/6r/bulk/${jobId}`,
      onMessage,
      onError,
      onOpen,
      onClose
    );
  }

  disconnectWebSocket(endpoint: string): void {
    this.ws.disconnect(endpoint);
  }

  sendWebSocketMessage(endpoint: string, data: Record<string, unknown>): boolean {
    return this.ws.send(endpoint, data);
  }

  // Cache Management
  clearCache(): void {
    // Cache management would be handled by the apiCall function
    console.log('Cache cleared');
  }

  invalidateCache(pattern: string): void {
    // Cache management would be handled by the apiCall function
    console.log('Cache invalidated:', pattern);
  }

  // Cleanup
  cleanup(): void {
    this.ws.disconnectAll();
  }

  // List all analyses
  async listAnalyses(filters?: AnalysisFilters): Promise<SixRAnalysisListResponse> {
    try {
      const queryParams = new URLSearchParams();

      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, value.toString());
          }
        });
      }

      // CC: Add trailing slash to match FastAPI route definition and avoid 307 redirect
      const endpoint = `/6r/${queryParams.toString() ? `?${queryParams}` : ''}`;
      // Use the new API client directly to ensure proper URL handling in Docker
      // Fix #633: Backend returns paginated response object, not array
      return await apiClient.get<SixRAnalysisListResponse>(endpoint);
    } catch (error) {
      this.handleError('Failed to list analyses', error);
      throw error;
    }
  }

  // Error handling
  private handleError(context: string, error: unknown): void {
    console.error(`${context}:`, error);

    if (error instanceof Error) {
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      });
    }
  }
}

// Export the API client instance
export const sixrApi = new SixRApiClient();
