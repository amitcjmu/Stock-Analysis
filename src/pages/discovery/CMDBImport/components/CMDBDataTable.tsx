import React from 'react';
import { 
  Loader2, 
  Brain, 
  Cog, 
  CheckCircle, 
  AlertTriangle, 
  ArrowRight 
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { UploadFile } from '../CMDBImport.types';
import { getStatusIcon, getStatusColor } from '../utils/statusUtils';

interface CMDBDataTableProps {
  files: UploadFile[];
  setFiles: (files: UploadFile[] | ((prev: UploadFile[]) => UploadFile[])) => void;
  onStartFlow: () => void;
  isFlowRunning: boolean;
  flowState: any; // Replace with a proper type later
}

export const CMDBDataTable: React.FC<CMDBDataTableProps> = ({
  files,
  setFiles,
  onStartFlow,
  isFlowRunning,
  flowState,
}) => {
  if (files.length === 0) {
    return null;
  }

  const file = files[0]; // Assuming one file at a time for now
  const currentStatus = flowState?.status || file.status;
  const progress = flowState?.progress_percentage || 0;
  const currentPhase = flowState?.current_phase || file.current_phase;
  const StatusIcon = getStatusIcon(currentStatus);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Upload & Validation Status</h2>
      
      <Card key={file.id} className="border border-gray-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <StatusIcon className={`h-5 w-5 ${
                currentStatus === 'running' ? 'animate-spin text-purple-500' :
                currentStatus === 'completed' ? 'text-green-500' :
                currentStatus === 'failed' ? 'text-red-500' :
                'text-gray-400'
              }`} />
              <div>
                <h3 className="font-medium text-gray-900">{file.name}</h3>
                <p className="text-sm text-gray-600">
                  {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type}
                </p>
              </div>
            </div>
            <Badge className={getStatusColor(currentStatus)}>
              {currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* CrewAI Discovery Flow Progress */}
          {isFlowRunning && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>CrewAI Discovery Flow Progress</span>
                  <span>{progress.toFixed(0)}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
              
              {/* Current Phase */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <Cog className="h-4 w-4 text-purple-600 animate-spin" />
                  <span className="text-sm font-medium text-purple-900">
                    Current Phase: {currentPhase || 'Initializing...'}
                  </span>
                </div>
                <p className="text-xs text-purple-700 mt-1">
                  CrewAI agents are analyzing your data. See activity log below.
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t mt-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {currentStatus === 'completed' 
                    ? 'Discovery Flow Complete' 
                    : 'Ready for Discovery Flow'}
                </p>
                <p className="text-sm text-gray-600">
                  {currentStatus === 'completed'
                    ? 'Data analysis complete. View results in the Asset Inventory.'
                    : 'Data has been uploaded. Start the AI-powered discovery flow.'
                  }
                </p>
              </div>
              <Button
                onClick={onStartFlow}
                disabled={isFlowRunning || currentStatus === 'completed'}
                className="bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
              >
                {isFlowRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Flow in Progress...</span>
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4" />
                    <span>
                      {currentStatus === 'completed'
                        ? 'View Results' 
                        : 'Start Discovery Flow'
                      }
                    </span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>

          {currentStatus === 'failed' && (
            <Alert className="mt-4 border-red-200 bg-red-50">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <AlertDescription className="text-red-800">
                The discovery flow failed. Please check the agent activity log for details.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};