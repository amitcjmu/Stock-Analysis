import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Upload, ArrowLeft, Zap, RefreshCw, CheckCircle, XCircle, Trash2, Clock } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useNavigate } from 'react-router-dom';
import { flowRecoveryService } from '../../../../services/flow-recovery';
import type { RecoveryProgress, BlockingFlow } from '../../../../services/flow-recovery';

interface ErrorAndStatusAlertsProps {
  isFlowNotFound: boolean;
  isLoading: boolean;
  hasData: boolean;
  flowId: string | null;
  flowList: unknown[];
  effectiveFlowId: string | null;
  isAnalyzing: boolean;
  onTriggerFieldMappingCrew: () => void;
  // Flow recovery props
  isRecovering?: boolean;
  recoveryProgress?: RecoveryProgress;
  recoveryError?: string | null;
  recoveredFlowId?: string | null;
  onTriggerFlowRecovery?: (flowId: string) => Promise<boolean>;
  // Multi-flow blocking props
  blockingFlows?: BlockingFlow[];
  hasMultipleBlockingFlows?: boolean;
  onRefresh?: () => Promise<void>;
}

export const ErrorAndStatusAlerts: React.FC<ErrorAndStatusAlertsProps> = ({
  isFlowNotFound,
  isLoading,
  hasData,
  flowId,
  flowList,
  effectiveFlowId,
  isAnalyzing,
  onTriggerFieldMappingCrew,
  // Flow recovery props
  isRecovering = false,
  recoveryProgress,
  recoveryError,
  recoveredFlowId,
  onTriggerFlowRecovery,
  // Multi-flow blocking props
  blockingFlows = [],
  hasMultipleBlockingFlows = false,
  onRefresh
}) => {
  const navigate = useNavigate();

  // Multi-flow blocking state
  const [isCleaningFlows, setIsCleaningFlows] = useState(false);
  const [deletingFlowIds, setDeletingFlowIds] = useState<Set<string>>(new Set());
  const [cleanupProgress, setCleanupProgress] = useState<{
    current: number;
    total: number;
    currentFlowId?: string;
  } | null>(null);

  // Automatic flow recovery trigger
  const handleAutomaticRecovery = useCallback(async () => {
    if (!onTriggerFlowRecovery) return false;

    const targetFlowId = flowId || effectiveFlowId;
    if (!targetFlowId) {
      console.warn('⚠️ [ErrorAndStatusAlerts] No flow ID available for recovery');
      return false;
    }

    console.log(`🚀 [ErrorAndStatusAlerts] Triggering automatic recovery for flow: ${targetFlowId}`);
    return await onTriggerFlowRecovery(targetFlowId);
  }, [flowId, effectiveFlowId, onTriggerFlowRecovery]);

  // Handle individual flow deletion
  const handleDeleteFlow = useCallback(async (flowIdToDelete: string) => {
    try {
      setDeletingFlowIds(prev => new Set([...prev, flowIdToDelete]));
      console.log(`🗑️ [ErrorAndStatusAlerts] Deleting flow: ${flowIdToDelete}`);

      const result = await flowRecoveryService.deleteFlow(flowIdToDelete);

      if (result.success) {
        console.log(`✅ [ErrorAndStatusAlerts] Successfully deleted flow: ${flowIdToDelete}`);
        // Refresh the data to update the blocking flows list
        if (onRefresh) {
          await onRefresh();
        }
      } else {
        console.error(`❌ [ErrorAndStatusAlerts] Failed to delete flow: ${result.message}`);
      }
    } catch (error) {
      console.error(`❌ [ErrorAndStatusAlerts] Error deleting flow ${flowIdToDelete}:`, error);
    } finally {
      setDeletingFlowIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(flowIdToDelete);
        return newSet;
      });
    }
  }, [onRefresh]);

  // Handle bulk flow deletion
  const handleDeleteAllBlockingFlows = useCallback(async () => {
    if (!blockingFlows.length) return;

    try {
      setIsCleaningFlows(true);
      setCleanupProgress({ current: 0, total: blockingFlows.length });

      console.log(`🗑️ [ErrorAndStatusAlerts] Deleting ${blockingFlows.length} blocking flows in bulk`);

      const flowIds = blockingFlows.filter(flow => flow.canDelete).map(flow => flow.id);

      if (flowIds.length === 0) {
        console.warn(`⚠️ [ErrorAndStatusAlerts] No deletable flows found`);
        return;
      }

      const result = await flowRecoveryService.deleteMultipleFlows(flowIds);

      // Update progress during cleanup
      for (let i = 0; i < result.results.length; i++) {
        const flowResult = result.results[i];
        setCleanupProgress({
          current: i + 1,
          total: result.results.length,
          currentFlowId: flowResult.flowId
        });

        if (flowResult.success) {
          console.log(`✅ [ErrorAndStatusAlerts] Deleted flow: ${flowResult.flowId}`);
        } else {
          console.error(`❌ [ErrorAndStatusAlerts] Failed to delete flow ${flowResult.flowId}: ${flowResult.message}`);
        }

        // Small delay for UX
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      console.log(`📊 [ErrorAndStatusAlerts] Bulk cleanup completed: ${result.message}`);

      // Refresh data after cleanup
      if (onRefresh) {
        await onRefresh();
      }

    } catch (error) {
      console.error(`❌ [ErrorAndStatusAlerts] Bulk flow cleanup failed:`, error);
    } finally {
      setIsCleaningFlows(false);
      setCleanupProgress(null);
    }
  }, [blockingFlows, onRefresh]);

  // Automatically attempt recovery when flow is not found (if recovery service is available)
  useEffect(() => {
    if (isFlowNotFound && !isRecovering && onTriggerFlowRecovery && (flowId || effectiveFlowId)) {
      console.log('🔧 [ErrorAndStatusAlerts] Flow not found, attempting automatic recovery...');
      handleAutomaticRecovery();
    }
  }, [isFlowNotFound, isRecovering, onTriggerFlowRecovery, flowId, effectiveFlowId, handleAutomaticRecovery]);

  // Show multi-flow blocking scenario first (highest priority)
  if (hasMultipleBlockingFlows && blockingFlows.length > 1) {
    return (
      <Alert className="mb-6 border-orange-200 bg-orange-50">
        <AlertTriangle className="h-5 w-5 text-orange-600" />
        <AlertDescription className="text-orange-800">
          <div className="space-y-4">
            <div>
              <p className="font-medium mb-2">Multiple Incomplete Flows Detected</p>
              <p className="text-sm mb-3">
                We found {blockingFlows.length} incomplete discovery flows that are preventing you from proceeding.
                Please resolve these conflicts by completing or deleting the blocking flows below.
              </p>
            </div>

            {/* Cleanup Progress */}
            {isCleaningFlows && cleanupProgress && (
              <div className="bg-blue-50 border border-blue-200 rounded p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                  <span className="text-sm font-medium text-blue-800">Cleaning up flows...</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>{cleanupProgress.currentFlowId ? `Deleting ${cleanupProgress.currentFlowId}` : 'Processing...'}</span>
                    <span>{cleanupProgress.current}/{cleanupProgress.total}</span>
                  </div>
                  <Progress value={(cleanupProgress.current / cleanupProgress.total) * 100} className="h-2" />
                </div>
              </div>
            )}

            {/* Blocking Flows List */}
            {!isCleaningFlows && (
              <div className="space-y-3">
                <p className="text-sm font-medium text-orange-700">Blocking Flows:</p>
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {blockingFlows.map((flow) => (
                    <div key={flow.id} className="bg-white border border-orange-200 rounded p-3 flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-800 truncate">
                            Flow {flow.id.substring(0, 8)}...
                          </span>
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            {flow.phase}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded ${
                            flow.status === 'failed' ? 'bg-red-100 text-red-700' :
                            flow.status === 'incomplete' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {flow.status}
                          </span>
                        </div>
                        <div className="mt-1">
                          <p className="text-xs text-gray-600">
                            Created: {new Date(flow.created_at).toLocaleDateString()}
                          </p>
                          {flow.issues.length > 0 && (
                            <p className="text-xs text-red-600 mt-1">
                              Issues: {flow.issues.join(', ')}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {flow.canRecover && (
                          <Button
                            onClick={() => onTriggerFlowRecovery?.(flow.id)}
                            disabled={isRecovering || deletingFlowIds.has(flow.id)}
                            size="sm"
                            variant="outline"
                            className="text-blue-600 hover:bg-blue-50"
                          >
                            <RefreshCw className={`h-3 w-3 mr-1 ${isRecovering ? 'animate-spin' : ''}`} />
                            Recover
                          </Button>
                        )}
                        {flow.canDelete && (
                          <Button
                            onClick={() => handleDeleteFlow(flow.id)}
                            disabled={deletingFlowIds.has(flow.id) || isCleaningFlows}
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className={`h-3 w-3 mr-1 ${deletingFlowIds.has(flow.id) ? 'animate-spin' : ''}`} />
                            Delete
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {!isCleaningFlows && (
              <div className="flex flex-wrap gap-2 pt-2">
                <Button
                  onClick={handleDeleteAllBlockingFlows}
                  disabled={isCleaningFlows || blockingFlows.filter(f => f.canDelete).length === 0}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete All Incomplete Flows ({blockingFlows.filter(f => f.canDelete).length})
                </Button>
                <Button
                  onClick={() => navigate('/discovery/cmdb-import')}
                  variant="outline"
                  className="border-orange-300 text-orange-700 hover:bg-orange-50"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Start Fresh Import
                </Button>
                <Button
                  onClick={() => navigate('/discovery')}
                  variant="outline"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Discovery
                </Button>
              </div>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Show recovery progress instead of flow not found error when recovery is active
  if (isFlowNotFound && (isRecovering || recoveryProgress)) {
    return (
      <Alert className="mb-6 border-blue-200 bg-blue-50">
        <RefreshCw className={`h-5 w-5 text-blue-600 ${isRecovering ? 'animate-spin' : ''}`} />
        <AlertDescription className="text-blue-800">
          <div className="space-y-4">
            <div>
              <p className="font-medium mb-2">Automatic Flow Recovery in Progress</p>
              <p className="text-sm mb-3">
                We detected an issue with your discovery flow and are automatically attempting to recover it.
                This usually takes just a few moments.
              </p>
            </div>

            {recoveryProgress && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>{recoveryProgress.currentStep || 'Processing...'}</span>
                  <span>{recoveryProgress.progress}%</span>
                </div>
                <Progress value={recoveryProgress.progress} className="h-2" />
                {recoveryProgress.message && (
                  <p className="text-xs text-blue-600 italic">{recoveryProgress.message}</p>
                )}
              </div>
            )}

            {recoveryError && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <div className="flex items-center space-x-2">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <p className="text-sm text-red-800 font-medium">Automatic Recovery Failed</p>
                </div>
                <p className="text-xs text-red-700 mt-1">{recoveryError}</p>
                <div className="mt-3 flex space-x-2">
                  <Button
                    onClick={() => handleAutomaticRecovery()}
                    disabled={isRecovering}
                    size="sm"
                    className="bg-red-600 hover:bg-red-700"
                  >
                    <RefreshCw className={`h-3 w-3 mr-1 ${isRecovering ? 'animate-spin' : ''}`} />
                    Retry Recovery
                  </Button>
                  <Button
                    onClick={() => navigate('/discovery/cmdb-import')}
                    variant="outline"
                    size="sm"
                  >
                    Start New Import
                  </Button>
                </div>
              </div>
            )}

            {recoveredFlowId && (
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <p className="text-sm text-green-800 font-medium">Recovery Successful!</p>
                </div>
                <p className="text-xs text-green-700 mt-1">Flow has been recovered and is now ready to use.</p>
              </div>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Flow not found error (fallback when recovery is not available or has permanently failed)
  if (isFlowNotFound) {
    return (
      <Alert className="mb-6 border-red-200 bg-red-50">
        <AlertTriangle className="h-5 w-5 text-red-600" />
        <AlertDescription className="text-red-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium mb-2">
                {flowId ? 'Discovery Flow Recovery Failed' : 'No Active Discovery Flows'}
              </p>
              <p className="text-sm mb-3">
                {flowId
                  ? 'We attempted to automatically recover your discovery flow, but were unable to restore it.'
                  : 'No active discovery flows were found for your current engagement.'
                } {onTriggerFlowRecovery ? 'Automatic recovery was attempted but failed.' : ''} This might happen if:
              </p>
              <ul className="text-sm list-disc list-inside space-y-1 mb-3">
                {flowId ? (
                  <>
                    <li>The flow was deleted or expired</li>
                    <li>You're using an invalid or outdated flow ID</li>
                    <li>The flow wasn't created properly during data import</li>
                  </>
                ) : (
                  <>
                    <li>No data has been imported yet for this engagement</li>
                    <li>All existing flows have been completed or deleted</li>
                    <li>You may be in the wrong engagement or client context</li>
                  </>
                )}
              </ul>
              <p className="text-sm">
                Please start a new discovery flow by uploading your data on the Data Import page.
              </p>
            </div>
            <div className="ml-4 flex flex-col space-y-2">
              {onTriggerFlowRecovery && (flowId || effectiveFlowId) && (
                <Button
                  onClick={handleAutomaticRecovery}
                  disabled={isRecovering}
                  className="bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
                >
                  <RefreshCw className={`h-4 w-4 ${isRecovering ? 'animate-spin' : ''}`} />
                  <span>Retry Recovery</span>
                </Button>
              )}
              <Button
                onClick={() => navigate('/discovery/cmdb-import')}
                className="bg-red-600 hover:bg-red-700 flex items-center space-x-2"
              >
                <Upload className="h-4 w-4" />
                <span>Start New Import</span>
              </Button>
              <Button
                onClick={() => navigate('/discovery')}
                variant="outline"
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Discovery</span>
              </Button>
            </div>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // No field mapping available
  if (!isLoading && !hasData && !isFlowNotFound) {
    return (
      <Alert className="mb-6 border-yellow-200 bg-yellow-50">
        <AlertTriangle className="h-5 w-5 text-yellow-600" />
        <AlertDescription className="text-yellow-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium mb-2">No Field Mapping Available</p>
              <p className="text-sm mb-3">
                {flowList && flowList.length > 0
                  ? `Found ${flowList.length} flow(s) but none contain field mapping data ready for attribute mapping.`
                  : 'No discovery flows found for your current context.'
                }
              </p>
              <p className="text-sm">
                Please import data or trigger field mapping analysis to continue.
              </p>
            </div>
            <div className="ml-4 flex flex-col space-y-2">
              <Button
                onClick={() => navigate('/discovery/cmdb-import')}
                className="bg-yellow-600 hover:bg-yellow-700 flex items-center space-x-2"
              >
                <Upload className="h-4 w-4" />
                <span>Import Data</span>
              </Button>
              {effectiveFlowId && (
                <Button
                  onClick={onTriggerFieldMappingCrew}
                  disabled={isAnalyzing}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <Zap className="h-4 w-4" />
                  <span>Trigger Field Mapping</span>
                </Button>
              )}
            </div>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Viewing previous discovery data
  if (!flowId && !isFlowNotFound && hasData) {
    return (
      <Alert className="mb-6 border-blue-200 bg-blue-50">
        <Upload className="h-5 w-5 text-blue-600" />
        <AlertDescription className="text-blue-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium mb-2">Viewing Previous Discovery Data</p>
              <p className="text-sm">
                You're viewing field mapping data from a previous discovery flow.
                To start a new discovery with fresh data, upload a new CMDB file.
              </p>
            </div>
            <Button
              onClick={() => navigate('/discovery/cmdb-import')}
              className="ml-4 bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
            >
              <Upload className="h-4 w-4" />
              <span>Start New Import</span>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  return null;
};
