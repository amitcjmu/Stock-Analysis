import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';

// Types
export interface UploadedFile {
  id: string;
  file: File;
  type: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
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
  status: 'running' | 'completed' | 'failed' | 'idle';
  session_id: string;
  current_phase: string;
  workflow_phases: string[];
  progress_percentage?: number;
  message?: string;
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
  
  return useMutation<DiscoveryFlowResponse, Error, { file: File; sessionId: string }>({
    mutationFn: async ({ file, sessionId }) => {
      // Parse CSV file
      const { headers, sample_data } = await parseCSVFile(file);
      
      // Prepare request for the working backend endpoint
      const requestBody: DiscoveryFlowRequest = {
        headers,
        sample_data,
        filename: file.name,
        options: {
          enable_parallel_execution: true,
          enable_retry_logic: true,
          quality_threshold: 7.0
        }
      };

      // Call the working backend endpoint
      return apiCall<DiscoveryFlowResponse>('/api/v1/discovery/flow/run', {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });
    },
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['discoveryFlow', data.session_id] });
    },
  });
};

// Hook for polling workflow status
export const useDiscoveryFlowStatus = (sessionId: string | null) => {
  return useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['discoveryFlowStatus', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      
      const response = await apiCall<AnalysisStatusResponse>(
        `/api/v1/discovery/flow/agentic-analysis/status?session_id=${sessionId}`
      );
      
      return response;
    },
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 2 seconds if workflow is running
      const isRunning = data?.status === 'running';
      
      console.log(`Polling decision for ${sessionId}:`, {
        status: data?.status,
        current_phase: data?.current_phase,
        isRunning,
        willPoll: isRunning ? 2000 : false
      });
      
      return isRunning ? 2000 : false;
    },
    refetchOnWindowFocus: false,
    retry: 2,
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
            sessionId: id,
          });
          
          // Use the session ID returned by the backend
          const actualSessionId = result.session_id || id;
          
          // Update file with backend session ID
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => 
            old.map(f => f.id === id ? { 
              ...f, 
              id: actualSessionId,
              status: 'analyzing',
              processingMessages: [`✅ Workflow started: ${result.current_phase}`]
            } : f)
          );
          
          return {
            id: actualSessionId,
            file,
            type,
            status: 'analyzing' as const,
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
      // Refresh uploaded files list
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
      
      // Start status polling for successful uploads
      if (data) {
        data.forEach((file) => {
          if (file.status === 'analyzing') {
            queryClient.invalidateQueries({ 
              queryKey: ['discoveryFlowStatus', file.id] 
            });
          }
        });
      }
    },
  });
}; 