import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { masterFlowService } from '@/services/api/masterFlowService';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { AgentGuidanceModal } from './AgentGuidanceModal';
import type { FlowContinuationResponse, UserGuidance, RoutingContext } from '@/types/api/flow-continuation';

interface FlowResumptionHandlerProps {
  children: (props: {
    resumeFlow: (flowId: string) => void;
    isResuming: boolean;
  }) => React.ReactNode;
}

export const FlowResumptionHandler: React.FC<FlowResumptionHandlerProps> = ({ children }) => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { client, engagement } = useAuth();

  // State for agent guidance modal
  const [guidanceState, setGuidanceState] = useState<{
    isOpen: boolean;
    guidance: UserGuidance | null;
    routingContext: RoutingContext | null;
    flowId: string | null;
  }>({
    isOpen: false,
    guidance: null,
    routingContext: null,
    flowId: null,
  });

  const resumeMutation = useMutation({
    mutationFn: async (flowId: string) => {
      if (!client?.id || !engagement?.id) {
        throw new Error('Missing client or engagement context for flow resumption');
      }
      return masterFlowService.resumeFlow(flowId, client.id, engagement.id);
    },
    onSuccess: (response, flowId) => {
      console.log('🎉 Flow resumption success:', response);

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['incomplete-flows'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-flows'] });

      // Extract the flow continuation data
      const data = response.data;

      // Check if we have agent guidance to display
      if (data.user_guidance) {
        // Show the guidance in a modal
        setGuidanceState({
          isOpen: true,
          guidance: data.user_guidance,
          routingContext: data.routing_context || null,
          flowId: flowId,
        });

        console.log('🤖 Agent Guidance:', {
          primary: data.user_guidance.primary_message,
          actions: data.user_guidance.action_items,
          userActions: data.user_guidance.user_actions,
        });
      } else {
        // No guidance - proceed with navigation
        handleNavigation(data, flowId);

        // Show success toast
        toast({
          title: "Flow Resumed",
          description: "The discovery flow has been resumed successfully.",
        });
      }
    },
    onError: (error: any) => {
      console.error('❌ Flow resumption error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to resume flow",
        variant: "destructive",
      });
    },
  });

  const handleNavigation = (data: FlowContinuationResponse, flowId: string) => {
    const target = data.routing_context?.target_page || data.routing_context?.recommended_page;
    if (target) {
      navigate(target);
      return;
    }
    if (data.current_phase) {
      navigate(getDiscoveryPhaseRoute(data.current_phase, flowId));
      return;
    }
    navigate(getDiscoveryPhaseRoute('field_mapping', flowId));
  };

  const handleCloseGuidance = () => {
    // Navigate after closing if we have routing context
    const target = guidanceState.routingContext?.target_page || guidanceState.routingContext?.recommended_page;
    if (target) {
      navigate(target);
    }

    // Clear the guidance state
    setGuidanceState({
      isOpen: false,
      guidance: null,
      routingContext: null,
      flowId: null,
    });
  };

  return (
    <>
      {children({
        resumeFlow: (flowId: string) => resumeMutation.mutate(flowId),
        isResuming: resumeMutation.isPending,
      })}

      <AgentGuidanceModal
        isOpen={guidanceState.isOpen}
        onClose={handleCloseGuidance}
        guidance={guidanceState.guidance}
        routingContext={guidanceState.routingContext}
        flowId={guidanceState.flowId || undefined}
      />
    </>
  );
};
