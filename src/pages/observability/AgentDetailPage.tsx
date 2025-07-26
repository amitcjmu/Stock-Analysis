/**
 * Agent Detail Page
 * Comprehensive individual agent view with performance analytics, task history, and detailed insights
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 *
 * Modularized version with extracted components and hooks
 */

import React from 'react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, RefreshCw, Settings, AlertTriangle } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { AgentStatusIndicator, AgentMetricsChart } from '../../components/observability';
import { LoadingSpinner } from '../../components/observability/LoadingStates';

// Modularized imports
import { useAgentDetail } from './hooks/useAgentDetail';
import { useAgentMetrics } from './hooks/useAgentMetrics';
import { TaskHistoryRow } from './components/TaskHistoryRow';
import { MetricsCards } from './components/MetricsCards';
import { AgentProfileCard } from './components/AgentProfileCard';
import { PerformanceCharts } from './components/PerformanceCharts';
import { ResourceAnalytics } from './components/ResourceAnalytics';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';



const AgentDetailPage: React.FC = () => {
  const { agentName } = useParams<{ agentName: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [taskHistoryPage, setTaskHistoryPage] = useState(0);

  // Use modularized hooks
  const { agentData, loading, refreshing, error, handleRefresh } = useAgentDetail(agentName, taskHistoryPage);
  const { performanceMetrics } = useAgentMetrics(agentData);


  const handleExportData = (): void => {
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

  const handleViewTaskDetails = (taskId: string): void => {
    // This would navigate to a task detail view
    console.log('View task details:', taskId);
  };


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
      <MetricsCards agentData={agentData} performanceMetrics={performanceMetrics} />

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
            <AgentProfileCard agentData={agentData} />

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
                    trend: performanceMetrics?.trend,
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
          <PerformanceCharts agentData={agentData} performanceMetrics={performanceMetrics} />
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
          <ResourceAnalytics agentData={agentData} />
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
