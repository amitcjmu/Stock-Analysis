import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
// Use type-only import for Papaparse
import type * as PapaType from 'papaparse';
// @ts-ignore - Workaround for Papaparse types
const Papa = window.Papa as typeof PapaType;

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

export interface FileAnalysisRequest {
  analysis_type: string;
  data_source: {
    file_data: string; // Base64 encoded file content
    metadata: {
      filename: string;
      size: number;
      type: string;
      lastModified: number;
      import_session_id: string;
    };
  };
}

export interface FileAnalysisResponse {
  session_id: string;
  agent_analysis: {
    suggestions: string[];
    next_steps: Array<{
      label: string;
      route?: string;
      description?: string;
      isExternal?: boolean;
      dataQualityIssues?: any[];
    }>;
    confidence: number;
  };
  workflow_status: string;
}

// Helper function to read file content as base64
const readFileAsBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      // Convert to base64
      const base64Content = btoa(content);
      resolve(base64Content);
    };
    reader.onerror = (e) => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsBinaryString(file);
  });
};

// Hooks
export const useFileAnalysis = () => {
  const queryClient = useQueryClient();
  
  return useMutation<FileAnalysisResponse, Error, { file: File; type: string; sessionId: string }>({
    mutationFn: async ({ file, type, sessionId }) => {
      let fileData: any = null;
      let columns: string[] = [];
      let sample_data: any[] = [];
      let detectedType = file.name.split('.').pop()?.toLowerCase();

      if (detectedType === 'csv') {
        // Parse CSV into array of objects
        const text = await file.text();
        const parsed = Papa.parse(text, { header: true });
        fileData = parsed.data;
        columns = parsed.meta.fields || [];
        sample_data = fileData.slice(0, 10);
      } else {
        // Fallback to base64 for non-CSV
        fileData = await readFileAsBase64(file);
      }

      const requestBody: any = {
        analysis_type: 'data_source_analysis',
        data_source: {
          file_data: fileData,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            import_session_id: sessionId,
          },
        },
      };
      if (columns.length) requestBody.data_source.columns = columns;
      if (sample_data.length) requestBody.data_source.sample_data = sample_data;

      return apiCall<FileAnalysisResponse>('/api/v1/discovery/flow/agent/analysis', {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });
    },
    onSuccess: (data) => {
      // Invalidate any related queries
      queryClient.invalidateQueries({ queryKey: ['fileAnalysis', data.session_id] });
    },
  });
};

interface AnalysisStatusResponse {
  status: 'running' | 'completed' | 'failed' | 'idle';
  session_id: string;
  flow_status: {
    status: 'running' | 'completed' | 'failed' | 'idle';
    current_phase: string;
    workflow_phases: string[];
    [key: string]: any;
  };
  current_phase?: string;
  message?: string;
  [key: string]: any;
}

export const useFileAnalysisStatus = (sessionId: string | null) => {
  return useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['fileAnalysisStatus', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID is required');
      
      try {
        const response = await apiCall<AnalysisStatusResponse>(
          `/api/v1/discovery/flow/agentic-analysis/status?session_id=${sessionId}`
        );
        
        return response;
      } catch (error) {
        console.error('Error fetching analysis status:', error);
        throw error;
      }
    },
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Only poll if the workflow is still in progress
      return data?.workflow_status === 'in_progress' || 
             data?.status === 'in_progress' ? 2000 : false;
    },
    refetchOnWindowFocus: true,
    retry: 3,
    retryDelay: 1000,
  });
};

// Helper hook for file uploads
export const useFileUpload = () => {
  const queryClient = useQueryClient();
  const fileAnalysis = useFileAnalysis();
  
  return useMutation({
    mutationFn: async (files: { file: File; type: string; id: string }[]) => {
      const uploadPromises = files.map(async ({ file, type, id }) => {
        try {
          // Update the file status to 'analyzing'
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => 
            old.map(f => f.id === id ? { 
              ...f, 
              status: 'analyzing',
              analysisError: undefined,
              processingMessages: ['🤖 AI crew initializing...']
            } : f)
          );
          
          // Start the analysis
          const result = await fileAnalysis.mutateAsync({
            file,
            type,
            sessionId: id,
          });
          
          // Use the session ID returned by the backend for polling
          const actualSessionId = result.session_id || id;
          
          // Update the file with the actual session ID from the backend
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) => 
            old.map(f => f.id === id ? { 
              ...f, 
              id: actualSessionId,  // Update to use the actual session ID
              status: 'analyzing',
              processingMessages: ['🤖 AI crew is analyzing your file...']
            } : f)
          );
          
          // Return initial state with the actual session ID
          return {
            id: actualSessionId,  // Use the actual session ID returned by backend
            file,
            type,
            status: 'analyzing' as const,
            detectedFileType: file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
            analysisSteps: [
              'Initial file scan',
              'Content structure analysis',
              'Data pattern recognition',
              'Field mapping suggestions',
              'Quality assessment',
              'Next steps generation'
            ],
            currentStep: 0,
            processingMessages: ['🤖 AI crew is analyzing your file...']
          };
        } catch (error) {
          // Update the file status to 'error'
          return {
            id,
            file,
            type,
            status: 'error' as const,
            analysisError: (error as Error).message,
            processingMessages: [`Error: ${(error as Error).message}`]
          };
        }
      });
      
      return Promise.all(uploadPromises);
    },
    onMutate: (files) => {
      // Optimistically update the UI
      const newFiles: UploadedFile[] = files.map(({ file, type, id }) => ({
        id,
        file,
        type,
        status: 'uploaded' as const,
        detectedFileType: file.name.split('.').pop()?.toUpperCase(),
        analysisSteps: [
          'Initial file scan',
          'Content structure analysis',
          'Data pattern recognition',
          'Field mapping suggestions',
          'Quality assessment',
          'Next steps generation'
        ],
        currentStep: 0,
        processingMessages: []
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
      // Refresh the list of uploaded files
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
      
      // Start polling for status updates for each uploaded file
      if (data) {
        data.forEach((file) => {
          if (file.status === 'analyzing') {
            // The useFileAnalysisStatus hook will handle the polling automatically
            // We just need to ensure the query is enabled with the actual session ID
            queryClient.invalidateQueries({ 
              queryKey: ['fileAnalysisStatus', file.id] 
            });
          }
        });
      }
    },
  });
};
