import React from 'react';
import { Info } from 'lucide-react'
import { Loader2, Brain, Cog, CheckCircle, AlertTriangle, ArrowRight, FileText, Shield, Database } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { UploadFile } from '../CMDBImport.types';
import { getStatusColor } from '../utils/statusUtils'
import { getStatusIcon } from '../utils/statusUtils'

interface CMDBDataTableProps {
  files?: UploadFile[]; // Legacy prop name
  uploadedFiles?: UploadFile[]; // New prop name
  setFiles?: (files: UploadFile[] | ((prev: UploadFile[]) => UploadFile[])) => void; // Legacy
  setUploadedFiles?: (files: UploadFile[] | ((prev: UploadFile[]) => UploadFile[])) => void; // New
  onStartFlow?: () => void; // Legacy
  onStartDiscoveryFlow?: () => void; // New
  isFlowRunning?: boolean;
  isStartingFlow?: boolean;
  flowState?: unknown;
}

export const CMDBDataTable: React.FC<CMDBDataTableProps> = ({
  files,
  uploadedFiles,
  setFiles,
  setUploadedFiles,
  onStartFlow,
  onStartDiscoveryFlow,
  isFlowRunning,
  isStartingFlow,
  flowState,
}) => {
  // Support both prop names for compatibility
  const actualFiles = uploadedFiles || files || [];
  const actualSetFiles = setUploadedFiles || setFiles;
  const actualOnStartFlow = onStartDiscoveryFlow || onStartFlow;
  const actualIsFlowRunning = isStartingFlow || isFlowRunning;

  if (actualFiles.length === 0) {
    return null;
  }

  const file = actualFiles[0]; // Assuming one file at a time for now

  // Map flow states to display statuses
  const mapFlowStatusToDisplayStatus = (flowStatus: string, fileStatus: string, currentPhase: string, progress: number, hasFieldMappings: boolean): string => {
    // If flow is active but stuck in resuming phase with no progress, treat as ready
    if (flowStatus === 'active' && currentPhase === 'resuming' && progress === 0) {
      return 'approved';
    }

    // Special handling for initialized status - depends on whether field mappings are ready
    if (flowStatus === 'initialized') {
      return hasFieldMappings ? 'waiting_for_approval' : 'processing';
    }

    const flowStatusMapping: Record<string, string> = {
      'running': 'processing',
      'active': 'processing',
      'in_progress': 'processing',
      'processing': 'processing',
      'completed': 'approved',
      'failed': 'error',
      'cancelled': 'error',
      'paused': 'processing',
      'waiting_for_approval': 'waiting_for_approval' // Should show as waiting for user action
    };

    if (flowStatus && flowStatusMapping[flowStatus]) {
      return flowStatusMapping[flowStatus];
    }

    return fileStatus || 'processing';
  };

  const progress = flowState?.progress_percentage || 0;
  const currentPhase = flowState?.current_phase || file.current_phase;
  const hasFieldMappings = flowState?.field_mappings && Object.keys(flowState.field_mappings).length > 0;
  const currentStatus = mapFlowStatusToDisplayStatus(flowState?.status, file.status, currentPhase, progress, hasFieldMappings);
  const StatusIcon = getStatusIcon(currentStatus);

  // Extract agent insights from flow state
  const agentInsights = flowState?.agent_insights || [];
  const flowSummary = file.flow_summary || {};

  // Parse agent insights for security, privacy, and quality analysis
  const getInsightsByType = (type: string) =>
    agentInsights.filter(insight =>
      insight.category === type ||
      insight.agent_name?.toLowerCase().includes(type) ||
      insight.message?.toLowerCase().includes(type)
    );

  const securityInsights = getInsightsByType('security');
  const privacyInsights = getInsightsByType('privacy');
  const qualityInsights = getInsightsByType('quality');
  const validationInsights = getInsightsByType('validation');

  // Determine security and privacy status from agent insights
  // Analysis is complete when agents have actually run and provided insights, flow is truly completed,
  // or when field mappings are available (indicating successful upload processing)
  const isAnalysisComplete = flowState?.status === 'completed' || currentStatus === 'approved' || hasFieldMappings;

  const securityStatus = securityInsights.length > 0 ?
    (securityInsights.some(i => i.severity === 'high' || i.confidence < 0.7) ? false : true) :
    (isAnalysisComplete ? true : undefined); // Default to secure if analysis complete

  const privacyStatus = privacyInsights.length > 0 ?
    (privacyInsights.some(i => i.severity === 'high' || i.confidence < 0.7) ? false : true) :
    (isAnalysisComplete ? true : undefined); // Default to compliant if analysis complete

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
              {currentStatus === 'waiting_for_approval' ? 'Waiting for Approval' :
               currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Data Statistics Section */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-blue-900 mb-3 flex items-center">
              <Info className="h-4 w-4 mr-2" />
              File Analysis Summary
            </h4>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Records Count */}
              <div className="flex items-center space-x-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Database className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {flowSummary.total_assets || flowState?.raw_data?.length || 'Analyzing...'}
                  </p>
                  <p className="text-xs text-gray-600">Records Found</p>
                </div>
              </div>

              {/* File Type */}
              <div className="flex items-center space-x-3">
                <div className="bg-green-100 p-2 rounded-lg">
                  <FileText className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {file.type === 'text/csv' ? 'CSV Data' :
                     file.type === 'application/json' ? 'JSON Data' :
                     file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ? 'Excel Data' :
                     'Data File'}
                  </p>
                  <p className="text-xs text-gray-600">File Type</p>
                </div>
              </div>

              {/* Security Status */}
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  securityStatus === false ? 'bg-red-100' :
                  securityStatus === true ? 'bg-green-100' : 'bg-yellow-100'
                }`}>
                  <Shield className={`h-4 w-4 ${
                    securityStatus === false ? 'text-red-600' :
                    securityStatus === true ? 'text-green-600' : 'text-yellow-600'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {securityStatus === false ? 'Issues Found' :
                     securityStatus === true ? 'Secure' : 'Analyzing...'}
                  </p>
                  <p className="text-xs text-gray-600">Security Status</p>
                </div>
              </div>

              {/* Data Quality */}
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  (flowState?.errors?.length || 0) > 0 ? 'bg-red-100' :
                  (flowState?.warnings?.length || 0) > 0 ? 'bg-yellow-100' :
                  qualityInsights.length > 0 ? 'bg-green-100' :
                  isAnalysisComplete ? 'bg-green-100' : 'bg-yellow-100'
                }`}>
                  <CheckCircle className={`h-4 w-4 ${
                    (flowState?.errors?.length || 0) > 0 ? 'text-red-600' :
                    (flowState?.warnings?.length || 0) > 0 ? 'text-yellow-600' :
                    qualityInsights.length > 0 ? 'text-green-600' :
                    isAnalysisComplete ? 'text-green-600' : 'text-yellow-600'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {(flowState?.errors?.length || 0) > 0 ? `${flowState.errors.length} Errors` :
                     (flowState?.warnings?.length || 0) > 0 ? `${flowState.warnings.length} Warnings` :
                     qualityInsights.length > 0 ? 'Good Quality' :
                     isAnalysisComplete ? 'Good Quality' : 'Analyzing...'}
                  </p>
                  <p className="text-xs text-gray-600">Data Quality</p>
                </div>
              </div>
            </div>

            {/* Agent Insights & Concerns */}
            {(securityInsights.length > 0 || privacyInsights.length > 0 || qualityInsights.length > 0) && (
              <div className="mt-4 space-y-3">
                {/* Security Insights */}
                {securityInsights.length > 0 && (
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <Shield className="h-4 w-4 text-orange-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-orange-900">Security Analysis</p>
                        <ul className="text-xs text-orange-700 mt-1 space-y-1">
                          {securityInsights.slice(0, 3).map((insight, idx) => (
                            <li key={idx}>• {insight.message || insight.recommendation}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Privacy Insights */}
                {privacyInsights.length > 0 && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <Info className="h-4 w-4 text-blue-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-900">Privacy Analysis</p>
                        <ul className="text-xs text-blue-700 mt-1 space-y-1">
                          {privacyInsights.slice(0, 3).map((insight, idx) => (
                            <li key={idx}>• {insight.message || insight.recommendation}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quality Insights */}
                {qualityInsights.length > 0 && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-green-900">Quality Analysis</p>
                        <ul className="text-xs text-green-700 mt-1 space-y-1">
                          {qualityInsights.slice(0, 3).map((insight, idx) => (
                            <li key={idx}>• {insight.message || insight.recommendation}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
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
                onClick={actualOnStartFlow}
                disabled={actualIsFlowRunning || currentStatus === 'completed'}
                className="bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
              >
                {actualIsFlowRunning ? (
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
