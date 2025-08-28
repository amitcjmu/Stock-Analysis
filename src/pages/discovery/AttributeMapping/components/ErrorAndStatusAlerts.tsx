import React from 'react';
import { AlertTriangle, Upload, ArrowLeft, Zap } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface ErrorAndStatusAlertsProps {
  isFlowNotFound: boolean;
  isLoading: boolean;
  hasData: boolean;
  flowId: string | null;
  flowList: unknown[];
  effectiveFlowId: string | null;
  isAnalyzing: boolean;
  onTriggerFieldMappingCrew: () => void;
  // Additional props for flow recovery
  isRecovering?: boolean;
  recoveryProgress?: number;
  recoveryError?: string | null;
  recoveredFlowId?: string | null;
  onTriggerFlowRecovery?: () => void;
  // Multi-flow blocking props
  blockingFlows?: unknown[];
  hasMultipleBlockingFlows?: boolean;
  onRefresh?: () => void;
}

export const ErrorAndStatusAlerts: React.FC<ErrorAndStatusAlertsProps> = ({
  isFlowNotFound,
  isLoading,
  hasData,
  flowId,
  flowList,
  effectiveFlowId,
  isAnalyzing,
  onTriggerFieldMappingCrew
}) => {
  const navigate = useNavigate();

  // Show flow not found error
  if (isFlowNotFound) {
    return (
      <Alert className="border-orange-500/50 bg-orange-50 dark:bg-orange-900/20">
        <AlertTriangle className="h-4 w-4 text-orange-600" />
        <AlertDescription className="text-gray-700 dark:text-gray-300">
          <div className="space-y-2">
            <p className="font-medium">Discovery Flow Not Found</p>
            {flowList?.length > 0 ? (
              <>
                <p>The requested flow ({flowId || 'none'}) was not found. You have {flowList.length} active flow(s) available.</p>
                <p>Using auto-detected flow: {effectiveFlowId}</p>
              </>
            ) : (
              <>
                <p>No active discovery flows found. Please complete the data import step first.</p>
                <Button
                  onClick={() => navigate('/discovery/cmdb-import')}
                  className="mt-2"
                  variant="outline"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Go to Data Import
                </Button>
              </>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Show loading state
  if (isLoading) {
    return (
      <Alert className="border-blue-500/50 bg-blue-50 dark:bg-blue-900/20">
        <AlertDescription className="text-gray-700 dark:text-gray-300">
          Loading attribute mapping data...
        </AlertDescription>
      </Alert>
    );
  }

  // Show no data state with action button
  if (!hasData && !isAnalyzing) {
    return (
      <Alert className="border-yellow-500/50 bg-yellow-50 dark:bg-yellow-900/20">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertDescription className="text-gray-700 dark:text-gray-300">
          <div className="space-y-3">
            <p className="font-medium">No Attribute Mappings Found</p>
            <p>Field mappings haven't been created yet. Click the button below to start the AI-powered mapping process.</p>
            <Button
              onClick={onTriggerFieldMappingCrew}
              className="mt-2"
              disabled={isAnalyzing}
            >
              <Zap className="h-4 w-4 mr-2" />
              Start Attribute Mapping Analysis
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Show analyzing state
  if (isAnalyzing) {
    return (
      <Alert className="border-blue-500/50 bg-blue-50 dark:bg-blue-900/20">
        <AlertDescription className="text-gray-700 dark:text-gray-300">
          <div className="space-y-2">
            <p className="font-medium">AI Analysis in Progress</p>
            <p>The Field Mapping Crew is analyzing your data and creating attribute mappings...</p>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  return null;
};
