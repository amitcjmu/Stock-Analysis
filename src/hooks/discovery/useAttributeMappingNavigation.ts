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
  const { flowState: flow, executeFlowPhase: updatePhase } = useUnifiedDiscoveryFlow(flowState?.flow_id);
  const { toast } = useToast();

  const handleContinueToDataCleansing = useCallback(async () => {
    try {
      const flowId = flowState?.flow_id || flow?.flow_id;

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
      toast({
        title: "Continuing Discovery Flow",
        description: "Applying field mappings and continuing with data cleansing...",
      });

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

        // Execute the next phase with mapping approval data using discovery flow service
        await masterFlowService.executePhase(
          flowId,
          'data_cleansing',
          {
            approved_mappings: true,
            mapping_data: mappingProgress,
            phase_transition: 'field_mapping_approval_to_data_cleansing'
          },
          clientAccountId,
          engagementId
        );

        toast({
          title: "Flow Continued",
          description: "Discovery flow is now continuing with data cleansing phase.",
        });

        // Navigate to data cleansing after a short delay
        setTimeout(() => {
          navigate(`/discovery/data-cleansing/${flowId}`);
        }, 1500);
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
  }, [flow, flowState, navigate, mappingProgress, toast, client?.id, engagement?.id]);

  return {
    handleContinueToDataCleansing
  };
};
