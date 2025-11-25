import React from 'react';
import { RefreshCw, Zap, ArrowRight, AlertCircle, Wifi, WifiOff, Activity, CheckCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { isFlowTerminal } from '@/constants/flowStates';
import { AttributeMappingState } from '../types';
import type { FieldMapping } from '@/types/api/discovery/field-mapping-types';

interface AttributeMappingHeaderProps {
  mappingProgress: {
    total: number;
    mapped: number;
    critical_mapped: number;
  };
  isAgenticLoading: boolean;
  onRefetch: () => void;
  onTriggerAnalysis: () => void;
  onBulkApproveNeedsReview: () => void;
  onReprocessMappings?: () => void;
  flowStatus?: string;
  hasFieldMappings?: boolean;
  fieldMappings?: FieldMapping[];
  // NEW AGENTIC PROPS: SSE connection status
  isSSEConnected?: boolean;
  connectionType?: 'sse' | 'polling' | 'disconnected';
}

export const AttributeMappingHeader: React.FC<AttributeMappingHeaderProps> = ({
  mappingProgress,
  isAgenticLoading,
  onRefetch,
  onTriggerAnalysis,
  onBulkApproveNeedsReview,
  onReprocessMappings,
  flowStatus,
  hasFieldMappings,
  fieldMappings,
  isSSEConnected,
  connectionType
}) => {
  const isFlowPaused = flowStatus === 'paused' || flowStatus === 'waiting_for_approval' || flowStatus === 'waiting_for_user_approval';

  // CRITICAL FIX: Disable Execute button when flow is in terminal state
  const isFlowTerminalState = isFlowTerminal(flowStatus);

  // Count mappings that need review
  // CC FIX: Align filter logic with ThreeColumnFieldMapper's categorization
  // Must match the "Needs Review" column logic in mappingUtils.ts
  const needsReviewCount = React.useMemo(() => {
    if (!fieldMappings) return 0;
    return fieldMappings.filter(m =>
      m.status !== 'approved' &&
      m.status !== 'rejected' &&
      (
        !m.target_field ||
        m.target_field === 'UNMAPPED' ||
        m.target_field === '' ||
        m.target_field === 'unmapped' ||
        m.target_field === 'Unassigned'
      )
    ).length;
  }, [fieldMappings]);

  return (
    <>
      {/* Show completion message if flow is completed */}
      {isFlowTerminalState && flowStatus?.toLowerCase() === 'completed' && (
        <Alert className="mb-6 border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>Discovery Flow Completed Successfully</strong>
            <p className="mt-1">
              The discovery flow has been completed. All field mappings and data processing have been finished.
              You can review the results below or proceed to the next phase of your migration.
            </p>
          </AlertDescription>
        </Alert>
      )}

      {/* Show alert if flow is paused and waiting for approval */}
      {isFlowPaused && hasFieldMappings && !isFlowTerminalState && (
        <Alert className="mb-6 border-blue-200 bg-blue-50">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <strong>Flow Paused for Your Review</strong>
            <p className="mt-1">
              The discovery flow has generated field mapping suggestions and is waiting for your approval.
              Please review the mappings below, make any necessary adjustments, and click "Continue to Data Cleansing" to resume the flow.
            </p>
          </AlertDescription>
        </Alert>
      )}

      {/* Show alert if flow is cancelled or failed */}
      {isFlowTerminalState && flowStatus && flowStatus.toLowerCase() !== 'completed' && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Flow {flowStatus.charAt(0).toUpperCase() + flowStatus.slice(1)}</strong>
            <p className="mt-1">
              The discovery flow has been {flowStatus.toLowerCase()}. No further actions can be performed on this flow.
            </p>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Field Mapping & Critical Attributes</h1>
            <div className="flex items-center space-x-3">
              <p className="text-gray-600">
                {mappingProgress.total > 0
                  ? `${mappingProgress.total} attributes analyzed with ${mappingProgress.mapped} mapped and ${mappingProgress.critical_mapped} migration-critical`
                  : 'AI-powered field mapping and critical attribute identification'
                }
              </p>
              {/* AGENTIC UI: Real-time connection status */}
              {connectionType && (
                <div className="flex items-center space-x-1 text-sm">
                  {connectionType === 'sse' && isSSEConnected && (
                    <>
                      <Wifi className="w-4 h-4 text-green-500" />
                      <span className="text-green-600">Live updates</span>
                    </>
                  )}
                  {connectionType === 'polling' && (
                    <>
                      <Activity className="w-4 h-4 text-yellow-500" />
                      <span className="text-yellow-600">Polling updates</span>
                    </>
                  )}
                  {(!isSSEConnected || connectionType === 'disconnected') && (
                    <>
                      <WifiOff className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">Manual refresh</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
        <Button
          onClick={onRefetch}
          disabled={isAgenticLoading}
          variant="outline"
          className="flex items-center space-x-2"
        >
          {isAgenticLoading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span>Refresh</span>
        </Button>

        <Button
          onClick={onTriggerAnalysis}
          disabled={isAgenticLoading || isFlowTerminalState}
          variant="outline"
          className="flex items-center space-x-2"
          title={isFlowTerminalState ? `Cannot execute: Flow is ${flowStatus}` : 'Trigger field mapping analysis'}
        >
          <Zap className="h-4 w-4" />
          <span>Trigger Analysis</span>
        </Button>

        {needsReviewCount > 0 && (
          <Button
            onClick={onBulkApproveNeedsReview}
            disabled={isAgenticLoading || isFlowTerminalState}
            variant="outline"
            className="flex items-center space-x-2 bg-blue-50 hover:bg-blue-100 border-blue-300"
            title={isFlowTerminalState ? `Cannot approve: Flow is ${flowStatus}` : `Approve ${needsReviewCount} unmapped ${needsReviewCount === 1 ? 'field' : 'fields'} as custom_attributes`}
          >
            <CheckCircle className="h-4 w-4 text-blue-600" />
            <span className="text-blue-700">
              Approve {needsReviewCount} as Custom Attrs
            </span>
          </Button>
        )}

        {onReprocessMappings && hasFieldMappings && (
          <Button
            onClick={onReprocessMappings}
            disabled={isAgenticLoading || isFlowTerminalState}
            variant="outline"
            className="flex items-center space-x-2"
            title={isFlowTerminalState ? `Cannot reprocess: Flow is ${flowStatus}` : 'Reprocess Mappings'}
          >
            <RefreshCw className="h-4 w-4" />
            <span>Reprocess Mappings</span>
          </Button>
        )}

        {canContinueToDataCleansing && (
          <Button
            onClick={onContinueToDataCleansing}
            className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
            title="Continue to data cleansing phase"
          >
            <span>Continue to Data Cleansing</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
        </div>
      </div>
    </>
  );
};
