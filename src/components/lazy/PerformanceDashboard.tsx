/**
 * Performance Dashboard - Visual monitoring for lazy loading performance
 */

import React from 'react'
import type { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Clock, 
  Database, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  Download,
  RefreshCw
} from 'lucide-react';
import { performanceMonitor } from '@/utils/lazy/performanceMonitor';
import type { BundleAnalysis } from '@/types/lazy';

interface PerformanceInsight {
  type: 'optimization' | 'warning' | 'error' | 'info';
  category: 'bundle-size' | 'load-time' | 'cache-efficiency' | 'error-rate';
  message: string;
  impact: 'high' | 'medium' | 'low';
  suggestion: string;
  metrics?: {
    averageLoadTime?: number;
    cacheHitRate?: number;
    errorRate?: number;
    bundleSize?: number;
  };
}

interface LoadingPattern {
  route: string;
  component: string;
  frequency: number;
  averageLoadTime: number;
  cacheHitRate: number;
  errorRate: number;
}

interface PerformanceData {
  summary: {
    totalLoads: number;
    averageLoadTime: number;
    cacheHitRate: number;
    errorRate: number;
    performanceScore: number;
  };
  bundleAnalysis: BundleAnalysis;
  insights: PerformanceInsight[];
  patterns: LoadingPattern[];
}

interface PerformanceDashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  autoRefresh = true,
  refreshInterval = 5000
}) => {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshData = async () => {
    setLoading(true);
    try {
      const data = performanceMonitor.getPerformanceAnalysis();
      setPerformanceData(data);
    } catch (error) {
      console.error('Failed to load performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();

    if (autoRefresh) {
      const interval = setInterval(refreshData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const exportPerformanceData = () => {
    const data = performanceMonitor.exportPerformanceData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-data-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPerformanceScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case 'optimization':
        return <TrendingUp className="h-4 w-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  if (loading && !performanceData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading performance data...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { summary, bundleAnalysis, insights, patterns } = performanceData || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Lazy Loading Performance</h2>
          <p className="text-gray-600">Monitor and optimize component loading performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={refreshData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportPerformanceData}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Performance Score</p>
                <p className={`text-2xl font-bold ${getPerformanceScoreColor(summary?.performanceScore || 0)}`}>
                  {summary?.performanceScore || 0}
                </p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
            <Progress 
              value={summary?.performanceScore || 0} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Load Time</p>
                <p className="text-2xl font-bold">{summary?.averageLoadTime || 0}ms</p>
              </div>
              <Clock className="h-8 w-8 text-green-500" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {summary?.totalLoads || 0} total loads
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Cache Hit Rate</p>
                <p className="text-2xl font-bold">{summary?.cacheHitRate || 0}%</p>
              </div>
              <Database className="h-8 w-8 text-purple-500" />
            </div>
            <Progress 
              value={summary?.cacheHitRate || 0} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Error Rate</p>
                <p className="text-2xl font-bold text-red-600">{summary?.errorRate || 0}%</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Target: &lt; 2%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      <Tabs defaultValue="insights" className="space-y-4">
        <TabsList>
          <TabsTrigger value="insights">Insights</TabsTrigger>
          <TabsTrigger value="bundle">Bundle Analysis</TabsTrigger>
          <TabsTrigger value="patterns">Loading Patterns</TabsTrigger>
        </TabsList>

        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Insights</CardTitle>
            </CardHeader>
            <CardContent>
              {insights && insights.length > 0 ? (
                <div className="space-y-4">
                  {insights.map((insight, index) => (
                    <div key={index} className="flex items-start space-x-3 p-4 border rounded-lg">
                      {getInsightTypeIcon(insight.type)}
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="font-medium">{insight.message}</h4>
                          <Badge variant={insight.impact === 'high' ? 'destructive' : 
                                        insight.impact === 'medium' ? 'default' : 'secondary'}>
                            {insight.impact} impact
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{insight.suggestion}</p>
                        <Badge variant="outline" className="mt-2">
                          {insight.category}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <p className="text-gray-600">No performance issues detected!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bundle" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Bundle Size Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Total Bundle Size</span>
                    <span className="text-sm">
                      {Math.round((bundleAnalysis?.totalBundleSize || 0) / 1024)}KB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Initial Bundle Size</span>
                    <span className="text-sm">
                      {Math.round((bundleAnalysis?.initialBundleSize || 0) / 1024)}KB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Cache Effectiveness</span>
                    <span className="text-sm">
                      {bundleAnalysis?.cacheEffectiveness?.toFixed(1) || 0}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Loaded Chunks</span>
                    <span className="text-sm">
                      {bundleAnalysis?.loadedChunks?.length || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Chunk Sizes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {bundleAnalysis?.chunkSizes && Object.entries(bundleAnalysis.chunkSizes).map(([chunk, size]) => (
                    <div key={chunk} className="flex justify-between text-sm">
                      <span className="truncate mr-2">{chunk}</span>
                      <span className="font-mono">{Math.round((size as number) / 1024)}KB</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Loading Patterns</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Component</th>
                      <th className="text-left p-2">Frequency</th>
                      <th className="text-left p-2">Avg Load Time</th>
                      <th className="text-left p-2">Cache Hit Rate</th>
                      <th className="text-left p-2">Error Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patterns && patterns.map((pattern, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2 font-medium">{pattern.component}</td>
                        <td className="p-2">{pattern.frequency}</td>
                        <td className="p-2">{Math.round(pattern.averageLoadTime)}ms</td>
                        <td className="p-2">{pattern.cacheHitRate.toFixed(1)}%</td>
                        <td className="p-2">{pattern.errorRate.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};