/**
 * Enhanced Observability Dashboard
 * Integrates new agent observability components with existing system metrics
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React, { useState } from 'react'
import Sidebar from '../components/Sidebar';
import { Clock } from 'lucide-react'
import { Activity, AlertCircle, CheckCircle, Users, BarChart3, TrendingUp, Network } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';

// Import our new agent observability components
import { AgentListOverview } from '../components/observability';
import type { AgentCardData } from '../types/api/observability/agent-performance';

const EnhancedObservability = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentCardData | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Existing system metrics (kept for compatibility)
  const metrics = [
    {
      name: 'API Latency',
      value: '200ms',
      trend: 'up',
      change: '+5%',
      status: 'normal'
    },
    {
      name: 'Task Duration',
      value: '5.2s',
      trend: 'down',
      change: '-12%',
      status: 'good'
    },
    {
      name: 'Error Rate',
      value: '0.02%',
      trend: 'down',
      change: '-30%',
      status: 'good'
    },
    {
      name: 'Throughput',
      value: '1,247/min',
      trend: 'up',
      change: '+18%',
      status: 'normal'
    }
  ];

  const systemHealth = [
    {
      component: 'Migration Service',
      status: 'healthy',
      uptime: '99.9%',
      lastCheck: '2 mins ago'
    },
    {
      component: 'Assessment Engine',
      status: 'healthy',
      uptime: '99.8%',
      lastCheck: '1 min ago'
    },
    {
      component: 'Wave Scheduler',
      status: 'warning',
      uptime: '97.2%',
      lastCheck: '30 secs ago'
    },
    {
      component: 'Cost Tracker',
      status: 'healthy',
      uptime: '99.9%',
      lastCheck: '1 min ago'
    }
  ];

  const recentEvents = [
    {
      time: '14:32',
      event: 'W1 migration batch completed successfully',
      type: 'success',
      details: '12 applications migrated'
    },
    {
      time: '14:28',
      event: 'High memory usage detected in Wave Scheduler',
      type: 'warning',
      details: 'Memory usage: 85%'
    },
    {
      time: '14:15',
      event: 'Assessment scan completed for G3 applications',
      type: 'info',
      details: '15 applications assessed'
    },
    {
      time: '14:02',
      event: 'Cost optimization alert triggered',
      type: 'info',
      details: 'Potential savings detected in W2'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-blue-500" />;
    }
  };

  const handleAgentSelect = (agent: AgentCardData) => {
    setSelectedAgent(agent);
    setActiveTab('agents');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <Network className="h-8 w-8 mr-3 text-blue-600" />
                Enhanced Observability Dashboard
              </h1>
              <p className="text-gray-600">
                Monitor system metrics, application performance, and individual agent observability across your migration infrastructure
              </p>
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview" className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4" />
                  <span>System Overview</span>
                </TabsTrigger>
                <TabsTrigger value="agents" className="flex items-center space-x-2">
                  <Users className="h-4 w-4" />
                  <span>Agent Observability</span>
                </TabsTrigger>
                <TabsTrigger value="performance" className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Performance Analytics</span>
                </TabsTrigger>
              </TabsList>

              {/* System Overview Tab */}
              <TabsContent value="overview" className="space-y-8">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {metrics.map((metric) => (
                    <div key={metric.name} className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-300">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">{metric.name}</p>
                          <p className="text-2xl font-semibold text-gray-900">{metric.value}</p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            metric.trend === 'up' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {metric.change}
                          </span>
                        </div>
                      </div>
                      <div className="mt-4">
                        <div className="flex items-center">
                          <Activity className="h-4 w-4 text-purple-500 mr-2" />
                          <span className="text-xs text-gray-500">Last 24h</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* System Health and Events */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* System Health */}
                  <div className="bg-white rounded-lg shadow">
                    <div className="p-6 border-b border-gray-200">
                      <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
                    </div>
                    <div className="p-6">
                      <div className="space-y-4">
                        {systemHealth.map((component) => (
                          <div key={component.component} className="flex items-center justify-between p-4 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                component.status === 'healthy' ? 'bg-green-500' :
                                component.status === 'warning' ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}></div>
                              <div>
                                <p className="font-medium text-gray-900">{component.component}</p>
                                <p className="text-sm text-gray-500">Uptime: {component.uptime}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(component.status)}`}>
                                {component.status}
                              </span>
                              <p className="text-xs text-gray-500 mt-1">{component.lastCheck}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Recent Events */}
                  <div className="bg-white rounded-lg shadow">
                    <div className="p-6 border-b border-gray-200">
                      <h2 className="text-xl font-semibold text-gray-900">Recent Events</h2>
                    </div>
                    <div className="p-6">
                      <div className="space-y-4">
                        {recentEvents.map((event, index) => (
                          <div key={index} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50">
                            <div className="flex-shrink-0 mt-1">
                              {getEventIcon(event.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900">{event.event}</p>
                              <p className="text-xs text-gray-500">{event.details}</p>
                            </div>
                            <div className="text-xs text-gray-500">
                              {event.time}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Performance Graphs */}
                <div className="bg-white rounded-lg shadow">
                  <div className="p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900">Performance Metrics</h2>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      {/* API Latency Graph */}
                      <div className="border-purple-300 border rounded-lg p-4">
                        <h3 className="text-lg font-semibold mb-4">API Latency (24h)</h3>
                        <div className="h-48 flex items-end justify-between space-x-2">
                          {[180, 200, 190, 220, 195, 210, 185, 205, 200, 215, 190, 200].map((value, index) => (
                            <div key={index} className="flex-1 bg-purple-200 rounded-t relative" style={{ height: `${(value / 250) * 100}%` }}>
                              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600">
                                {value}ms
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="flex justify-between mt-4 text-xs text-gray-500">
                          <span>00:00</span>
                          <span>12:00</span>
                          <span>24:00</span>
                        </div>
                      </div>

                      {/* Task Duration Graph */}
                      <div className="border-purple-300 border rounded-lg p-4">
                        <h3 className="text-lg font-semibold mb-4">Task Duration (24h)</h3>
                        <div className="h-48 flex items-end justify-between space-x-2">
                          {[4.2, 5.1, 4.8, 5.5, 4.9, 5.2, 4.6, 5.0, 4.7, 5.3, 4.5, 5.2].map((value, index) => (
                            <div key={index} className="flex-1 bg-blue-200 rounded-t relative" style={{ height: `${(value / 6) * 100}%` }}>
                              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600">
                                {value}s
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="flex justify-between mt-4 text-xs text-gray-500">
                          <span>00:00</span>
                          <span>12:00</span>
                          <span>24:00</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* Agent Observability Tab */}
              <TabsContent value="agents" className="space-y-6">
                <AgentListOverview
                  refreshInterval={30}
                  showFilters={true}
                  compactView={false}
                  onAgentSelect={handleAgentSelect}
                />

                {selectedAgent && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Users className="h-5 w-5 text-blue-600" />
                        <span>Selected Agent: {selectedAgent.name}</span>
                        <Badge variant="outline">
                          {selectedAgent.status}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-600">
                            {(selectedAgent.successRate * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-600">Success Rate</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-green-600">
                            {selectedAgent.totalTasks}
                          </div>
                          <div className="text-sm text-gray-600">Total Tasks</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-purple-600">
                            {selectedAgent.avgDuration.toFixed(1)}s
                          </div>
                          <div className="text-sm text-gray-600">Avg Duration</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-orange-600">
                            {selectedAgent.lastActive}
                          </div>
                          <div className="text-sm text-gray-600">Last Active</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Performance Analytics Tab */}
              <TabsContent value="performance" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TrendingUp className="h-5 w-5 text-green-600" />
                      <span>Performance Analytics</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-12">
                      <BarChart3 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Advanced Analytics</h3>
                      <p className="text-gray-600">
                        Detailed performance analytics and trend analysis will be displayed here.
                        This section will be enhanced in Phase 4B with advanced charting and analytics features.
                      </p>
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

export default EnhancedObservability;
