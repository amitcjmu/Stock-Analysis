import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';
import { masterFlowService } from '@/services/api/masterFlowService';
import { useToast } from '@/components/ui/use-toast';

export const useAttributeMappingNavigation = (flowState?: unknown, mappingProgress?: unknown): unknown => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  // SMART FLOW RESOLUTION: Use masterFlowService to get the correct flow ID
  // before initializing useUnifiedDiscoveryFlow
  const getCorrectFlowId = useCallback(async (inputId: string) => {
    if (!inputId) return null;

    try {
      // CC FIX: If we already have a valid UUID flow ID, return it directly
      // This allows completed flows to transition to next phase (e.g., field_mapping -> data_cleansing)
      // The backend will validate flow existence and permissions
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (inputId.match(uuidRegex)) {
        console.log('✅ Using provided flow ID directly (allows completed flows):', inputId);
        return inputId;
      }

      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

      // Use masterFlowService smart resolution to find the correct flow
      const flows = await masterFlowService.getActiveFlows(clientAccountId, engagementId);

      // First try exact match
      const exactMatch = flows.find(f => f.flowId === inputId);
      if (exactMatch) return inputId;

      // Then try to find flow by data_import_id
      const importMatch = flows.find(f => f.metadata?.data_import_id === inputId);
      if (importMatch) return importMatch.flowId;

      // Fallback to first available flow
      if (flows.length > 0) return flows[0].flowId;

      return inputId; // Return original if no matches found
    } catch (error) {
      console.warn('Failed to resolve flow ID:', error);
      return inputId;
    }
  }, [client?.id, engagement?.id]);

  // Get the resolved flow ID for useUnifiedDiscoveryFlow
  const { flowState: flow, executeFlowPhase: updatePhase } = useUnifiedDiscoveryFlow(flowState?.flow_id);
  const { toast } = useToast();

  const handleContinueToDataCleansing = useCallback(async () => {
    try {
      // CC FIX: Check multiple possible property names for flow_id
      // flowState might have: flow_id, flowId, id
      const rawFlowId =
        flowState?.flow_id ||
        flowState?.flowId ||
        flowState?.id ||
        flow?.flow_id ||
        flow?.flowId ||
        flow?.id;

      console.log('🔍 DEBUG: Flow ID resolution:', {
        flowState_flow_id: flowState?.flow_id,
        flowState_flowId: flowState?.flowId,
        flowState_id: flowState?.id,
        flow_flow_id: flow?.flow_id,
        flow_flowId: flow?.flowId,
        flow_id: flow?.id,
        rawFlowId
      });

      const flowId = rawFlowId ? await getCorrectFlowId(rawFlowId) : null;

      if (!flowId) {
        toast({
          title: "Error",
          description: "No active flow found. Please start a new discovery flow.",
          variant: "destructive"
        });
        return;
      }

      // Check if flow is paused and needs to be resumed
      const flowStatus = flowState?.status || flow?.status;

      // Handle cancelled flows with detailed feedback
      if (flowStatus === 'cancelled' || flowStatus === 'failed' || flowStatus === 'error') {
        console.error('🚨 Flow is in cancelled/failed state:', flowStatus);

        let title = "Flow Cannot Continue";
        let description = "This flow has an issue that prevents continuation.";

        switch (flowStatus) {
          case 'cancelled':
            title = "Flow Was Deleted";
            description = "This flow has been deleted and cannot be continued. If you did not delete this flow, please report this issue. You can create a new discovery flow to start over.";
            break;
          case 'failed':
            title = "Flow Failed";
            description = "This flow encountered an error and failed. Please create a new discovery flow to start over.";
            break;
          case 'error':
            title = "Flow Error";
            description = "This flow is in an error state. Please create a new discovery flow to start over.";
            break;
        }

        toast({
          title,
          description,
          variant: "destructive"
        });

        // Navigate to flow creation page - NO automatic deletion here
        navigate('/discovery/cmdb-import');
        return;
      }

      // For any flow state, just execute the data cleansing phase with approved mappings
      try {
        const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
        const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

        // If flow is failed, retry it first with error handling
        if (flowStatus === 'failed') {
          try {
            console.log('⚠️ Flow is in failed state, retrying first');
            const retryResult = await masterFlowService.retryFlow(flowId, clientAccountId, engagementId);
            console.log('✅ Flow retry successful');

            // Verify retry was successful before proceeding
            if (!retryResult?.data?.success) {
              throw new Error('Retry operation did not succeed');
            }

            // Wait for flow state to stabilize after retry
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (retryError) {
            console.warn('⚠️ Flow retry failed, continuing with phase execution:', retryError);
            // Continue with phase execution even if retry fails
          }
        }

        // Prepare mapping data with defaults for unmapped fields
        const processedMappingData = {
          ...mappingProgress,
          // Add instruction to map unmapped fields to custom_attributes
          default_unmapped_target: 'custom_attributes',
          apply_defaults_to_unmapped: true
        };

        // Execute the next phase with mapping approval data using discovery flow service
        // CC FIX: Pass force=true to allow phase execution on completed flows (phase transitions)
        await masterFlowService.executePhase(
          flowId,
          'data_cleansing',
          {
            approved_mappings: true,
            mapping_data: processedMappingData,
            phase_transition: 'field_mapping_approval_to_data_cleansing',
            // Include instruction for handling unmapped fields
            unmapped_fields_strategy: 'map_to_custom_attributes'
          },
          clientAccountId,
          engagementId,
          true  // force execution to allow phase transitions on completed flows
        );

        // Navigate immediately to show loading state on data cleansing page
        navigate(`/discovery/data-cleansing/${flowId}`);

        // Show toast after navigation
        toast({
          title: "Flow Continued",
          description: "Data cleansing phase is now processing. This may take 15-30 seconds.",
        });
      } catch (executeError) {
        console.error('Failed to continue flow:', executeError);
        toast({
          title: "Continue Failed",
          description: "Failed to continue the discovery flow. Please try again.",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Failed to proceed to data cleansing:', error);
      toast({
        title: "Error",
        description: "Failed to continue to data cleansing. Please try again.",
        variant: "destructive"
      });
    }
  }, [flow, flowState, navigate, mappingProgress, toast, client?.id, engagement?.id, getCorrectFlowId]);

  return {
    handleContinueToDataCleansing
  };
};
