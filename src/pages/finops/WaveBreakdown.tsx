import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCostMetrics, useResourceCosts } from '@/hooks/finops/useFinOpsQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import type { Waves, BarChart, LineChart, Filter, RefreshCw } from 'lucide-react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Progress } from '@/components/ui/progress';

const WaveBreakdown = () => {
  const { isAuthenticated } = useAuth();

  // Queries
  const { data: metricsData, isLoading: isLoadingMetrics, error: metricsError } = useCostMetrics();
  const { data: waveData, isLoading: isLoadingWave, error: waveError } = useResourceCosts();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access wave breakdown.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingWave || isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (waveError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {waveError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const waves = waveData || [];
  const waveMetrics = [
    { label: 'Total Cloud Spend', value: metricsData?.totalCost || '$0', color: 'text-blue-600', icon: Waves },
    { label: 'Projected Annual', value: metricsData?.projectedAnnual || '$0', color: 'text-green-600', icon: LineChart },
    { label: 'Savings Identified', value: metricsData?.savingsIdentified || '$0', color: 'text-purple-600', icon: BarChart },
    { label: 'Optimization Score', value: metricsData?.optimizationScore || '0', color: 'text-orange-600', icon: RefreshCw },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <NavigationSidebar />
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
                              <Badge variant={wave.type === 'Critical' ? 'destructive' : 'secondary'}>
                                {wave.type}
                              </Badge>
                              <Badge variant={wave.status === 'Active' ? 'default' : 'outline'}>
                                {wave.status}
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
                            <span className="ml-2 font-medium">${wave.currentCost}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Target Cost:</span>
                            <span className="ml-2 font-medium">${wave.targetCost}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Variance:</span>
                            <span className="ml-2 font-medium">{wave.variance}%</span>
                          </div>
                        </div>
                        <div className="space-y-4">
                          {wave.categories.map((category) => (
                            <div key={category.name} className="space-y-2">
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">{category.name}</span>
                                <span className="font-medium">${category.cost}</span>
                              </div>
                              <Progress value={category.percentage} className="h-2" />
                            </div>
                          ))}
                        </div>
                        {wave.recommendation && (
                          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                            <p className="text-sm text-blue-800">
                              <strong>Optimization:</strong> {wave.recommendation}
                            </p>
                          </div>
                        )}
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
