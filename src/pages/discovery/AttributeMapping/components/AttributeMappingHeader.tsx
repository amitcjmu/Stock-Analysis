import React from 'react';
import { RefreshCw, Zap, ArrowRight, AlertCircle, Wifi, WifiOff, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { AttributeMappingState } from '../types';

interface AttributeMappingHeaderProps {
  mappingProgress: {
    total: number;
    mapped: number;
    critical_mapped: number;
  };
  isAgenticLoading: boolean;
  canContinueToDataCleansing: boolean;
  onRefetch: () => void;
  onTriggerAnalysis: () => void;
  onContinueToDataCleansing: () => void;
  onReprocessMappings?: () => void;
  flowStatus?: string;
  hasFieldMappings?: boolean;
  // NEW AGENTIC PROPS: SSE connection status
  isSSEConnected?: boolean;
  connectionType?: 'sse' | 'polling' | 'disconnected';
}

export const AttributeMappingHeader: React.FC<AttributeMappingHeaderProps> = ({
  mappingProgress,
  isAgenticLoading,
  canContinueToDataCleansing,
  onRefetch,
  onTriggerAnalysis,
  onContinueToDataCleansing,
  onReprocessMappings,
  flowStatus,
  hasFieldMappings,
  isSSEConnected,
  connectionType
}) => {
  const isFlowPaused = flowStatus === 'paused' || flowStatus === 'waiting_for_approval' || flowStatus === 'waiting_for_user_approval';
  
  return (
    <>
      {/* Show alert if flow is paused and waiting for approval */}
      {isFlowPaused && hasFieldMappings && (
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
          disabled={isAgenticLoading}
          variant="outline"
          className="flex items-center space-x-2"
        >
          <Zap className="h-4 w-4" />
          <span>Trigger Analysis</span>
        </Button>
        
        {onReprocessMappings && hasFieldMappings && (
          <Button
            onClick={onReprocessMappings}
            disabled={isAgenticLoading}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Reprocess Mappings</span>
          </Button>
        )}

        {canContinueToDataCleansing && (
          <Button
            onClick={onContinueToDataCleansing}
            className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
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