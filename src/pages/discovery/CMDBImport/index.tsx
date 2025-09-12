import React from "react";
import {
  Upload,
  Activity,
  Shield,
  AlertTriangle,
  Loader2,
  FileText,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Components
import Sidebar from "../../../components/Sidebar";
import ContextBreadcrumbs from "@/components/context/ContextBreadcrumbs";
import { UploadBlocker } from "@/components/discovery/UploadBlocker";
import { IncompleteFlowManager } from "@/components/discovery/IncompleteFlowManager";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
// import { PollingStatusIndicator } from '@/components/common/PollingControls';
// import { AgentActivityViewer } from '@/components/discovery/AgentActivityViewer';
import { FlowDeletionModal } from "@/components/flows/FlowDeletionModal";
import { DiscoveryErrorBoundary } from "@/components/discovery/DiscoveryErrorBoundary";

// Custom hooks and components
import { useCMDBImport } from "./hooks/useCMDBImport";
import { uploadCategories } from "./utils/uploadCategories";
import { CMDBUploadSection } from "./components/CMDBUploadSection";
import { CMDBDataTable } from "./components/CMDBDataTable";

// Contexts
import { useAuth } from "@/contexts/AuthContext";

const CMDBImportContainer: React.FC = () => {
  const { user, client, engagement, isLoading: isAuthLoading } = useAuth();

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
    startDiscoveryFlow,

    // Unified Flow State
    activeFlowId,
    flowState,
    isFlowStateLoading,
    flowStateError,
    pollingStatus,

    // Deletion state and actions
    deletionState,
    deletionActions,
  } = useCMDBImport();

  // Show loading state while authentication context is being established
  if (isAuthLoading || !user) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-6xl">
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">
                Loading authentication context...
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

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

          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Upload className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">
                  Secure Data Import
                </h1>
              </div>

              {/* Authentication Context Status */}
              <div className="flex items-center space-x-3">
                <div
                  className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                    client && engagement
                      ? "bg-green-100 text-green-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  <Activity className="h-4 w-4" />
                  <span>
                    {client && engagement
                      ? `${client.name} • ${engagement.name}`
                      : "Select Client & Engagement"}
                  </span>
                </div>
                {user && (
                  <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    <span>{user.full_name}</span>
                  </div>
                )}
                {/* <PollingStatusIndicator /> */}
              </div>
            </div>
            <p className="mt-2 text-gray-600 max-w-3xl">
              Upload migration data files for AI-powered validation and security
              analysis. Our specialized agents ensure data quality, security,
              and privacy compliance before processing.
            </p>

            {/* Context Warning */}
            {(!client || !engagement) && (
              <Alert className="mb-4 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <strong>Context Required:</strong> Please select a client and
                  engagement before uploading data.
                </AlertDescription>
              </Alert>
            )}

            {/* Security Notice */}
            <Alert className="mb-6 border-blue-200 bg-blue-50">
              <Shield className="h-5 w-5 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>Enterprise Security:</strong> All uploaded data is
                analyzed by specialized validation agents for compliance,
                security, and data quality.
              </AlertDescription>
            </Alert>
          </div>

          {/* Conditional Upload Interface */}
          {checkingFlows ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">
                Checking for incomplete discovery flows...
              </span>
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
            flowState={flowState}
          />


          {/* Flow Manager Dialog */}
          <Dialog open={showFlowManager} onOpenChange={setShowFlowManager}>
            <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage Discovery Flows</DialogTitle>
              </DialogHeader>
              <IncompleteFlowManager
                flows={incompleteFlows}
                onContinueFlow={handleContinueFlow}
                onDeleteFlow={handleDeleteFlow}
                onBatchDelete={handleBatchDeleteFlows}
                onViewDetails={handleViewFlowDetails}
                isLoading={isStartingFlow}
              />
            </DialogContent>
          </Dialog>

          {/* Flow Deletion Modal */}
          <FlowDeletionModal
            open={deletionState.isModalOpen}
            candidates={deletionState.candidates}
            deletionSource={deletionState.deletionSource}
            isDeleting={deletionState.isDeleting}
            onConfirm={deletionActions.confirmDeletion}
            onCancel={deletionActions.cancelDeletion}
          />
        </div>
      </div>
    </div>
  );
};

const CMDBImportWithErrorBoundary: React.FC = () => (
  <DiscoveryErrorBoundary>
    <CMDBImportContainer />
  </DiscoveryErrorBoundary>
);

export default CMDBImportWithErrorBoundary;
