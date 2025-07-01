import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/config/api';
import { UploadFile } from '../CMDBImport.types';
import { useFileUpload } from './useFileUpload';
import { useFlowManagement } from './useFlowManagement';

export const useCMDBImport = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();
  const [isStartingFlow, setIsStartingFlow] = useState(false);
  const [isLoadingFlowDetails, setIsLoadingFlowDetails] = useState(false);

  const fileUpload = useFileUpload();
  const flowManagement = useFlowManagement();

  // Fetch flow details for existing flows
  const fetchFlowDetails = useCallback(async (file: UploadFile) => {
    if (!file.flow_id || file.flow_summary) {
      return; // Skip if no flow_id or already has summary
    }
    
    try {
      const flowResponse = await apiCall(`/api/v1/discovery/flow/${file.flow_id}/processing-status`);
      
      const flowSummary = {
        total_assets: flowResponse.total_records || 0,
        errors: flowResponse.errors || 0,
        warnings: flowResponse.warnings || 0,
        phases_completed: [
          ...(flowResponse.data_import_completed ? ['data_import'] : []),
          ...(flowResponse.attribute_mapping_completed ? ['attribute_mapping'] : []),
          ...(flowResponse.data_cleansing_completed ? ['data_cleansing'] : []),
          ...(flowResponse.inventory_completed ? ['inventory'] : []),
          ...(flowResponse.dependencies_completed ? ['dependencies'] : []),
          ...(flowResponse.tech_debt_completed ? ['tech_debt'] : [])
        ],
        agent_insights: flowResponse.agent_insights || []
      };
      
      // Update the file with flow details
      fileUpload.setUploadedFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { 
              ...f, 
              flow_status: flowResponse.status,
              flow_summary: flowSummary,
              current_phase: flowResponse.current_phase || 'inventory',
              discovery_progress: flowResponse.progress || 0,
              status: flowResponse.status === 'completed' ? 'approved' : f.status
            }
          : f
      ));
      
    } catch (error) {
      console.error('Error fetching flow details for file:', file.name, error);
    }
  }, [fileUpload.setUploadedFiles]);

  // Initialize flow details for existing uploaded files
  useEffect(() => {
    const initializeFlowDetails = async () => {
      if (fileUpload.uploadedFiles.length > 0 && !isLoadingFlowDetails) {
        setIsLoadingFlowDetails(true);
        
        // Fetch details for all files with flow_id but no flow_summary
        const filesToUpdate = fileUpload.uploadedFiles.filter(f => f.flow_id && !f.flow_summary);
        
        if (filesToUpdate.length > 0) {
          console.log(`Initializing flow details for ${filesToUpdate.length} files`);
          await Promise.all(filesToUpdate.map(fetchFlowDetails));
        }
        
        setIsLoadingFlowDetails(false);
      }
    };
    
    initializeFlowDetails();
  }, [fileUpload.uploadedFiles.length, fetchFlowDetails, isLoadingFlowDetails]);

  // Retrieve stored data for discovery flow
  const getStoredImportData = useCallback(async (importSessionId: string | undefined): Promise<any[]> => {
    console.log('getStoredImportData called with:', importSessionId);
    if (!importSessionId) {
      console.error("No import session ID provided");
      return [];
    }
  
    try {
      const response = await apiCall(`/data-import/import/${importSessionId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });
  
      if (response.data && Array.isArray(response.data)) {
        console.log(`Retrieved ${response.data.length} records.`);
        return response.data;
      } else {
        console.warn("No data array found in the response:", response);
        return [];
      }
    } catch (error) {
      console.error("Error retrieving stored import data:", error);
      toast({
        title: "Data Retrieval Error",
        description: "Could not retrieve processed data for the discovery flow.",
        variant: "destructive",
      });
      return [];
    }
  }, [getAuthHeaders, toast]);

  // Start Discovery Flow or Navigate to Results
  const startDiscoveryFlow = useCallback(async () => {
    const uploadedFile = fileUpload.uploadedFiles[0];
    if (!uploadedFile) {
        toast({
            title: "Error",
            description: "No uploaded file found. Please upload a file first.",
            variant: "destructive",
        });
        return;
    }

    // ✅ Check for CrewAI flow_id first (preferred for navigation)
    if (!uploadedFile.flow_id) {
        toast({
            title: "Error",
            description: "No CrewAI Flow ID found. The discovery flow may not have been created properly.",
            variant: "destructive",
        });
        return;
    }

    setIsStartingFlow(true); // ✅ Set loading state

    try {
        console.log(`Processing Discovery Flow with CrewAI Flow ID: ${uploadedFile.flow_id}`);
        console.log(`Flow Status: ${uploadedFile.flow_status}, Has Summary: ${!!uploadedFile.flow_summary}`);
        
        // ✅ SMART NAVIGATION: Handle both new flows and completed flows
        if (uploadedFile.flow_summary && uploadedFile.flow_status === 'completed') {
            // Flow is completed - navigate to results/next appropriate phase
            console.log('Flow is completed, navigating to results phase');
            
            // Check current phase from the flow summary or default to inventory
            const currentPhase = uploadedFile.current_phase || 'inventory';
            
            // Navigate to the appropriate discovery phase based on completion status
            switch (currentPhase) {
                case 'inventory':
                    navigate(`/discovery/inventory`);
                    break;
                case 'dependencies': 
                    navigate(`/discovery/dependencies`);
                    break;
                case 'tech_debt':
                    navigate(`/discovery/tech-debt`);
                    break;
                case 'attribute_mapping':
                    navigate(`/discovery/attribute-mapping`);
                    break;
                case 'data_cleansing':
                    navigate(`/discovery/data-cleansing`);
                    break;
                default:
                    // Default to inventory phase for completed flows
                    navigate(`/discovery/inventory`);
            }
            
            toast({
                title: "Navigating to Results",
                description: `Proceeding to ${currentPhase.replace('_', ' ')} phase with your completed flow.`,
            });
            
        } else {
            // New flow - verify data exists and start discovery process
            if (!uploadedFile.importSessionId) {
                throw new Error("No import session found. The discovery flow cannot start.");
            }
            
            // Retrieve stored data to ensure it's available for the flow
            const storedData = await getStoredImportData(uploadedFile.importSessionId);
            console.log('Retrieved stored data for flow:', { 
              count: storedData.length,
              hasData: storedData.length > 0
            });

            if (storedData.length === 0) {
              throw new Error("No data found for the import session. The discovery flow cannot start.");
            }

            // ✅ Navigate to data import phase (new flows should start with data import)
            console.log('Starting new discovery flow');
            navigate(`/discovery/data-import`);
            
            toast({
                title: "Starting Discovery Flow",
                description: "Initiating AI-powered analysis of your uploaded data.",
            });
        }

    } catch (error) {
        const errorMessage = (error instanceof Error) ? error.message : "An unknown error occurred.";
        console.error("Failed to process Discovery Flow:", error);
        toast({
            title: "Failed to Process Discovery Flow",
            description: errorMessage,
            variant: "destructive",
        });
    } finally {
      setIsStartingFlow(false); // ✅ Reset loading state
    }
  }, [fileUpload.uploadedFiles, navigate, toast, getStoredImportData]);

  return {
    // File upload state and actions
    uploadedFiles: fileUpload.uploadedFiles,
    setUploadedFiles: fileUpload.setUploadedFiles,
    selectedCategory: fileUpload.selectedCategory,
    isDragging: fileUpload.isDragging,
    handleFileUpload: fileUpload.handleFileUpload,
    handleDragOver: fileUpload.handleDragOver,
    handleDragLeave: fileUpload.handleDragLeave,
    handleDrop: fileUpload.handleDrop,
    
    // Flow management
    ...flowManagement,
    
    // Loading states
    isStartingFlow,
    isLoadingFlowDetails,
    
    // Actions
    startDiscoveryFlow,
    fetchFlowDetails,
    getStoredImportData
  };
};