import React, { useEffect, useRef, useState } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  FileSpreadsheet, 
  ExternalLink,
  AlertCircle,
  Lightbulb,
  ArrowRight,
  Loader2,
  Bot,
  Clock,
  StopCircle,
  Play
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UploadedFile, useDiscoveryFlowStatus } from '../../hooks/useCMDBImport';
import { useQueryClient } from '@tanstack/react-query';

interface FileAnalysisProps {
  file: UploadedFile;
  onRetry?: () => void;
  onNavigate: (path: string, state?: any) => void;
}

export const FileAnalysis: React.FC<FileAnalysisProps> = ({ file, onRetry, onNavigate }) => {
  const queryClient = useQueryClient();
  const lastStatusRef = useRef<string | null>(null);
  const [showWorkflowControls, setShowWorkflowControls] = useState(false);
  
  // Use the updated useDiscoveryFlowStatus hook with proper endpoint and polling logic
  const { 
    data: statusData, 
    isLoading: isStatusLoading, 
    error: statusError,
    refetch: refetchStatus 
  } = useDiscoveryFlowStatus(file.sessionId);

  // Only trigger effects when status actually changes (prevent excessive updates)
  useEffect(() => {
    const currentStatus = statusData?.status;
    if (currentStatus && currentStatus !== lastStatusRef.current) {
      lastStatusRef.current = currentStatus;
      
      // Handle workflow status messages that indicate existing workflows
      if (statusData?.message?.includes("already running") || 
          statusData?.message?.includes("Workflow already")) {
        setShowWorkflowControls(true);
      }
      
      // Only invalidate queries when we reach terminal states
      if (currentStatus === 'completed' || currentStatus === 'failed') {
        // Invalidate relevant queries to refresh UI data
        queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
        queryClient.invalidateQueries({ queryKey: ['assetCounts'] });
      }
    }
  }, [statusData?.status, statusData?.message, queryClient]);

  const getStatusDisplay = () => {
    if (isStatusLoading) {
      return {
        icon: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
        text: 'Checking workflow status...',
        color: 'text-blue-600',
        bgColor: 'bg-blue-50'
      };
    }

    if (statusError) {
      return {
        icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
        text: 'Error checking status',
        color: 'text-red-600',
        bgColor: 'bg-red-50'
      };
    }

    const status = statusData?.status;
    const phase = statusData?.current_phase;
    const message = statusData?.message;

    switch (status) {
      case 'running':
      case 'in_progress':
      case 'processing':
        return {
          icon: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
          text: `Processing: ${phase || 'Unknown phase'}`,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          showControls: showWorkflowControls
        };
      case 'completed':
        return {
          icon: <CheckCircle className="h-4 w-4 text-green-500" />,
          text: 'Analysis completed successfully',
          color: 'text-green-600', 
          bgColor: 'bg-green-50'
        };
      case 'failed':
      case 'error':
        return {
          icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
          text: `Analysis failed: ${phase || 'Unknown error'}`,
          color: 'text-red-600',
          bgColor: 'bg-red-50'
        };
      default:
        return {
          icon: <Clock className="h-4 w-4 text-gray-500" />,
          text: message || 'Workflow status unknown',
          color: 'text-gray-600',
          bgColor: 'bg-gray-50'
        };
    }
  };

  const handleCancelWorkflow = async () => {
    // This would call an API to cancel the existing workflow
    console.log('Cancel workflow requested for session:', file.sessionId);
    setShowWorkflowControls(false);
    // In the future, implement actual cancellation logic
  };

  const handleRetryWorkflow = () => {
    setShowWorkflowControls(false);
    if (onRetry) {
      onRetry();
    }
  };

  const statusDisplay = getStatusDisplay();

  return (
    <div className="space-y-4">
      {/* File Information */}
      <div className="flex items-center space-x-3">
        <FileSpreadsheet className="h-5 w-5 text-blue-500" />
        <div>
          <h3 className="font-medium text-gray-900">{file.filename}</h3>
          <p className="text-sm text-gray-500">
            {file.recordCount} records • Session: {file.sessionId?.slice(0, 8)}...
          </p>
        </div>
      </div>

      {/* Workflow Status */}
      <div className={`p-4 rounded-lg border ${statusDisplay.bgColor}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {statusDisplay.icon}
            <div>
              <p className={`font-medium ${statusDisplay.color}`}>
                {statusDisplay.text}
              </p>
              {statusData?.message && (
                <p className="text-sm text-gray-600 mt-1">
                  {statusData.message}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => refetchStatus()}
              disabled={isStatusLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isStatusLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Workflow Controls (shown when there's an existing workflow) */}
        {statusDisplay.showControls && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                A workflow is already running for this session. What would you like to do?
              </p>
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleCancelWorkflow}
                  className="flex items-center space-x-1"
                >
                  <StopCircle className="h-4 w-4" />
                  <span>Cancel & Restart</span>
                </Button>
                <Button 
                  variant="default" 
                  size="sm"
                  onClick={() => setShowWorkflowControls(false)}
                  className="flex items-center space-x-1"
                >
                  <Clock className="h-4 w-4" />
                  <span>Wait for Completion</span>
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Progress */}
      {statusData?.status && ['running', 'in_progress', 'processing'].includes(statusData.status) && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 flex items-center">
            <Bot className="h-4 w-4 mr-2 text-blue-500" />
            AI Crew Analysis
          </h4>
          <div className="space-y-2">
            {statusData.workflow_phases?.map((phase: string, index: number) => {
              const isActive = statusData.current_phase === phase;
              const isCompleted = statusData.workflow_phases?.indexOf(statusData.current_phase) > index;
              
              return (
                <div key={phase} className={`flex items-center space-x-3 p-2 rounded ${
                  isActive ? 'bg-blue-50 border border-blue-200' : 
                  isCompleted ? 'bg-green-50' : 'bg-gray-50'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : isActive ? (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={`text-sm ${
                    isActive ? 'text-blue-700 font-medium' : 
                    isCompleted ? 'text-green-700' : 'text-gray-600'
                  }`}>
                    {phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
              );
            }) || (
              <div className="flex items-center space-x-3 p-2 rounded bg-blue-50 border border-blue-200">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                <span className="text-sm text-blue-700">Analysis in progress...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 border-t">
        <div className="flex space-x-2">
          {statusData?.status === 'failed' && onRetry && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRetryWorkflow}
              className="flex items-center space-x-1"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Retry Analysis</span>
            </Button>
          )}
        </div>
        
        <div className="flex space-x-2">
          {statusData?.status === 'completed' && (
            <Button 
              variant="default" 
              size="sm"
              onClick={() => onNavigate(`/discovery/analysis/${file.sessionId}`)}
              className="flex items-center space-x-1"
            >
              <span>View Results</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
