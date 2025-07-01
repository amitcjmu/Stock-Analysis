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
import { CMDBValidationPanel } from './CMDBValidationPanel';

interface CMDBDataTableProps {
  uploadedFiles: UploadFile[];
  setUploadedFiles: (files: UploadFile[] | ((prev: UploadFile[]) => UploadFile[])) => void;
  isStartingFlow: boolean;
  onStartDiscoveryFlow: () => void;
}

export const CMDBDataTable: React.FC<CMDBDataTableProps> = ({
  uploadedFiles,
  setUploadedFiles,
  isStartingFlow,
  onStartDiscoveryFlow
}) => {
  if (uploadedFiles.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Upload & Validation Status</h2>
      
      {uploadedFiles.map((file) => {
        const StatusIcon = getStatusIcon(file.status);
        
        return (
          <Card key={file.id} className="border border-gray-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <StatusIcon className={`h-5 w-5 ${
                    file.status === 'uploading' ? 'animate-spin text-blue-500' :
                    file.status === 'validating' ? 'animate-pulse text-orange-500' :
                    file.status === 'processing' ? 'animate-spin text-purple-500' :
                    file.status === 'approved' ? 'text-green-500' :
                    file.status === 'approved_with_warnings' ? 'text-yellow-500' :
                    file.status === 'rejected' ? 'text-red-500' :
                    file.status === 'error' ? 'text-red-500' :
                    'text-gray-400'
                  }`} />
                  <div>
                    <h3 className="font-medium text-gray-900">{file.name}</h3>
                    <p className="text-sm text-gray-600">
                      {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type}
                    </p>
                  </div>
                </div>
                <Badge className={getStatusColor(file.status)}>
                  {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {/* Upload Progress */}
              {file.status === 'uploading' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Uploading file...</span>
                    <span>{file.upload_progress}%</span>
                  </div>
                  <Progress value={file.upload_progress} className="h-2" />
                </div>
              )}

              {/* CrewAI Discovery Flow Progress */}
              {file.status === 'processing' && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>CrewAI Discovery Flow Progress</span>
                      <span>{file.discovery_progress || 0}%</span>
                    </div>
                    <Progress value={file.discovery_progress || 0} className="h-2" />
                  </div>
                  
                  {/* Current Phase */}
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Cog className="h-4 w-4 text-purple-600 animate-spin" />
                      <span className="text-sm font-medium text-purple-900">
                        Current Phase: {file.current_phase || 'Initializing...'}
                      </span>
                    </div>
                    <p className="text-xs text-purple-700 mt-1">
                      CrewAI agents are analyzing your data using advanced AI techniques
                    </p>
                  </div>
                </div>
              )}

              {/* Validation Progress */}
              {(file.status === 'validating' || file.status === 'approved' || file.status === 'approved_with_warnings' || file.status === 'rejected') && (
                <CMDBValidationPanel 
                  file={file}
                  onValidationUpdate={(validationData) => {
                    // Update file validation status based on real-time data
                    setUploadedFiles(prev => prev.map(f => 
                      f.id === file.id 
                        ? { 
                            ...f, 
                            format_validation: validationData.format_validation?.status === 'passed',
                            security_clearance: validationData.security_scan?.status === 'passed',
                            privacy_clearance: !validationData.privacy_issues || validationData.privacy_issues.length === 0,
                            validation_progress: validationData.validation_progress || 0,
                            agents_completed: validationData.agents_completed || 0,
                            total_agents: validationData.total_agents || 4
                          }
                        : f
                    ));
                  }}
                />
              )}

              {/* Flow Summary - Completed Flow */}
              {file.status === 'approved' && file.flow_summary && (
                <div className="pt-4 border-t">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <h4 className="text-sm font-semibold text-green-900">CrewAI Discovery Flow Complete</h4>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-700">{file.flow_summary.total_assets}</div>
                        <div className="text-xs text-green-600">Assets Processed</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-700">{file.flow_summary.phases_completed.length}</div>
                        <div className="text-xs text-green-600">Phases Complete</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-yellow-700">{file.flow_summary.warnings}</div>
                        <div className="text-xs text-yellow-600">Warnings</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-red-700">{file.flow_summary.errors}</div>
                        <div className="text-xs text-red-600">Errors</div>
                      </div>
                    </div>
                    
                    {file.flow_summary.phases_completed.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-green-800 mb-1">Completed Phases:</p>
                        <div className="flex flex-wrap gap-1">
                          {file.flow_summary.phases_completed.map(phase => (
                            <Badge key={phase} variant="secondary" className="text-xs bg-green-100 text-green-800">
                              {phase}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {(file.status === 'approved' || file.status === 'approved_with_warnings') && (
                <div className="pt-4 border-t">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {file.flow_summary ? 'Discovery Flow Complete' : 'Ready for Discovery Flow'}
                      </p>
                      <p className="text-sm text-gray-600">
                        {file.flow_summary 
                          ? 'Data analysis complete. Proceed to field mapping and detailed insights.'
                          : 'Data validation complete. Proceed to field mapping and AI-powered analysis.'
                        }
                      </p>
                    </div>
                    <Button
                      onClick={onStartDiscoveryFlow}
                      disabled={isStartingFlow}
                      className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
                    >
                      {isStartingFlow ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Starting Flow...</span>
                        </>
                      ) : (
                        <>
                          <Brain className="h-4 w-4" />
                          <span>{file.flow_summary ? 'View Results' : 'Start Discovery Flow'}</span>
                          <ArrowRight className="h-4 w-4" />
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}

              {file.status === 'approved_with_warnings' && (
                <Alert className="border-yellow-200 bg-yellow-50">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  <AlertDescription className="text-yellow-800">
                    File validation completed with warnings. Review agent feedback before proceeding to field mapping.
                  </AlertDescription>
                </Alert>
              )}

              {file.status === 'rejected' && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <AlertDescription className="text-red-800">
                    File validation failed. Please review agent feedback and upload a corrected file.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};