import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  FileText, 
  Shield, 
  Database, 
  Bot, 
  Loader2,
  PlayCircle,
  PauseCircle,
  RefreshCw,
  XCircle,
  AlertCircle,
  Info,
  Zap,
  TrendingUp,
  Users,
  Network
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  useComprehensiveRealTimeMonitoring, 
  ProcessingUpdate 
} from '@/hooks/useRealTimeProcessing';

interface RealTimeProcessingMonitorProps {
  flow_id: string;
  page_context?: string;
  className?: string;
  onProcessingComplete?: () => void;
  onValidationFailed?: (issues: string[]) => void;
}

const RealTimeProcessingMonitor: React.FC<RealTimeProcessingMonitorProps> = ({
  flow_id,
  page_context = 'data_import',
  className = '',
  onProcessingComplete,
  onValidationFailed
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['processing', 'validation', 'insights'])
  );
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());

  const {
    processing,
    insights,
    validation,
    actions,
    isAnyProcessingActive,
    hasAnyIssues,
    overallStatus
  } = useComprehensiveRealTimeMonitoring(flow_id, page_context);

  // Update last update time when new data arrives
  useEffect(() => {
    if (processing.processingStatus || insights.latestInsights.length > 0) {
      setLastUpdateTime(new Date());
    }
  }, [processing.processingStatus, insights.latestInsights]);

  // Handle processing completion
  useEffect(() => {
    if (processing.processingStatus?.status === 'completed' && onProcessingComplete) {
      onProcessingComplete();
    }
  }, [processing.processingStatus?.status, onProcessingComplete]);

  // Handle validation failures
  useEffect(() => {
    if (hasAnyIssues && onValidationFailed) {
      const allIssues = [
        ...validation.getSecurityIssues(),
        ...validation.getFormatErrors(),
        ...(validation.hasDataQualityIssues ? ['Data quality score below threshold'] : [])
      ];
      onValidationFailed(allIssues);
    }
  }, [hasAnyIssues, validation, onValidationFailed]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
      case 'validating':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'initializing':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getUpdateTypeIcon = (type: ProcessingUpdate['update_type']) => {
    switch (type) {
      case 'progress':
        return <TrendingUp className="w-3 h-3 text-blue-500" />;
      case 'validation':
        return <Shield className="w-3 h-3 text-purple-500" />;
      case 'insight':
        return <Bot className="w-3 h-3 text-green-500" />;
      case 'error':
        return <XCircle className="w-3 h-3 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-3 h-3 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="w-3 h-3 text-green-500" />;
      default:
        return <Info className="w-3 h-3 text-gray-500" />;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  };

  const formatRecordCount = (count: number) => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toString();
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Overall Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(overallStatus)}
              <div>
                <CardTitle className="text-lg">Real-Time Processing Monitor</CardTitle>
                <p className="text-sm text-gray-600">
                  Flow: {flow_id.substring(0, 8)}... • {page_context.replace('_', ' ')}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={isAnyProcessingActive ? 'default' : 'secondary'}>
                {isAnyProcessingActive ? 'Processing' : 'Idle'}
              </Badge>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => processing.refetch()}
                disabled={processing.isLoading}
              >
                <RefreshCw className={`w-3 h-3 mr-1 ${processing.isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        {processing.processingStatus && (
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {processing.processingStatus.progress_percentage.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600">Progress</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatRecordCount(processing.processingStatus.records_processed)}
                </div>
                <div className="text-xs text-gray-600">Processed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {formatRecordCount(processing.processingStatus.records_failed)}
                </div>
                <div className="text-xs text-gray-600">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {insights.insights.length}
                </div>
                <div className="text-xs text-gray-600">Insights</div>
              </div>
            </div>

            <Progress 
              value={processing.processingStatus.progress_percentage} 
              className="h-2 mb-2"
            />
            
            <div className="flex justify-between text-xs text-gray-500">
              <span>
                {formatRecordCount(processing.processingStatus.records_processed)} / {formatRecordCount(processing.processingStatus.records_total)} records
              </span>
              <span>
                Last update: {formatTimeAgo(lastUpdateTime.toISOString())}
              </span>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Validation Status */}
      {validation.validationData && (
        <Card>
          <CardHeader 
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleSection('validation')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-purple-500" />
                <CardTitle className="text-base">Security & Validation</CardTitle>
                {hasAnyIssues && (
                  <Badge variant="destructive">Issues Found</Badge>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {validation.overallValidationPassed ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                )}
              </div>
            </div>
          </CardHeader>

          {expandedSections.has('validation') && (
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className={`p-3 rounded-lg border ${validation.hasSecurityIssues ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Security Scan</span>
                    {validation.hasSecurityIssues ? (
                      <XCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {validation.getSecurityIssues().length} issues found
                  </div>
                </div>

                <div className={`p-3 rounded-lg border ${validation.hasFormatErrors ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Format Check</span>
                    {validation.hasFormatErrors ? (
                      <XCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {validation.getFormatErrors().length} errors found
                  </div>
                </div>

                <div className={`p-3 rounded-lg border ${validation.hasDataQualityIssues ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Data Quality</span>
                    <span className="text-sm font-bold">
                      {Math.round(validation.getQualityScore() * 100)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    Quality score
                  </div>
                </div>
              </div>

              {/* Validation Issues */}
              {hasAnyIssues && (
                <div className="space-y-2">
                  {validation.getSecurityIssues().map((issue, index) => (
                    <Alert key={index} variant="destructive">
                      <Shield className="h-4 w-4" />
                      <AlertDescription>Security: {issue}</AlertDescription>
                    </Alert>
                  ))}
                  {validation.getFormatErrors().map((error, index) => (
                    <Alert key={index} variant="destructive">
                      <FileText className="h-4 w-4" />
                      <AlertDescription>Format: {error}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}

              {/* Validation Actions */}
              <div className="flex space-x-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => actions.triggerValidation.mutate({ flow_id, validation_type: 'security' })}
                  disabled={actions.triggerValidation.isPending}
                >
                  <Shield className="w-3 h-3 mr-1" />
                  Re-scan Security
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => actions.triggerValidation.mutate({ flow_id, validation_type: 'format' })}
                  disabled={actions.triggerValidation.isPending}
                >
                  <FileText className="w-3 h-3 mr-1" />
                  Re-check Format
                </Button>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Agent Status and Insights */}
      {processing.processingStatus?.agent_status && (
        <Card>
          <CardHeader 
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleSection('insights')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-green-500" />
                <CardTitle className="text-base">Agent Activity & Insights</CardTitle>
                <Badge variant="outline">
                  {Object.keys(processing.processingStatus.agent_status).length} agents
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-gray-600">
                  {insights.insights.length} insights
                </span>
              </div>
            </div>
          </CardHeader>

          {expandedSections.has('insights') && (
            <CardContent>
              {/* Agent Status Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                {Object.entries(processing.processingStatus.agent_status).map(([agentName, status]) => (
                  <div key={agentName} className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{agentName}</span>
                      <Badge variant={
                        status.status === 'processing' ? 'default' :
                        status.status === 'completed' ? 'secondary' :
                        status.status === 'error' ? 'destructive' : 'outline'
                      }>
                        {status.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                      <div>
                        <div className="font-medium">{Math.round(status.confidence * 100)}%</div>
                        <div>Confidence</div>
                      </div>
                      <div>
                        <div className="font-medium">{status.insights_generated}</div>
                        <div>Insights</div>
                      </div>
                      <div>
                        <div className="font-medium">{status.clarifications_pending}</div>
                        <div>Questions</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Recent Insights */}
              {insights.insights.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-3 flex items-center">
                    <Zap className="w-4 h-4 mr-1 text-yellow-500" />
                    Recent Agent Insights
                  </h4>
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {insights.insights.slice(-10).reverse().map((insight, index) => (
                        <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <div className="flex items-start justify-between mb-1">
                            <span className="font-medium text-sm text-blue-900">
                              {insight.agent_name}
                            </span>
                            <span className="text-xs text-blue-600">
                              {formatTimeAgo(insight.created_at)}
                            </span>
                          </div>
                          <h5 className="font-medium text-sm text-blue-900 mb-1">
                            {insight.title}
                          </h5>
                          <p className="text-sm text-blue-800">
                            {insight.description}
                          </p>
                          {insight.confidence && (
                            <div className="mt-2">
                              <Badge variant="outline" className="text-xs">
                                {insight.confidence} confidence
                              </Badge>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Live Updates Feed */}
      <Card>
        <CardHeader 
          className="cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => toggleSection('updates')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-500" />
              <CardTitle className="text-base">Live Updates</CardTitle>
              {processing.accumulatedUpdates.length > 0 && (
                <Badge variant="outline">
                  {processing.accumulatedUpdates.length} updates
                </Badge>
              )}
            </div>
            {isAnyProcessingActive && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-600">Live</span>
              </div>
            )}
          </div>
        </CardHeader>

        {expandedSections.has('updates') && (
          <CardContent>
            {processing.accumulatedUpdates.length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <Network className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No processing updates yet</p>
                <p className="text-xs mt-1">Updates will appear here as agents process your data</p>
              </div>
            ) : (
              <ScrollArea className="h-64">
                <div className="space-y-2">
                  {processing.accumulatedUpdates.slice().reverse().map((update) => (
                    <div key={update.id} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded">
                      {getUpdateTypeIcon(update.update_type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{update.agent_name}</span>
                          <span className="text-xs text-gray-500">
                            {formatTimeAgo(update.timestamp)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mt-1">{update.message}</p>
                        {update.details && (
                          <div className="mt-2 text-xs text-gray-600">
                            {update.details.records_processed !== undefined && (
                              <span className="mr-3">
                                📊 {update.details.records_processed} records
                              </span>
                            )}
                            {update.details.confidence_score !== undefined && (
                              <span className="mr-3">
                                🎯 {Math.round(update.details.confidence_score * 100)}% confidence
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}

            {processing.accumulatedUpdates.length > 0 && (
              <div className="mt-4 flex justify-between items-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={processing.clearUpdates}
                >
                  Clear Updates
                </Button>
                <span className="text-xs text-gray-500">
                  Showing last {processing.accumulatedUpdates.length} updates
                </span>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Processing Controls */}
      {isAnyProcessingActive && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => actions.pauseProcessing.mutate({ flow_id })}
                disabled={actions.pauseProcessing.isPending}
              >
                <PauseCircle className="w-3 h-3 mr-1" />
                Pause
              </Button>
              {processing.processingStatus?.records_failed > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => actions.retryProcessing.mutate({ flow_id, retry_failed_only: true })}
                  disabled={actions.retryProcessing.isPending}
                >
                  <PlayCircle className="w-3 h-3 mr-1" />
                  Retry Failed
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RealTimeProcessingMonitor; 