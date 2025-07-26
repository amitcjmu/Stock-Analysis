import React from 'react';
import { Flag } from 'lucide-react'
import { Calendar, Loader2, AlertTriangle, Clock, AlertCircle, ChevronRight } from 'lucide-react'
import { useTimeline } from '@/hooks/useTimeline';
import { Sidebar, SidebarProvider } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const Timeline = (): JSX.Element => {
  const { data, isLoading, isError, error } = useTimeline();

  if (isLoading) {
    return (
      <SidebarProvider>
        <div className="min-h-screen bg-gray-50 flex">
          <Sidebar />
          <div className="flex-1 ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-gray-600">Loading timeline data...</p>
            </div>
          </div>
        </div>
      </SidebarProvider>
    );
  }

  if (isError) {
    return (
      <SidebarProvider>
        <div className="min-h-screen bg-gray-50 flex">
          <Sidebar />
          <div className="flex-1 ml-64 p-8">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <p>Error loading timeline data: {error?.message}</p>
            </Alert>
          </div>
        </div>
      </SidebarProvider>
    );
  }

  const getStatusColor = (status: string): any => {
    const colors = {
      'Not Started': 'bg-gray-100 text-gray-800',
      'In Progress': 'bg-blue-100 text-blue-800',
      'Completed': 'bg-green-100 text-green-800',
      'Delayed': 'bg-red-100 text-red-800',
      'At Risk': 'bg-yellow-100 text-yellow-800',
      'Pending': 'bg-purple-100 text-purple-800',
      'On Track': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getImpactColor = (impact: string): any => {
    const colors = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return colors[impact] || 'bg-gray-100 text-gray-800';
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Timeline</h1>
                  <p className="text-lg text-gray-600">
                    Track and manage the migration schedule and milestones
                  </p>
                </div>
                <Button variant="outline" className="bg-white">
                  <Calendar className="h-5 w-5 mr-2" />
                  Export Schedule
                </Button>
              </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Duration</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.total_duration_weeks} weeks</h3>
                  </div>
                  <Clock className="h-8 w-8 text-blue-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Progress</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.overall_progress}%</h3>
                  </div>
                  <Progress value={data.metrics.overall_progress} className="w-24" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Schedule Health</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.schedule_health.status}</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(data.schedule_health.status)}`}>
                    {data.metrics.delayed_milestones} delays
                  </span>
                </div>
              </Card>
            </div>

            {/* Schedule Health */}
            <Card className="mb-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Schedule Health Analysis</h2>
                <div className="space-y-4">
                  {data.schedule_health.issues.map((issue, index) => (
                    <Alert key={index} variant="warning">
                      <AlertCircle className="h-4 w-4" />
                      <p>{issue}</p>
                    </Alert>
                  ))}
                  {data.schedule_health.recommendations.map((rec, index) => (
                    <Alert key={index} variant="info">
                      <p>{rec}</p>
                    </Alert>
                  ))}
                </div>
              </div>
            </Card>

            {/* Critical Path */}
            <Card className="mb-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Critical Path</h2>
                <div className="flex items-center space-x-2">
                  {data.critical_path.map((phase, index) => (
                    <React.Fragment key={index}>
                      <Badge variant="outline">{phase}</Badge>
                      {index < data.critical_path.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </Card>

            {/* Timeline Phases */}
            <div className="space-y-6">
              {data.phases.map((phase) => (
                <Card key={phase.id}>
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{phase.name}</h3>
                        <p className="text-sm text-gray-600">
                          {new Date(phase.start_date).toLocaleDateString()} - {new Date(phase.end_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(phase.status)}`}>
                          {phase.status}
                        </span>
                        <div className="w-32">
                          <Progress value={phase.progress} />
                        </div>
                      </div>
                    </div>

                    {/* Dependencies */}
                    {phase.dependencies.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-600 mb-2">Dependencies</p>
                        <div className="flex flex-wrap gap-2">
                          {phase.dependencies.map((dep, index) => (
                            <Badge key={index} variant="outline">{dep}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Milestones */}
                    <div className="space-y-3">
                      {phase.milestones.map((milestone, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                          <div>
                            <div className="font-medium">{milestone.name}</div>
                            <div className="text-sm text-gray-600">{milestone.description}</div>
                            <div className="text-sm text-gray-500">{new Date(milestone.date).toLocaleDateString()}</div>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(milestone.status)}`}>
                            {milestone.status}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Risks */}
                    {phase.risks.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-600 mb-2">Risks</p>
                        <div className="space-y-2">
                          {phase.risks.map((risk, index) => (
                            <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                              <div>
                                <div className="text-sm">{risk.description}</div>
                                <div className="text-sm text-gray-600">Mitigation: {risk.mitigation}</div>
                              </div>
                              <Badge className={getImpactColor(risk.impact)}>{risk.impact} Impact</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Timeline;
