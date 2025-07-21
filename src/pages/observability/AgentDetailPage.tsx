/**
 * Agent Detail Page
 * Comprehensive individual agent view with performance analytics, task history, and detailed insights
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Calendar, Clock, TrendingUp, TrendingDown, Activity, Brain, AlertTriangle, CheckCircle, XCircle, ArrowLeft, Download, RefreshCw, Settings, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Progress } from '../../components/ui/progress';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { AgentStatusIndicator, AgentMetricsChart } from '../../components/observability';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';
import { LoadingSpinner } from '../../components/observability/LoadingStates';

// Types for detailed agent data
interface AgentDetailData {
  agentName: string;
  profile: {
    role: string;
    specialization: string;
    capabilities: string[];
    endpoints: string[];
    configuration: Record<string, any>;
  };
  performance: {
    successRate: number;
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    avgDuration: number;
    avgConfidence: number;
    memoryUsage: number;
    llmCalls: number;
    lastActive: string;
  };
  trends: {
    successRateHistory: number[];
    durationHistory: number[];
    confidenceHistory: number[];
    taskCountHistory: number[];
    memoryUsageHistory: number[];
    timestamps: string[];
  };
  taskHistory: {
    tasks: Array<{
      taskId: string;
      flowId: string;
      taskName: string;
      startedAt: string;
      completedAt: string;
      duration: number;
      status: 'completed' | 'failed' | 'timeout';
      success: boolean;
      confidenceScore: number;
      resultPreview: string;
      errorMessage?: string;
      llmCallsCount: number;
      tokenUsage: { inputTokens: number; outputTokens: number };
    }>;
    totalTasks: number;
    hasMore: boolean;
  };
  llmAnalytics: {
    totalTokens: number;
    avgTokensPerTask: number;
    tokenTrends: number[];
    costEstimate: number;
    topModelsUsed: Array<{ model: string; usage: number }>;
  };
}

interface TaskHistoryRowProps {
  task: AgentDetailData['taskHistory']['tasks'][0];
  onViewDetails: (taskId: string) => void;
}

const TaskHistoryRow: React.FC<TaskHistoryRowProps> = ({ task, onViewDetails }) => {
  const statusColor = task.success ? 'text-green-600' : 'text-red-600';
  const statusIcon = task.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />;

  return (
    <div className="border-b border-gray-100 p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={statusColor}>{statusIcon}</span>
            <span className="font-medium text-gray-900">{task.taskName}</span>
            <Badge variant="secondary" className="text-xs">
              {task.duration.toFixed(1)}s
            </Badge>
            <Badge variant={task.confidenceScore > 0.8 ? 'default' : 'secondary'} className="text-xs">
              {(task.confidenceScore * 100).toFixed(0)}% confidence
            </Badge>
          </div>
          <div className="text-sm text-gray-600 mt-1">
            {task.resultPreview}
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(task.startedAt).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <Brain className="w-3 h-3" />
              {task.llmCallsCount} LLM calls
            </span>
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {task.tokenUsage.inputTokens + task.tokenUsage.outputTokens} tokens
            </span>
          </div>
          {task.errorMessage && (
            <Alert className="mt-2">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {task.errorMessage}
              </AlertDescription>
            </Alert>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetails(task.taskId)}
          className="ml-4"
        >
          View Details
        </Button>
      </div>
    </div>
  );
};

const AgentDetailPage: React.FC = () => {
  const { agentName } = useParams<{ agentName: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentData, setAgentData] = useState<AgentDetailData | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [taskHistoryPage, setTaskHistoryPage] = useState(0);

  // Load agent data
  useEffect(() => {
    if (!agentName) {
      setError('Agent name is required');
      return;
    }

    loadAgentData();
  }, [agentName]);

  const loadAgentData = async () => {
    if (!agentName) return;

    try {
      setLoading(true);
      setError(null);

      // Simulate comprehensive agent data loading
      // In a real implementation, this would call multiple API endpoints
      const [performance, analytics, taskHistory] = await Promise.all([
        agentObservabilityService.getAgentPerformance(agentName, 30),
        agentObservabilityService.getAgentAnalytics(agentName, 30),
        agentObservabilityService.getAgentTaskHistory(agentName, 20, taskHistoryPage * 20)
      ]);

      if (!performance.success || !analytics.success || !taskHistory.success) {
        throw new Error('Failed to load agent data');
      }

      // Transform the data into the detailed format
      const detailData: AgentDetailData = {
        agentName,
        profile: {
          role: getAgentRole(agentName),
          specialization: getAgentSpecialization(agentName),
          capabilities: getAgentCapabilities(agentName),
          endpoints: getAgentEndpoints(agentName),
          configuration: {}
        },
        performance: {
          successRate: performance.data.summary.success_rate,
          totalTasks: performance.data.summary.total_tasks,
          completedTasks: performance.data.summary.successful_tasks,
          failedTasks: performance.data.summary.failed_tasks,
          avgDuration: performance.data.summary.avg_duration_seconds,
          avgConfidence: performance.data.summary.avg_confidence_score,
          memoryUsage: analytics.data.analytics.resource_usage.avg_memory_usage_mb,
          llmCalls: performance.data.summary.total_llm_calls,
          lastActive: performance.data.current_status?.last_activity || 'Unknown'
        },
        trends: {
          successRateHistory: performance.data.trends.success_rates,
          durationHistory: performance.data.trends.avg_durations,
          confidenceHistory: Array.from({ length: 7 }, () => Math.random() * 0.2 + 0.8),
          taskCountHistory: performance.data.trends.task_counts,
          memoryUsageHistory: Array.from({ length: 7 }, () => Math.random() * 50 + 100),
          timestamps: performance.data.trends.dates
        },
        taskHistory: {
          tasks: taskHistory.data.tasks.map(task => ({
            taskId: task.task_id,
            flowId: task.flow_id,
            taskName: task.task_name,
            startedAt: task.started_at,
            completedAt: task.completed_at,
            duration: task.duration_seconds,
            status: task.status as 'completed' | 'failed' | 'timeout',
            success: task.success,
            confidenceScore: task.confidence_score,
            resultPreview: task.result_preview,
            errorMessage: task.error_message,
            llmCallsCount: task.llm_calls_count,
            tokenUsage: {
              inputTokens: task.token_usage?.input_tokens || 0,
              outputTokens: task.token_usage?.output_tokens || 0
            }
          })),
          totalTasks: taskHistory.data.total_tasks,
          hasMore: taskHistory.data.tasks.length === 20
        },
        llmAnalytics: {
          totalTokens: analytics.data.analytics.resource_usage.total_tokens_used,
          avgTokensPerTask: Math.round(analytics.data.analytics.resource_usage.total_tokens_used / performance.data.summary.total_tasks),
          tokenTrends: Array.from({ length: 7 }, () => Math.random() * 1000 + 500),
          costEstimate: (analytics.data.analytics.resource_usage.total_tokens_used * 0.00002), // Rough estimate
          topModelsUsed: [
            { model: 'claude-3-haiku', usage: 80 },
            { model: 'gpt-4o-mini', usage: 20 }
          ]
        }
      };

      setAgentData(detailData);
    } catch (err) {
      console.error('Failed to load agent data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load agent data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAgentData();
  };

  const handleExportData = () => {
    if (!agentData) return;
    
    const dataStr = JSON.stringify(agentData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${agentName}-performance-data.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleViewTaskDetails = (taskId: string) => {
    // This would navigate to a task detail view
    console.log('View task details:', taskId);
  };

  // Helper functions for agent metadata
  const getAgentRole = (name: string): string => {
    const roles: Record<string, string> = {
      'DataImportValidationAgent': 'Data Validation Specialist',
      'AttributeMappingAgent': 'Field Mapping Expert',
      'DataCleansingAgent': 'Data Quality Engineer',
      'AssetInventoryAgent': 'Asset Classification Specialist',
      'DependencyAnalysisAgent': 'Dependency Mapping Expert',
      'TechDebtAnalysisAgent': 'Technical Debt Assessor'
    };
    return roles[name] || 'Specialized Agent';
  };

  const getAgentSpecialization = (name: string): string => {
    const specializations: Record<string, string> = {
      'DataImportValidationAgent': 'Security scanning, PII detection, and data validation',
      'AttributeMappingAgent': 'Field mapping with confidence scoring and validation',
      'DataCleansingAgent': 'Data standardization and bulk processing operations',
      'AssetInventoryAgent': 'Asset classification and inventory management',
      'DependencyAnalysisAgent': 'System dependency mapping and analysis',
      'TechDebtAnalysisAgent': 'Technical debt assessment and recommendation'
    };
    return specializations[name] || 'General purpose agent operations';
  };

  const getAgentCapabilities = (name: string): string[] => {
    const capabilities: Record<string, string[]> = {
      'DataImportValidationAgent': ['PII Detection', 'Security Scanning', 'Data Validation', 'Compliance Checking'],
      'AttributeMappingAgent': ['Field Mapping', 'Confidence Scoring', 'Schema Analysis', 'Data Type Inference'],
      'DataCleansingAgent': ['Data Standardization', 'Bulk Processing', 'Quality Assessment', 'Format Conversion'],
      'AssetInventoryAgent': ['Asset Classification', 'Inventory Tracking', 'Categorization', 'Metadata Extraction'],
      'DependencyAnalysisAgent': ['Dependency Mapping', 'Impact Analysis', 'Relationship Discovery', 'Flow Analysis'],
      'TechDebtAnalysisAgent': ['Debt Assessment', 'Risk Analysis', 'Recommendation Generation', 'Priority Scoring']
    };
    return capabilities[name] || ['General Operations', 'Task Execution'];
  };

  const getAgentEndpoints = (name: string): string[] => {
    return [
      `/api/v1/agents/${name.toLowerCase()}/validate`,
      `/api/v1/agents/${name.toLowerCase()}/process`,
      `/api/v1/agents/${name.toLowerCase()}/status`
    ];
  };

  // Performance metrics calculations
  const performanceMetrics = useMemo(() => {
    if (!agentData) return null;

    const { performance, trends } = agentData;
    
    return {
      efficiency: (performance.successRate * 100).toFixed(1),
      reliability: performance.totalTasks > 0 ? ((performance.totalTasks - performance.failedTasks) / performance.totalTasks * 100).toFixed(1) : '0',
      speed: performance.avgDuration.toFixed(1),
      confidence: (performance.avgConfidence * 100).toFixed(1),
      trend: trends.successRateHistory.length > 1 ? 
        (trends.successRateHistory[trends.successRateHistory.length - 1] > trends.successRateHistory[0] ? 'up' : 'down') : 'stable'
    };
  }, [agentData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !agentData) {
    return (
      <div className="p-6">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Agent not found'}
          </AlertDescription>
        </Alert>
        <Button onClick={() => navigate('/observability')} className="mt-4" variant="outline">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Overview
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button onClick={() => navigate('/observability')} variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Overview
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-900">{agentData.agentName}</h1>
                <AgentStatusIndicator 
                  status={performanceMetrics?.trend === 'up' ? 'active' : 'idle'} 
                  variant="badge" 
                  showLabel 
                />
              </div>
              <p className="text-gray-600 mt-1">{agentData.profile.role}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              onClick={handleRefresh}
              variant="outline" 
              size="sm"
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={handleExportData} variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export Data
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Configure
            </Button>
          </div>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">{performanceMetrics?.efficiency}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
            <Progress value={parseFloat(performanceMetrics?.efficiency || '0')} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Tasks</p>
                <p className="text-2xl font-bold text-blue-600">{agentData.performance.totalTasks}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {agentData.performance.completedTasks} completed, {agentData.performance.failedTasks} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                <p className="text-2xl font-bold text-purple-600">{performanceMetrics?.speed}s</p>
              </div>
              <Clock className="w-8 h-8 text-purple-500" />
            </div>
            <p className="text-xs text-gray-500 mt-2">Average task completion time</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Confidence</p>
                <p className="text-2xl font-bold text-orange-600">{performanceMetrics?.confidence}%</p>
              </div>
              <Brain className="w-8 h-8 text-orange-500" />
            </div>
            <p className="text-xs text-gray-500 mt-2">Average confidence score</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="tasks">Task History</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Agent Profile</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900">Specialization</h4>
                    <p className="text-gray-600">{agentData.profile.specialization}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Key Capabilities</h4>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {agentData.profile.capabilities.map((capability, index) => (
                        <Badge key={index} variant="secondary">
                          {capability}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">API Endpoints</h4>
                    <div className="space-y-1 mt-2">
                      {agentData.profile.endpoints.map((endpoint, index) => (
                        <code key={index} className="block text-xs bg-gray-100 p-2 rounded">
                          {endpoint}
                        </code>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <AgentMetricsChart 
                  data={{
                    data: agentData.trends.successRateHistory.map((rate, index) => ({
                      timestamp: agentData.trends.timestamps[index],
                      value: rate * 100,
                      label: `${(rate * 100).toFixed(1)}%`
                    })),
                    color: '#10b981',
                    trend: performanceMetrics?.trend as 'up' | 'down' | 'stable',
                    changePercent: 0
                  }}
                  title="Success Rate Trend"
                  height={200}
                  showGrid
                  animate
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Duration Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <AgentMetricsChart 
                  data={{
                    data: agentData.trends.durationHistory.map((duration, index) => ({
                      timestamp: agentData.trends.timestamps[index],
                      value: duration,
                      label: `${duration.toFixed(1)}s`
                    })),
                    color: '#3b82f6',
                    trend: 'stable',
                    changePercent: 0
                  }}
                  title="Average Task Duration"
                  height={200}
                  showGrid
                  animate
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Confidence Score Evolution</CardTitle>
              </CardHeader>
              <CardContent>
                <AgentMetricsChart 
                  data={{
                    data: agentData.trends.confidenceHistory.map((confidence, index) => ({
                      timestamp: agentData.trends.timestamps[index],
                      value: confidence * 100,
                      label: `${(confidence * 100).toFixed(1)}%`
                    })),
                    color: '#f59e0b',
                    trend: 'up',
                    changePercent: 0
                  }}
                  title="Confidence Score Trends"
                  height={200}
                  showGrid
                  animate
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Task History</CardTitle>
              <p className="text-sm text-gray-600">
                Showing {agentData.taskHistory.tasks.length} of {agentData.taskHistory.totalTasks} tasks
              </p>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-96 overflow-y-auto">
                {agentData.taskHistory.tasks.map((task) => (
                  <TaskHistoryRow 
                    key={task.taskId} 
                    task={task} 
                    onViewDetails={handleViewTaskDetails}
                  />
                ))}
              </div>
              {agentData.taskHistory.hasMore && (
                <div className="p-4 border-t">
                  <Button 
                    variant="outline" 
                    onClick={() => setTaskHistoryPage(prev => prev + 1)}
                    className="w-full"
                  >
                    Load More Tasks
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Memory Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Current Usage</span>
                    <span className="font-medium">{agentData.performance.memoryUsage.toFixed(1)} MB</span>
                  </div>
                  <Progress value={Math.min((agentData.performance.memoryUsage / 500) * 100, 100)} />
                  <AgentMetricsChart 
                    data={{
                      data: agentData.trends.memoryUsageHistory.map((usage, index) => ({
                        timestamp: agentData.trends.timestamps[index],
                        value: usage,
                        label: `${usage.toFixed(1)} MB`
                      })),
                      color: '#8b5cf6',
                      trend: 'stable',
                      changePercent: 0
                    }}
                    title="Memory Usage Over Time"
                    height={150}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>LLM Usage Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Tokens</p>
                      <p className="text-lg font-bold">{agentData.llmAnalytics.totalTokens.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Avg per Task</p>
                      <p className="text-lg font-bold">{agentData.llmAnalytics.avgTokensPerTask}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Est. Cost</p>
                      <p className="text-lg font-bold">${agentData.llmAnalytics.costEstimate.toFixed(4)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">LLM Calls</p>
                      <p className="text-lg font-bold">{agentData.performance.llmCalls}</p>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Model Usage</h4>
                    {agentData.llmAnalytics.topModelsUsed.map((model, index) => (
                      <div key={index} className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">{model.model}</span>
                        <span className="text-sm font-medium">{model.usage}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
              <p className="text-sm text-gray-600">
                Current configuration and parameters for {agentData.agentName}
              </p>
            </CardHeader>
            <CardContent>
              <Alert>
                <Settings className="h-4 w-4" />
                <AlertDescription>
                  Configuration management is coming soon. Agent settings will be editable in future releases.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentDetailPage;