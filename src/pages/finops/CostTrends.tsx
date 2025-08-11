import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCostMetrics, useResourceCosts } from '@/hooks/finops/useFinOpsQueries';
import Sidebar from '../../components/Sidebar';
import { TrendingUp, TrendingDown, LineChart, Filter, RefreshCw } from 'lucide-react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Progress } from '@/components/ui/progress';

const CostTrends = (): JSX.Element => {
  const { isAuthenticated } = useAuth();

  // Queries
  const { data: metricsData, isLoading: isLoadingMetrics, error: metricsError } = useCostMetrics();
  const { data: trendsData, isLoading: isLoadingTrends, error: trendsError } = useResourceCosts();

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <Alert variant="destructive">
              <AlertDescription>
                Please log in to access cost trends.
              </AlertDescription>
            </Alert>
          </main>
        </div>
      </div>
    );
  }

  if (isLoadingTrends || isLoadingMetrics) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <LoadingSkeleton />
          </main>
        </div>
      </div>
    );
  }

  if (trendsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <Alert variant="destructive">
              <AlertDescription>
                Error: {trendsError.message}
              </AlertDescription>
            </Alert>
          </main>
        </div>
      </div>
    );
  }

  const trends = trendsData || [];
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const trendMetrics = [
    { label: 'Total Cloud Spend', value: formatCurrency(metricsData?.totalCost || 0), color: 'text-blue-600', icon: TrendingUp },
    { label: 'Projected Annual', value: formatCurrency(metricsData?.projectedAnnual || 0), color: 'text-green-600', icon: LineChart },
    { label: 'Savings Identified', value: formatCurrency(metricsData?.savingsIdentified || 0), color: 'text-purple-600', icon: TrendingDown },
    { label: 'Optimization Score', value: `${metricsData?.optimizationScore || 0}%`, color: 'text-orange-600', icon: RefreshCw },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cost Trends</h1>
                  <p className="text-lg text-gray-600">
                    Analyze cost trends and patterns
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button variant="outline">
                    <Filter className="h-5 w-5 mr-2" />
                    Filter
                  </Button>
                  <Button variant="default" className="bg-blue-600 hover:bg-blue-700">
                    <Download className="h-5 w-5 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> No insights available
                </p>
              </div>
            </div>

            {/* Trend Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {trendMetrics.map((metric, index) => {
                const Icon = metric.icon;
                return (
                  <Card key={index}>
                    <CardContent className="flex items-center justify-between p-6">
                      <div>
                        <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                        <p className={`text-2xl font-bold ${metric.color}`}>
                          {metric.value}
                        </p>
                      </div>
                      <Icon className={`h-8 w-8 ${metric.color}`} />
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Trends List */}
            <Card>
              <CardHeader>
                <CardTitle>Cost Trend Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {trends.map((trend) => (
                    <Card key={trend.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-gray-900">{trend.name}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={trend.type === 'AI/ML' ? 'destructive' : 'secondary'}>
                                {trend.type}
                              </Badge>
                              <Badge variant={trend.trend === 'Increasing' ? 'destructive' : (trend.trend === 'Decreasing' ? 'default' : 'outline')}>
                                {trend.trend || 'Stable'}
                              </Badge>
                            </div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            Export
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                          <div>
                            <span className="text-gray-600">Current Cost:</span>
                            <span className="ml-2 font-medium">{formatCurrency(trend.currentCost || 0)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Previous Cost:</span>
                            <span className="ml-2 font-medium">{formatCurrency(trend.previousCost || 0)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Utilization:</span>
                            <span className="ml-2 font-medium">{trend.utilizationRate || 0}%</span>
                          </div>
                        </div>
                        <div className="space-y-4">
                          {trend.recommendations && trend.recommendations.map((recommendation, idx) => (
                            <div key={idx} className="p-3 bg-blue-50 rounded-lg">
                              <p className="text-sm text-blue-800">
                                <strong>Recommendation:</strong> {recommendation}
                              </p>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default CostTrends;
