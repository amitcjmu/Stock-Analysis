import React, { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload,
  FileCheck, 
  AlertTriangle, 
  CheckCircle, 
  Shield,
  Brain,
  Database,
  Monitor,
  Activity,
  FileText,
  AlertCircle,
  Loader2,
  Eye,
  ArrowRight,
  FileSpreadsheet,
  Lock,
  Scan,
  UserCheck,
  Cog,
  XCircle,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { DataImportValidationService, ValidationAgentResult } from '@/services/dataImportValidationService';
import { apiCall } from '@/config/api';
import UniversalProcessingStatus from '@/components/discovery/UniversalProcessingStatus';
import { PollingStatusIndicator, PollingControls } from '@/components/common/PollingControls';
import { useComprehensiveRealTimeMonitoring } from '@/hooks/useRealTimeProcessing';

// Flow Management Components
import { UploadBlocker } from '@/components/discovery/UploadBlocker';
import { IncompleteFlowManager } from '@/components/discovery/IncompleteFlowManager';
import { 
  useIncompleteFlowDetectionV2, 
  useFlowResumptionV2, 
  useFlowDeletionV2, 
  useBulkFlowOperationsV2 
} from '@/hooks/discovery/useIncompleteFlowDetectionV2';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

// Data Import Validation Agents
// interface DataImportAgent {
//   id: string;
//   name: string;
//   role: string;
//   icon: any;
//   status: 'pending' | 'analyzing' | 'completed' | 'failed';
//   result?: ValidationAgentResult;
// }

interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'validating' | 'processing' | 'approved' | 'approved_with_warnings' | 'rejected' | 'error';
  agentResults: ValidationAgentResult[];
  validationSessionId?: string;
  importSessionId?: string;
  flow_id?: string;  // ✅ CrewAI-generated flow ID
  // Additional progress tracking properties
  upload_progress?: number;
  validation_progress?: number;
  discovery_progress?: number;  // NEW: Track CrewAI flow progress
  agents_completed?: number;
  total_agents?: number;
  // Security clearance properties
  security_clearance?: boolean;
  privacy_clearance?: boolean;
  format_validation?: boolean;
  agent_results?: ValidationAgentResult[];
  // Error handling
  error_message?: string;
  // NEW: Flow tracking properties
  current_phase?: string;
  flow_status?: 'running' | 'completed' | 'failed' | 'paused';
  flow_summary?: {
    total_assets: number;
    errors: number;
    warnings: number;
    phases_completed: string[];
    agent_insights?: any[];
  };
}

// Upload categories for proper data handling
const uploadCategories = [
  {
    id: 'cmdb',
    title: 'CMDB Export Data',
    description: 'Configuration Management Database exports with asset information',
    icon: Database,
    color: 'bg-blue-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files'],
    securityLevel: 'standard',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor']
  },
  {
    id: 'app-discovery',
    title: 'Application Discovery Data',
    description: 'Application portfolio and dependency scan results',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['Application scans', 'Dependency maps', 'Service inventories'],
    securityLevel: 'elevated',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'dependency_validator']
  },
  {
    id: 'infrastructure',
    title: 'Infrastructure Assessment',
    description: 'Server, network, and infrastructure discovery data',
    icon: Activity,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['Network scans', 'Server inventories', 'Performance data'],
    securityLevel: 'high',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'infrastructure_validator']
  },
  {
    id: 'sensitive',
    title: 'Sensitive Data Assets',
    description: 'Data containing PII, financial, or confidential information',
    icon: Lock,
    color: 'bg-red-500',
    acceptedTypes: ['.csv', '.xlsx'],
    examples: ['Customer data', 'Financial records', 'HR systems'],
    securityLevel: 'maximum',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'pii_detector', 'compliance_checker']
  }
];

const DataImport: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, client, engagement, session, getAuthHeaders } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([]);
  
  // Flow Management State
  const { data: incompleteFlowsData, isLoading: checkingFlows } = useIncompleteFlowDetectionV2();
  const flowResumption = useFlowResumptionV2();
  const flowDeletion = useFlowDeletionV2();
  const bulkFlowOperations = useBulkFlowOperationsV2();
  const [showFlowManager, setShowFlowManager] = useState(false);
  const [conflictFlows, setConflictFlows] = useState<any[]>([]);
  const [isLoadingFlowDetails, setIsLoadingFlowDetails] = useState(false);
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;
  
  // NEW: Real-time flow tracking state
  // REMOVED: Legacy polling system - replaced by UniversalProcessingStatus component
  // Real-time updates are now handled by the UniversalProcessingStatus component with proper polling controls

  // REMOVED: Legacy polling function - replaced by UniversalProcessingStatus component
  // Real-time updates are now handled by the UniversalProcessingStatus component

  // Flow Management Handlers
  const handleContinueFlow = useCallback((sessionId: string) => {
    flowResumption.mutate(sessionId);
  }, [flowResumption]);

  const handleDeleteFlow = useCallback((sessionId: string) => {
    flowDeletion.mutate(sessionId);
  }, [flowDeletion]);

  const handleBatchDeleteFlows = useCallback((sessionIds: string[]) => {
    bulkFlowOperations.mutate({ session_ids: sessionIds });
  }, [bulkFlowOperations]);

  const handleViewFlowDetails = useCallback((sessionId: string, phase: string) => {
    // Navigate to phase-specific page using correct phase names
    const phaseRoutes = {
      'data_import': `/discovery/import`,
      'attribute_mapping': `/discovery/attribute-mapping/${sessionId}`,
      'data_cleansing': `/discovery/data-cleansing/${sessionId}`,
      'inventory': `/discovery/inventory/${sessionId}`,
      'dependencies': `/discovery/dependencies/${sessionId}`,
      'tech_debt': `/discovery/tech-debt/${sessionId}`
    };
    const route = phaseRoutes[phase as keyof typeof phaseRoutes] || `/discovery/enhanced-dashboard`;
    navigate(route);
  }, [navigate]);

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isStartingFlow, setIsStartingFlow] = useState(false);

  // File upload handling with authentication context - SIMPLIFIED for UnifiedDiscoveryFlow
  const handleFileUpload = useCallback(async (files: File[], categoryId: string) => {
    if (files.length === 0) return;

    // Debug authentication state
    console.log('🔍 Upload Debug - Auth State:', {
      user: user ? { id: user.id, role: user.role, name: user.full_name } : null,
      client: client ? { id: client.id, name: client.name } : null,
      engagement: engagement ? { id: engagement.id, name: engagement.name } : null,
      session: session ? { id: session.id } : null,
      categoryId,
      fileCount: files.length
    });

    // For admin users, allow upload even without client/engagement context (demo mode)
    const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';
    const hasContext = client && engagement;
    
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in before uploading data.",
        variant: "destructive"
      });
      return;
    }

    if (!hasContext && !isAdmin) {
      toast({
        title: "Context Required",
        description: "Please select a client and engagement before uploading data.",
        variant: "destructive"
      });
      return;
    }

    // Provide demo context for admin users if needed
    const effectiveClient = client || (isAdmin ? { id: 'demo-client', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: 'demo-engagement', name: 'Demo Engagement' } : null);

    if (!effectiveClient || !effectiveEngagement) {
      toast({
        title: "Context Error",
        description: "Unable to determine client/engagement context.",
        variant: "destructive"
      });
      return;
    }

    const file = files[0];
    const newFile: UploadFile = {
      id: `${file.name}-${new Date().toISOString()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'uploading',
      agentResults: [],
      upload_progress: 0,
    };

    setUploadedFiles([newFile]);
    setSelectedCategory(categoryId);

    try {
      // Update to processing status
      setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
        ...f, 
        status: 'validating', 
        upload_progress: 100 
      } : f));
      
      // Parse CSV data
      const csvData = await parseCsvData(file);
      
      if (csvData.length === 0) {
        throw new Error("No valid data found in the CSV file");
      }

      console.log(`Parsed ${csvData.length} records from CSV file`);
      
      // Generate a proper UUID for the upload session
      const tempSessionId = crypto.randomUUID();
      
      // Store data and trigger UnifiedDiscoveryFlow directly
      console.log('Storing data and triggering UnifiedDiscoveryFlow...');
      const { import_session_id, flow_id } = await storeImportData(csvData, file, tempSessionId, categoryId);
      
      if (flow_id) {
        // Success - UnifiedDiscoveryFlow was triggered - START PROCESSING TRACKING
        setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
          ...f, 
          status: 'processing',  // Changed from 'approved' to 'processing'
          importSessionId: import_session_id || undefined,
          flow_id: flow_id,
          discovery_progress: 0,
          current_phase: 'data_import',
          flow_status: 'running',
          agentResults: [{
            agent_id: 'unified_flow',
            agent_name: 'UnifiedDiscoveryFlow',
            validation: 'passed',
            confidence: 1.0,
            message: 'CrewAI Discovery Flow initiated - processing in progress',
            timestamp: new Date().toISOString(),
            details: [
              `Successfully uploaded ${csvData.length} records`,
              'UnifiedDiscoveryFlow started with CrewAI agents',
              'Real-time progress tracking enabled'
            ]
          }]
        } : f));
        
        toast({
          title: "Discovery Flow Started",
          description: `File uploaded successfully. CrewAI agents are now processing ${csvData.length} records.`,
        });
        
        // Real-time updates will be handled by UniversalProcessingStatus component
        
      } else {
        throw new Error("Failed to trigger UnifiedDiscoveryFlow - no flow ID returned");
      }
      
    } catch (error) {
      console.error("File upload and flow trigger error:", error);
      const errorMessage = (error instanceof Error) ? error.message : "An unknown error occurred.";
      setUploadedFiles(prev => prev.map(f => f.id === newFile.id ? { 
        ...f, 
        status: 'error', 
        error_message: errorMessage 
      } : f));
      toast({
        title: "Upload Failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  }, [user, client, engagement, session, toast, getAuthHeaders]);


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
      setUploadedFiles(prev => prev.map(f => 
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
  }, []);

  // Initialize flow details for existing uploaded files
  useEffect(() => {
    const initializeFlowDetails = async () => {
      if (uploadedFiles.length > 0 && !isLoadingFlowDetails) {
        setIsLoadingFlowDetails(true);
        
        // Fetch details for all files with flow_id but no flow_summary
        const filesToUpdate = uploadedFiles.filter(f => f.flow_id && !f.flow_summary);
        
        if (filesToUpdate.length > 0) {
          console.log(`Initializing flow details for ${filesToUpdate.length} files`);
          await Promise.all(filesToUpdate.map(fetchFlowDetails));
        }
        
        setIsLoadingFlowDetails(false);
      }
    };
    
    initializeFlowDetails();
  }, [uploadedFiles.length, fetchFlowDetails, isLoadingFlowDetails]);

  // Start Discovery Flow or Navigate to Results
  const startDiscoveryFlow = useCallback(async () => {
    const uploadedFile = uploadedFiles[0];
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
}, [uploadedFiles, navigate, toast]);

  // Retrieve stored data for discovery flow
  const getStoredImportData = async (importSessionId: string | undefined): Promise<any[]> => {
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
  };

  const parseCsvData = async (file: File): Promise<any[]> => {
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    console.log(`🔍 DEBUG: Parsed ${lines.length} lines from CSV file`);
    if (lines.length <= 1) {
      console.warn('🚨 DEBUG: CSV file has no data rows or only header');
      return [];
    }
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/\"/g, ''));
    const records = lines.slice(1).map((line, index) => {
      const values = line.split(',').map(v => v.trim().replace(/\"/g, ''));
      const record: any = { row_index: index + 1 };
      headers.forEach((header, headerIndex) => {
        record[header] = values[headerIndex] || '';
      });
      return record;
    });
    
    console.log(`🔍 DEBUG: Parsed ${records.length} data records from CSV`);
    console.log(`🔍 DEBUG: Headers: ${headers.join(', ')}`);
    if (records.length > 0) {
      console.log(`🔍 DEBUG: First record sample:`, records[0]);
    }
    
    return records;
  };

  const storeImportData = async (csvData: any[], file: File, sessionId: string, categoryId: string): Promise<{import_session_id: string | null, flow_id: string | null}> => {
    if (!sessionId) {
      console.error('No session ID available for storing data.');
      return { import_session_id: null, flow_id: null };
    }

    // Use effective client and engagement (same logic as handleFileUpload)
    const isAdmin = user?.role === 'admin' || user?.role === 'platform_admin';
    const effectiveClient = client || (isAdmin ? { id: 'demo-client', name: 'Demo Client' } : null);
    const effectiveEngagement = engagement || (isAdmin ? { id: 'demo-engagement', name: 'Demo Engagement' } : null);

    try {
      console.log(`Storing data for session: ${sessionId}`);
      console.log('Using effective context:', { 
        client: effectiveClient?.id, 
        engagement: effectiveEngagement?.id 
      });
      
      const response = await apiCall(`/data-import/store-import`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_data: csvData,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type,
          },
          upload_context: {
            intended_type: categoryId,
            validation_session_id: sessionId,
            upload_timestamp: new Date().toISOString(),
          },
          client_id: effectiveClient?.id || null,
          engagement_id: effectiveEngagement?.id || null,
        }),
      });

      if (response.success) {
        console.log('✅ Data stored successfully, import session ID:', response.import_session_id);
        console.log('✅ CrewAI Flow ID:', response.flow_id);
        return { 
          import_session_id: response.import_session_id,
          flow_id: response.flow_id 
        };
      } else {
        console.error('❌ Failed to store data:', response.error);
        return { import_session_id: null, flow_id: null };
      }
    } catch (error: any) {
      console.error('❌ Error storing data:', error);
      
      // Handle discovery flow conflict error (409 status)
      if (error?.response?.status === 409) {
        const responseData = error.response.data;
        
        // Check if this is the new format with flow management data
        if (responseData?.show_flow_manager && responseData?.all_incomplete_flows) {
          // New format: Show flow management UI
          console.log('🚫 Incomplete discovery flows detected:', responseData.all_incomplete_flows);
          
                     // Store flow data for the flow management UI
           setConflictFlows(responseData.all_incomplete_flows);
           setShowFlowManager(true);
          
          // Show user-friendly message
          toast({
            title: "Incomplete Discovery Flow Detected",
            description: responseData.message || "Please complete or delete existing flows before importing new data.",
            variant: "destructive",
          });
          
          return { import_session_id: null, flow_id: null };
        }
        
        // Legacy format handling (fallback)
        if (responseData?.detail?.error === 'incomplete_discovery_flow_exists') {
          const conflictData = responseData.detail;
          
          // Show detailed conflict information to user
          toast({
            title: "Incomplete Discovery Flow Found",
            description: conflictData.message,
            variant: "destructive",
          });
          
          // Show additional information and recommendations
          setTimeout(() => {
            toast({
              title: "Next Steps",
              description: `Current phase: ${conflictData.existing_flow.current_phase}. Please complete the existing flow before importing new data.`,
              variant: "default",
            });
          }, 2000);
          
          // Optionally navigate to the existing flow
          const existingSessionId = conflictData.existing_flow.session_id;
          if (existingSessionId) {
            setTimeout(() => {
              const shouldNavigate = window.confirm(
                `Would you like to continue with the existing Discovery Flow (${conflictData.existing_flow.current_phase} phase, ${conflictData.existing_flow.progress_percentage}% complete)?`
              );
              if (shouldNavigate) {
                // Navigate to data import phase for incomplete flows
                navigate(`/discovery/data-import`);
              }
            }, 3000);
          }
        }
      }
      
      return { import_session_id: null, flow_id: null };
    }
  };


  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent, categoryId: string) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files, categoryId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading': return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'validating': return <Brain className="h-5 w-5 animate-pulse text-orange-500" />;
      case 'processing': return <Cog className="h-5 w-5 animate-spin text-purple-500" />;
      case 'approved': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'approved_with_warnings': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'rejected': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'error': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <FileCheck className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading': return 'bg-blue-100 text-blue-800';
      case 'validating': return 'bg-orange-100 text-orange-800';
      case 'processing': return 'bg-purple-100 text-purple-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'approved_with_warnings': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // New component for enhanced validation progress with real-time data
  interface ValidationProgressSectionProps {
    file: UploadFile;
    onValidationUpdate: (validationData: any) => void;
  }

  const ValidationProgressSection: React.FC<ValidationProgressSectionProps> = ({ file, onValidationUpdate }) => {
    const [hasPollingError, setHasPollingError] = useState(false);
    const [errorRetryCount, setErrorRetryCount] = useState(0);
    const MAX_RETRY_COUNT = 3;
    
    // Only use real-time monitoring if we have a flow_id and haven't exceeded error threshold
    const shouldUseRealTimeMonitoring = file.flow_id && !hasPollingError && errorRetryCount < MAX_RETRY_COUNT;
    const monitoring = shouldUseRealTimeMonitoring ? useComprehensiveRealTimeMonitoring(file.flow_id, 'data_import') : null;
    
    // Monitor for errors and disable polling if too many occur
    React.useEffect(() => {
      if (monitoring?.processing.error || monitoring?.validation.error || monitoring?.insights.error) {
        setErrorRetryCount(prev => prev + 1);
        console.warn('Real-time monitoring error detected, retry count:', errorRetryCount + 1);
        
        if (errorRetryCount >= MAX_RETRY_COUNT - 1) {
          setHasPollingError(true);
          console.warn('Too many polling errors, disabling real-time monitoring for this file');
        }
      }
    }, [monitoring?.processing.error, monitoring?.validation.error, monitoring?.insights.error, errorRetryCount]);
    
    // Use real-time validation data if available, otherwise fall back to file properties
    const validationData = monitoring?.validation.validationData;
    const hasRealTimeData = !!validationData && !hasPollingError;
    
    // Determine validation status with real-time data priority
    const formatStatus = hasRealTimeData 
      ? (validationData.format_validation?.status === 'passed' ? 'passed' : 
         (validationData.format_validation?.errors && validationData.format_validation.errors.length > 0) ? 'failed' : 'pending')
      : (file.format_validation ? 'passed' : 'pending');
      
    const securityStatus = hasRealTimeData
      ? (validationData.security_scan?.status === 'passed' ? 'passed' :
         (validationData.security_scan?.issues && validationData.security_scan.issues.length > 0) ? 'failed' : 'pending')
      : (file.security_clearance ? 'passed' : 'pending');
      
    const privacyStatus = hasRealTimeData
      ? (validationData.data_quality?.score > 0.7 ? 'passed' :
         validationData.data_quality?.score < 0.5 ? 'failed' : 'warning')
      : (file.privacy_clearance ? 'passed' : 'pending');
    
    // Calculate progress from real-time data
    const validationProgress = hasRealTimeData 
      ? (validationData.validation_progress || 0)
      : (file.validation_progress || 0);
      
    const agentsCompleted = hasRealTimeData
      ? (validationData.agents_completed || 0)
      : (file.agents_completed || 0);
      
    const totalAgents = hasRealTimeData
      ? (validationData.total_agents || 4)
      : (file.total_agents || 4);
    
    // Update parent component when validation data changes
    React.useEffect(() => {
      if (hasRealTimeData && onValidationUpdate) {
        try {
          onValidationUpdate(validationData);
        } catch (error) {
          console.error('Error updating validation data:', error);
        }
      }
    }, [validationData, hasRealTimeData, onValidationUpdate]);
    
    // Helper function to get status styling
    const getStatusStyling = (status: string) => {
      switch (status) {
        case 'passed':
          return {
            bg: 'bg-green-50 border-green-200',
            icon: 'text-green-600',
            text: 'text-green-900'
          };
        case 'failed':
          return {
            bg: 'bg-red-50 border-red-200',
            icon: 'text-red-600',
            text: 'text-red-900'
          };
        case 'warning':
          return {
            bg: 'bg-yellow-50 border-yellow-200',
            icon: 'text-yellow-600',
            text: 'text-yellow-900'
          };
        default:
          return {
            bg: 'bg-gray-50 border-gray-200',
            icon: 'text-gray-400',
            text: 'text-gray-600'
          };
      }
    };
    
    const formatStyling = getStatusStyling(formatStatus);
    const securityStyling = getStatusStyling(securityStatus);
    const privacyStyling = getStatusStyling(privacyStatus);
    
    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Validation Progress</span>
            <span>{agentsCompleted}/{totalAgents} agents completed</span>
          </div>
          <Progress value={validationProgress} className="h-2" />
          {hasRealTimeData && (
            <div className="text-xs text-gray-500">
              Real-time validation status • Last updated: {new Date().toLocaleTimeString()}
            </div>
          )}
          {hasPollingError && (
            <div className="text-xs text-amber-600">
              ⚠️ Real-time updates disabled due to connection issues
            </div>
          )}
        </div>

        {/* Security Clearances with Real-time Status */}
        <div className="grid grid-cols-3 gap-4">
          <div className={`p-3 rounded-lg border ${formatStyling.bg}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileCheck className={`h-4 w-4 ${formatStyling.icon}`} />
                <span className={`text-sm font-medium ${formatStyling.text}`}>Format Valid</span>
              </div>
              {formatStatus === 'failed' && (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              {formatStatus === 'passed' && (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              {formatStatus === 'pending' && (
                <Clock className="h-4 w-4 text-gray-400" />
              )}
            </div>
            {hasRealTimeData && validationData.format_validation?.errors && validationData.format_validation.errors.length > 0 && (
              <div className="mt-1 text-xs text-red-600">
                {validationData.format_validation.errors.length} error(s) found
              </div>
            )}
          </div>
          
          <div className={`p-3 rounded-lg border ${securityStyling.bg}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className={`h-4 w-4 ${securityStyling.icon}`} />
                <span className={`text-sm font-medium ${securityStyling.text}`}>Security Clear</span>
              </div>
              {securityStatus === 'failed' && (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              {securityStatus === 'passed' && (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              {securityStatus === 'pending' && (
                <Clock className="h-4 w-4 text-gray-400" />
              )}
            </div>
            {hasRealTimeData && validationData.security_scan?.issues && validationData.security_scan.issues.length > 0 && (
              <div className="mt-1 text-xs text-red-600">
                {validationData.security_scan.issues.length} issue(s) found
              </div>
            )}
          </div>
          
          <div className={`p-3 rounded-lg border ${privacyStyling.bg}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <UserCheck className={`h-4 w-4 ${privacyStyling.icon}`} />
                <span className={`text-sm font-medium ${privacyStyling.text}`}>Privacy Clear</span>
              </div>
              {privacyStatus === 'failed' && (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              {privacyStatus === 'passed' && (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              {privacyStatus === 'warning' && (
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              )}
              {privacyStatus === 'pending' && (
                <Clock className="h-4 w-4 text-gray-400" />
              )}
            </div>
            {hasRealTimeData && validationData.data_quality?.score && (
              <div className="mt-1 text-xs text-gray-600">
                Quality: {Math.round(validationData.data_quality.score * 100)}%
              </div>
            )}
          </div>
        </div>
        
        {/* Validation Error Details */}
        {hasRealTimeData && (
          <div className="space-y-2">
            {validationData.format_validation?.errors && validationData.format_validation.errors.map((error, index) => (
              <Alert key={index} variant="destructive" className="py-2">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  <strong>Format Error:</strong> {error}
                </AlertDescription>
              </Alert>
            ))}
            {validationData.security_scan?.issues && validationData.security_scan.issues.map((issue, index) => (
              <Alert key={index} variant="destructive" className="py-2">
                <Shield className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  <strong>Security Issue:</strong> {issue}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-6xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Upload className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Secure Data Import</h1>
              </div>
              
              {/* Authentication Context Status */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                  client && engagement ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  <Activity className="h-4 w-4" />
                  <span>
                    {client && engagement 
                      ? `${client.name} • ${engagement.name}` 
                      : 'Select Client & Engagement'
                    }
                  </span>
                </div>
                {user && (
                  <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    <span>{user.full_name}</span>
                  </div>
                )}
                {/* Polling Status Indicator */}
                <PollingStatusIndicator />
              </div>
            </div>
            <p className="mt-2 text-gray-600 max-w-3xl">
              Upload migration data files for AI-powered validation and security analysis. 
              Our specialized agents ensure data quality, security, and privacy compliance before processing.
            </p>
            
            {/* Authentication Context Warning */}
            {(!client || !engagement) && (
              <Alert className="mt-4 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <strong>Context Required:</strong> Please select a client and engagement using the context selector above 
                  before uploading data. This ensures proper data isolation and agentic flow integration.
                </AlertDescription>
              </Alert>
            )}

            {/* Security Notice */}
            <Alert className="mt-4 border-blue-200 bg-blue-50">
              <Shield className="h-5 w-5 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>Enterprise Security:</strong> All uploaded data is analyzed by specialized validation agents 
                for format compliance, security threats, privacy protection, and data quality before any processing begins.
              </AlertDescription>
            </Alert>
          </div>

          {/* Conditional Upload Interface */}
          {checkingFlows ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Checking for incomplete discovery flows...</span>
            </div>
          ) : hasIncompleteFlows ? (
            <UploadBlocker 
              incompleteFlows={incompleteFlows}
              onContinueFlow={handleContinueFlow}
              onDeleteFlow={handleDeleteFlow}
              onViewDetails={handleViewFlowDetails}
              onManageFlows={() => setShowFlowManager(true)}
              isLoading={flowResumption.isPending || flowDeletion.isPending}
            />
          ) : (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Choose Data Category</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {uploadCategories.map((category) => (
                <Card 
                  key={category.id}
                  className={`relative cursor-pointer transition-all hover:shadow-md border-2 ${
                    selectedCategory === category.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  } ${isDragging ? 'border-dashed border-blue-400 bg-blue-50' : ''}`}
                  onClick={() => setSelectedCategory(category.id)}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, category.id)}
                >
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${category.color} text-white`}>
                        <category.icon className="h-6 w-6" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{category.title}</CardTitle>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {category.securityLevel} security
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {category.agents.length} validation agents
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <CardDescription className="mt-2">
                      {category.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Accepted formats:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {category.acceptedTypes.map(type => (
                            <Badge key={type} variant="secondary" className="text-xs">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">Examples:</p>
                        <p className="text-sm text-gray-600">{category.examples.join(', ')}</p>
                      </div>
                    </div>
                    
                    {/* File Input */}
                    <div className="mt-4">
                      <input
                        type="file"
                        id={`file-${category.id}`}
                        accept={category.acceptedTypes.join(',')}
                        onChange={(e) => {
                          console.log('🔍 File Input Change Event:', {
                            categoryId: category.id,
                            files: e.target.files,
                            fileCount: e.target.files?.length || 0
                          });
                          const files = Array.from(e.target.files || []);
                          if (files.length > 0) {
                            console.log('🔍 Calling handleFileUpload with:', files[0].name);
                            handleFileUpload(files, category.id);
                          } else {
                            console.log('🔍 No files selected');
                          }
                        }}
                        className="hidden"
                      />
                      <Button
                        onClick={() => {
                          console.log('🔍 Upload Button Clicked:', {
                            categoryId: category.id,
                            categoryTitle: category.title,
                            inputElement: document.getElementById(`file-${category.id}`)
                          });
                          document.getElementById(`file-${category.id}`)?.click();
                        }}
                        variant="outline"
                        className="w-full"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload {category.title}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
          )}

          {/* Upload Progress & Validation */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Upload & Validation Status</h2>
              
              {uploadedFiles.map((file) => (
                <Card key={file.id} className="border border-gray-200">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(file.status)}
                        <div>
                          <h3 className="font-medium text-gray-900">{file.name}</h3>
                          <p className="text-sm text-gray-600">
                            {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(file.status)}>
                        {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Upload Progress */}
                    {file.status === 'uploading' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Uploading file...</span>
                          <span>{file.upload_progress}%</span>
                        </div>
                        <Progress value={file.upload_progress} className="h-2" />
                      </div>
                    )}

                    {/* CrewAI Discovery Flow Progress */}
                    {file.status === 'processing' && (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span>CrewAI Discovery Flow Progress</span>
                            <span>{file.discovery_progress || 0}%</span>
                          </div>
                          <Progress value={file.discovery_progress || 0} className="h-2" />
                        </div>
                        
                        {/* Current Phase */}
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                          <div className="flex items-center space-x-2">
                            <Cog className="h-4 w-4 text-purple-600 animate-spin" />
                            <span className="text-sm font-medium text-purple-900">
                              Current Phase: {file.current_phase || 'Initializing...'}
                            </span>
                          </div>
                          <p className="text-xs text-purple-700 mt-1">
                            CrewAI agents are analyzing your data using advanced AI techniques
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Validation Progress */}
                    {(file.status === 'validating' || file.status === 'approved' || file.status === 'approved_with_warnings' || file.status === 'rejected') && (
                      <ValidationProgressSection 
                        file={file}
                        onValidationUpdate={(validationData) => {
                          // Update file validation status based on real-time data
                          setUploadedFiles(prev => prev.map(f => 
                            f.id === file.id 
                              ? { 
                                  ...f, 
                                  format_validation: validationData.format_validation?.status === 'passed',
                                  security_clearance: validationData.security_scan?.status === 'passed',
                                  privacy_clearance: !validationData.privacy_issues || validationData.privacy_issues.length === 0,
                                  validation_progress: validationData.validation_progress || 0,
                                  agents_completed: validationData.agents_completed || 0,
                                  total_agents: validationData.total_agents || 4
                                }
                              : f
                          ));
                        }}
                      />
                    )}

                    {/* Flow Summary - Completed Flow */}
                    {file.status === 'approved' && file.flow_summary && (
                      <div className="pt-4 border-t">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <h4 className="text-sm font-semibold text-green-900">CrewAI Discovery Flow Complete</h4>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                              <div className="text-lg font-bold text-green-700">{file.flow_summary.total_assets}</div>
                              <div className="text-xs text-green-600">Assets Processed</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-green-700">{file.flow_summary.phases_completed.length}</div>
                              <div className="text-xs text-green-600">Phases Complete</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-yellow-700">{file.flow_summary.warnings}</div>
                              <div className="text-xs text-yellow-600">Warnings</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-red-700">{file.flow_summary.errors}</div>
                              <div className="text-xs text-red-600">Errors</div>
                            </div>
                          </div>
                          
                          {file.flow_summary.phases_completed.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-green-800 mb-1">Completed Phases:</p>
                              <div className="flex flex-wrap gap-1">
                                {file.flow_summary.phases_completed.map(phase => (
                                  <Badge key={phase} variant="secondary" className="text-xs bg-green-100 text-green-800">
                                    {phase}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    {(file.status === 'approved' || file.status === 'approved_with_warnings') && (
                      <div className="pt-4 border-t">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {file.flow_summary ? 'Discovery Flow Complete' : 'Ready for Discovery Flow'}
                            </p>
                            <p className="text-sm text-gray-600">
                              {file.flow_summary 
                                ? 'Data analysis complete. Proceed to field mapping and detailed insights.'
                                : 'Data validation complete. Proceed to field mapping and AI-powered analysis.'
                              }
                            </p>
                          </div>
                          <Button
                            onClick={() => startDiscoveryFlow()}
                            disabled={isStartingFlow}
                            className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
                          >
                            {isStartingFlow ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Starting Flow...</span>
                              </>
                            ) : (
                              <>
                                <Brain className="h-4 w-4" />
                                <span>{file.flow_summary ? 'View Results' : 'Start Discovery Flow'}</span>
                                <ArrowRight className="h-4 w-4" />
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    )}

                    {file.status === 'approved_with_warnings' && (
                      <Alert className="border-yellow-200 bg-yellow-50">
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">
                          File validation completed with warnings. Review agent feedback before proceeding to field mapping.
                        </AlertDescription>
                      </Alert>
                    )}

                    {file.status === 'rejected' && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertTriangle className="h-5 w-5 text-red-600" />
                        <AlertDescription className="text-red-800">
                          File validation failed. Please review agent feedback and upload a corrected file.
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Universal Real-Time Processing Status */}
          {uploadedFiles.length > 0 && uploadedFiles.some(f => f.flow_id) && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Real-Time Processing Monitor</h2>
              {uploadedFiles.filter(f => f.flow_id).map((file) => {
                // Create callback functions for this specific file
                const handleProcessingComplete = async () => {
                  // Guard against repeated calls
                  if (file.status === 'approved' || file.flow_status === 'completed') {
                    return;
                  }
                  
                  console.log(`Processing completed for file: ${file.name}`);
                  
                  try {
                    // Fetch the complete flow details to get current phase and summary
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
                    
                    toast({
                      title: "Processing Complete",
                      description: `${file.name} has been successfully processed. ${flowSummary.phases_completed.length} phases completed.`,
                    });
                    
                    // Update the file status with complete flow information
                    setUploadedFiles(prev => prev.map(f => 
                      f.id === file.id 
                        ? { 
                            ...f, 
                            status: 'approved', 
                            flow_status: 'completed',
                            flow_summary: flowSummary,
                            current_phase: flowResponse.current_phase || 'inventory',
                            discovery_progress: flowResponse.progress || 0
                          }
                        : f
                    ));
                    
                  } catch (error) {
                    console.error('Error fetching flow details:', error);
                    // Fallback to basic status update
                    toast({
                      title: "Processing Complete",
                      description: `${file.name} has been successfully processed.`,
                    });
                    setUploadedFiles(prev => prev.map(f => 
                      f.id === file.id 
                        ? { ...f, status: 'approved', flow_status: 'completed' }
                        : f
                    ));
                  }
                };

                const handleValidationFailed = (issues: string[]) => {
                  // Guard against repeated calls
                  if (file.status === 'rejected' && file.error_message) {
                    return;
                  }
                  
                  console.error(`Validation failed for file: ${file.name}`, issues);
                  toast({
                    title: "Validation Issues Found",
                    description: `${file.name}: ${issues.join(', ')}`,
                    variant: "destructive",
                  });
                  // Update the file status
                  setUploadedFiles(prev => prev.map(f => 
                    f.id === file.id 
                      ? { ...f, status: 'rejected', error_message: issues.join(', ') }
                      : f
                  ));
                };

                return (
                  <UniversalProcessingStatus
                    key={file.flow_id}
                    flow_id={file.flow_id}
                    page_context="data_import"
                    title={`${file.name} - Processing Status`}
                    showAgentInsights={true}
                    showValidationDetails={true}
                    onProcessingComplete={handleProcessingComplete}
                    onValidationFailed={handleValidationFailed}
                  />
                );
              })}
            </div>
          )}

          {/* Polling Controls - Show when there are active uploads or processing */}
          {uploadedFiles.length > 0 && (
            <div className="mt-8">
              <PollingControls 
                flowId={uploadedFiles.find(f => f.flow_id)?.flow_id}
                showDetailedStatus={true}
                onEmergencyStop={() => {
                  toast({
                    title: "Emergency Stop Activated",
                    description: "All polling operations have been stopped. Use refresh to manually check status.",
                    variant: "destructive"
                  });
                }}
                onRefresh={() => {
                  toast({
                    title: "Data Refreshed",
                    description: "All data has been manually refreshed.",
                  });
                }}
              />
            </div>
          )}

          {/* Getting Started Guide */}
          {uploadedFiles.length === 0 && (
            <Card className="border border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-900">Getting Started with Secure Data Import</CardTitle>
              </CardHeader>
              <CardContent className="text-blue-800">
                <ol className="list-decimal list-inside space-y-2">
                  <li><strong>Choose data category</strong> based on your file type and security requirements</li>
                  <li><strong>Upload your file</strong> - our validation agents will automatically begin analysis</li>
                  <li><strong>Review validation results</strong> from specialized security and privacy agents</li>
                  <li><strong>Proceed to field mapping</strong> once all validations pass successfully</li>
                </ol>
                <div className="mt-4 p-3 bg-blue-100 rounded-lg">
                  <p className="text-sm">
                    <strong>Security Promise:</strong> Your data never leaves our secure environment and is 
                    analyzed by AI agents that ensure compliance with enterprise security and privacy standards.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Flow Management Modal */}
      <Dialog open={showFlowManager} onOpenChange={setShowFlowManager}>
        <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Incomplete Discovery Flows</DialogTitle>
          </DialogHeader>
          <IncompleteFlowManager 
            flows={conflictFlows.length > 0 ? conflictFlows : incompleteFlows}
            onContinueFlow={handleContinueFlow}
            onDeleteFlow={handleDeleteFlow}
            onBatchDelete={handleBatchDeleteFlows}
            onViewDetails={handleViewFlowDetails}
            isLoading={flowResumption.isPending || flowDeletion.isPending || bulkFlowOperations.bulkDelete.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataImport;

