import React from 'react';
import { Shield, AlertTriangle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Components
import Sidebar from '../../../components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import { PollingStatusIndicator } from '@/components/common/PollingControls';
import { AgentActivityViewer } from '@/components/discovery/AgentActivityViewer';

// Custom hooks and components
import { useCMDBImport } from './hooks/useCMDBImport';
import { uploadCategories } from './utils/uploadCategories';
import { CMDBUploadSection } from './components/CMDBUploadSection';
import { CMDBDataTable } from './components/CMDBDataTable';

// Contexts
import { useAuth } from '@/contexts/AuthContext';

const CMDBImportContainer: React.FC = () => {
  const { client, engagement } = useAuth();
  
  const {
    // File upload state
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
    isStartingFlow,
    
    // Actions
    startFlow,

    // Unified Flow State
    activeFlowId,
    flowState,
    isFlowStateLoading,
    flowStateError
  } = useCMDBImport();

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
          <ContextBreadcrumbs />

          {/* Page Header */}
          <div className="my-6 md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                    CMDB Data Import
                </h2>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <PollingStatusIndicator 
                flowId={activeFlowId}
              />
            </div>
          </div>
          
            {/* Context Warning */}
            {(!client || !engagement) && (
              <Alert className="mb-4 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <strong>Context Required:</strong> Please select a client and engagement before uploading data.
                </AlertDescription>
              </Alert>
            )}

            {/* Security Notice */}
            <Alert className="mb-6 border-blue-200 bg-blue-50">
              <Shield className="h-5 w-5 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>Enterprise Security:</strong> All uploaded data is analyzed by specialized validation agents for compliance, security, and data quality.
              </AlertDescription>
            </Alert>

          {/* Main Content */}
          <div className="space-y-6">
            {/* Conditional Upload Blocker */}
            {uploadedFiles.length > 0 && (
                <Alert variant="default" className="bg-orange-50 border-orange-200 text-orange-800">
                    <AlertTriangle className="h-4 w-4 !text-orange-600" />
                    <AlertDescription>
                        A file is already being processed. Please wait for the flow to complete before uploading a new file.
                    </AlertDescription>
              </Alert>
            )}
            
            {/* CMDB Upload Section */}
            {!isStartingFlow && uploadedFiles.length === 0 && (
                <CMDBUploadSection 
                  isDragging={isDragging}
                  selectedCategory={selectedCategory}
                  categories={uploadCategories}
                  setSelectedCategory={setSelectedCategory}
                  onDragLeave={onDragLeave}
                  onDragOver={onDragOver}
                  onDrop={onDrop}
                  onFileUpload={onFileUpload}
                  disabled={isStartingFlow || uploadedFiles.length > 0 || !client || !engagement}
                />
            )}
            
            {/* Loading Indicator for Initial Flow Start */}
            {isStartingFlow && (
              <div className="flex items-center justify-center p-8 border-2 border-dashed rounded-lg bg-gray-50">
                <Loader2 className="mr-2 h-6 w-6 animate-spin text-blue-500" />
                <p className="text-lg text-gray-600">Starting discovery flow...</p>
              </div>
            )}
            
            {/* CMDB Data Table */}
            {uploadedFiles.length > 0 && (
              <CMDBDataTable 
                files={uploadedFiles} 
                setFiles={setUploadedFiles}
                onStartFlow={startFlow}
                isFlowRunning={!!activeFlowId}
                flowState={flowState}
              />
            )}

            {/* Agent Activity Viewer */}
            {activeFlowId && flowState && (
              <AgentActivityViewer insights={flowState.agent_insights || []} />
            )}
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default CMDBImportContainer;