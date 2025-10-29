import React, { useState } from 'react'
import { Code2, Loader2, AlertTriangle, RefreshCw, Calendar, Users, Activity, AlertCircle } from 'lucide-react';
import { useRewrite } from '@/hooks/useRewrite';
import Sidebar from '@/components/Sidebar';;
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

const Rewrite = (): JSX.Element => {
  const [activeTab, setActiveTab] = useState('projects');
  const [statusFilter, setStatusFilter] = useState('All');
  const { data, isLoading, isError, error } = useRewrite(statusFilter !== 'All' ? statusFilter : undefined);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading replace projects...</p>
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
            <p>Error loading replace data: {error?.message}</p>
          </Alert>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity: string): unknown => {
    const colors = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return colors[severity] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string): unknown => {
    const colors = {
      'Planning': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-green-100 text-green-800',
      'On Hold': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          {/* Context Breadcrumbs */}
          <ContextBreadcrumbs showContextSelector={true} />

          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Replace Strategy</h1>
                  <p className="text-lg text-gray-600">
                    Replace with COTS/SaaS solutions or rewrite custom applications with modern technologies
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button variant="outline" className="bg-white">
                    <RefreshCw className="h-5 w-5 mr-2" />
                    Sync Status
                  </Button>
                  <Button variant="primary">
                    <Code2 className="h-5 w-5 mr-2" />
                    New Replace Project
                  </Button>
                </div>
              </div>

              {/* AI Insights */}
              <Card className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Insights</h3>
                  <div className="space-y-4">
                    {data?.ai_insights.key_findings.map((finding, index) => (
                      <Alert key={index} variant="info" className="bg-white/50">
                        <p>{finding}</p>
                      </Alert>
                    ))}
                    <p className="text-sm text-gray-600">
                      Last updated: {data?.ai_insights.last_updated}
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Main Content */}
            <Card>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="border-b border-gray-200">
                  <TabsTrigger value="projects" className="flex items-center space-x-2">
                    <Code2 className="h-4 w-4 mr-2" />
                    Projects
                  </TabsTrigger>
                  <TabsTrigger value="teams" className="flex items-center space-x-2">
                    <Users className="h-4 w-4 mr-2" />
                    Teams
                  </TabsTrigger>
                  <TabsTrigger value="timeline" className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 mr-2" />
                    Timeline
                  </TabsTrigger>
                  <TabsTrigger value="metrics" className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 mr-2" />
                    Metrics
                  </TabsTrigger>
                </TabsList>

                <div className="p-6">
                  {activeTab === 'projects' && (
                    <div>
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-semibold text-gray-900">Replace Projects</h3>
                        <Select
                          value={statusFilter}
                          onValueChange={(value) => setStatusFilter(value)}
                        >
                          <option value="All">All Status</option>
                          <option value="Planning">Planning</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                          <option value="On Hold">On Hold</option>
                        </Select>
                      </div>

                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Project</TableHead>
                            <TableHead>Technology</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Progress</TableHead>
                            <TableHead>Timeline</TableHead>
                            <TableHead>Risks</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data?.projects.map((project) => (
                            <TableRow key={project.id}>
                              <TableCell>
                                <div>
                                  <div className="font-medium">{project.name}</div>
                                  <div className="text-sm text-gray-500">{project.id}</div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  <Badge variant="outline">{project.technology.current}</Badge>
                                  <div className="flex items-center">
                                    <span className="text-gray-400 mx-2">→</span>
                                    <Badge variant="default">{project.technology.target}</Badge>
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                                  {project.status}
                                </span>
                              </TableCell>
                              <TableCell>
                                <div className="w-32">
                                  <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-600">{project.progress}%</span>
                                  </div>
                                  <Progress value={project.progress} />
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="text-sm">
                                  <div>Start: {new Date(project.timeline.start).toLocaleDateString()}</div>
                                  <div>Est. Completion: {new Date(project.timeline.estimated_completion).toLocaleDateString()}</div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  {project.risks.map((risk, index) => (
                                    <div key={index} className="flex items-center space-x-2">
                                      <AlertCircle className="h-4 w-4 text-gray-400" />
                                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(risk.severity)}`}>
                                        {risk.type}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                  {activeTab === 'metrics' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <Card className="p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Project Metrics</h4>
                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Overall Completion</span>
                              <span className="font-medium">{data?.metrics.average_completion}%</span>
                            </div>
                            <Progress value={data?.metrics.average_completion} />
                          </div>
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Success Rate</span>
                              <span className="font-medium">{data?.metrics.overall_success_rate}%</span>
                            </div>
                            <Progress value={data?.metrics.overall_success_rate} />
                          </div>
                        </div>
                      </Card>

                      <Card className="p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Project Status</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Total Projects</span>
                            <span className="font-medium">{data?.metrics.total_projects}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Completed</span>
                            <span className="font-medium text-green-600">{data?.metrics.completed_projects}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">In Progress</span>
                            <span className="font-medium text-blue-600">{data?.metrics.in_progress}</span>
                          </div>
                        </div>
                      </Card>
                    </div>
                  )}

                  {activeTab === 'teams' && (
                    <div className="space-y-6">
                      {data?.projects.map((project) => (
                        <Card key={project.id} className="p-6">
                          <div className="flex justify-between items-center mb-4">
                            <div>
                              <h4 className="font-semibold text-gray-900">{project.name}</h4>
                              <p className="text-sm text-gray-600">Team Size: {project.team.size}</p>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {project.team.skills.map((skill, index) => (
                              <Badge key={index} variant="outline">{skill}</Badge>
                            ))}
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}

                  {activeTab === 'timeline' && (
                    <div className="space-y-6">
                      {data?.projects.map((project) => (
                        <Card key={project.id} className="p-6">
                          <div className="flex justify-between items-center mb-4">
                            <div>
                              <h4 className="font-semibold text-gray-900">{project.name}</h4>
                              <div className="text-sm text-gray-600">
                                <span>Start: {new Date(project.timeline.start).toLocaleDateString()}</span>
                                <span className="mx-2">•</span>
                                <span>Est. Completion: {new Date(project.timeline.estimated_completion).toLocaleDateString()}</span>
                              </div>
                            </div>
                            <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(project.status)}`}>
                              {project.status}
                            </span>
                          </div>
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Progress</span>
                              <span>{project.progress}%</span>
                            </div>
                            <Progress value={project.progress} />
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              </Tabs>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Rewrite;
