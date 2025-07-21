/**
 * Enhanced Observability Dashboard
 * Comprehensive agent observability with Phase 4A & 4B components
 * Part of the Agent Observability Enhancement project
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { BarChart3, Activity, TrendingUp, Brain, Users, Settings, RefreshCw, Download, Eye, ChevronRight } from 'lucide-react';
import Sidebar from '../../components/Sidebar';

// Import Phase 4A & 4B components
import {
  AgentListOverview,
  ActivityFeed,
  AgentComparison,
  RecommendationEngine,
  AdvancedAnalytics
} from '../../components/observability';

// Import service
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

interface DashboardState {
  selectedAgents: string[];
  refreshInterval: number;
  realTimeEnabled: boolean;
  lastRefresh: Date | null;
}

const EnhancedObservabilityDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [state, setState] = useState<DashboardState>({
    selectedAgents: [],
    refreshInterval: 30000, // 30 seconds
    realTimeEnabled: true,
    lastRefresh: null
  });

  const [activeTab, setActiveTab] = useState(() => {
    return searchParams.get('tab') || 'overview';
  });

  const [dashboardStats, setDashboardStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    avgSuccessRate: 0,
    totalTasksToday: 0,
    criticalIssues: 0
  });

  const [loading, setLoading] = useState(false);

  // Update URL when tab changes
  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    params.set('tab', activeTab);
    setSearchParams(params, { replace: true });
  }, [activeTab, searchParams, setSearchParams]);

  // Load dashboard statistics
  useEffect(() => {
    loadDashboardStats();
    
    if (state.realTimeEnabled && state.refreshInterval > 0) {
      const interval = setInterval(loadDashboardStats, state.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [state.realTimeEnabled, state.refreshInterval]);

  const loadDashboardStats = async () => {
    setLoading(true);
    try {
      const summary = await agentObservabilityService.getAllAgentsSummary(1);
      
      if (summary.success) {
        // Transform the API response to agent card data
        const agentCards = agentObservabilityService.transformToAgentCardData(summary);
        
        if (agentCards && agentCards.length > 0) {
          const activeCount = agentCards.filter(agent => agent.status === 'active').length;
          const avgSuccess = agentCards.reduce((sum, agent) => sum + agent.successRate, 0) / agentCards.length;
          const totalTasks = agentCards.reduce((sum, agent) => sum + agent.totalTasks, 0);
          
          setDashboardStats({
            totalAgents: agentCards.length,
            activeAgents: activeCount,
            avgSuccessRate: avgSuccess * 100,
            totalTasksToday: totalTasks,
            criticalIssues: agentCards.filter(agent => agent.status === 'error' || agent.status === 'offline' || (agent.successRate > 0 && agent.successRate < 0.5)).length
          });
        } else {
          // Handle case with no agents
          setDashboardStats({
            totalAgents: 0,
            activeAgents: 0,
            avgSuccessRate: 0,
            totalTasksToday: 0,
            criticalIssues: 0
          });
        }
      }

      setState(prev => ({ ...prev, lastRefresh: new Date() }));
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentSelect = (agentName: string) => {
    // Navigate to agent detail page
    navigate(`/observability/agent/${encodeURIComponent(agentName)}`);
  };

  const handleAgentSelectionChange = (agents: string[]) => {
    setState(prev => ({ ...prev, selectedAgents: agents }));
  };

  const handleRefresh = () => {
    loadDashboardStats();
  };

  const handleExportDashboard = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      stats: dashboardStats,
      selectedAgents: state.selectedAgents,
      activeTab
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `observability-dashboard-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleToggleRealTime = () => {
    setState(prev => ({ ...prev, realTimeEnabled: !prev.realTimeEnabled }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Breadcrumb */}
            <div className="mb-4 flex items-center text-sm text-gray-600">
              <span>Observability</span>
              <ChevronRight className="w-4 h-4 mx-2" />
              <span className="text-gray-900">
                {activeTab === 'analytics' ? 'Enhanced Analytics' : 
                 activeTab === 'comparison' ? 'Agent Comparison' :
                 activeTab === 'recommendations' ? 'Recommendations' :
                 activeTab === 'settings' ? 'Settings' :
                 activeTab === 'activity' ? 'Activity Feed' :
                 'Agent Dashboard'}
              </span>
            </div>
            
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <BarChart3 className="w-8 h-8 text-blue-600" />
                    Agent Observability Dashboard
                  </h1>
                  <p className="text-gray-600 mt-1">
                    Comprehensive monitoring and analytics for AI agents
                  </p>
                </div>
          
          <div className="flex items-center gap-3">
            <Button 
              onClick={handleToggleRealTime}
              variant={state.realTimeEnabled ? "default" : "outline"}
              size="sm"
            >
              <Activity className={`w-4 h-4 mr-2 ${state.realTimeEnabled ? 'animate-pulse' : ''}`} />
              Real-time {state.realTimeEnabled ? 'On' : 'Off'}
            </Button>
            
            <Button onClick={handleRefresh} variant="outline" size="sm" disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button onClick={handleExportDashboard} variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Last refresh indicator */}
        {state.lastRefresh && (
          <div className="mt-2 text-sm text-gray-500">
            Last updated: {state.lastRefresh.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Agents</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardStats.totalAgents}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Now</p>
                <p className="text-2xl font-bold text-green-600">{dashboardStats.activeAgents}</p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Success Rate</p>
                <p className="text-2xl font-bold text-blue-600">{dashboardStats.avgSuccessRate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasks Today</p>
                <p className="text-2xl font-bold text-purple-600">{dashboardStats.totalTasksToday}</p>
              </div>
              <Brain className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">{dashboardStats.criticalIssues}</p>
              </div>
              <div className="relative">
                {dashboardStats.criticalIssues > 0 && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                )}
                <Eye className="w-8 h-8 text-red-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="activity">Activity Feed</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="analytics">Advanced Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Agent List Overview - Takes 2/3 width */}
            <div className="xl:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Agent Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <AgentListOverview
                    refreshInterval={state.realTimeEnabled ? state.refreshInterval : 0}
                    onAgentSelect={handleAgentSelect}
                    showFilters
                    compactView={false}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Activity Feed - Takes 1/3 width */}
            <div className="xl:col-span-1">
              <ActivityFeed
                height="600px"
                realTime={state.realTimeEnabled}
                refreshInterval={state.refreshInterval}
                compact
                showControls={false}
                onEventClick={(event) => {
                  if (event.agentName) {
                    handleAgentSelect(event.agentName);
                  }
                }}
              />
            </div>
          </div>

          {/* Quick Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Quick Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RecommendationEngine
                showAllAgents
                maxRecommendations={3}
                enableFeedback={false}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-6">
          <ActivityFeed
            height="800px"
            realTime={state.realTimeEnabled}
            refreshInterval={state.refreshInterval}
            showControls
            enableFeedback
            onEventClick={(event) => {
              if (event.agentName) {
                handleAgentSelect(event.agentName);
              }
            }}
          />
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6">
          <AgentComparison
            maxAgents={4}
            showRanking
            enableExport
            onComparisonChange={handleAgentSelectionChange}
          />
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <RecommendationEngine
            showAllAgents
            maxRecommendations={10}
            enableFeedback
            onRecommendationApply={(recommendation) => {
              console.log('Applying recommendation:', recommendation.title);
              // Implementation would handle recommendation application
            }}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <AdvancedAnalytics
            agentNames={state.selectedAgents.length > 0 ? state.selectedAgents : undefined}
            defaultTimeRange={30}
            showPredictions
            enableExport
            refreshInterval={0}
          />
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Dashboard Settings</CardTitle>
              <p className="text-sm text-gray-600">
                Configure dashboard behavior and preferences
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-3">Real-time Updates</h3>
                  <div className="flex items-center gap-4">
                    <Button
                      onClick={handleToggleRealTime}
                      variant={state.realTimeEnabled ? "default" : "outline"}
                    >
                      {state.realTimeEnabled ? 'Disable' : 'Enable'} Real-time Updates
                    </Button>
                    {state.realTimeEnabled && (
                      <Badge variant="secondary">
                        Updates every {state.refreshInterval / 1000}s
                      </Badge>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3">Selected Agents</h3>
                  {state.selectedAgents.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {state.selectedAgents.map(agent => (
                        <Badge key={agent} variant="outline">
                          {agent}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500">No agents selected for comparison</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3">Dashboard Actions</h3>
                  <div className="flex gap-3">
                    <Button onClick={handleExportDashboard} variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      Export Dashboard Data
                    </Button>
                    <Button onClick={handleRefresh} variant="outline">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refresh All Data
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
};

export default EnhancedObservabilityDashboard;