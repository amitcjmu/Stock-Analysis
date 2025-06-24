/**
 * Discovery Flow V2 - Incomplete Flow Detection
 * V2 version using flow_id instead of session_id and V2 API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import { useToast } from '@/hooks/use-toast';
import { unifiedDiscoveryService } from '../../services/discoveryUnifiedService';

export interface IncompleteFlowV2 {
  flow_id: string;  // Primary identifier - CrewAI Flow ID
  id: string;       // Database ID
  current_phase: string;
  status: 'active' | 'running' | 'paused' | 'failed' | 'completed';
  progress_percentage: number;
  phases: Record<string, boolean>;
  flow_name: string;
  flow_description?: string;
  next_phase?: string;
  is_complete: boolean;
  assessment_ready: boolean;
  migration_readiness_score: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  can_resume: boolean;
  agent_insights: Array<{
    id?: string;
    agent_id?: string;
    agent_name?: string;
    insight_type?: string;
    title?: string;
    description?: string;
    confidence?: string | number;
    supporting_data?: Record<string, any>;
    actionable?: boolean;
    page?: string;
    created_at?: string;
    // Legacy V1 format support
    agent?: string;
    insight?: string;
    priority?: string;
    timestamp?: string;
    phase?: string;
  }>;
  deletion_impact?: {
    flow_phase: string;
    data_to_delete: Record<string, number>;
    estimated_cleanup_time: string;
  };
  flow_management_info?: {
    estimated_remaining_time: string;
    next_phase: string;
    completion_percentage: number;
    resumption_possible: boolean;
  };
}

export interface FlowDetectionResultV2 {
  flows: IncompleteFlowV2[];
  total_count: number;
  can_start_new_flow: boolean;
  blocking_flows: IncompleteFlowV2[];
}

export interface BulkDeleteRequestV2 {
  flow_ids: string[];
  force_delete?: boolean;
}

export interface BulkDeleteResultV2 {
  batch_results: Array<{
    flow_id: string;
    success: boolean;
    result?: any;
    error?: string;
  }>;
  total_processed: number;
  successful: number;
  failed: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Default headers for multi-tenant context
const getDefaultHeaders = () => ({
  'Content-Type': 'application/json',
  'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',
  'X-Engagement-Id': '22222222-2222-2222-2222-222222222222'
});

/**
 * Hook for detecting incomplete V2 discovery flows
 * Uses flow_id as primary identifier and V2 API endpoints
 */
export const useIncompleteFlowDetectionV2 = () => {
  const { client, engagement } = useAuth();
  
  return useQuery({
    queryKey: ['incomplete-flows-v2', client?.id, engagement?.id],
    queryFn: async (): Promise<FlowDetectionResultV2> => {
      // DEPRECATED: Redirecting to unified discovery service
      console.log('🔄 DEPRECATED: Redirecting to unified discovery service');
      const flows = await unifiedDiscoveryService.getActiveFlows();
      
      // The unified service returns { flows: [...], total_flows: n }
      const flowList = flows.flows || [];
      
      // Transform to IncompleteFlowV2 format and filter incomplete
      const incompleteFlows: IncompleteFlowV2[] = flowList
        .filter((flow: any) => !flow.is_complete && flow.status !== 'completed')
        .map((flow: any) => ({
          flow_id: flow.flow_id,
          id: flow.client_id, // V2 API uses client_id in flow_details
          current_phase: flow.current_phase || 'data_import',
          status: flow.status,
          progress_percentage: flow.progress || 0,
          phases: flow.phases || {},
          flow_name: flow.client_name || 'Discovery Flow', // V2 API structure
          flow_description: flow.engagement_name || '',
          next_phase: flow.current_phase,
          is_complete: false, // Active flows are not complete
          assessment_ready: false,
          migration_readiness_score: 0,
          created_at: flow.created_at,
          updated_at: flow.updated_at,
          completed_at: flow.completed_at,
          can_resume: flow.status === 'paused' || flow.status === 'failed',
          agent_insights: flow.agent_insights || [],
          deletion_impact: {
            flow_phase: flow.current_phase || 'unknown',
            data_to_delete: { 'discovery_assets': 0 },
            estimated_cleanup_time: '< 1 minute'
          },
          flow_management_info: {
            estimated_remaining_time: '5-10 minutes',
            next_phase: flow.current_phase || 'data_import',
            completion_percentage: flow.progress || 0,
            resumption_possible: flow.status !== 'failed'
          }
        }));
      
      return {
        flows: incompleteFlows,
        total_count: incompleteFlows.length,
        can_start_new_flow: incompleteFlows.length === 0,
        blocking_flows: incompleteFlows.filter(f => f.status === 'running' || f.status === 'active')
      };
    },
    enabled: !!client?.id && !!engagement?.id,
    refetchInterval: false, // DISABLED: No automatic polling - use manual refresh
    staleTime: 60000, // Consider data fresh for 1 minute
    retry: 1, // Reduce retry attempts
    retryDelay: 5000, // Fixed 5 second delay
  });
};

/**
 * Hook for validating if new V2 flow can be started
 */
export const useNewFlowValidationV2 = () => {
  const { data: incompleteFlows } = useIncompleteFlowDetectionV2();
  
  return useQuery({
    queryKey: ['flow-validation-v2', 'can-start-new', incompleteFlows?.flows?.length],
    queryFn: async (): Promise<{ can_start: boolean; blocking_flows?: IncompleteFlowV2[]; reason?: string }> => {
      if (!incompleteFlows) {
        return { can_start: false, reason: 'Loading flow state...' };
      }
      
      const blockingFlows = incompleteFlows.blocking_flows || [];
      
      if (blockingFlows.length > 0) {
        return {
          can_start: false,
          blocking_flows: blockingFlows,
          reason: `${blockingFlows.length} active flow(s) must be completed or deleted first`
        };
      }
      
      return { can_start: true };
    },
    enabled: !!incompleteFlows,
    staleTime: 60000, // Consider validation data fresh for 1 minute
  });
};

/**
 * Hook for getting detailed V2 flow information
 */
export const useFlowDetailsV2 = (flowId: string | null) => {
  return useQuery({
    queryKey: ['flow-details-v2', flowId],
    queryFn: async (): Promise<IncompleteFlowV2> => {
      if (!flowId) throw new Error('Flow ID required');
      
      const response = await fetch(`${API_BASE_URL}/api/v2/discovery-flows/flows/${flowId}`, {
        headers: getDefaultHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get flow details: ${response.statusText}`);
      }
      
      const flow = await response.json();
      
      // Transform to IncompleteFlowV2 format
      return {
        flow_id: flow.flow_id,
        id: flow.id,
        current_phase: flow.next_phase || 'data_import',
        status: flow.status,
        progress_percentage: flow.progress_percentage,
        phases: flow.phases,
        flow_name: flow.flow_name,
        flow_description: flow.flow_description,
        next_phase: flow.next_phase,
        is_complete: flow.is_complete,
        assessment_ready: flow.assessment_ready,
        migration_readiness_score: flow.migration_readiness_score,
        created_at: flow.created_at,
        updated_at: flow.updated_at,
        completed_at: flow.completed_at,
        can_resume: flow.status === 'paused' || flow.status === 'failed',
        agent_insights: flow.agent_insights || [],
        deletion_impact: {
          flow_phase: flow.next_phase || 'unknown',
          data_to_delete: { 'discovery_assets': 0 },
          estimated_cleanup_time: '< 1 minute'
        },
        flow_management_info: {
          estimated_remaining_time: '5-10 minutes',
          next_phase: flow.next_phase || 'data_import',
          completion_percentage: flow.progress_percentage,
          resumption_possible: flow.status !== 'failed'
        }
      };
    },
    enabled: !!flowId,
    staleTime: 300000, // Consider flow details fresh for 5 minutes
  });
};

/**
 * Hook for resuming V2 flows (placeholder - V2 flows use different resumption pattern)
 */
export const useFlowResumptionV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: async (flowId: string) => {
      // V2 flows don't have traditional "resumption" - they're managed through phase completion
      // This is a placeholder that redirects to the appropriate phase
      console.log('🔄 V2 Flow continuation request for:', flowId);
      
      // Get flow details to determine next phase
      const response = await fetch(`${API_BASE_URL}/api/v2/discovery-flows/flows/${flowId}`, {
        headers: getDefaultHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get flow details: ${response.statusText}`);
      }
      
      const flow = await response.json();
      return flow;
    },
    onSuccess: (data, flowId) => {
      // Invalidate incomplete flows query to refresh UI
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows-v2'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation-v2'] });
      
      // Determine next phase and navigate appropriately
      const nextPhase = data?.next_phase || 'data_import';
      
      // V2 phase routes using flow_id
      const phaseRoutes = {
        'data_import': `/discovery/v2/${flowId}`,
        'attribute_mapping': `/discovery/v2/${flowId}/attribute-mapping`,
        'data_cleansing': `/discovery/v2/${flowId}/data-cleansing`,
        'inventory': `/discovery/v2/${flowId}/inventory`,
        'dependencies': `/discovery/v2/${flowId}/dependencies`,
        'tech_debt': `/discovery/v2/${flowId}/tech-debt`
      };
      
      const nextRoute = phaseRoutes[nextPhase as keyof typeof phaseRoutes] || `/discovery/v2/${flowId}`;
      
      toast({
        title: "Flow Continued Successfully",
        description: `Redirecting to ${nextPhase?.replace('_', ' ')} phase...`,
        variant: "default",
      });
      
      // Navigate to the appropriate phase after a short delay
      setTimeout(() => {
        window.location.href = nextRoute;
      }, 2000);
    },
    onError: (error: any, flowId) => {
      console.error('Flow continuation failed:', error);
      
      toast({
        title: "Flow Continuation Failed",
        description: error?.message || `Failed to continue flow ${flowId.substring(0, 8)}...`,
        variant: "destructive",
      });
    }
  });
};

/**
 * Hook for deleting individual V2 flows
 */
export const useFlowDeletionV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  return useMutation({
    mutationFn: async (flowId: string | { flowId: string; forceDelete?: boolean }) => {
      // Handle both string and object parameter formats for backward compatibility
      const actualFlowId = typeof flowId === 'string' ? flowId : flowId.flowId;
      const forceDelete = typeof flowId === 'string' ? true : (flowId.forceDelete ?? true);
      
      console.log('🗑️ V2 Flow deletion request:', { flowId: actualFlowId, forceDelete });
      
      const response = await fetch(`${API_BASE_URL}/api/v2/discovery-flows/flows/${actualFlowId}?force_delete=${forceDelete}`, {
        method: 'DELETE',
        headers: getDefaultHeaders()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.detail || `Failed to delete flow: ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: (data, flowId) => {
      const actualFlowId = typeof flowId === 'string' ? flowId : flowId.flowId;
      
      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows-v2'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation-v2'] });
      queryClient.invalidateQueries({ queryKey: ['flow-details-v2', actualFlowId] });
      
      toast({
        title: "Flow Deleted Successfully",
        description: `Discovery flow ${actualFlowId.substring(0, 8)}... has been deleted with cleanup.`,
        variant: "default",
      });
    },
    onError: (error: any, flowId) => {
      const actualFlowId = typeof flowId === 'string' ? flowId : flowId.flowId;
      console.error('Flow deletion failed:', error);
      
      toast({
        title: "Flow Deletion Failed",
        description: error?.message || `Failed to delete flow ${actualFlowId.substring(0, 8)}...`,
        variant: "destructive",
      });
    }
  });
};

/**
 * Hook for bulk V2 flow operations
 */
export const useBulkFlowOperationsV2 = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const bulkDelete = useMutation({
    mutationFn: async (request: BulkDeleteRequestV2 | { session_ids: string[] }): Promise<BulkDeleteResultV2> => {
      // Handle both V2 format and legacy format
      const flow_ids = 'flow_ids' in request ? request.flow_ids : request.session_ids;
      const force_delete = 'force_delete' in request ? request.force_delete : true;
      
      console.log('🗑️ Bulk V2 flow deletion request:', { flow_ids, force_delete });
      
      // Process deletions sequentially to avoid overwhelming the server
      const results = [];
      let successful = 0;
      let failed = 0;
      
      for (const flowId of flow_ids) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/v2/discovery-flows/flows/${flowId}?force_delete=${force_delete}`, {
            method: 'DELETE',
            headers: getDefaultHeaders()
          });
          
          if (response.ok) {
            const result = await response.json();
            results.push({
              flow_id: flowId,
              success: true,
              result
            });
            successful++;
          } else {
            const error = await response.json().catch(() => ({ error: 'Unknown error' }));
            results.push({
              flow_id: flowId,
              success: false,
              error: error.detail || `Failed to delete: ${response.statusText}`
            });
            failed++;
          }
        } catch (error) {
          results.push({
            flow_id: flowId,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
          failed++;
        }
      }
      
      return {
        batch_results: results,
        total_processed: flow_ids.length,
        successful,
        failed
      };
    },
    onSuccess: (data) => {
      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows-v2'] });
      queryClient.invalidateQueries({ queryKey: ['flow-validation-v2'] });
      
      toast({
        title: "Bulk Operation Completed",
        description: `${data.successful}/${data.total_processed} flows processed successfully.`,
        variant: data.failed > 0 ? "destructive" : "default",
      });
    },
    onError: (error: any) => {
      console.error('Bulk operation failed:', error);
      
      toast({
        title: "Bulk Operation Failed",
        description: error?.message || "Failed to process bulk operation",
        variant: "destructive",
      });
    }
  });
  
  return {
    bulkDelete,
    mutate: bulkDelete.mutate // Alias for backward compatibility
  };
};

/**
 * Hook for real-time V2 flow monitoring
 * Provides WebSocket-like updates for active flows
 */
export const useFlowMonitoringV2 = (flowIds: string[]) => {
  const queryClient = useQueryClient();
  
  return useQuery({
    queryKey: ['flow-monitoring-v2', flowIds],
    queryFn: async () => {
      // Poll multiple flows for status updates
      const promises = flowIds.map(flowId => 
        fetch(`${API_BASE_URL}/api/v2/discovery-flows/flows/${flowId}`, {
          headers: getDefaultHeaders()
        }).then(res => res.ok ? res.json() : null).catch(() => null)
      );
      const results = await Promise.all(promises);
      return results.filter(Boolean);
    },
    enabled: flowIds.length > 0,
    refetchInterval: false, // DISABLED: No automatic monitoring polling
    staleTime: 5000,
  });
};

// API functions - Updated to use unified discovery service
const fetchFlowDetails = async (flowId: string): Promise<IncompleteFlow | null> => {
  try {
    const response = await unifiedDiscoveryService.getFlowStatus(flowId);
    
    // Convert unified response to IncompleteFlow format
    return {
      flow_id: flowId,
      status: response.status,
      current_phase: response.current_phase || 'unknown',
      progress_percentage: response.progress_percentage || 0,
      phases: response.phases || {},
      last_activity: new Date().toISOString(),
      is_resumable: response.status !== 'completed' && response.status !== 'failed'
    };
  } catch (error) {
    console.error(`Failed to fetch flow details for ${flowId}:`, error);
    return null;
  }
};

// Delete flow function - Updated to use unified discovery service
const deleteFlowById = async (flowId: string, forceDelete: boolean = false): Promise<boolean> => {
  try {
    // Use unified discovery service for deletion
    await unifiedDiscoveryService.deleteFlow(flowId, forceDelete);
    return true;
  } catch (error) {
    console.error(`Failed to delete flow ${flowId}:`, error);
    return false;
  }
};

// Continue flow function - Updated to use unified discovery service  
const continueFlowById = async (flowId: string, force_delete: boolean = false): Promise<boolean> => {
  try {
    // Get current flow status first
    const flowStatus = await unifiedDiscoveryService.getFlowStatus(flowId);
    
    if (flowStatus.status === 'completed') {
      console.log(`Flow ${flowId} is already completed`);
      return true;
    }
    
    // Continue with next phase
    const nextPhase = flowStatus.next_phase || 'analysis';
    await unifiedDiscoveryService.executePhase(flowId, nextPhase);
    return true;
  } catch (error) {
    console.error(`Failed to continue flow ${flowId}:`, error);
    return false;
  }
};

// Health check function - Updated to use unified discovery service
const checkFlowHealth = async (flowId: string): Promise<boolean> => {
  try {
    const response = await unifiedDiscoveryService.getFlowStatus(flowId);
    return response.status !== 'failed';
  } catch (error) {
    console.error(`Health check failed for flow ${flowId}:`, error);
    return false;
  }
}; 