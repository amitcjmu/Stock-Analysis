import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCostMetrics, useResourceCosts, useSavingsOpportunities, useBudgetAlerts } from '@/hooks/finops/useFinOpsQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import { DollarSign, TrendingDown, TrendingUp, AlertTriangle, Sparkles, BarChart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

const Overview = () => {
  const { isAuthenticated } = useAuth();

  // Queries
  const {
    data: metricsData,
    isLoading: isLoadingMetrics,
    error: metricsError
  } = useCostMetrics();

  const {
    data: resourcesData,
    isLoading: isLoadingResources
  } = useResourceCosts();

  const {
    data: opportunitiesData,
    isLoading: isLoadingOpportunities
  } = useSavingsOpportunities();

  const {
    data: alertsData,
    isLoading: isLoadingAlerts
  } = useBudgetAlerts();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access the FinOps dashboard.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingMetrics || isLoadingResources || isLoadingOpportunities || isLoadingAlerts) {
    return <LoadingSkeleton />;
  }

  if (metricsError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {metricsError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const { metrics = {} } = metricsData || {};
  const { resources = [] } = resourcesData || {};
  const { opportunities = [] } = opportunitiesData || {};
  const { alerts = [] } = alertsData || {};

  const costMetrics = [
    { label: 'Total Monthly Cost', value: `$${metrics.totalCost?.toLocaleString() || 0}`, color: 'text-blue-600' },
    { label: 'Month over Month', value: `${metrics.monthOverMonth || 0}%`, color: metrics.monthOverMonth > 0 ? 'text-red-600' : 'text-green-600' },
    { label: 'Projected Annual', value: `$${metrics.projectedAnnual?.toLocaleString() || 0}`, color: 'text-purple-600' },
    { label: 'Savings Identified', value: `$${metrics.savingsIdentified?.toLocaleString() || 0}`, color: 'text-green-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">FinOps Overview</h1>
                  <p className="text-lg text-gray-600">
                    Cloud cost management and optimization
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-blue-600 to-green-600 text-white hover:from-blue-700 hover:to-green-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Optimize
                  </Button>
                  <Button variant="default" className="bg-blue-600 hover:bg-blue-700">
                    <BarChart className="h-5 w-5 mr-2" />
                    Cost Analysis
                  </Button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> {metrics.optimizationScore || 0}% optimization score with ${metrics.wastedSpend?.toLocaleString() || 0} in potential savings identified
                </p>
              </div>
            </div>

            {/* Cost Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {costMetrics.map((metric, index) => (
                <Card key={index}>
                  <CardContent className="flex items-center justify-between p-6">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                    </div>
                    <DollarSign className={`h-8 w-8 ${metric.color}`} />
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Resource Costs */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Resource Cost Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {resources.map((resource) => (
                    <div key={resource.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{resource.name}</span>
                          <Badge variant="outline">{resource.type}</Badge>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm text-gray-600">
                            ${resource.currentCost.toLocaleString()}
                          </span>
                          <Badge
                            variant={resource.trend === 'Increasing' ? 'destructive' : 'default'}
                            className="flex items-center"
                          >
                            {resource.trend === 'Increasing' ? (
                              <TrendingUp className="h-4 w-4 mr-1" />
                            ) : (
                              <TrendingDown className="h-4 w-4 mr-1" />
                            )}
                            {((resource.currentCost - resource.previousCost) / resource.previousCost * 100).toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                      <Progress value={resource.utilizationRate} className="h-2" />
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>Utilization: {resource.utilizationRate}%</span>
                        <span>{resource.recommendations.length} recommendations</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Savings Opportunities */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Cost Optimization Opportunities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {opportunities.map((opportunity) => (
                    <Card key={opportunity.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">{opportunity.title}</h4>
                            <p className="text-sm text-gray-600 mt-1">{opportunity.description}</p>
                          </div>
                          <Badge variant="outline" className="text-green-600">
                            ${opportunity.potentialSavings.toLocaleString()}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-4 mt-4">
                          <Badge variant={opportunity.effort === 'High' ? 'destructive' : 'default'}>
                            {opportunity.effort} Effort
                          </Badge>
                          <Badge variant={opportunity.impact === 'High' ? 'default' : 'secondary'}>
                            {opportunity.impact} Impact
                          </Badge>
                          <Badge variant={
                            opportunity.status === 'Implemented' ? 'default' :
                            opportunity.status === 'In Progress' ? 'secondary' : 'outline'
                          }>
                            {opportunity.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Budget Alerts */}
            <Card>
              <CardHeader>
                <CardTitle>Budget Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <Card key={alert.id}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <AlertTriangle className={`h-5 w-5 ${
                              alert.status === 'Critical' ? 'text-red-500' :
                              alert.status === 'Warning' ? 'text-yellow-500' :
                              'text-green-500'
                            }`} />
                            <span className="font-medium">{alert.resourceGroup}</span>
                          </div>
                          <Badge variant={
                            alert.status === 'Critical' ? 'destructive' :
                            alert.status === 'Warning' ? 'secondary' : 'default'
                          }>
                            {alert.status}
                          </Badge>
                        </div>
                        <div className="mt-2">
                          <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>Current Spend: ${alert.currentSpend.toLocaleString()}</span>
                            <span>Threshold: ${alert.threshold.toLocaleString()}</span>
                          </div>
                          <Progress
                            value={(alert.currentSpend / alert.threshold) * 100}
                            className={`h-2 ${
                              alert.status === 'Critical' ? 'bg-red-500' :
                              alert.status === 'Warning' ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}
                          />
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                          Last updated: {new Date(alert.lastUpdated).toLocaleString()}
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

export default Overview;
