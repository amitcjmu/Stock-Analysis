import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '@/hooks/useUnifiedDiscoveryFlow';
import { useFileUpload } from './useFileUpload';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { 
  useIncompleteFlowDetectionV2, 
  useFlowResumptionV2
} from '@/hooks/discovery/useFlowOperations';
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { apiCall } from '@/config/api';

export const useCMDBImport = () => {
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
  const [conflictFlows, setConflictFlows] = useState<any[]>([]);

  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    refreshFlow,
    initializeFlow,
    isInitializing,
    pollingStatus,
  } = useUnifiedDiscoveryFlow(activeFlowId);
  
  // Flow Management hooks
  const { data: incompleteFlowsData, isLoading: checkingFlows, refetch: refetchIncompleteFlows } = useIncompleteFlowDetectionV2();
  const flowResumption = useFlowResumptionV2();
  const { 
    deleteFlow, 
    bulkDeleteFlows, 
    isDeleting 
  } = useFlowDeletion({ deletion_source: 'manual' });
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;
  
  // Effect to set active flow ID once upload is done
  useEffect(() => {
    if (uploadedFiles.length > 0 && uploadedFiles[0].flow_id) {
      setActiveFlowId(uploadedFiles[0].flow_id);
    }
  }, [uploadedFiles]);


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
    try {
      await deleteFlow(flowId);
      refetchIncompleteFlows();
    } catch (error) {
      console.error('Failed to delete flow:', error);
    }
  }, [deleteFlow, refetchIncompleteFlows]);

  const handleBatchDeleteFlows = useCallback(async (flowIds: string[]) => {
    try {
      await bulkDeleteFlows(flowIds);
      refetchIncompleteFlows();
    } catch (error) {
      console.error('Failed to delete flows:', error);
    }
  }, [bulkDeleteFlows, refetchIncompleteFlows]);

  const handleViewFlowDetails = useCallback((flowId: string, phase: string) => {
    const actualPhase = phase || 'field_mapping';
    const route = getDiscoveryPhaseRoute(actualPhase, flowId);
    navigate(route);
  }, [navigate]);

  // Poll for flow status updates
  useEffect(() => {
    const pollFlowStatus = async () => {
      const processingFiles = uploadedFiles.filter(f => 
        f.flow_id && 
        (f.status === 'processing' || f.flow_status === 'running' || f.flow_status === 'active')
      );

      for (const file of processingFiles) {
        try {
          const response = await apiCall(`/api/v1/flows/${file.flow_id}/status`, {
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

    if (uploadedFiles.some(f => f.flow_id && (f.status === 'processing' || f.flow_status === 'running'))) {
      const interval = setInterval(pollFlowStatus, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [uploadedFiles, setUploadedFiles, getAuthHeaders]);

  // Start Discovery Flow
  const startDiscoveryFlow = useCallback(async () => {
    const uploadedFile = uploadedFiles[0];
    if (!uploadedFile) {
      toast({
        title: "Error",
        description: "No uploaded file found.",
        variant: "destructive",
      });
      return;
    }

    if (!uploadedFile.flow_id) {
      toast({
        title: "Error",
        description: "No flow ID found.",
        variant: "destructive",
      });
      return;
    }

    // Navigate to attribute mapping phase (next step after data import)
    const route = getDiscoveryPhaseRoute('attribute_mapping', uploadedFile.flow_id);
    navigate(route);
    toast({
      title: "Starting Discovery Flow",
      description: "Navigating to attribute mapping phase.",
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
    isDeletingFlows: isDeleting,
    
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
  };
};