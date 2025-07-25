import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext';
import { useReplatformProjects, useExecutionMetrics, useUpdateReplatformProject } from '@/hooks/execute/useExecuteQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import { Settings, ArrowRight } from 'lucide-react'
import { Cloud, Sparkles, Play, Clock, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

const Replatform = () => {
  const [activeTab, setActiveTab] = useState('planning');
  const { isAuthenticated } = useAuth();

  // Queries
  const {
    data: replatformData,
    isLoading: isLoadingReplatform,
    error: replatformError
  } = useReplatformProjects();

  const {
    data: metricsData,
    isLoading: isLoadingMetrics
  } = useExecutionMetrics();

  // Mutations
  const { mutate: updateProject } = useUpdateReplatformProject();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access the replatform migration execution.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingReplatform || isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (replatformError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {replatformError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const { projects = [], metrics = {} } = replatformData || {};
  const executionMetrics = [
    { label: 'Active Replatform Projects', value: metrics.activeReplatform || '0', color: 'text-purple-600' },
    { label: 'Platform Migrations', value: metrics.totalMigrations || '0', color: 'text-blue-600' },
    { label: 'Success Rate', value: metrics.successRate || '0%', color: 'text-green-600' },
    { label: 'Avg Modernization Time', value: metrics.avgMigrationTime || '0 weeks', color: 'text-orange-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Replatform Migration Execution</h1>
                  <p className="text-lg text-gray-600">
                    Platform modernization with optimized cloud services
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Optimize
                  </Button>
                  <Button variant="default" className="bg-purple-600 hover:bg-purple-700">
                    <Play className="h-5 w-5 mr-2" />
                    Start Migration
                  </Button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-purple-800 text-sm">
                  <strong>AI Insight:</strong> Replatform migrations show {metrics.successRate || '0%'} success rate with {metrics.avgMigrationTime || '0 week'} average completion
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
                    <Cloud className={`h-8 w-8 ${metric.color}`} />
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Navigation Tabs */}
            <Card>
              <CardContent className="p-0">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="w-full border-b">
                    <TabsTrigger value="planning" className="flex items-center">
                      <Clock className="h-5 w-5 mr-2" />
                      Platform Planning
                    </TabsTrigger>
                    <TabsTrigger value="execution" className="flex items-center">
                      <Play className="h-5 w-5 mr-2" />
                      Active Modernizations
                    </TabsTrigger>
                    <TabsTrigger value="reports" className="flex items-center">
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Platform Reports
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="planning" className="p-6">
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-gray-900">Platform Planning</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {projects.filter(project => project.status === 'Planned').map(project => (
                          <Card key={project.id}>
                            <CardHeader>
                              <CardTitle className="flex items-center justify-between">
                                <span>{project.name}</span>
                                <Badge variant={project.complexity === 'High' ? 'destructive' : 'default'}>
                                  {project.complexity}
                                </Badge>
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Start Date:</span>
                                  <span className="font-medium">{new Date(project.startDate).toLocaleDateString()}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Target Date:</span>
                                  <span className="font-medium">{new Date(project.targetDate).toLocaleDateString()}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Target Platform:</span>
                                  <Badge variant="outline">{project.platform}</Badge>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="execution" className="p-6">
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-gray-900">Active Modernizations</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {projects.filter(project => project.status === 'In Progress').map(project => (
                          <Card key={project.id} className="bg-purple-50">
                            <CardHeader>
                              <CardTitle>{project.name} ({project.id})</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Progress:</span>
                                  <span className="font-medium">{project.progress}% Complete</span>
                                </div>
                                <Progress value={project.progress} className="mt-2" />
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Platform:</span>
                                  <Badge variant="outline">{project.platform}</Badge>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Complexity:</span>
                                  <Badge variant={project.complexity === 'High' ? 'destructive' : 'default'}>
                                    {project.complexity}
                                  </Badge>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="reports" className="p-6">
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-gray-900">Platform Reports</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <Card className="bg-green-50">
                          <CardContent className="p-6 text-center">
                            <div className="text-3xl font-bold text-green-600 mb-2">
                              {metrics.completedPlatforms || 0}
                            </div>
                            <div className="text-gray-600">Completed Platforms</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-purple-50">
                          <CardContent className="p-6 text-center">
                            <div className="text-3xl font-bold text-purple-600 mb-2">
                              {metrics.inProgress || 0}
                            </div>
                            <div className="text-gray-600">In Progress</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-yellow-50">
                          <CardContent className="p-6 text-center">
                            <div className="text-3xl font-bold text-yellow-600 mb-2">
                              {metrics.costReduction || '0%'}
                            </div>
                            <div className="text-gray-600">Cost Reduction</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-blue-50">
                          <CardContent className="p-6 text-center">
                            <div className="text-3xl font-bold text-blue-600 mb-2">
                              {metrics.successRate || '0%'}
                            </div>
                            <div className="text-gray-600">Success Rate</div>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Replatform;
