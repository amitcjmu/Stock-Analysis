import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useBudgetAlerts, useCostMetrics } from '@/hooks/finops/useFinOpsQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import type { Bell, AlertTriangle, CheckCircle, Filter } from 'lucide-react'
import { Settings, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Progress } from '@/components/ui/progress';

const BudgetAlerts = () => {
  const { isAuthenticated } = useAuth();

  // Queries
  const { 
    data: alertsData,
    isLoading: isLoadingAlerts,
    error: alertsError
  } = useBudgetAlerts();

  const { data: metricsData, isLoading: isLoadingMetrics } = useCostMetrics();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access budget alerts.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingAlerts || isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (alertsError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {alertsError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const alerts = alertsData || [];
  const alertMetrics = [
    { label: 'Active Alerts', value: metricsData?.activeAlerts || '0', color: 'text-red-600', icon: AlertTriangle },
    { label: 'Resolved', value: metricsData?.resolvedAlerts || '0', color: 'text-green-600', icon: CheckCircle },
    { label: 'Budget Usage', value: metricsData?.budgetUsage || '0%', color: 'text-blue-600', icon: Settings },
    { label: 'Alert Rules', value: metricsData?.totalRules || '0', color: 'text-purple-600', icon: Bell },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Budget Alerts</h1>
                  <p className="text-lg text-gray-600">
                    Monitor and manage budget thresholds
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button variant="outline">
                    <Filter className="h-5 w-5 mr-2" />
                    Filter
                  </Button>
                  <Button variant="default" className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-5 w-5 mr-2" />
                    New Alert
                  </Button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> No insights available
                </p>
              </div>
            </div>

            {/* Alert Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {alertMetrics.map((metric, index) => {
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

            {/* Alert List */}
            <Card>
              <CardHeader>
                <CardTitle>Active Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {alerts.map((alert) => (
                    <Card key={alert.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-gray-900">{alert.name}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={alert.severity === 'High' ? 'destructive' : 'secondary'}>
                                {alert.severity} Priority
                              </Badge>
                              <Badge variant={alert.status === 'Active' ? 'destructive' : 'default'}>
                                {alert.status}
                              </Badge>
                            </div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Settings className="h-4 w-4 mr-2" />
                            Configure
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                          <div>
                            <span className="text-gray-600">Threshold:</span>
                            <span className="ml-2 font-medium">${alert.threshold}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Current Usage:</span>
                            <span className="ml-2 font-medium">${alert.currentUsage}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Last Triggered:</span>
                            <span className="ml-2 font-medium">{alert.lastTriggered}</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Usage</span>
                            <span className="font-medium">{alert.usagePercentage}%</span>
                          </div>
                          <Progress value={alert.usagePercentage} className="h-2" />
                        </div>
                        {alert.message && (
                          <div className="mt-4 text-sm text-gray-600">
                            {alert.message}
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

export default BudgetAlerts;
