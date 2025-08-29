import { useMutation, useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

// Types
export interface UploadedFile {
  id: string;
  file: File;
  type: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
  flowId?: string; // Flow ID from the CrewAI workflow
  filename?: string; // File name for display
  recordCount?: number; // Number of records in the file
  aiSuggestions?: string[];
  nextSteps?: Array<{
    label: string;
    route?: string;
    description?: string;
    isExternal?: boolean;
    dataQualityIssues?: Array<{
      issue: string;
      severity: 'high' | 'medium' | 'low';
      count?: number;
    }>;
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
  sample_data: Array<Record<string, unknown>>;
  filename: string;
  options?: Record<string, unknown>;
}

export interface DiscoveryFlowResponse {
  status: string;
  message: string;
  flow_id: string;
  workflow_status: string;
  current_phase: string;
  flow_result: Record<string, unknown>;
  next_steps: {
    ready_for_assessment: boolean;
    recommended_actions: string[];
  };
}

interface AnalysisStatusResponse {
  status: 'running' | 'completed' | 'failed' | 'idle' | 'error' | 'in_progress' | 'processing';
  flow_id: string;
  current_phase: string;
  workflow_phases: string[];
  progress_percentage?: number;
  message?: string;
  // Raw agent data (pass through what CrewAI agents actually produce)
  flow_status?: Record<string, unknown>;
  agent_insights?: Array<string | Record<string, unknown>>;
  agent_results?: Record<string, unknown>;
  clarification_questions?: Array<string | Record<string, unknown>>;
  data_quality_assessment?: Record<string, unknown>;
  field_mappings?: Record<string, unknown>;
  classified_assets?: Array<{
    id: string;
    name: string;
    type: string;
    [key: string]: unknown;
  }>;
  processing_summary?: {
    total_records_processed?: number;
    records_found?: number;
    data_source?: string;
    workflow_phase?: string;
    agent_status?: string;
  };
  [key: string]: unknown;
}

// Helper function to parse CSV file into structured data
const parseCSVFile = (file: File): Promise<{ headers: string[]; sample_data: Array<Record<string, unknown>> }> => {
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
        const sample_data: Array<Record<string, unknown>> = [];
        for (let i = 1; i < Math.min(lines.length, 11); i++) { // Take first 10 data rows
          const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
          const row: Record<string, unknown> = {};
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
export const useDiscoveryFlow = (): JSX.Element => {
  const queryClient = useQueryClient();
  const { flowId } = useAuth(); // Get flow ID from AuthContext

  return useMutation<DiscoveryFlowResponse, Error, { file: File }>(
    {
      mutationFn: async ({ file }) => {
        console.log('🔍 Starting discovery flow for file:', file.name);
        console.log('📋 Using flow ID from AuthContext:', flowId);

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
            flow_id: flowId // Use flow ID from AuthContext
          }
        };

        console.log('🚀 Sending request to backend:', {
          endpoint: '/api/v1/unified-discovery/flows/run-redesigned',
          flow_id: flowId,
          filename: file.name,
          headers_count: headers.length,
          sample_data_count: sample_data.length
        });

        // Call the redesigned backend endpoint with proper crew implementation
        const response = await apiCall('/api/v1/unified-discovery/flows/run-redesigned', {
          method: 'POST',
          body: JSON.stringify(requestBody),
        }) as DiscoveryFlowResponse;

        console.log('✅ Discovery flow response:', response);

        return response;
      },
      onSuccess: (data) => {
        console.log('🎉 Discovery flow completed successfully:', data);
        // Only invalidate the specific query for this workflow, not all discovery queries
        queryClient.invalidateQueries({ queryKey: ['discoveryFlowStatus', data.flow_id] });
      },
      onError: (error) => {
        console.error('❌ Discovery flow failed:', error);
      }
    }
  );
};

// Hook for polling workflow status
export const useDiscoveryFlowStatus = (flowId: string | null): JSX.Element => {
  return useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['discoveryFlowStatus', flowId],
    queryFn: async () => {
      if (!flowId) throw new Error('Flow ID is required');

      // Use the public status endpoint that doesn't require authentication
      const response = await apiCall(
        `/api/v1/unified-discovery/flows/agentic-analysis/status-public?flow_id=${flowId}`
      ) as AnalysisStatusResponse;

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
        flow_id: flowId,
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
    enabled: !!flowId,
    staleTime: Infinity, // Never automatically consider data stale
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
    refetchInterval: false, // DISABLED: No automatic polling - use manual refresh only
    refetchOnWindowFocus: false, // DISABLED: No refetch on focus
    refetchOnMount: false, // DISABLED: No refetch on mount after initial load
    refetchOnReconnect: false, // DISABLED: No refetch on reconnect
    retry: 1, // Minimal retries
    retryDelay: 2000 // 2 second delay between retries
  });
};

// Simplified file upload hook
/**
 * Get discovery flow status with authentication
 * Uses the authenticated endpoint for better security and more detailed status
 */
export const useAuthenticatedDiscoveryStatus = (flowId: string | null): JSX.Element => {
  const { user, client, engagement } = useAuth();

  return useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['authenticatedDiscoveryStatus', flowId],
    queryFn: async () => {
      if (!flowId) throw new Error('Flow ID is required');
      if (!user) throw new Error('Authentication required');

      try {
        // Get the current context from the auth context
        let clientId = client?.id || '';
        let engagementId = engagement?.id || '';

        console.log('Auth context - Client ID:', clientId, 'Engagement ID:', engagementId);

        // If we're missing either ID, try to fetch the full context
        if (!clientId || !engagementId) {
          try {
            console.log('Fetching user context from /api/v1/context/me');
            const contextResponse = await apiCall('/context/me', { method: 'GET' });
            console.log('User context response:', contextResponse);

            if (contextResponse?.client?.id) {
              clientId = contextResponse.client.id;
            }
            if (contextResponse?.engagement?.id) {
              engagementId = contextResponse.engagement.id;
            }
          } catch (contextError) {
            console.error('Failed to fetch user context:', contextError);
            throw new Error('Failed to load user context. Please ensure you have selected a client and engagement.');
          }
        }

        if (!clientId || !engagementId) {
          throw new Error('Missing client or engagement context. Please ensure you have selected a client and engagement.');
        }

        // Prepare headers for the status request
        const headers: Record<string, string> = {
          'X-Client-Account-Id': clientId,
          'X-Engagement-Id': engagementId,
          'X-Flow-ID': flowId,
          'X-Requested-With': 'XMLHttpRequest' // Helps identify AJAX requests
        };

        if (process.env.NODE_ENV !== 'production') {
          console.log('Making authenticated status request for flow:', flowId);
        }

        // Build query parameters
        const queryParams = new URLSearchParams({
          flow_id: flowId,
          page_context: 'data-import',
          client_id: clientId,
          engagement_id: engagementId,
          ...(user?.id && { user_id: user.id })
        });

        console.log('Calling authenticated status endpoint with params:', queryParams.toString());

        // Call the authenticated endpoint with context headers and query params
        const endpoint = `/api/v1/agents/discovery/agent-status?${queryParams.toString()}`;
        console.log('Calling authenticated status endpoint:', endpoint);

        const response = await apiCall(
          endpoint,
          {
            method: 'GET',
            headers: {
              ...headers,
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            credentials: 'include' // Ensure cookies are sent with the request
          }
        ) as AnalysisStatusResponse;

        // Transform response to match AnalysisStatusResponse
        const flowStatus = response.flow_status || {};
        const workflowStatus = flowStatus.status || response.status || 'unknown';
        const currentPhase = flowStatus.current_phase || response.current_phase || 'unknown';
        const progressPercentage = flowStatus.progress_percentage || 0;

        console.log('🔒 Authenticated status response:', {
          status: workflowStatus,
          phase: currentPhase,
          progress: progressPercentage
        });

        return {
          status: workflowStatus,
          flow_id: flowId,
          current_phase: currentPhase,
          workflow_phases: flowStatus.workflow_phases || [],
          progress_percentage: progressPercentage,
          message: flowStatus.message || response.message,
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
        };
      } catch (error) {
        console.error('Error in authenticated status check:', error);
        throw new Error('Failed to fetch status with authentication');
      }
    },
    enabled: !!flowId,
    refetchInterval: false, // DISABLED: No automatic polling - use manual refresh only
    retry: (failureCount, error) => {
      // Only retry on network errors, not on 4xx errors
      if (error.message.includes('Failed to fetch') && failureCount < 3) {
        return true;
      }
      return false;
    }
  });
};

export const useFileUpload = (): JSX.Element => {
  const queryClient = useQueryClient();
  const discoveryFlow = useDiscoveryFlow();

  return useMutation({
    mutationFn: async (files: Array<{ file: File; type: string; id: string }>) => {
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

          // Use the flow ID returned by the backend
          const actualFlowId = result.flow_id || id;

          // Parse CSV to get record count for display
          const { headers, sample_data } = await parseCSVFile(file);

          // Update file with backend flow ID and additional metadata
          queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) =>
            old.map(f => f.id === id ? {
              ...f,
              id: actualFlowId,
              flowId: actualFlowId, // Add flow ID for status polling
              filename: file.name, // Add filename for display
              recordCount: sample_data.length, // Add record count for display
              status: 'analyzing',
              processingMessages: [`✅ Workflow started: ${result.current_phase}`]
            } : f)
          );

          return {
            id: actualFlowId,
            file,
            type,
            status: 'analyzing' as const,
            flowId: actualFlowId, // Add flow ID for status polling
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
        flowId: id, // Temporary until backend returns real flow ID
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
