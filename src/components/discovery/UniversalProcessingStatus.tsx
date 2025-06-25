import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  FileText, 
  Shield, 
  Bot, 
  Loader2,
  RefreshCw,
  XCircle,
  AlertCircle,
  Info,
  Zap,
  TrendingUp,
  Network,
  Upload,
  Database,
  Cpu
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useComprehensiveRealTimeMonitoring } from '@/hooks/useRealTimeProcessing';

interface UniversalProcessingStatusProps {
  flow_id?: string;
  page_context?: string;
  title?: string;
  className?: string;
  compact?: boolean;
  showAgentInsights?: boolean;
  showValidationDetails?: boolean;
  onProcessingComplete?: () => void;
  onValidationFailed?: (issues: string[]) => void;
}

const UniversalProcessingStatus: React.FC<UniversalProcessingStatusProps> = ({
  flow_id,
  page_context = 'data_import',
  title = 'Upload & Validation Status',
  className = '',
  compact = false,
  showAgentInsights = true,
  showValidationDetails = true,
  onProcessingComplete,
  onValidationFailed
}) => {
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['status']));

  // Only use real-time monitoring if flow_id is provided
  const monitoring = flow_id ? useComprehensiveRealTimeMonitoring(flow_id, page_context) : null;

  // Update last update time when new data arrives
  useEffect(() => {
    if (monitoring?.processing.processingStatus || monitoring?.insights.latestInsights.length > 0) {
      setLastUpdateTime(new Date());
    }
  }, [monitoring?.processing.processingStatus, monitoring?.insights.latestInsights]);

  // Handle processing completion
  useEffect(() => {
    if (monitoring?.processing.processingStatus?.status === 'completed' && onProcessingComplete) {
      onProcessingComplete();
    }
  }, [monitoring?.processing.processingStatus?.status, onProcessingComplete]);

  // Handle validation failures
  useEffect(() => {
    if (monitoring?.hasAnyIssues && onValidationFailed) {
      const allIssues = [
        ...(monitoring.validation.getSecurityIssues?.() || []),
        ...(monitoring.validation.getFormatErrors?.() || []),
        ...(monitoring.validation.hasDataQualityIssues ? ['Data quality score below threshold'] : [])
      ];
      onValidationFailed(allIssues);
    }
  }, [monitoring?.hasAnyIssues, monitoring?.validation, onValidationFailed]);

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

  const getStatusIcon = (status?: string) => {
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

  // If no flow_id is provided, show a placeholder/demo state
  if (!flow_id) {
    return (
      <Card className={`${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Upload className="w-4 h-4 text-gray-500" />
              <div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <p className="text-sm text-gray-600">
                  Real-time processing updates will appear here
                </p>
              </div>
            </div>
            <Badge variant="secondary">Idle</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-gray-500">
            <Network className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-sm font-medium">No Active Processing</p>
            <p className="text-xs mt-1">Start a data import or discovery flow to see live updates</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const processingStatus = monitoring?.processing.processingStatus;
  const isProcessingActive = monitoring?.isAnyProcessingActive || false;
  const overallStatus = monitoring?.overallStatus || 'unknown';
  const hasIssues = monitoring?.hasAnyIssues || false;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Main Status Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(overallStatus)}
              <div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <p className="text-sm text-gray-600">
                  {page_context.replace('_', ' ')} • Flow: {flow_id.substring(0, 8)}...
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={isProcessingActive ? 'default' : 'secondary'}>
                {isProcessingActive ? 'Processing' : 'Idle'}
              </Badge>
              {hasIssues && (
                <Badge variant="destructive">Issues</Badge>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => monitoring?.processing.refetch()}
                disabled={monitoring?.processing.isLoading}
              >
                <RefreshCw className={`w-3 h-3 mr-1 ${monitoring?.processing.isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {processingStatus ? (
            <>
              {/* Progress Overview */}
              <div className={`grid ${compact ? 'grid-cols-2' : 'grid-cols-4'} gap-4 mb-4`}>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {processingStatus.progress_percentage.toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-600">Progress</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatRecordCount(processingStatus.records_processed)}
                  </div>
                  <div className="text-xs text-gray-600">Processed</div>
                </div>
                {!compact && (
                  <>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {formatRecordCount(processingStatus.records_failed)}
                      </div>
                      <div className="text-xs text-gray-600">Failed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {monitoring?.insights.insights.length || 0}
                      </div>
                      <div className="text-xs text-gray-600">Insights</div>
                    </div>
                  </>
                )}
              </div>

              {/* Progress Bar */}
              <Progress 
                value={processingStatus.progress_percentage} 
                className="h-2 mb-2"
              />
              
              <div className="flex justify-between text-xs text-gray-500">
                <span>
                  {formatRecordCount(processingStatus.records_processed)} / {formatRecordCount(processingStatus.records_total)} records
                </span>
                <span>
                  Last update: {formatTimeAgo(lastUpdateTime.toISOString())}
                </span>
              </div>

              {/* Current Phase */}
              <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">
                    Current Phase: {processingStatus.phase.replace('_', ' ')}
                  </span>
                  {processingStatus.estimated_completion && (
                    <span className="text-xs text-blue-600">
                      • ETA: {formatTimeAgo(processingStatus.estimated_completion)}
                    </span>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-4 text-gray-500">
              <Loader2 className="w-6 h-6 mx-auto mb-2 animate-spin text-blue-500" />
              <p className="text-sm">Loading processing status...</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Validation Status - Only show if enabled and has data */}
      {showValidationDetails && monitoring?.validation.validationData && (
        <Card>
          <CardHeader 
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleSection('validation')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-purple-500" />
                <CardTitle className="text-base">Security & Validation</CardTitle>
                {hasIssues && (
                  <Badge variant="destructive">Issues Found</Badge>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {monitoring.validation.overallValidationPassed ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                )}
              </div>
            </div>
          </CardHeader>

          {expandedSections.has('validation') && (
            <CardContent>
              <div className="grid grid-cols-3 gap-3">
                <div className={`p-3 rounded-lg border text-center ${monitoring.validation.hasSecurityIssues ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-center mb-1">
                    <Shield className={`w-4 h-4 ${monitoring.validation.hasSecurityIssues ? 'text-red-500' : 'text-green-500'}`} />
                  </div>
                  <div className="text-sm font-medium">Security</div>
                  <div className="text-xs text-gray-600">
                    {monitoring.validation.getSecurityIssues().length} issues
                  </div>
                </div>

                <div className={`p-3 rounded-lg border text-center ${monitoring.validation.hasFormatErrors ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-center mb-1">
                    <FileText className={`w-4 h-4 ${monitoring.validation.hasFormatErrors ? 'text-red-500' : 'text-green-500'}`} />
                  </div>
                  <div className="text-sm font-medium">Format</div>
                  <div className="text-xs text-gray-600">
                    {monitoring.validation.getFormatErrors().length} errors
                  </div>
                </div>

                <div className={`p-3 rounded-lg border text-center ${monitoring.validation.hasDataQualityIssues ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center justify-center mb-1">
                    <Database className={`w-4 h-4 ${monitoring.validation.hasDataQualityIssues ? 'text-yellow-500' : 'text-green-500'}`} />
                  </div>
                  <div className="text-sm font-medium">Quality</div>
                  <div className="text-xs text-gray-600">
                    {Math.round(monitoring.validation.getQualityScore() * 100)}%
                  </div>
                </div>
              </div>

              {/* Show validation issues */}
              {hasIssues && (
                <div className="mt-3 space-y-2">
                  {monitoring.validation.getSecurityIssues().map((issue, index) => (
                    <Alert key={index} variant="destructive">
                      <Shield className="h-4 w-4" />
                      <AlertDescription>Security: {issue}</AlertDescription>
                    </Alert>
                  ))}
                  {monitoring.validation.getFormatErrors().map((error, index) => (
                    <Alert key={index} variant="destructive">
                      <FileText className="h-4 w-4" />
                      <AlertDescription>Format: {error}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Agent Insights - Only show if enabled and has insights */}
      {showAgentInsights && monitoring?.insights.insights.length > 0 && (
        <Card>
          <CardHeader 
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleSection('insights')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-green-500" />
                <CardTitle className="text-base">Agent Insights</CardTitle>
                <Badge variant="outline">
                  {monitoring.insights.insights.length} insights
                </Badge>
              </div>
              <Zap className="w-4 h-4 text-yellow-500" />
            </div>
          </CardHeader>

          {expandedSections.has('insights') && (
            <CardContent>
              <ScrollArea className="h-32">
                <div className="space-y-2">
                  {monitoring.insights.insights.slice(-5).reverse().map((insight, index) => (
                    <div key={index} className="p-2 bg-blue-50 border border-blue-200 rounded">
                      <div className="flex items-start justify-between mb-1">
                        <span className="font-medium text-sm text-blue-900">
                          {insight.agent_name}
                        </span>
                        <span className="text-xs text-blue-600">
                          {formatTimeAgo(insight.created_at)}
                        </span>
                      </div>
                      <h5 className="font-medium text-sm text-blue-900">
                        {insight.title}
                      </h5>
                      <p className="text-sm text-blue-800 mt-1">
                        {insight.description}
                      </p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          )}
        </Card>
      )}

      {/* Live Updates Feed - Only show if not compact and has updates */}
      {!compact && monitoring?.processing.accumulatedUpdates.length > 0 && (
        <Card>
          <CardHeader 
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleSection('updates')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <CardTitle className="text-base">Live Updates</CardTitle>
                <Badge variant="outline">
                  {monitoring.processing.accumulatedUpdates.length} updates
                </Badge>
              </div>
              {isProcessingActive && (
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-green-600">Live</span>
                </div>
              )}
            </div>
          </CardHeader>

          {expandedSections.has('updates') && (
            <CardContent>
              <ScrollArea className="h-24">
                <div className="space-y-1">
                  {monitoring.processing.accumulatedUpdates.slice(-3).reverse().map((update) => (
                    <div key={update.id} className="flex items-start space-x-2 p-1 text-sm">
                      <TrendingUp className="w-3 h-3 text-blue-500 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <span className="font-medium">{update.agent_name}:</span>
                        <span className="text-gray-700 ml-1">{update.message}</span>
                        <span className="text-xs text-gray-500 ml-2">
                          {formatTimeAgo(update.timestamp)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
};

export default UniversalProcessingStatus; 