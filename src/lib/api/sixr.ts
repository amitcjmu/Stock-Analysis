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

// API Configuration
const getApiBaseUrl = (): string => {
  // In development, use localhost:8000
  if (import.meta.env.DEV) {
    return 'http://localhost:8000/api/v1';
  }
  
  // In production, prioritize environment variable, then fall back to Railway URL
  const backendUrl = import.meta.env.VITE_API_BASE_URL;
  if (backendUrl) {
    return backendUrl;
  }
  
  // If no environment variable is set, check if we're likely on Vercel and use Railway
  if (window.location.hostname.includes('vercel.app')) {
    // Default Railway backend URL - you should replace this with your actual Railway URL
    return 'https://migrate-ui-orchestrator-production.up.railway.app/api/v1';
  }
  
  // For local production builds or other deployments, use same origin
  return `${window.location.origin}/api/v1`;
};

const getWsBaseUrl = (): string => {
  // In development, use localhost:8000
  if (import.meta.env.DEV) {
    return 'ws://localhost:8000/api/v1/ws';
  }
  
  // In production, prioritize environment variable, then fall back to Railway URL
  const wsUrl = import.meta.env.VITE_WS_BASE_URL;
  if (wsUrl) {
    return wsUrl;
  }
  
  // If no environment variable is set, check if we're likely on Vercel and use Railway
  if (window.location.hostname.includes('vercel.app')) {
    // Default Railway backend URL - you should replace this with your actual Railway URL
    return 'wss://migrate-ui-orchestrator-production.up.railway.app/api/v1/ws';
  }
  
  // For local production builds or other deployments, use same origin
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/v1/ws`;
};

const API_BASE_URL = getApiBaseUrl();
const WS_BASE_URL = getWsBaseUrl();

// Request/Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface ApiError {
  message: string;
  code: string;
  details?: any;
  status: number;
}

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

// Cache Management
class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  
  set(key: string, data: any, ttl: number = 300000): void { // 5 minutes default
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  delete(key: string): void {
    this.cache.delete(key);
  }
  
  clear(): void {
    this.cache.clear();
  }
  
  invalidatePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

// Error Classes
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

// HTTP Client with retry logic
class HttpClient {
  private cache = new ApiCache();
  private maxRetries = 3;
  
  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = this.maxRetries,
    useCache: boolean = false,
    cacheTtl?: number
  ): Promise<T> {
    // Check cache first for GET requests
    if (options.method === 'GET' && useCache) {
      const cached = this.cache.get(endpoint);
      if (cached) return cached;
    }
    
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`,
        ...options.headers,
      },
      ...options,
    };

    let lastError: Error;
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new APIError(
            errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            'server',
            errorData
          );
        }
        
        const data = await response.json();
        
        // Cache successful GET responses
        if (options.method === 'GET' && useCache) {
          this.cache.set(endpoint, data, cacheTtl);
        }
        
        return data;
        
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Don't retry on client errors (4xx)
        if (error instanceof APIError && error.status >= 400 && error.status < 500) {
          throw error;
        }
        
        // Wait before retry (exponential backoff)
        if (attempt < retries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError;
  }

  private getAuthToken(): string {
    // In a real app, this would get the token from localStorage, cookies, or auth context
    return localStorage.getItem('auth_token') || 'demo-token';
  }

  private handleError(context: string, error: unknown): void {
    if (error instanceof APIError) {
      console.error(`${context}:`, error.message, error.details);
    } else if (error instanceof Error) {
      console.error(`${context}:`, error.message);
    } else {
      console.error(`${context}:`, String(error));
    }
  }
  
  async get<T>(url: string, useCache: boolean = true, cacheTtl?: number): Promise<T> {
    return this.makeRequest<T>(url, { method: 'GET' }, this.maxRetries, useCache, cacheTtl);
  }
  
  async post<T>(url: string, data?: any): Promise<T> {
    return this.makeRequest<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async put<T>(url: string, data?: any): Promise<T> {
    return this.makeRequest<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async delete<T>(url: string): Promise<T> {
    return this.makeRequest<T>(url, { method: 'DELETE' });
  }
  
  clearCache(): void {
    this.cache.clear();
  }
  
  invalidateCache(pattern: string): void {
    this.cache.invalidatePattern(pattern);
  }
}

// WebSocket Manager
class WebSocketManager {
  private connections = new Map<string, WebSocket>();
  private reconnectAttempts = new Map<string, number>();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  
  connect(
    endpoint: string,
    onMessage?: (data: any) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    const url = `${WS_BASE_URL}${endpoint}`;
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      this.reconnectAttempts.set(endpoint, 0);
      onOpen?.();
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      onError?.(error);
    };
    
    ws.onclose = () => {
      this.connections.delete(endpoint);
      onClose?.();
      
      // Auto-reconnect logic
      const attempts = this.reconnectAttempts.get(endpoint) || 0;
      if (attempts < this.maxReconnectAttempts) {
        this.reconnectAttempts.set(endpoint, attempts + 1);
        setTimeout(() => {
          this.connect(endpoint, onMessage, onError, onOpen, onClose);
        }, this.reconnectDelay * Math.pow(2, attempts));
      }
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
  
  send(endpoint: string, data: any): boolean {
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
  private http = new HttpClient();
  private ws = new WebSocketManager();
  
  // Analysis Management
  async createAnalysis(request: CreateAnalysisRequest): Promise<number> {
    try {
      const response = await this.http.post<{ analysis_id: number }>('/sixr/analyze', {
        application_ids: request.application_ids,
        initial_parameters: request.parameters,
        analysis_name: request.queue_name || `Analysis ${Date.now()}`
      });
      
      // Cache the new analysis
      this.http.invalidateCache('/sixr');
      
      return response.analysis_id;
    } catch (error) {
      this.handleError('Failed to create analysis', error);
      throw error;
    }
  }
  
  async getAnalysis(analysisId: number): Promise<SixRAnalysisResponse> {
    const cacheKey = `analysis_${analysisId}`;
    
    try {
      const response = await this.http.get<SixRAnalysisResponse>(`/sixr/${analysisId}`);
      return response;
    } catch (error) {
      this.handleError('Failed to get analysis', error);
      throw error;
    }
  }
  
  async updateParameters(analysisId: number, parameters: SixRParameters): Promise<SixRAnalysisResponse> {
    try {
      const response = await this.http.put<SixRAnalysisResponse>(`/sixr/${analysisId}/parameters`, {
        parameters: parameters,
        update_reason: 'Parameter update from UI'
      });
      
      // Update cache
      this.http.invalidateCache(`/sixr/${analysisId}`);
      this.http.invalidateCache('analysis_*');
      
      return response;
    } catch (error) {
      this.handleError('Failed to update parameters', error);
      throw error;
    }
  }
  
  async submitQuestions(analysisId: number, responses: QuestionResponse[], isPartial: boolean = false): Promise<SixRAnalysisResponse> {
    try {
      const response = await this.http.post<SixRAnalysisResponse>(`/sixr/${analysisId}/questions`, {
        responses,
        is_partial: isPartial
      });
      
      // Update cache
      this.http.invalidateCache(`/sixr/${analysisId}`);
      
      return response;
    } catch (error) {
      this.handleError('Failed to submit questions', error);
      throw error;
    }
  }
  
  async iterateAnalysis(analysisId: number, iterationNotes: string): Promise<SixRAnalysisResponse> {
    try {
      const response = await this.http.post<SixRAnalysisResponse>(`/sixr/${analysisId}/iterate`, {
        iteration_reason: 'User-initiated iteration',
        stakeholder_feedback: iterationNotes
      });
      
      // Update cache
      this.http.invalidateCache(`/sixr/${analysisId}`);
      this.http.invalidateCache('analysis_*');
      
      return response;
    } catch (error) {
      this.handleError('Failed to iterate analysis', error);
      throw error;
    }
  }
  
  async getRecommendation(analysisId: number): Promise<SixRRecommendation> {
    try {
      const response = await this.http.get<{ recommendation: SixRRecommendation }>(`/sixr/${analysisId}/recommendation`);
      return response.recommendation;
    } catch (error) {
      this.handleError('Failed to get recommendation', error);
      throw error;
    }
  }
  
  async getQualifyingQuestions(analysisId: number): Promise<QualifyingQuestion[]> {
    // Return mock data since this endpoint doesn't exist in fallback mode
    return [];
  }
  
  // Analysis History
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
      // Use the listAnalyses function to get all analyses
      const analysisFilters: AnalysisFilters = {};
      if (filters?.status) analysisFilters.status = filters.status;
      
      const analyses = await this.listAnalyses(analysisFilters);
      
      // Get real application data from discovery API
      let applicationNames: Record<number, { name: string; department: string }> = {};
      try {
        const discoveryResponse = await this.http.get<{ applications: any[] }>('/discovery/applications');
        applicationNames = discoveryResponse.applications.reduce((acc, app) => {
          acc[app.id] = { 
            name: app.name, 
            department: app.department || 'Unknown' 
          };
          return acc;
        }, {});
      } catch (error) {
        console.warn('Could not fetch application names from discovery API, using fallback data');
        // Fallback to mock data only when discovery data is unavailable
        applicationNames = {
          1: { name: 'Customer Portal', department: 'Finance' },
          2: { name: 'Legacy Billing System', department: 'Finance' },
          3: { name: 'Analytics Engine', department: 'IT' },
          4: { name: 'Mobile Banking App', department: 'Digital Banking' },
          5: { name: 'HR Management System', department: 'Human Resources' }
        };
      }
      
      // Transform SixRAnalysisResponse to AnalysisHistoryItem
      const historyItems: AnalysisHistoryItem[] = analyses.map(analysis => {
        const appId = analysis.applications[0]?.id || 0;
        const appInfo = applicationNames[appId] || { 
          name: `Application ${appId}`, 
          department: 'Unknown' 
        };
        
        return {
          id: analysis.analysis_id,
          application_name: appInfo.name,
          application_id: appId,
          department: appInfo.department,
          business_unit: 'Migration Team',
          analysis_date: new Date(analysis.created_at),
          analyst: 'CrewAI Agents',
          status: analysis.status as 'completed' | 'in_progress' | 'failed' | 'archived',
          recommended_strategy: analysis.recommendation?.recommended_strategy || 'pending',
          confidence_score: analysis.recommendation?.confidence_score || 0,
          iteration_count: analysis.current_iteration,
          estimated_effort: analysis.recommendation?.estimated_effort || 'unknown',
          estimated_timeline: analysis.recommendation?.estimated_timeline || 'unknown',
          estimated_cost_impact: analysis.recommendation?.estimated_cost_impact || 'unknown',
          parameters: {
            business_value: analysis.parameters.business_value,
            technical_complexity: analysis.parameters.technical_complexity,
            migration_urgency: analysis.parameters.migration_urgency,
            compliance_requirements: analysis.parameters.compliance_requirements,
            cost_sensitivity: analysis.parameters.cost_sensitivity,
            risk_tolerance: analysis.parameters.risk_tolerance,
            innovation_priority: analysis.parameters.innovation_priority,
            application_type: analysis.parameters.application_type
          },
          key_factors: analysis.recommendation?.key_factors || [],
          next_steps: analysis.recommendation?.next_steps || [],
          tags: [`${analysis.status}`, `iteration-${analysis.current_iteration}`],
          notes: analysis.recommendation ? 'Analysis completed by CrewAI agents' : 'Analysis in progress'
        };
      });
      
      // Apply additional filters that aren't supported by the backend
      let filteredItems = historyItems;
      
      if (filters?.strategy) {
        filteredItems = filteredItems.filter(item => 
          item.recommended_strategy === filters.strategy
        );
      }

      if (filters?.department) {
        filteredItems = filteredItems.filter(item => 
          item.department === filters.department
        );
      }

      if (filters?.search) {
        const searchLower = filters.search.toLowerCase();
        filteredItems = filteredItems.filter(item => 
          item.application_name.toLowerCase().includes(searchLower) ||
          item.department.toLowerCase().includes(searchLower) ||
          item.analyst.toLowerCase().includes(searchLower)
        );
      }

      if (filters?.date_range) {
        const now = new Date();
        filteredItems = filteredItems.filter(item => {
          const itemDate = new Date(item.analysis_date);
          switch (filters.date_range) {
            case 'week':
              return (now.getTime() - itemDate.getTime()) <= 7 * 24 * 60 * 60 * 1000;
            case 'month':
              return (now.getTime() - itemDate.getTime()) <= 30 * 24 * 60 * 60 * 1000;
            case 'quarter':
              return (now.getTime() - itemDate.getTime()) <= 90 * 24 * 60 * 60 * 1000;
            default:
              return true;
          }
        });
      }

      // Sort by analysis date (newest first)
      filteredItems.sort((a, b) => 
        new Date(b.analysis_date).getTime() - new Date(a.analysis_date).getTime()
      );

      return filteredItems;
    } catch (error) {
      this.handleError('Failed to get analysis history', error);
      // Return empty array on error instead of throwing
      return [];
    }
  }
  
  async deleteAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    // Return mock success since this endpoint doesn't exist in fallback mode
    return { success: true, message: 'Analysis deleted (mock)' };
  }
  
  async archiveAnalysis(analysisId: number): Promise<{ success: boolean; message: string }> {
    // Return mock success since this endpoint doesn't exist in fallback mode
    return { success: true, message: 'Analysis archived (mock)' };
  }
  
  // Bulk Analysis
  async createBulkAnalysis(request: BulkAnalysisRequest): Promise<string> {
    // This endpoint should only be called from the actual bulk analysis workflow
    throw new Error('Bulk analysis should be initiated from the Discovery phase. This page is for monitoring existing bulk operations only.');
  }
  
  async getBulkJobs(): Promise<BulkAnalysisJob[]> {
    try {
      // Try to get real bulk jobs from backend
      const response = await this.http.get<{ jobs: BulkAnalysisJob[] }>('/sixr/bulk/jobs');
      return response.jobs || [];
    } catch (error) {
      // Return empty array instead of mock data
      console.info('No bulk analysis jobs found or endpoint not available');
      return [];
    }
  }
  
  async getBulkJobResults(jobId: string): Promise<BulkAnalysisResult[]> {
    try {
      const response = await this.http.get<{ results: BulkAnalysisResult[] }>(`/sixr/bulk/jobs/${jobId}/results`);
      return response.results || [];
    } catch (error) {
      console.warn(`No results found for bulk job ${jobId}`);
      return [];
    }
  }
  
  async getBulkSummary(): Promise<BulkAnalysisSummary> {
    try {
      const response = await this.http.get<BulkAnalysisSummary>('/sixr/bulk/summary');
      return response;
    } catch (error) {
      // Return empty summary instead of mock data
      return {
        total_jobs: 0,
        active_jobs: 0,
        completed_jobs: 0,
        failed_jobs: 0,
        total_applications_processed: 0,
        average_confidence: 0,
        strategy_distribution: {},
        processing_time_stats: { min: 0, max: 0, average: 0, total: 0 }
      };
    }
  }
  
  async controlBulkJob(
    jobId: string,
    action: 'start' | 'pause' | 'cancel' | 'retry'
  ): Promise<{ success: boolean; message: string }> {
    // Return mock success since this endpoint doesn't exist in fallback mode
    return { success: true, message: `Job ${action}ed (mock)` };
  }
  
  async deleteBulkJob(jobId: string): Promise<{ success: boolean; message: string }> {
    // Return mock success since this endpoint doesn't exist in fallback mode
    return { success: true, message: 'Job deleted (mock)' };
  }
  
  // Export Functions
  async exportAnalysis(
    analysisIds: number[],
    format: 'csv' | 'pdf' | 'json'
  ): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/sixr/export`, {
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
    
    return response.blob();
  }
  
  async exportBulkResults(
    jobId: string,
    format: 'csv' | 'pdf' | 'json'
  ): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/sixr/bulk/jobs/${jobId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ format })
    });
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    
    return response.blob();
  }
  
  // WebSocket Management
  connectToAnalysis(
    analysisId: number,
    onMessage?: (data: any) => void,
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
    onMessage?: (data: any) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void,
    onClose?: () => void
  ): WebSocket {
    return this.ws.connect(
      `/bulk/${jobId}`,
      onMessage,
      onError,
      onOpen,
      onClose
    );
  }
  
  disconnectWebSocket(endpoint: string): void {
    this.ws.disconnect(endpoint);
  }
  
  sendWebSocketMessage(endpoint: string, data: any): boolean {
    return this.ws.send(endpoint, data);
  }
  
  // Cache Management
  clearCache(): void {
    this.http.clearCache();
  }
  
  invalidateCache(pattern: string): void {
    this.http.invalidateCache(pattern);
  }
  
  // Cleanup
  cleanup(): void {
    this.ws.disconnectAll();
    this.http.clearCache();
  }

  /**
   * List all analyses for the current user
   */
  async listAnalyses(filters?: AnalysisFilters): Promise<SixRAnalysisResponse[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.status) queryParams.append('status', filters.status);
      if (filters?.application_id) queryParams.append('application_id', filters.application_id.toString());
      if (filters?.created_after) queryParams.append('created_after', filters.created_after);
      if (filters?.created_before) queryParams.append('created_before', filters.created_before);
      if (filters?.limit) queryParams.append('page_size', filters.limit.toString());
      if (filters?.offset) queryParams.append('page', Math.floor((filters.offset || 0) / (filters.limit || 20)) + 1);
      
      const url = `/sixr${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await this.http.get<{ analyses: SixRAnalysisResponse[]; total_count: number; page: number; page_size: number }>(url);
      
      return response.analyses || [];
    } catch (error) {
      this.handleError('Failed to list analyses', error);
      throw error;
    }
  }

  private handleError(context: string, error: unknown): void {
    if (error instanceof APIError) {
      console.error(`${context}:`, error.message, error.details);
    } else if (error instanceof Error) {
      console.error(`${context}:`, error.message);
    } else {
      console.error(`${context}:`, String(error));
    }
  }
}

// Singleton instance
export const sixrApi = new SixRApiClient();

// Export types for use in components
export type {
  ApiResponse,
  ApiError,
  CreateAnalysisRequest,
  CreateAnalysisResponse,
  UpdateParametersRequest,
  SubmitQuestionsRequest,
  IterateAnalysisRequest,
  BulkAnalysisRequest
}; 