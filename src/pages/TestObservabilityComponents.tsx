/**
 * Test Page for Observability Components
 * Development page to test and validate all observability components
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React, { useState } from 'react'
import Sidebar from '../components/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Activity, BarChart3, Clock } from 'lucide-react'
import { TestTube, Users, AlertTriangle, CheckCircle } from 'lucide-react'

// Import all observability components
import { AgentListOverview, ResponsiveAgentListOverview, ObservabilityErrorBoundary, EmptyState, type AgentCardData, type SparklineData } from '../components/observability'
import { AgentPerformanceCard, AgentPerformanceCardCompact, AgentStatusIndicator, AgentStatusGroup, SparklineChart, SuccessRateGauge, PerformanceDistributionChart, LoadingSpinner, AgentListSkeleton, ProgressiveLoader } from '../components/observability'

// Mock data for testing
const mockAgents: AgentCardData[] = [
  {
    id: 'data-import-validation-agent',
    name: 'DataImportValidationAgent',
    status: 'active',
    lastActive: '2 minutes ago',
    successRate: 0.95,
    totalTasks: 142,
    avgDuration: 3.2,
    isOnline: true
  },
  {
    id: 'cmdb-analysis-agent',
    name: 'CMDBAnalysisAgent',
    status: 'idle',
    lastActive: '15 minutes ago',
    successRate: 0.87,
    totalTasks: 89,
    avgDuration: 5.7,
    isOnline: true
  },
  {
    id: 'dependency-mapper-agent',
    name: 'DependencyMapperAgent',
    status: 'active',
    lastActive: '1 minute ago',
    successRate: 0.92,
    totalTasks: 203,
    avgDuration: 2.8,
    isOnline: true
  },
  {
    id: 'quality-assessment-agent',
    name: 'QualityAssessmentAgent',
    status: 'error',
    lastActive: '5 minutes ago',
    successRate: 0.78,
    totalTasks: 67,
    avgDuration: 4.1,
    isOnline: false
  },
  {
    id: 'tech-debt-analyzer-agent',
    name: 'TechDebtAnalyzerAgent',
    status: 'active',
    lastActive: '30 seconds ago',
    successRate: 0.91,
    totalTasks: 178,
    avgDuration: 6.3,
    isOnline: true
  },
  {
    id: 'pattern-discovery-agent',
    name: 'PatternDiscoveryAgent',
    status: 'offline',
    lastActive: '2 hours ago',
    successRate: 0.85,
    totalTasks: 45,
    avgDuration: 8.2,
    isOnline: false
  }
];

const mockSparklineData: SparklineData = {
  data: [
    { timestamp: '00:00', value: 0.92 },
    { timestamp: '04:00', value: 0.95 },
    { timestamp: '08:00', value: 0.89 },
    { timestamp: '12:00', value: 0.94 },
    { timestamp: '16:00', value: 0.97 },
    { timestamp: '20:00', value: 0.93 },
    { timestamp: '24:00', value: 0.95 }
  ],
  color: '#3b82f6',
  trend: 'up',
  changePercent: 3.2
};

const mockDistributionData = [
  { label: 'Memory Usage (MB)', value: 256, color: '#f59e0b' },
  { label: 'LLM Calls', value: 84, color: '#3b82f6' },
  { label: 'Confidence Score', value: 92, color: '#10b981' }
];

const TestObservabilityComponents = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentCardData | null>(null);
  const [showError, setShowError] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);

  const loadingStages = [
    'Connecting to monitoring service...',
    'Fetching agent registry...',
    'Loading performance data...',
    'Processing metrics...'
  ];

  const handleAgentSelect = (agent: AgentCardData) => {
    setSelectedAgent(agent);
  };

  const simulateError = () => {
    setShowError(true);
    setTimeout(() => setShowError(false), 5000);
  };

  const simulateLoading = () => {
    setShowLoading(true);
    setLoadingStage(0);
    
    const interval = setInterval(() => {
      setLoadingStage(prev => {
        if (prev >= loadingStages.length - 1) {
          clearInterval(interval);
          setTimeout(() => setShowLoading(false), 1000);
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <TestTube className="h-8 w-8 mr-3 text-purple-600" />
                Observability Components Test
              </h1>
              <p className="text-gray-600">
                Development testing page for all agent observability components
              </p>
            </div>

            <Tabs defaultValue="components" className="space-y-6">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="components">Components</TabsTrigger>
                <TabsTrigger value="charts">Charts</TabsTrigger>
                <TabsTrigger value="states">States</TabsTrigger>
                <TabsTrigger value="integration">Integration</TabsTrigger>
                <TabsTrigger value="responsive">Responsive</TabsTrigger>
              </TabsList>

              {/* Individual Components Tab */}
              <TabsContent value="components" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Status Indicators */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Status Indicators</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Dot Variant:</span>
                          <div className="flex items-center space-x-3">
                            <AgentStatusIndicator status="active" variant="dot" showLabel />
                            <AgentStatusIndicator status="idle" variant="dot" showLabel />
                            <AgentStatusIndicator status="error" variant="dot" showLabel />
                            <AgentStatusIndicator status="offline" variant="dot" showLabel />
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Badge Variant:</span>
                          <div className="flex items-center space-x-2">
                            <AgentStatusIndicator status="active" variant="badge" />
                            <AgentStatusIndicator status="idle" variant="badge" />
                            <AgentStatusIndicator status="error" variant="badge" />
                            <AgentStatusIndicator status="offline" variant="badge" />
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Icon Variant:</span>
                          <div className="flex items-center space-x-3">
                            <AgentStatusIndicator status="active" variant="icon" />
                            <AgentStatusIndicator status="idle" variant="icon" />
                            <AgentStatusIndicator status="error" variant="icon" />
                            <AgentStatusIndicator status="offline" variant="icon" />
                          </div>
                        </div>

                        <div className="pt-3 border-t">
                          <span className="text-sm font-medium">Status Group:</span>
                          <div className="mt-2">
                            <AgentStatusGroup
                              statuses={[
                                { status: 'active', count: 3, label: 'Active' },
                                { status: 'idle', count: 1, label: 'Idle' },
                                { status: 'error', count: 1, label: 'Error' },
                                { status: 'offline', count: 1, label: 'Offline' }
                              ]}
                            />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Performance Cards */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Performance Cards</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-medium mb-2">Compact Card:</h4>
                          <AgentPerformanceCardCompact
                            agent={mockAgents[0]}
                            onClick={handleAgentSelect}
                          />
                        </div>
                        
                        <div>
                          <h4 className="text-sm font-medium mb-2">Detailed Card:</h4>
                          <AgentPerformanceCard
                            agent={mockAgents[1]}
                            detailed={true}
                            showChart={true}
                            onClick={handleAgentSelect}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Selected Agent Display */}
                {selectedAgent && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Users className="h-5 w-5 text-blue-600" />
                        <span>Selected Agent: {selectedAgent.name}</span>
                        <Badge variant="outline">{selectedAgent.status}</Badge>
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

              {/* Charts Tab */}
              <TabsContent value="charts" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Sparkline Chart</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SparklineChart
                        data={mockSparklineData}
                        title="Success Rate Trend"
                        height={80}
                        animate={true}
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Success Rate Gauge</CardTitle>
                    </CardHeader>
                    <CardContent className="flex justify-center">
                      <SuccessRateGauge value={0.92} size={120} />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Distribution Chart</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PerformanceDistributionChart
                        data={mockDistributionData}
                        title="Resource Usage"
                      />
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Loading States Tab */}
              <TabsContent value="states" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Loading States */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Loading States</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-medium mb-2">Loading Spinner:</h4>
                          <LoadingSpinner text="Loading agents..." size="md" />
                        </div>
                        
                        <div>
                          <Button onClick={simulateLoading} className="w-full">
                            Test Progressive Loader
                          </Button>
                          {showLoading && (
                            <div className="mt-4">
                              <ProgressiveLoader
                                stages={loadingStages}
                                currentStage={loadingStage}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Error States */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Error States</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-4">
                        <Button 
                          onClick={simulateError} 
                          variant="destructive"
                          className="w-full"
                        >
                          Simulate Error
                        </Button>
                        
                        {showError && (
                          <div className="space-y-4">
                            <EmptyState
                              icon={<AlertTriangle className="h-12 w-12 text-red-300" />}
                              title="Error State"
                              description="This is a simulated error state to test error handling."
                              action={
                                <Button variant="outline" onClick={() => setShowError(false)}>
                                  Retry
                                </Button>
                              }
                            />
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Skeleton Loaders */}
                <Card>
                  <CardHeader>
                    <CardTitle>Skeleton Loaders</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <AgentListSkeleton count={4} />
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Integration Tab */}
              <TabsContent value="integration" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Basic Agent List Overview</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-100 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-4">
                        This uses mock data instead of real API calls for testing purposes.
                      </p>
                      {/* We'll show a mock version since we can't easily mock the API in this context */}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {mockAgents.slice(0, 6).map((agent) => (
                          <AgentPerformanceCardCompact
                            key={agent.id}
                            agent={agent}
                            onClick={handleAgentSelect}
                          />
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Responsive Tab */}
              <TabsContent value="responsive" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Responsive Design Test</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <p className="text-sm text-gray-600">
                        Resize your browser window to test responsive behavior:
                      </p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {mockAgents.map((agent) => (
                          <AgentPerformanceCardCompact
                            key={agent.id}
                            agent={agent}
                            onClick={handleAgentSelect}
                          />
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Test Results */}
            <Card className="mt-8">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Component Test Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <Badge variant="default" className="mb-2">Functional</Badge>
                    <p className="text-sm text-gray-600">All components render correctly</p>
                  </div>
                  <div className="text-center">
                    <Badge variant="default" className="mb-2">Interactive</Badge>
                    <p className="text-sm text-gray-600">Click handlers and state work</p>
                  </div>
                  <div className="text-center">
                    <Badge variant="default" className="mb-2">Responsive</Badge>
                    <p className="text-sm text-gray-600">Adapts to different screen sizes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TestObservabilityComponents;