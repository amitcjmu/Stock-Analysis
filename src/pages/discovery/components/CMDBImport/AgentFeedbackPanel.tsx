import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import { Info } from 'lucide-react'
import { Bot, FileSpreadsheet, AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface ProcessingSummary {
  records_found?: number;
  data_source?: string;
  workflow_phase?: string;
  agent_status?: string;
}

interface StatusData {
  flow_status?: {
    current_phase?: string;
    status?: string;
    cmdb_data?: {
      file_data?: unknown[];
    };
    metadata?: Record<string, unknown>;
  };
  current_phase?: string;
  status?: string;
  metadata?: {
    filename?: string;
    [key: string]: unknown;
  };
  message?: string;
  processing_summary?: ProcessingSummary;
  agent_insights?: Array<string | Record<string, unknown>>;
  clarification_questions?: Array<string | Record<string, unknown>>;
  data_quality_assessment?: Record<string, unknown>;
  field_mappings?: Record<string, string | number | boolean>;
  agent_results?: Record<string, unknown>;
}

interface AgentFeedbackPanelProps {
  flowId: string;
  statusData: StatusData | null;
}

const AgentFeedbackPanel: React.FC<AgentFeedbackPanelProps> = ({
  flowId,
  statusData
}) => {
  // Show loading state while waiting for data
  if (!statusData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center text-gray-500">
            <Clock className="h-5 w-5 mr-2 animate-spin" />
            <span>Loading agent status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Extract data from the API response
  const flowStatus = statusData.flow_status || {};
  const currentPhase = flowStatus.current_phase || statusData.current_phase || 'unknown';
  const workflowStatus = flowStatus.status || statusData.status || 'unknown';
  const cmdbData = flowStatus.cmdb_data || {};
  const metadata = flowStatus.metadata || statusData.metadata || {};
  const recordCount = cmdbData.file_data?.length || 0;
  const filename = metadata.filename || 'Unknown file';

  console.log('📊 AgentFeedbackPanel received data:', {
    workflowStatus,
    currentPhase,
    recordCount,
    filename,
    hasFlowStatus: !!flowStatus,
    hasCmdbData: !!cmdbData.file_data
  });

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'running':
      case 'in_progress':
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Info className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string): any => {
    switch (status) {
      case 'running':
      case 'in_progress':
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6 text-blue-600" />
              <div>
                <CardTitle>Agent Analysis Status</CardTitle>
                <CardDescription>
                  Flow: {flowId?.substring(0, 8)}...
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(workflowStatus)}
              <Badge className={getStatusColor(workflowStatus)}>
                {workflowStatus}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Current Phase:</p>
              <p className="text-lg">{currentPhase?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}</p>
            </div>

            {/* Data Summary */}
            {recordCount > 0 && (
              <div className="grid grid-cols-3 gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <p className="text-lg font-bold text-blue-600">{recordCount}</p>
                  <p className="text-xs text-gray-600">Records</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-green-600 truncate" title={filename || 'Unknown file'}>
                    {filename && filename.length > 12 ? filename.substring(0, 12) + '...' : (filename || 'Unknown file')}
                  </p>
                  <p className="text-xs text-gray-600">Source File</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold text-purple-600">{workflowStatus}</p>
                  <p className="text-xs text-gray-600">Status</p>
                </div>
              </div>
            )}

            {statusData.message && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>{statusData.message}</AlertDescription>
              </Alert>
            )}

            {/* Progress message for initialization phase */}
            {workflowStatus === 'running' && currentPhase === 'initialization' && !statusData.message && (
              <Alert className="border-blue-200 bg-blue-50">
                <Bot className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                    <span>CrewAI agents are analyzing your {recordCount} records. The Data Ingestion Crew is validating data format and structure...</span>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Processing Summary */}
      {statusData.processing_summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Data Processing Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {statusData.processing_summary.records_found && (
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {statusData.processing_summary.records_found}
                  </p>
                  <p className="text-sm text-gray-600">Records Found</p>
                </div>
              )}

              {statusData.processing_summary.data_source && (
                <div className="text-center">
                  <p className="text-sm font-bold text-green-600 truncate">
                    {statusData.processing_summary.data_source}
                  </p>
                  <p className="text-sm text-gray-600">Data Source</p>
                </div>
              )}

              <div className="text-center">
                <p className="text-lg font-bold text-purple-600">
                  {statusData.processing_summary.workflow_phase?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}
                </p>
                <p className="text-sm text-gray-600">Current Phase</p>
              </div>

              <div className="text-center">
                <p className="text-lg font-bold text-orange-600">
                  {statusData.processing_summary.agent_status?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}
                </p>
                <p className="text-sm text-gray-600">Agent Status</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Insights */}
      {statusData.agent_insights && statusData.agent_insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Insights</CardTitle>
            <CardDescription>Real-time analysis from CrewAI agents</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {statusData.agent_insights.map((insight, index) => (
                <Alert key={index}>
                  <Bot className="h-4 w-4" />
                  <AlertDescription>
                    {typeof insight === 'string' ? insight : JSON.stringify(insight, null, 2)}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Clarification Questions */}
      {statusData.clarification_questions && statusData.clarification_questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Questions</CardTitle>
            <CardDescription>Agents need clarification on these items</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {statusData.clarification_questions.map((question, index) => (
                <Alert key={index}>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {typeof question === 'string' ? question : JSON.stringify(question, null, 2)}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Quality Assessment */}
      {statusData.data_quality_assessment && Object.keys(statusData.data_quality_assessment).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Data Quality Assessment</CardTitle>
            <CardDescription>Agent analysis of data quality</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm overflow-auto">
                {JSON.stringify(statusData.data_quality_assessment, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Field Mappings */}
      {statusData.field_mappings && Object.keys(statusData.field_mappings).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Field Mappings</CardTitle>
            <CardDescription>Agent-suggested field mappings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(statusData.field_mappings).map(([source, target]) => (
                <div key={source} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-mono text-sm">{source}</span>
                  <span className="text-gray-400">→</span>
                  <span className="font-mono text-sm text-green-600">{String(target)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Results (if any) */}
      {statusData.agent_results && Object.keys(statusData.agent_results).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Results</CardTitle>
            <CardDescription>Detailed results from agent processing</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm overflow-auto max-h-96">
                {JSON.stringify(statusData.agent_results, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Raw Data (for debugging - can be removed later) */}
      {process.env.NODE_ENV === 'development' && (
        <Card>
          <CardHeader>
            <CardTitle>Raw Agent Data (Debug)</CardTitle>
            <CardDescription>Full response from agents</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-xs overflow-auto max-h-96">
                {JSON.stringify(statusData, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentFeedbackPanel;
