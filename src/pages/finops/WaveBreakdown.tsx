import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCostMetrics, useResourceCosts } from '@/hooks/finops/useFinOpsQueries';
import Sidebar from '../../components/Sidebar';
import { Waves, BarChart, LineChart, Filter, RefreshCw } from 'lucide-react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Progress } from '@/components/ui/progress';

const WaveBreakdown = (): JSX.Element => {
  const { isAuthenticated } = useAuth();

  // Queries
  const { data: metricsData, isLoading: isLoadingMetrics, error: metricsError } = useCostMetrics();
  const { data: waveData, isLoading: isLoadingWave, error: waveError } = useResourceCosts();

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <Alert variant="destructive">
              <AlertDescription>
                Please log in to access wave breakdown.
              </AlertDescription>
            </Alert>
          </main>
        </div>
      </div>
    );
  }

  if (isLoadingWave || isLoadingMetrics) {
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

  if (waveError) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <Alert variant="destructive">
              <AlertDescription>
                Error: {waveError.message}
              </AlertDescription>
            </Alert>
          </main>
        </div>
      </div>
    );
  }

  const waves = waveData || [];
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const waveMetrics = [
    { label: 'Total Cloud Spend', value: formatCurrency(metricsData?.totalCost || 0), color: 'text-blue-600', icon: Waves },
    { label: 'Projected Annual', value: formatCurrency(metricsData?.projectedAnnual || 0), color: 'text-green-600', icon: LineChart },
    { label: 'Savings Identified', value: formatCurrency(metricsData?.savingsIdentified || 0), color: 'text-purple-600', icon: BarChart },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Wave Breakdown</h1>
                  <p className="text-lg text-gray-600">
                    Analyze costs by migration wave
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

            {/* Wave Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {waveMetrics.map((metric, index) => {
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

            {/* Waves List */}
            <Card>
              <CardHeader>
                <CardTitle>Wave Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {waves.map((wave) => (
                    <Card key={wave.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-gray-900">{wave.name}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={wave.type === 'AI/ML' ? 'destructive' : 'secondary'}>
                                {wave.type}
                              </Badge>
                              <Badge variant={wave.trend === 'Increasing' ? 'destructive' : (wave.trend === 'Decreasing' ? 'default' : 'outline')}>
                                {wave.trend || 'Stable'}
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
                            <span className="ml-2 font-medium">{formatCurrency(wave.currentCost || 0)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Previous Cost:</span>
                            <span className="ml-2 font-medium">{formatCurrency(wave.previousCost || 0)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Utilization:</span>
                            <span className="ml-2 font-medium">{wave.utilizationRate || 0}%</span>
                          </div>
                        </div>
                        <div className="space-y-4">
                          {wave.recommendations && wave.recommendations.map((recommendation, idx) => (
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

export default WaveBreakdown;
