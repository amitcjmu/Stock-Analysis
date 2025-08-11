import type React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useExecutionMetrics, useExecutionReports } from '@/hooks/execute/useExecuteQueries';
import Sidebar from '../../components/Sidebar';
import { BarChart, LineChart, PieChart, Filter, RefreshCw } from 'lucide-react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const Reports = (): JSX.Element => {
  const { isAuthenticated } = useAuth();

  // Queries
  const {
    data: reportsData,
    isLoading: isLoadingReports,
    error: reportsError
  } = useExecutionReports();

  const {
    data: metricsData,
    isLoading: isLoadingMetrics
  } = useExecutionMetrics();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access the execution reports.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingReports || isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (reportsError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Error: {reportsError.message}
        </AlertDescription>
      </Alert>
    );
  }

  const { reports = [], metrics = {} } = reportsData || {};
  const executionMetrics = [
    { label: 'Total Migrations', value: metrics.totalMigrations || '0', color: 'text-blue-600', icon: BarChart },
    { label: 'Success Rate', value: metrics.successRate || '0%', color: 'text-green-600', icon: LineChart },
    { label: 'Avg Duration', value: metrics.avgMigrationTime || '0h', color: 'text-purple-600', icon: PieChart },
    { label: 'Active Projects', value: metrics.activeProjects || '0', color: 'text-orange-600', icon: RefreshCw },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Execution Reports</h1>
                  <p className="text-lg text-gray-600">
                    Track and analyze migration execution metrics
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
                  <strong>AI Insight:</strong> {metrics.aiInsight || 'No insights available'}
                </p>
              </div>
            </div>

            {/* Execution Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {executionMetrics.map((metric, index) => {
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

            {/* Reports List */}
            <Card>
              <CardHeader>
                <CardTitle>Migration Reports</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {reports.map((report) => (
                    <Card key={report.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium text-gray-900">{report.title}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={report.type === 'Technical' ? 'destructive' : 'secondary'}>
                                {report.type}
                              </Badge>
                              <Badge variant={report.status === 'Completed' ? 'default' : 'outline'}>
                                {report.status}
                              </Badge>
                            </div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                          <div>
                            <span className="text-gray-600">Generated:</span>
                            <span className="ml-2 font-medium">{report.date}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Project:</span>
                            <span className="ml-2 font-medium">{report.project}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Author:</span>
                            <span className="ml-2 font-medium">{report.author}</span>
                          </div>
                        </div>
                        <div className="text-sm text-gray-600">
                          {report.description}
                        </div>
                        {report.metrics && (
                          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(report.metrics).map(([key, value]) => (
                              <div key={key} className="bg-gray-50 p-3 rounded-lg">
                                <div className="text-xs text-gray-500">{key}</div>
                                <div className="font-medium">{value}</div>
                              </div>
                            ))}
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

export default Reports;
