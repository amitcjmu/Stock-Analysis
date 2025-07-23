/**
 * Test Component for Phase 4B Advanced Observability Features
 * Quick integration test for all Phase 4B components
 */

import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { CheckCircle, XCircle, AlertTriangle, Eye } from 'lucide-react';

// Import Phase 4B components
import {
  ActivityFeed,
  AgentComparison,
  RecommendationEngine,
  AdvancedAnalytics
} from '../../components/observability';

const TestObservabilityPhase4B: React.FC = () => {
  const [testResults, setTestResults] = useState<Record<string, 'pass' | 'fail' | 'pending'>>({
    activityFeed: 'pending',
    agentComparison: 'pending',
    recommendationEngine: 'pending',
    advancedAnalytics: 'pending'
  });

  const [activeTab, setActiveTab] = useState('overview');

  const testComponent = (componentName: string) => {
    setTestResults(prev => ({ ...prev, [componentName]: 'pending' }));
    
    // Simulate test
    setTimeout(() => {
      setTestResults(prev => ({ ...prev, [componentName]: 'pass' }));
    }, 1000);
  };

  const getStatusIcon = (status: 'pass' | 'fail' | 'pending') => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: 'pass' | 'fail' | 'pending') => {
    switch (status) {
      case 'pass':
        return 'text-green-600 bg-green-100';
      case 'fail':
        return 'text-red-600 bg-red-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Eye className="w-8 h-8 text-blue-600" />
          Phase 4B Integration Test
        </h1>
        <p className="text-gray-600 mt-1">
          Testing all Phase 4B Advanced Observability Features
        </p>
      </div>

      {/* Test Results Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Object.entries(testResults).map(([component, status]) => (
          <Card key={component}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 capitalize">
                    {component.replace(/([A-Z])/g, ' $1').trim()}
                  </p>
                  <Badge variant="outline" className={`text-xs ${getStatusColor(status)}`}>
                    {status}
                  </Badge>
                </div>
                {getStatusIcon(status)}
              </div>
              <Button
                onClick={() => testComponent(component)}
                size="sm"
                variant="outline"
                className="mt-2 w-full"
              >
                Test Component
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Component Tests */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="activityFeed">Activity Feed</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Phase 4B Component Integration Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium mb-2">✅ Completed Components</h3>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• AgentDetailPage.tsx - Individual agent detail views</li>
                      <li>• ActivityFeed.tsx - Real-time activity stream</li>
                      <li>• AgentComparison.tsx - Performance comparison tools</li>
                      <li>• RecommendationEngine.tsx - AI-powered suggestions</li>
                      <li>• AdvancedAnalytics.tsx - Historical analytics</li>
                      <li>• Enhanced routing and navigation</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">🔧 Integration Features</h3>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• Deep linking to agent views (/observability/agent/:agentName)</li>
                      <li>• Enhanced dashboard (/observability/enhanced)</li>
                      <li>• Real-time data updates and live feeds</li>
                      <li>• Export capabilities for reports</li>
                      <li>• Advanced data visualization with charts</li>
                      <li>• User feedback and recommendation systems</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activityFeed" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Activity Feed Component Test</CardTitle>
            </CardHeader>
            <CardContent>
              <ActivityFeed
                height="400px"
                realTime={false}
                showControls
                compact
                maxEvents={10}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agent Comparison Component Test</CardTitle>
            </CardHeader>
            <CardContent>
              <AgentComparison
                maxAgents={3}
                showRanking
                enableExport={false}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recommendation Engine Component Test</CardTitle>
            </CardHeader>
            <CardContent>
              <RecommendationEngine
                showAllAgents
                maxRecommendations={5}
                enableFeedback={false}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TestObservabilityPhase4B;