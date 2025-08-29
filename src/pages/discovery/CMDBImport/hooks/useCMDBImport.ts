import { useState } from 'react'
import { useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '@/hooks/useUnifiedDiscoveryFlow';
import { useFileUpload } from './useFileUpload';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import {
  useIncompleteFlowDetection,
  useFlowResumption
} from '@/hooks/discovery/useFlowOperations';
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { apiCall } from '@/config/api';

export const useCMDBImport = (): JSX.Element => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const {
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    onFileUpload,
    onDragOver,
    onDragLeave,
    onDrop,
  } = useFileUpload();

  const [activeFlowId, setActiveFlowId] = useState<string | null>(null);
  const [showFlowManager, setShowFlowManager] = useState(false);
  interface ConflictFlow {
    flow_id: string;
    phase: string;
    status: string;
    created_at: string;
    updated_at: string;
    [key: string]: unknown;
  }

  const [conflictFlows, setConflictFlows] = useState<ConflictFlow[]>([]);

  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    refreshFlow,
    initializeFlow,
    isInitializing,
    pollingStatus,
  } = useUnifiedDiscoveryFlow(activeFlowId);

  // Flow Management hooks - only run when we have proper authentication context
  const { data: incompleteFlowsData, isLoading: checkingFlows, refetch: refetchIncompleteFlows } = useIncompleteFlowDetection();
  const flowResumption = useFlowResumption();
  const [deletionState, deletionActions] = useFlowDeletion(
    // onDeletionComplete callback
    () => {
      refetchIncompleteFlows();
    },
    // onDeletionError callback
    (error) => {
      console.error('Flow deletion error:', error);
      toast({
        title: "Deletion Failed",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  );

  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Effect to set active flow ID once upload is done
  useEffect(() => {
    if (uploadedFiles.length > 0 && uploadedFiles[0].flow_id) {
      const newFlowId = uploadedFiles[0].flow_id;
      if (activeFlowId !== newFlowId) {
        console.log('🔄 Setting active flow ID:', {
          previous: activeFlowId,
          new: newFlowId,
          file: uploadedFiles[0].name
        });
        setActiveFlowId(newFlowId);
      }
    }
  }, [uploadedFiles, activeFlowId]);


  const handleStartFlow = useCallback(async () => {
    const uploadedFile = uploadedFiles[0];
    if (!uploadedFile) {
        toast({
            title: 'No file found',
            description: 'Please upload a file first.',
            variant: 'destructive',
        });
        return;
    }

    if (!uploadedFile.flow_id) {
        toast({
            title: 'Flow not ready',
            description: 'The discovery flow has not been initialized yet. Please wait.',
            variant: 'destructive',
        });
        return;
    }

    // The flow is already started by the backend, this is just for UI sync
    setActiveFlowId(uploadedFile.flow_id);
    toast({
        title: 'Monitoring Discovery Flow',
        description: 'AI agents are analyzing your data. See progress below.',
    });
  }, [uploadedFiles, toast]);

  // Flow Management Handlers
  const handleContinueFlow = useCallback(async (flowId: string) => {
    try {
      await flowResumption.mutateAsync(flowId);
      refetchIncompleteFlows();
    } catch (error) {
      console.error('Failed to resume flow:', error);
    }
  }, [flowResumption, refetchIncompleteFlows]);

  const handleDeleteFlow = useCallback(async (flowId: string) => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }

    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id
    );
  }, [deletionActions, client, engagement, user, toast]);

  const handleBatchDeleteFlows = useCallback(async (flowIds: string[]) => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }

    await deletionActions.requestDeletion(
      flowIds,
      client.id,
      engagement?.id,
      'bulk_cleanup',
      user?.id
    );
  }, [deletionActions, client, engagement, user, toast]);

  const handleViewFlowDetails = useCallback((flowId: string, phase: string) => {
    const actualPhase = phase || 'field_mapping';
    const route = getDiscoveryPhaseRoute(actualPhase, flowId);
    navigate(route);
  }, [navigate]);

  // Poll for flow status updates
  useEffect(() => {
    const pollFlowStatus = async (): Promise<void> => {
      const processingFiles = uploadedFiles.filter(f =>
        f.flow_id &&
        (f.status === 'processing' || f.flow_status === 'running' || f.flow_status === 'active')
      );

      for (const file of processingFiles) {
        try {
          const response = await apiCall(`/api/v1/unified-discovery/flows/${file.flow_id}/status`, {
            headers: getAuthHeaders()
          });

          if (response.status === 'completed') {
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  status: 'approved',
                  flow_status: 'completed',
                  discovery_progress: 100
                };
              }
              return f;
            }));
          } else if (response.status === 'waiting_for_approval' || response.awaitingUserApproval) {
            // Stop polling when waiting for approval
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  status: 'waiting_approval',
                  flow_status: 'waiting_for_approval',
                  discovery_progress: response.progress || 25,
                  current_phase: response.currentPhase || 'field_mapping'
                };
              }
              return f;
            }));
          } else if (response.status === 'failed' || response.status === 'error') {
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  status: 'error',
                  flow_status: 'failed',
                  error_message: response.error || 'Processing failed'
                };
              }
              return f;
            }));
          } else {
            // Update progress
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  discovery_progress: response.progress || f.discovery_progress,
                  current_phase: response.currentPhase || f.current_phase
                };
              }
              return f;
            }));
          }
        } catch (error) {
          console.error(`Error polling flow status for ${file.flow_id}:`, error);
        }
      }
    };

    if (uploadedFiles.some(f =>
      f.flow_id &&
      (f.status === 'processing' || f.flow_status === 'running' || f.flow_status === 'active') &&
      f.flow_status !== 'waiting_for_approval' &&
      f.status !== 'waiting_approval'
    )) {
      const interval = setInterval(pollFlowStatus, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [uploadedFiles, setUploadedFiles, getAuthHeaders]);

  // Start Discovery Flow
  const startDiscoveryFlow = useCallback(async () => {
    const uploadedFile = uploadedFiles[0];
    if (!uploadedFile) {
      console.error('❌ Navigation Error: No uploaded file found');
      toast({
        title: "Error",
        description: "No uploaded file found.",
        variant: "destructive",
      });
      return;
    }

    if (!uploadedFile.flow_id) {
      console.error('❌ Navigation Error: No flow ID found in uploaded file:', uploadedFile);
      toast({
        title: "Error",
        description: "No flow ID found. Please try uploading the file again.",
        variant: "destructive",
      });
      return;
    }

    // Debug logging to help trace navigation issues
    console.log('🎯 Navigation: Starting discovery flow with:', {
      file: uploadedFile.name,
      flow_id: uploadedFile.flow_id,
      status: uploadedFile.status,
      current_phase: uploadedFile.current_phase
    });

    // Resume/execute discovery flow so field mapping runs before navigation
    try {
      await apiCall(`/api/v1/unified-discovery/flows/${uploadedFile.flow_id}/execute`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ phase: 'field_mapping_suggestions', phase_input: {}, force: false })
      });
    } catch (e) {
      console.warn('Flow execute call failed (will still navigate):', e);
    }

    // Navigate to attribute mapping phase (next step after data import)
    const route = getDiscoveryPhaseRoute('attribute_mapping', uploadedFile.flow_id);
    console.log('🔗 Navigation: Navigating to route:', route);

    navigate(route);
    toast({
      title: "Navigating to Attribute Mapping",
      description: `Opening flow ${uploadedFile.flow_id} for field mapping review.`,
    });
  }, [uploadedFiles, navigate, toast]);

  return {
    // File upload state and handlers
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    handleFileUpload: onFileUpload,
    handleDragOver: onDragOver,
    handleDragLeave: onDragLeave,
    handleDrop: onDrop,

    // Flow management
    showFlowManager,
    setShowFlowManager,
    conflictFlows,
    incompleteFlows,
    hasIncompleteFlows,
    checkingFlows,
    handleContinueFlow,
    handleDeleteFlow,
    handleBatchDeleteFlows,
    handleViewFlowDetails,

    // Loading states
    isStartingFlow: isInitializing,
    isDeletingFlows: deletionState.isDeleting,

    // Actions
    startFlow: handleStartFlow,
    startDiscoveryFlow,

    // Unified Flow State
    activeFlowId,
    flowState,
    isFlowStateLoading,
    flowStateError,
    refreshFlow,
    pollingStatus,

    // Deletion state and actions for modal
    deletionState,
    deletionActions,
  };
};
