import type React from 'react';
import { Users, Loader2, AlertTriangle, UserPlus, BarChart, Calendar, Briefcase } from 'lucide-react';
import { useResource } from '@/hooks/useResource';
import { Sidebar, SidebarProvider } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';

const Resource = (): JSX.Element => {
  const { data, isLoading, isError, error } = useResource();

  if (isLoading) {
    return (
      <SidebarProvider>
        <div className="min-h-screen bg-gray-50 flex">
          <Sidebar />
          <div className="flex-1 ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-gray-600">Loading resource data...</p>
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
              <p>Error loading resource data: {error?.message}</p>
            </Alert>
          </div>
        </div>
      </SidebarProvider>
    );
  }

  const getUtilizationColor = (utilization: number): unknown => {
    if (utilization > 90) return 'text-red-600';
    if (utilization > 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getImpactColor = (impact: string): unknown => {
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Resource Planning</h1>
                  <p className="text-lg text-gray-600">
                    Manage and optimize team resources for migration projects
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button variant="outline" className="bg-white">
                    <BarChart className="h-5 w-5 mr-2" />
                    Resource Report
                  </Button>
                  <Button variant="primary">
                    <UserPlus className="h-5 w-5 mr-2" />
                    Add Team
                  </Button>
                </div>
              </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Teams</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.total_teams}</h3>
                  </div>
                  <Users className="h-8 w-8 text-blue-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Resources</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.total_resources}</h3>
                  </div>
                  <Briefcase className="h-8 w-8 text-green-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg. Utilization</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.average_utilization}%</h3>
                  </div>
                  <BarChart className="h-8 w-8 text-purple-600" />
                </div>
              </Card>
            </div>

            {/* Recommendations */}
            <Card className="mb-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Resource Recommendations</h2>
                <div className="space-y-4">
                  {data.recommendations.map((rec, index) => (
                    <Alert key={index} variant="info">
                      <div className="flex items-center justify-between">
                        <p className="text-sm">{rec.description}</p>
                        <Badge className={getImpactColor(rec.impact)}>{rec.impact} Impact</Badge>
                      </div>
                    </Alert>
                  ))}
                </div>
              </div>
            </Card>

            {/* Team Allocation Table */}
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Team Allocation</h2>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Team</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Skills</TableHead>
                      <TableHead>Utilization</TableHead>
                      <TableHead>Current Assignments</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.teams.map((team) => (
                      <TableRow key={team.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{team.name}</div>
                            <div className="text-sm text-gray-500">{team.id}</div>
                          </div>
                        </TableCell>
                        <TableCell>{team.size} members</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {team.skills.map((skill, index) => (
                              <Badge key={index} variant="outline">{skill}</Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="w-32">
                            <div className="flex justify-between text-sm mb-1">
                              <span className={getUtilizationColor(team.utilization)}>
                                {team.utilization}%
                              </span>
                            </div>
                            <Progress value={team.utilization} />
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-2">
                            {team.assignments.map((assignment, index) => (
                              <div key={index} className="text-sm">
                                <div className="font-medium">{assignment.project}</div>
                                <div className="text-gray-500 flex items-center">
                                  <Calendar className="h-4 w-4 mr-1" />
                                  {new Date(assignment.start_date).toLocaleDateString()} - {new Date(assignment.end_date).toLocaleDateString()}
                                </div>
                                <div className="text-blue-600">{assignment.allocation}% allocated</div>
                              </div>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>

            {/* Upcoming Resource Needs */}
            <Card className="mt-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Resource Needs</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {data.upcoming_needs.map((need, index) => (
                    <Card key={index} className="p-4">
                      <h3 className="font-medium text-gray-900">{need.skill}</h3>
                      <p className="text-sm text-gray-600 mt-1">Demand: {need.demand} resources</p>
                      <p className="text-sm text-blue-600 mt-1">Timeline: {need.timeline}</p>
                    </Card>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Resource;
