import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../../config/api';

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
      const fileContent = await readFileAsBase64(file);
      
      const requestBody: FileAnalysisRequest = {
        analysis_type: 'data_source_analysis',
        data_source: {
          file_data: fileContent,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            import_session_id: sessionId,
          },
        },
      };

      return apiCall<FileAnalysisResponse>(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
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

export const useFileAnalysisStatus = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['fileAnalysisStatus', sessionId],
    queryFn: async () => {
      if (!sessionId) return null;
      
      const response = await apiCall(
        `${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS}?session_id=${sessionId}`
      );
      
      return response as { workflow_status: string; [key: string]: any };
    },
    enabled: !!sessionId,
    refetchInterval: (data) => {
      // Only poll if the workflow is still in progress
      return data?.workflow_status === 'in_progress' ? 2000 : false;
    },
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
          
          // Update the file status to 'processed'
          return {
            id,
            file,
            type,
            status: 'processed' as const,
            aiSuggestions: result.agent_analysis.suggestions || [],
            nextSteps: result.agent_analysis.next_steps || [],
            confidence: result.agent_analysis.confidence || 0,
            detectedFileType: file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
            analysisSteps: [
              'Initial file scan',
              'Content structure analysis',
              'Data pattern recognition',
              'Field mapping suggestions',
              'Quality assessment',
              'Next steps generation'
            ],
            currentStep: 5, // All steps complete
            processingMessages: ['Analysis complete. Ready for next steps.']
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
    onSettled: () => {
      // Refresh the list of uploaded files
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
    },
  });
};
