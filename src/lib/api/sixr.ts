import { apiCall } from '@/config/api';
import { 
  SixRParameters, 
  QualifyingQuestion, 
  QuestionResponse, 
  SixRRecommendation,
  AnalysisProgressType,
  AnalysisHistoryItem,
  BulkAnalysisJob,
  BulkAnalysisResult,
  BulkAnalysisSummary
} from '../../components/sixr';

// Custom API Error class for SixR
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public type: 'network' | 'server' | 'client' | 'unknown',
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// API Configuration
const getWsBaseUrl = (): string => {
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

export interface CreateAnalysisRequest {
  application_ids: number[];
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

export interface BulkAnalysisRequest {
  name: string;
  description?: string;
  application_ids: number[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  parameters?: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

export interface AnalysisFilters {
  status?: string;
  application_id?: number;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

// WebSocket Manager
class WebSocketManager {
  private connections = new Map<string, WebSocket>();
  private reconnectAttempts = new Map<string, number>();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  connect(
    endpoint: string,
    onMessage?: (data: unknown) => void,
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
        onError?.(error);
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
  
  send(endpoint: string, data: unknown): boolean {
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
      const response = await apiCall<{ analysis_id: number }>('/sixr/analyze', {
        method: 'POST',
        body: JSON.stringify({
          application_ids: request.application_ids,
          initial_parameters: request.parameters,
          analysis_name: request.queue_name || `Analysis ${Date.now()}`
        })
      });
      
      return response.analysis_id;
    } catch (error) {
      this.handleError('Failed to create analysis', error);
      throw error;
    }
  }
  
  async getAnalysis(analysisId: number): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiCall<SixRAnalysisResponse>(`/sixr/${analysisId}`);
      return response;
    } catch (error) {
      this.handleError('Failed to get analysis', error);
      throw error;
    }
  }
  
  async updateParameters(analysisId: number, parameters: SixRParameters): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiCall<SixRAnalysisResponse>(`/sixr/${analysisId}/parameters`, {
        method: 'PUT',
        body: JSON.stringify({
          parameters,
          trigger_reanalysis: true
        })
      });
      
      return response;
    } catch (error) {
      this.handleError('Failed to update parameters', error);
      throw error;
    }
  }
  
  async submitQuestions(analysisId: number, responses: QuestionResponse[], isPartial: boolean = false): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiCall<SixRAnalysisResponse>(`/sixr/${analysisId}/questions`, {
        method: 'POST',
        body: JSON.stringify({
          responses,
          is_partial: isPartial
        })
      });
      
      return response;
    } catch (error) {
      this.handleError('Failed to submit questions', error);
      throw error;
    }
  }
  
  async iterateAnalysis(analysisId: number, iterationNotes: string): Promise<SixRAnalysisResponse> {
    try {
      const response = await apiCall<SixRAnalysisResponse>(`/sixr/${analysisId}/iterate`, {
        method: 'POST',
        body: JSON.stringify({
          iteration_reason: 'User-initiated iteration',
          stakeholder_feedback: iterationNotes
        })
      });
      
      return response;
    } catch (error) {
      this.handleError('Failed to iterate analysis', error);
      throw error;
    }
  }
  
  async getRecommendation(analysisId: number): Promise<SixRRecommendation> {
    try {
      const response = await apiCall<SixRRecommendation>(`/sixr/${analysisId}/recommendation`);
      return response;
    } catch (error) {
      this.handleError('Failed to get recommendation', error);
      throw error;
    }
  }
  
  async getQualifyingQuestions(analysisId: number): Promise<QualifyingQuestion[]> {
    try {
      const response = await apiCall<QualifyingQuestion[]>(`/sixr/${analysisId}/questions`);
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
      
      const endpoint = `/sixr/history${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await apiCall<AnalysisHistoryItem[]>(endpoint);
      return response;
    } catch (error) {
      this.handleError('Failed to get analysis history', error);
      throw error;
    }
  }
  
  async deleteAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    try {
      return await apiCall<{ success: boolean; message: string }>(`/sixr/${analysisId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      this.handleError('Failed to delete analysis', error);
      throw error;
    }
  }
  
  async archiveAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    try {
      return await apiCall<{ success: boolean; message: string }>(`/sixr/${analysisId}/archive`, {
        method: 'POST'
      });
    } catch (error) {
      this.handleError('Failed to archive analysis', error);
      throw error;
    }
  }
  
  async createBulkAnalysis(request: BulkAnalysisRequest): Promise<string> {
    try {
      const response = await apiCall<{ job_id: string }>('/sixr/bulk', {
        method: 'POST',
        body: JSON.stringify(request)
      });
      return response.job_id;
    } catch (error) {
      this.handleError('Failed to create bulk analysis', error);
      throw error;
    }
  }
  
  async getBulkJobs(): Promise<BulkAnalysisJob[]> {
    try {
      return await apiCall<BulkAnalysisJob[]>('/sixr/bulk');
    } catch (error) {
      this.handleError('Failed to get bulk jobs', error);
      throw error;
    }
  }
  
  async getBulkJobResults(jobId: string): Promise<BulkAnalysisResult[]> {
    try {
      return await apiCall<BulkAnalysisResult[]>(`/sixr/bulk/${jobId}/results`);
    } catch (error) {
      this.handleError('Failed to get bulk job results', error);
      throw error;
    }
  }
  
  async getBulkSummary(): Promise<BulkAnalysisSummary> {
    try {
      return await apiCall<BulkAnalysisSummary>('/sixr/bulk/summary');
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
      return await apiCall<{ success: boolean; message: string }>(`/sixr/bulk/${jobId}/${action}`, {
        method: 'POST'
      });
    } catch (error) {
      this.handleError('Failed to control bulk job', error);
      throw error;
    }
  }
  
  async deleteBulkJob(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      return await apiCall<{ success: boolean; message: string }>(`/sixr/bulk/${jobId}`, {
        method: 'DELETE'
      });
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
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/sixr/export`, {
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
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/sixr/bulk/${jobId}/export`, {
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
    onMessage?: (data: unknown) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    return this.ws.connect(
      `/sixr/${analysisId}`,
      onMessage,
      onError,
      onOpen,
      onClose
    );
  }
  
  connectToBulkJob(
    jobId: string,
    onMessage?: (data: unknown) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    return this.ws.connect(
      `/sixr/bulk/${jobId}`,
      onMessage,
      onError,
      onOpen,
      onClose
    );
  }
  
  disconnectWebSocket(endpoint: string): void {
    this.ws.disconnect(endpoint);
  }
  
  sendWebSocketMessage(endpoint: string, data: unknown): boolean {
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
  async listAnalyses(filters?: AnalysisFilters): Promise<SixRAnalysisResponse[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, value.toString());
          }
        });
      }
      
      const endpoint = `/sixr${queryParams.toString() ? `?${queryParams}` : ''}`;
      return await apiCall<SixRAnalysisResponse[]>(endpoint);
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