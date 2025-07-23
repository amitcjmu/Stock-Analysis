/**
 * Advanced Analytics Component - Main Orchestrator
 * Historical trends, pattern analysis, and predictive insights for agent performance
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React from 'react'
import { useState } from 'react'
import type { Calendar, Clock, Brain, Zap, Target, Filter, Eye, Activity, Layers } from 'lucide-react'
import { BarChart3, AlertTriangle, Download, RefreshCw } from 'lucide-react'
import type { CardHeader, CardTitle } from '../../ui/card'
import { Card, CardContent } from '../../ui/card'
import type { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import type { AdvancedAnalyticsProps } from './types';
import { METRIC_CONFIGS } from './constants';
import { TrendIndicator } from './components';
import type { useAnalyticsData, useChartData } from './hooks';
import type { handleExportData } from './utils';
import { TrendsTab, PatternsTab, CorrelationsTab, PredictionsTab, AnomaliesTab } from './tabs';

const AdvancedAnalytics: React.FC<AdvancedAnalyticsProps> = ({
  agentNames = [],
  defaultTimeRange = 30,
  showPredictions = true,
  enableExport = true,
  refreshInterval = 300000, // 5 minutes
  className = ''
}) => {
  const [timeRange, setTimeRange] = useState(defaultTimeRange);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['successRate', 'avgDuration', 'throughput']);
  const [activeTab, setActiveTab] = useState('trends');

  const { analyticsData, loading, error, refresh, dateRange } = useAnalyticsData({
    agentNames,
    timeRange,
    refreshInterval
  });

  const chartData = useChartData({
    analyticsData,
    agentNames,
    selectedMetrics
  });

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics(prev => 
      prev.includes(metric) 
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const handleExport = () => {
    handleExportData(analyticsData, timeRange, agentNames);
  };

  if (loading && !analyticsData) {
    return (
      <Card className={className}>
        <CardContent className="p-8">
          <div className="text-center">
            <BarChart3 className="w-8 h-8 text-gray-400 mx-auto mb-2 animate-pulse" />
            <p className="text-gray-500">Loading advanced analytics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-8">
          <div className="text-center">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-red-600">{error}</p>
            <Button onClick={refresh} variant="outline" size="sm" className="mt-4">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-blue-500" />
          <div>
            <h2 className="text-xl font-bold text-gray-900">Advanced Analytics</h2>
            <p className="text-gray-600">
              Deep insights into agent performance patterns and trends
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={timeRange.toString()} onValueChange={(value) => setTimeRange(parseInt(value))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 3 months</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
          
          <Button onClick={refresh} variant="outline" disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          {enableExport && (
            <Button onClick={handleExport} variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {analyticsData && (
        <>
          {/* Quick Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {analyticsData.predictiveInsights.trends.slice(0, 4).map((trend) => (
              <Card key={trend.metric}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">
                      {METRIC_CONFIGS.find(m => m.key === trend.metric)?.label || trend.metric}
                    </span>
                    <TrendIndicator trend={trend.direction} rate={trend.rate} />
                  </div>
                  <div className="text-xs text-gray-500">
                    Significance: {(trend.significance * 100).toFixed(0)}%
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Main Analytics Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="trends">Trends</TabsTrigger>
              <TabsTrigger value="patterns">Patterns</TabsTrigger>
              <TabsTrigger value="correlations">Correlations</TabsTrigger>
              <TabsTrigger value="predictions">Predictions</TabsTrigger>
              <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
            </TabsList>

            <TabsContent value="trends">
              <TrendsTab
                chartData={chartData}
                agentNames={agentNames}
                selectedMetrics={selectedMetrics}
                onMetricToggle={handleMetricToggle}
              />
            </TabsContent>

            <TabsContent value="patterns">
              <PatternsTab patternAnalysis={analyticsData.patternAnalysis} />
            </TabsContent>

            <TabsContent value="correlations">
              <CorrelationsTab correlationMatrix={analyticsData.correlationMatrix} />
            </TabsContent>

            <TabsContent value="predictions">
              <PredictionsTab 
                forecasts={analyticsData.predictiveInsights.forecasts}
                showPredictions={showPredictions}
              />
            </TabsContent>

            <TabsContent value="anomalies">
              <AnomaliesTab anomalies={analyticsData.predictiveInsights.anomalies} />
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
};

export default AdvancedAnalytics;