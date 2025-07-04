import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { apiCall } from '../../config/api';
import { useToast } from '../../hooks/use-toast';

export const useAttributeMappingNavigation = (flowState?: any, mappingProgress?: any) => {
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
      
      if (flowStatus === 'paused' || flowStatus === 'waiting_for_approval' || flowStatus === 'waiting_for_user_approval') {
        // Resume the paused flow
        toast({
          title: "Resuming Discovery Flow",
          description: "Applying field mappings and continuing with data cleansing...",
        });
        
        try {
          const response = await apiCall(`/api/v1/discovery/flow/${flowId}/resume`, {
            method: 'POST',
            body: JSON.stringify({
              field_mappings: flowState?.field_mappings || {},
              notes: 'User approved field mappings from UI',
              approval_timestamp: new Date().toISOString()
            })
          });
          
          if (response.success) {
            toast({
              title: "Flow Resumed",
              description: "Discovery flow is now continuing with data cleansing phase.",
            });
            
            // Navigate to data cleansing after a short delay
            setTimeout(() => {
              navigate('/discovery/data-cleansing');
            }, 1500);
          } else {
            throw new Error(response.message || 'Failed to resume flow');
          }
        } catch (resumeError) {
          console.error('Failed to resume flow:', resumeError);
          toast({
            title: "Resume Failed",
            description: "Failed to resume the discovery flow. Please try again.",
            variant: "destructive"
          });
        }
      } else {
        // Flow is not paused, just navigate to next phase
        await updatePhase('data_cleansing', { 
          completed_phases: [...(flow.phases ? Object.keys(flow.phases).filter(p => flow.phases[p]) : []), 'attribute_mapping'],
          current_phase: 'data_cleansing',
          progress_data: mappingProgress 
        });
        navigate('/discovery/data-cleansing');
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