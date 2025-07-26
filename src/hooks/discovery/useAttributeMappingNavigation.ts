import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';
import { useToast } from '@/components/ui/use-toast';

export const useAttributeMappingNavigation = (flowState?: unknown, mappingProgress?: unknown): any => {
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

      if (flowStatus === 'waiting_for_approval' || flowStatus === 'waiting_for_user_approval') {
        // Execute the next phase for flows waiting for approval
        toast({
          title: "Continuing Discovery Flow",
          description: "Applying field mappings and continuing with data cleansing...",
        });

        try {
          const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
          const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

          // Execute the next phase with mapping approval data
          await masterFlowServiceExtended.executePhase(
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
      } else if (flowStatus === 'paused') {
        // Resume truly paused flows
        toast({
          title: "Resuming Discovery Flow",
          description: "Resuming paused discovery flow...",
        });

        try {
          const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
          const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

          await masterFlowServiceExtended.resumeFlow(flowId, clientAccountId, engagementId);

          toast({
            title: "Flow Resumed",
            description: "Discovery flow has been resumed.",
          });

          // Navigate to data cleansing after a short delay
          setTimeout(() => {
            navigate(`/discovery/data-cleansing/${flowId}`);
          }, 1500);
        } catch (resumeError) {
          console.error('Failed to resume flow:', resumeError);
          toast({
            title: "Resume Failed",
            description: "Failed to resume the discovery flow. Please try again.",
            variant: "destructive"
          });
        }
      } else {
        // Flow is not paused, try to resume it first then continue
        console.log('🔍 Flow is not paused, attempting to resume and continue to data_cleansing');

        try {
          const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
          const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";

          // Try to resume the flow first
          const resumeResult = await masterFlowServiceExtended.resumeFlow(flowId, clientAccountId, engagementId);
          console.log('✅ Flow resumed successfully:', resumeResult);

          toast({
            title: "Flow Resumed",
            description: "Discovery flow has been resumed and is continuing to data cleansing.",
          });

          // Navigate to data cleansing after a short delay
          setTimeout(() => {
            navigate(`/discovery/data-cleansing/${flowId}`);
          }, 1500);

        } catch (resumeError) {
          console.error('❌ Failed to resume flow, trying direct phase execution:', resumeError);

          // If resume fails, try direct phase execution as fallback
          const phaseData = {
            completed_phases: [...(flow.phases ? Object.keys(flow.phases).filter(p => flow.phases[p]) : []), 'attribute_mapping'],
            current_phase: 'data_cleansing',
            progress_data: mappingProgress
          };

          console.log('🔍 Falling back to direct phase execution with data:', phaseData);
          await updatePhase('data_cleansing', phaseData);
          navigate(`/discovery/data-cleansing/${flowId}`);
        }
      }
    } catch (error) {
      console.error('Failed to proceed to data cleansing:', error);
      toast({
        title: "Error",
        description: "Failed to continue to data cleansing. Please try again.",
        variant: "destructive"
      });
    }
  }, [flow, flowState, updatePhase, navigate, mappingProgress, toast]);

  return {
    handleContinueToDataCleansing
  };
};
