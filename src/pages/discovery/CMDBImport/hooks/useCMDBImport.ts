import { useState, useCallback, useEffect } from 'react';
import { useUnifiedDiscoveryFlow } from '@/hooks/useUnifiedDiscoveryFlow';
import { useFileUpload } from './useFileUpload';
import { useToast } from '@/hooks/use-toast';

export const useCMDBImport = () => {
  const { toast } = useToast();
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

  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    refreshFlow,
    initializeFlow,
    isInitializing,
  } = useUnifiedDiscoveryFlow(activeFlowId);
  
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

  return {
    // File upload state and handlers
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    onFileUpload,
    onDragOver,
    onDragLeave,
    onDrop,
    
    // Loading states
    isStartingFlow: isInitializing,
    
    // Actions
    startFlow: handleStartFlow,

    // Unified Flow State
    activeFlowId,
    flowState,
    isFlowStateLoading,
    flowStateError,
    refreshFlow,
  };
};