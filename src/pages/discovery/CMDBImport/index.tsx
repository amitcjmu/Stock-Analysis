import React from 'react';
import { Upload, Activity, Shield, AlertTriangle, Loader2, FileText } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Components
import Sidebar from '../../../components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import { UploadBlocker } from '@/components/discovery/UploadBlocker';
import { IncompleteFlowManager } from '@/components/discovery/IncompleteFlowManager';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { SimplifiedFlowStatus } from '@/components/discovery/SimplifiedFlowStatus';
import { PollingStatusIndicator } from '@/components/common/PollingControls';

// Custom hooks and components
import { useCMDBImport } from './hooks/useCMDBImport';
import { uploadCategories } from './utils/uploadCategories';
import { CMDBUploadSection } from './components/CMDBUploadSection';
import { CMDBDataTable } from './components/CMDBDataTable';

// Contexts
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/config/api';

const CMDBImportContainer: React.FC = () => {
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const { toast } = useToast();
  
  const {
    // File upload state
    uploadedFiles,
    setUploadedFiles,
    selectedCategory,
    isDragging,
    handleFileUpload,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    
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
    isStartingFlow,
    
    // Actions
    startDiscoveryFlow
  } = useCMDBImport();

  // Poll for flow status updates
  React.useEffect(() => {
    const pollFlowStatus = async () => {
      // Only poll for files that have a flow_id and are in processing state
      const processingFiles = uploadedFiles.filter(f => 
        f.flow_id && 
        (f.status === 'processing' || f.flow_status === 'running' || f.flow_status === 'active') &&
        f.flow_status !== 'paused' &&
        f.flow_status !== 'waiting_for_approval' &&
        f.flow_status !== 'completed' &&
        f.flow_status !== 'failed'
      );

      for (const file of processingFiles) {
        try {
          const response = await apiCall(`/api/v1/flows/${file.flow_id}/status`, {
            headers: getAuthHeaders()
          });
          
          // Update file status based on flow status
          if (response.status === 'waiting_for_approval' || response.awaiting_user_approval) {
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  status: 'approved_with_warnings', // This will show yellow badge
                  flow_status: 'waiting_for_approval',
                  discovery_progress: response.progress_percentage || 25, // Show some progress
                  current_phase: 'field_mapping',
                  error_message: 'Field mapping suggestions ready. Review and approve to continue.'
                };
              }
              return f;
            }));
            
            // Show toast notification once
            if (file.flow_status !== 'waiting_for_approval') {
              toast({
                title: "Action Required",
                description: "Field mapping suggestions are ready for your review.",
              });
            }
          } else if (response.status === 'completed') {
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
          } else if (response.status === 'paused') {
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  flow_status: 'paused',
                  discovery_progress: response.progress_percentage || f.discovery_progress,
                  current_phase: response.current_phase || f.current_phase
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
            // Update progress for running flows
            setUploadedFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                return {
                  ...f,
                  discovery_progress: response.progress_percentage || f.discovery_progress,
                  current_phase: response.current_phase || f.current_phase
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

    // Start polling if there are processing files
    if (uploadedFiles.some(f => f.flow_id && (f.status === 'processing' || f.flow_status === 'running'))) {
      const interval = setInterval(pollFlowStatus, 30000); // Poll every 30 seconds
      return () => clearInterval(interval);
    }
  }, [uploadedFiles, setUploadedFiles, toast]);

  // Universal Real-Time Processing Status callbacks
  const handleProcessingComplete = async (file: any) => {
    if (file.status === 'approved' || file.flow_status === 'completed') {
      return;
    }
    
    console.log(`Processing completed for file: ${file.name}`);
    
    try {
      const flowResponse = await apiCall(`/api/v1/flows/${file.flow_id}/status`);
      
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

  const handleValidationFailed = (file: any, issues: string[]) => {
    if (file.status === 'rejected' && file.error_message) {
      return;
    }
    
    console.error(`Validation failed for file: ${file.name}`, issues);
    toast({
      title: "Validation Issues Found",
      description: `${file.name}: ${issues.join(', ')}`,
      variant: "destructive",
    });
    
    setUploadedFiles(prev => prev.map(f => 
      f.id === file.id 
        ? { ...f, status: 'rejected', error_message: issues.join(', ') }
        : f
    ));
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
              isLoading={false}
            />
          ) : (
            <CMDBUploadSection
              categories={uploadCategories}
              selectedCategory={selectedCategory}
              setSelectedCategory={() => {}} // This will be handled by the hook
              isDragging={isDragging}
              onFileUpload={handleFileUpload}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            />
          )}

          {/* Upload Progress & Validation */}
          <CMDBDataTable
            uploadedFiles={uploadedFiles}
            setUploadedFiles={setUploadedFiles}
            isStartingFlow={isStartingFlow}
            onStartDiscoveryFlow={startDiscoveryFlow}
          />

          {/* Simplified Flow Status */}
          {uploadedFiles.length > 0 && uploadedFiles.some(f => f.flow_id) && (
            <div className="space-y-6 mt-8">
              <h2 className="text-xl font-semibold text-gray-900">Discovery Flow Status</h2>
              {uploadedFiles.filter(f => f.flow_id).map((file) => (
                <div key={file.id}>
                  <div className="mb-2 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-purple-600" />
                        <span className="font-medium text-purple-900">{file.name}</span>
                      </div>
                      <span className="text-sm text-purple-700">{file.size}</span>
                    </div>
                  </div>
                  <SimplifiedFlowStatus
                    flow_id={file.flow_id!}
                    onNavigateToMapping={() => {
                      // Navigate to attribute mapping
                      window.location.href = `/discovery/attribute-mapping/${file.flow_id}`;
                    }}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Flow Manager Dialog */}
          <Dialog open={showFlowManager} onOpenChange={setShowFlowManager}>
            <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage Discovery Flows</DialogTitle>
              </DialogHeader>
              <IncompleteFlowManager
                flows={conflictFlows.length > 0 ? conflictFlows : incompleteFlows}
                onContinueFlow={handleContinueFlow}
                onDeleteFlow={handleDeleteFlow}
                onBatchDelete={handleBatchDeleteFlows}
                onViewDetails={handleViewFlowDetails}
                onClose={() => setShowFlowManager(false)}
                isLoading={false}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
};

export default CMDBImportContainer;