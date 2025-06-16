import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

// Types
export interface UploadedFile {
  id: string;
  file: File;
  type: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
  sessionId?: string; // Session ID from the CrewAI workflow
  filename?: string; // File name for display
  recordCount?: number; // Number of records in the file
  aiSuggestions?: string[];
  nextSteps?: Array<{
    label: string;
    route?: string;
    description?: string;
    isExternal?: boolean;
    dataQualityIssues?: any[];
  }>;
  confidence?: number;
  detectedFileType?: string;
  analysisSteps?: string[];
  currentStep?: number;
  processingMessages?: string[];
  analysisError?: string;
}

export interface DiscoveryFlowRequest {
  headers: string[];
  sample_data: Record<string, any>[];
  filename: string;
  options?: Record<string, any>;
}

export interface DiscoveryFlowResponse {
  status: string;
  message: string;
  session_id: string;
  flow_id: string;
  workflow_status: string;
  current_phase: string;
  flow_result: any;
  next_steps: {
    ready_for_assessment: boolean;
    recommended_actions: string[];
  };
}

interface AnalysisStatusResponse {
  status: 'running' | 'completed' | 'failed' | 'idle' | 'error' | 'in_progress' | 'processing';
  session_id: string;
  current_phase: string;
  workflow_phases: string[];
  progress_percentage?: number;
  message?: string;
  // Raw agent data (pass through what CrewAI agents actually produce)
  flow_status?: any;
  agent_insights?: any[];
  agent_results?: Record<string, any>;
  clarification_questions?: any[];
  data_quality_assessment?: any;
  field_mappings?: Record<string, any>;
  classified_assets?: any[];
  processing_summary?: {
    total_records_processed?: number;
    records_found?: number;
    data_source?: string;
    workflow_phase?: string;
    agent_status?: string;
  };
  [key: string]: any;
}

// Helper function to parse CSV file into structured data
const parseCSVFile = (file: File): Promise<{ headers: string[]; sample_data: Record<string, any>[] }> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length === 0) {
          reject(new Error('File is empty'));
          return;
        }
        
        // Parse headers
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        
        // Parse data rows
        const sample_data: Record<string, any>[] = [];
        for (let i = 1; i < Math.min(lines.length, 11); i++) { // Take first 10 data rows
          const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
          const row: Record<string, any> = {};
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          sample_data.push(row);
        }
        
        resolve({ headers, sample_data });
      } catch (error) {
        reject(new Error('Failed to parse CSV file'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};

// Main hook for initiating discovery workflow
export const useDiscoveryFlow = () => {
  const queryClient = useQueryClient();
  const { currentSessionId } = useAuth(); // Get session ID from AuthContext
  
  return useMutation<DiscoveryFlowResponse, Error, { file: File }>(
    {
      mutationFn: async ({ file }) => {
        console.log('🔍 Starting discovery flow for file:', file.name);
        console.log('📋 Using session ID from AuthContext:', currentSessionId);
        
        // Parse CSV file
        const { headers, sample_data } = await parseCSVFile(file);
        
        console.log('📊 Parsed CSV data:', {
          headers,
          sample_data_count: sample_data.length,
          first_record: sample_data[0]
        });
        
        // Prepare request for the working backend endpoint
        const requestBody: DiscoveryFlowRequest = {
          headers,
          sample_data,
          filename: file.name,
          options: {
            enable_parallel_execution: true,
            enable_retry_logic: true,
            max_retries: 3,
            timeout_seconds: 300,
            session_id: currentSessionId // Use session ID from AuthContext
          }
        };
        
        console.log('🚀 Sending request to backend:', {
          endpoint: '/api/v1/discovery/flow/run-redesigned',
          session_id: currentSessionId,
          filename: file.name,
          headers_count: headers.length,
          sample_data_count: sample_data.length
        });
        
        // Call the redesigned backend endpoint with proper crew implementation
        const response = await apiCall('/api/v1/discovery/flow/run-redesigned', {
          method: 'POST',
          body: JSON.stringify(requestBody),
        }) as DiscoveryFlowResponse;
        
        console.log('✅ Discovery flow response:', response);
        
        return response;
      },
      onSuccess: (data) => {
        console.log('🎉 Discovery flow completed successfully:', data);
        // Only invalidate the specific query for this workflow, not all discovery queries
        queryClient.invalidateQueries({ queryKey: ['discoveryFlowStatus', data.session_id] });
      },
      onError: (error) => {
        console.error('❌ Discovery flow failed:', error);
      }
    }
  );
};

// Hook for polling workflow status
export const useDiscoveryFlowStatus = (sessionId: string | null) => {
  return useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['discoveryFlowStatus', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      
      // Use the public status endpoint that doesn't require authentication
      const response = await apiCall(
        `/api/v1/discovery/flow/agentic-analysis/status-public?session_id=${sessionId}`
      ) as any;
      
      // Extract the actual workflow status from the backend response
      const flowStatus = response.flow_status || {};
      const workflowStatus = flowStatus.status || response.status || 'unknown';
      const currentPhase = flowStatus.current_phase || response.current_phase || 'unknown';
      const progressPercentage = flowStatus.progress_percentage || 0;
      
      console.log('📊 Status response from backend:', {
        response_status: response.status,
        flow_status: flowStatus.status,
        current_phase: currentPhase,
        progress: progressPercentage
      });
      
      // Simple transformation - just pass through what the agents provide
      return {
        status: workflowStatus,
        session_id: sessionId,
        current_phase: currentPhase,
        workflow_phases: flowStatus.workflow_phases || [],
        progress_percentage: progressPercentage,
        message: flowStatus.message || response.message,
        // Pass through all agent data as-is
        flow_status: flowStatus,
        agent_insights: flowStatus.agent_insights || [],
        agent_results: flowStatus.agent_results || {},
        clarification_questions: flowStatus.clarification_questions || [],
        data_quality_assessment: flowStatus.data_quality_assessment || {},
        field_mappings: flowStatus.field_mappings || {},
        classified_assets: flowStatus.classified_assets || [],
        processing_summary: {
          total_records_processed: flowStatus.cmdb_data?.file_data?.length || 0,
          records_found: flowStatus.cmdb_data?.file_data?.length || 0,
          data_source: flowStatus.metadata?.filename || 'Unknown file',
          workflow_phase: currentPhase,
          agent_status: workflowStatus
        }
      } as AnalysisStatusResponse;
    },
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      
      // Stop polling if workflow is completed, failed, or idle
      const shouldStopPolling = data?.status === 'completed' || 
                               data?.status === 'failed' || 
                               data?.status === 'idle' ||
                               data?.status === 'error';
      
      const shouldPoll = data?.status === 'running' || 
                        data?.status === 'in_progress' ||
                        data?.status === 'processing';
      
      console.log(`📊 Polling decision for ${sessionId}:`, {
        status: data?.status,
        current_phase: data?.current_phase,
        shouldPoll,
        shouldStopPolling,
        willPoll: shouldPoll ? 3000 : false
      });
      
      // Poll every 3 seconds if workflow is running, otherwise stop
      return shouldPoll ? 3000 : false;
    },
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry if workflow is completed or failed intentionally
      if (error?.message?.includes('completed') || error?.message?.includes('failed')) {
        return false;
      }
      // Only retry up to 2 times for network errors
      return failureCount < 2;
    },
    retryDelay: 1000,
  });
};

// Simplified file upload hook
export const useFileUpload = () => {
  const queryClient = useQueryClient();
  const discoveryFlow = useDiscoveryFlow();
  
  return useMutation({
    mutationFn: async (files: { file: File; type: string; id: string }[]) => {
      const uploadPromises = files.map(async ({ file, type, id }) => {
        try {
          // Update file status to analyzing
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => 
            old.map(f => f.id === id ? { 
              ...f, 
              status: 'analyzing',
              analysisError: undefined,
              processingMessages: ['🚀 Starting discovery workflow...']
            } : f)
          );
          
          // Start the discovery workflow
          const result = await discoveryFlow.mutateAsync({
            file,
          });
          
          // Use the session ID returned by the backend
          const actualSessionId = result.session_id || id;
          
          // Parse CSV to get record count for display
          const { headers, sample_data } = await parseCSVFile(file);
          
          // Update file with backend session ID and additional metadata
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => 
            old.map(f => f.id === id ? { 
              ...f, 
              id: actualSessionId,
              sessionId: actualSessionId, // Add session ID for status polling
              filename: file.name, // Add filename for display
              recordCount: sample_data.length, // Add record count for display
              status: 'analyzing',
              processingMessages: [`✅ Workflow started: ${result.current_phase}`]
            } : f)
          );
          
          return {
            id: actualSessionId,
            file,
            type,
            status: 'analyzing' as const,
            sessionId: actualSessionId, // Add session ID for status polling
            filename: file.name, // Add filename for display 
            recordCount: sample_data.length, // Add record count for display
            detectedFileType: file.name.split('.').pop()?.toUpperCase() || 'CSV',
            analysisSteps: [
              'Data source analysis',
              'Data validation', 
              'Field mapping',
              'Asset classification',
              'Dependency analysis',
              'Database integration'
            ],
            currentStep: 1,
            processingMessages: [`✅ Workflow started: ${result.current_phase}`]
          };
        } catch (error) {
          console.error('Discovery workflow failed:', error);
          return {
            id,
            file,
            type,
            status: 'error' as const,
            analysisError: (error as Error).message,
            processingMessages: [`❌ Error: ${(error as Error).message}`]
          };
        }
      });
      
      return Promise.all(uploadPromises);
    },
    onMutate: (files) => {
      // Optimistically add files to UI
      const newFiles: UploadedFile[] = files.map(({ file, type, id }) => ({
        id,
        file,
        type,
        status: 'uploaded' as const,
        sessionId: id, // Temporary until backend returns real session ID
        filename: file.name,
        recordCount: 0, // Will be updated after parsing
        detectedFileType: file.name.split('.').pop()?.toUpperCase(),
        analysisSteps: [
          'Data source analysis',
          'Data validation', 
          'Field mapping',
          'Asset classification',
          'Dependency analysis',
          'Database integration'
        ],
        currentStep: 0,
        processingMessages: ['📁 File uploaded, preparing analysis...']
      }));
      
      queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => [...old, ...newFiles]);
      
      return { previousFiles: queryClient.getQueryData<UploadedFile[]>(['uploadedFiles']) };
    },
    onError: (error, variables, context) => {
      // Revert on error
      if (context?.previousFiles) {
        queryClient.setQueryData(['uploadedFiles'], context.previousFiles);
      }
    },
    onSettled: (data) => {
      // Only refresh the uploaded files list, don't trigger status polling here
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
    },
  });
}; 