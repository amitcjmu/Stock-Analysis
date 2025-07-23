import type React, { useState } from 'react'
import type { Clock, CheckCircle, Filter } from 'lucide-react'
import { Code, Sparkles, Play, AlertTriangle, Loader2 } from 'lucide-react'
import { useRefactor } from '@/hooks/useRefactor';
import { Sidebar } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';

const Refactor = () => {
  const [activeTab, setActiveTab] = useState('planning');
  const [filterStatus, setFilterStatus] = useState('All');
  const { data, isLoading, isError, error } = useRefactor(filterStatus);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading refactor data...</p>
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
            <p>Error loading refactor data: {error?.message}</p>
          </Alert>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors = {
      'Planning': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-green-100 text-green-800',
      'On Hold': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getComplexityColor = (complexity: string) => {
    const colors = {
      'Low': 'bg-green-100 text-green-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'High': 'bg-red-100 text-red-800'
    };
    return colors[complexity] || 'bg-gray-100 text-gray-800';
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Refactor Planning & Execution</h1>
                  <p className="text-lg text-gray-600">
                    Plan and execute code refactoring projects with AI-driven recommendations
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="gradient"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Analysis
                  </Button>
                  <Button variant="success">
                    <Play className="h-5 w-5 mr-2" />
                    Start Refactor
                  </Button>
                </div>
              </div>
              <Alert className="mt-4" variant="info">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Refactor Assistant - Automated code analysis and optimization recommendations
                </p>
              </Alert>
            </div>

            {/* AI Insights Panel */}
            <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200 mb-8">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Code className="h-6 w-6 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Refactor AI Assistant</h3>
                </div>
                <p className="text-green-800 mb-3">{data?.aiInsights.analysis}</p>
                <div className="text-sm text-green-600">
                  Analysis completed: {data?.aiInsights.lastUpdated} | Code quality improvement potential: {data?.aiInsights.qualityImprovement}%
                </div>
              </div>
            </Card>

            {/* Tab Navigation */}
            <Card>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="border-b border-gray-200">
                  {[
                    { id: 'planning', name: 'Planning', icon: Clock },
                    { id: 'execution', name: 'Execution', icon: Play },
                    { id: 'progress', name: 'Progress', icon: CheckCircle }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <TabsTrigger
                        key={tab.id}
                        value={tab.id}
                        className="flex items-center space-x-2 px-6 py-4"
                      >
                        <Icon className="h-4 w-4 mr-2" />
                        <span>{tab.name}</span>
                      </TabsTrigger>
                    );
                  })}
                </TabsList>

                <div className="p-6">
                  {activeTab === 'planning' && (
                    <div>
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-semibold text-gray-900">Refactor Planning</h3>
                        <Select
                          value={filterStatus}
                          onValueChange={(value) => setFilterStatus(value)}
                        >
                          <option value="All">All Status</option>
                          <option value="Planning">Planning</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                          <option value="On Hold">On Hold</option>
                        </Select>
                      </div>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Project</TableHead>
                              <TableHead>Complexity</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Effort</TableHead>
                              <TableHead>AI Recommendation</TableHead>
                              <TableHead>Benefits</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {data?.projects.map((project) => (
                              <TableRow key={project.id} className="hover:bg-gray-50">
                                <TableCell>
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">{project.application}</div>
                                    <div className="text-sm text-gray-500">{project.id}</div>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getComplexityColor(project.complexity)}`}>
                                    {project.complexity}
                                  </span>
                                </TableCell>
                                <TableCell>
                                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                                    {project.status}
                                  </span>
                                </TableCell>
                                <TableCell className="text-sm text-gray-900">{project.effort}</TableCell>
                                <TableCell>
                                  <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded">
                                    {project.aiRecommendation}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <div className="flex flex-wrap gap-1">
                                    {project.benefits.map((benefit, index) => (
                                      <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                        {benefit}
                                      </span>
                                    ))}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  )}

                  {activeTab === 'execution' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-6">Execution Progress</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card className="p-6">
                          <h4 className="font-semibold text-gray-900 mb-4">Code Quality Metrics</h4>
                          <div className="space-y-4">
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Overall Progress</span>
                                <span className="font-medium">{data?.metrics.averageCompletion}%</span>
                              </div>
                              <Progress value={data?.metrics.averageCompletion} />
                            </div>
                            <div>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Code Quality Improvement</span>
                                <span className="font-medium">{data?.metrics.codeQualityImprovement}%</span>
                              </div>
                              <Progress value={data?.metrics.codeQualityImprovement} />
                            </div>
                          </div>
                        </Card>
                        <Card className="p-6">
                          <h4 className="font-semibold text-gray-900 mb-4">Project Status</h4>
                          <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Total Projects</span>
                              <span className="font-medium">{data?.metrics.totalProjects}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Completed</span>
                              <span className="font-medium text-green-600">{data?.metrics.completedProjects}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">In Progress</span>
                              <span className="font-medium text-blue-600">{data?.metrics.inProgressProjects}</span>
                            </div>
                          </div>
                        </Card>
                      </div>
                    </div>
                  )}

                  {activeTab === 'progress' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-6">Progress Report</h3>
                      <Alert variant="warning">
                        <p>Detailed progress reporting features coming soon...</p>
                      </Alert>
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

export default Refactor;
