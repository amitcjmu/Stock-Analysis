import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCutoverEvents, useExecutionMetrics } from '@/hooks/execute/useExecuteQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import { Play, Clock, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react'
import { Calendar, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

const Cutovers = (): JSX.Element => {
  const { isAuthenticated } = useAuth();

  // Queries
  const {
    data: cutoverData,
    isLoading: isLoadingCutovers,
    error: cutoverError
  } = useCutoverEvents();

  const {
    data: metricsData,
    isLoading: isLoadingMetrics
  } = useExecutionMetrics();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access the cutover management.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingCutovers || isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (cutoverError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {cutoverError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const { events = [], metrics = {} } = cutoverData || {};
  const executionMetrics = [
    { label: 'Active Cutovers', value: metrics.activeCutovers || '0', color: 'text-blue-600' },
    { label: 'Success Rate', value: metrics.successRate || '0%', color: 'text-green-600' },
    { label: 'Avg Duration', value: metrics.avgMigrationTime || '0h', color: 'text-purple-600' },
    { label: 'Total Apps', value: metrics.totalMigrations || '0', color: 'text-orange-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Cutover Management</h1>
                  <p className="text-lg text-gray-600">
                    Orchestrate and monitor application cutovers
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Schedule
                  </Button>
                  <Button variant="default" className="bg-blue-600 hover:bg-blue-700">
                    <Calendar className="h-5 w-5 mr-2" />
                    Schedule Cutover
                  </Button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> {metrics.successRate || '0%'} success rate with average duration of {metrics.avgMigrationTime || '0h'}
                </p>
              </div>
            </div>

            {/* Execution Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {executionMetrics.map((metric, index) => (
                <Card key={index}>
                  <CardContent className="flex items-center justify-between p-6">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                    </div>
                    <Calendar className={`h-8 w-8 ${metric.color}`} />
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Cutover Events */}
            <Card>
              <CardHeader>
                <CardTitle>Cutover Events</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {events.map((event) => (
                    <Card key={event.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-gray-900">{event.name}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={event.type === 'Production' ? 'destructive' : 'secondary'}>
                                {event.type}
                              </Badge>
                              <Badge variant={event.riskLevel === 'High' ? 'destructive' : 'default'}>
                                {event.riskLevel} Risk
                              </Badge>
                            </div>
                          </div>
                          <Badge variant={
                            event.status === 'Completed' ? 'default' :
                            event.status === 'In Progress' ? 'secondary' :
                            event.status === 'Blocked' ? 'destructive' : 'outline'
                          }>
                            {event.status}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                          <div>
                            <span className="text-gray-600">Date:</span>
                            <span className="ml-2 font-medium">{event.date}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Time:</span>
                            <span className="ml-2 font-medium">{event.time}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Duration:</span>
                            <span className="ml-2 font-medium">{event.duration}</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="text-sm text-gray-600">Applications:</div>
                          <div className="flex flex-wrap gap-2">
                            {event.applications.map((app, index) => (
                              <Badge key={index} variant="outline">
                                {app}
                              </Badge>
                            ))}
                          </div>
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

export default Cutovers;
