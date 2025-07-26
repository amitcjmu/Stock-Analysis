import React, { useState } from 'react'
import { Clock } from 'lucide-react'
import { Activity, Sparkles, TrendingUp, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { useModernizationProgress } from '@/hooks/useModernizationProgress';
import { Sidebar } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';

const ModernizationProgress = (): JSX.Element => {
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'quarter'>('month');
  const { data, isLoading, isError, error } = useModernizationProgress(timeframe);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading modernization progress...</p>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 p-8">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <p>Error loading modernization progress: {error?.message}</p>
          </Alert>
        </div>
      </div>
    );
  }

  const getActivityIcon = (type: string): JSX.Element => {
    switch (type) {
      case 'completion':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'delay':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      default:
        return <Activity className="h-5 w-5 text-blue-600" />;
    }
  };

  const getActivityColor = (status: string): unknown => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Modernization Progress</h1>
                  <p className="text-lg text-gray-600">
                    Track and monitor modernization project progress with AI-powered insights
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Select
                    value={timeframe}
                    onValueChange={(value: 'week' | 'month' | 'quarter') => setTimeframe(value)}
                  >
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="quarter">This Quarter</option>
                  </Select>
                  <Button
                    variant="gradient"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Insights
                  </Button>
                </div>
              </div>
              <Alert className="mt-4" variant="info">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Progress Analytics - Real-time project tracking and predictive insights
                </p>
              </Alert>
            </div>

            {/* AI Insights Panel */}
            <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200 mb-8">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-6 w-6 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Progress AI Assistant</h3>
                </div>
                <p className="text-green-800 mb-3">{data?.aiInsights.prediction}</p>
                <div className="text-sm text-green-600">
                  Predictive analysis: {data?.aiInsights.lastUpdated} | Forecast accuracy: {data?.aiInsights.accuracy}%
                </div>
              </div>
            </Card>

            {/* Progress Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {data?.metrics.map((metric, index) => (
                <Card key={index}>
                  <div className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                        <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                        <div className="flex items-center mt-2">
                          <TrendingUp className={`h-4 w-4 ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`} />
                          <span className={`text-sm font-medium ml-1 ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                            {metric.change}
                          </span>
                          <span className="text-sm text-gray-500 ml-1">vs last {timeframe}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Progress by Treatment */}
              <Card>
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Progress by Treatment</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-6">
                    {data?.projectsByTreatment.map((treatment) => (
                      <div key={treatment.treatment}>
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-medium text-gray-900">{treatment.treatment}</h4>
                          <span className="text-sm text-gray-600">
                            {treatment.completed}/{treatment.total} completed
                          </span>
                        </div>
                        <Progress
                          value={(treatment.completed / treatment.total) * 100}
                          className="h-3 mb-3"
                          segments={[
                            {
                              value: (treatment.completed / treatment.total) * 100,
                              color: 'bg-green-500'
                            },
                            {
                              value: (treatment.inProgress / treatment.total) * 100,
                              color: 'bg-blue-500'
                            },
                            {
                              value: (treatment.delayed / treatment.total) * 100,
                              color: 'bg-yellow-500'
                            }
                          ]}
                        />
                        <div className="grid grid-cols-3 gap-4 text-xs">
                          <div className="flex items-center">
                            <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                            <span>Completed ({treatment.completed})</span>
                          </div>
                          <div className="flex items-center">
                            <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                            <span>In Progress ({treatment.inProgress})</span>
                          </div>
                          <div className="flex items-center">
                            <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                            <span>Delayed ({treatment.delayed})</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>

              {/* Recent Activities */}
              <Card>
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Activities</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {data?.recentActivities.map((activity) => (
                      <div
                        key={activity.id}
                        className={`flex items-start space-x-3 p-3 rounded-lg border ${getActivityColor(activity.status)}`}
                      >
                        {getActivityIcon(activity.type)}
                        <div>
                          <p className="text-sm font-medium text-gray-900">{activity.project}</p>
                          <p className="text-xs text-gray-600">{activity.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>

            {/* Upcoming Milestones */}
            <Card>
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Upcoming Milestones</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {data?.upcomingMilestones.map((milestone, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{milestone.project}</p>
                        <p className="text-sm text-gray-600">{milestone.milestone}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{milestone.date}</p>
                        <p className="text-xs text-gray-600">{milestone.daysLeft} days left</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ModernizationProgress;
