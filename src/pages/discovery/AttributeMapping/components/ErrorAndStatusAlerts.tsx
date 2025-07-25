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

  // Flow not found error
  if (isFlowNotFound) {
    return (
      <Alert className="mb-6 border-red-200 bg-red-50">
        <AlertTriangle className="h-5 w-5 text-red-600" />
        <AlertDescription className="text-red-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium mb-2">
                {flowId ? 'Discovery Flow Not Found' : 'No Active Discovery Flows'}
              </p>
              <p className="text-sm mb-3">
                {flowId
                  ? 'The discovery flow you\'re trying to access could not be found.'
                  : 'No active discovery flows were found for your current engagement.'
                } This might happen if:
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
