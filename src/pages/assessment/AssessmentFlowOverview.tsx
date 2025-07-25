import type React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Filter } from 'lucide-react'
import { Plus, Search, MoreHorizontal, Play, Pause, CheckCircle2, AlertCircle, Clock, Users, Loader2 } from 'lucide-react'

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '../../config/api';
import { Button } from '@/components/ui/button';
import { CardDescription } from '@/components/ui/card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface AssessmentFlow {
  id: string;
  status: 'initialized' | 'processing' | 'paused_for_user_input' | 'completed' | 'error';
  current_phase: string;
  progress: number;
  selected_applications: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface AssessmentFlowMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  total_applications_assessed: number;
}

const AssessmentFlowOverview = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();

  // Fetch assessment flow metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery<AssessmentFlowMetrics>({
    queryKey: ['assessment-flow-metrics'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      // Mock data for now - would be replaced with actual API
      return {
        total_flows: 5,
        active_flows: 2,
        completed_flows: 3,
        total_applications_assessed: 47
      };
    }
  });

  // Fetch assessment flows
  const { data: flows = [], isLoading: flowsLoading } = useQuery<AssessmentFlow[]>({
    queryKey: ['assessment-flows'],
    queryFn: async () => {
      const headers = getAuthHeaders();
      try {
        // This would be the actual API call
        // const response = await apiCall('assessment-flow/list', { headers });
        // return response.flows;

        // Mock data for demonstration
        return [
          {
            id: 'flow-001',
            status: 'processing',
            current_phase: 'tech_debt_analysis',
            progress: 65,
            selected_applications: 12,
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-15T14:22:00Z',
            created_by: 'john.doe@company.com'
          },
          {
            id: 'flow-002',
            status: 'paused_for_user_input',
            current_phase: 'architecture_minimums',
            progress: 25,
            selected_applications: 8,
            created_at: '2024-01-14T09:15:00Z',
            updated_at: '2024-01-14T16:45:00Z',
            created_by: 'jane.smith@company.com'
          },
          {
            id: 'flow-003',
            status: 'completed',
            current_phase: 'finalization',
            progress: 100,
            selected_applications: 15,
            created_at: '2024-01-12T08:00:00Z',
            updated_at: '2024-01-13T17:30:00Z',
            created_by: 'mike.wilson@company.com'
          }
        ] as AssessmentFlow[];
      } catch (error) {
        console.error('Failed to fetch assessment flows:', error);
        return [];
      }
    }
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'paused_for_user_input':
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      processing: 'default',
      paused_for_user_input: 'secondary',
      completed: 'default',
      error: 'destructive',
      initialized: 'secondary'
    } as const;

    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const formatPhase = (phase: string) => {
    return phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Assessment Flows</h1>
                <p className="text-gray-600">
                  AI-powered application assessment flows and management
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button onClick={() => navigate('/assessment/initialize')}>
                <Plus className="h-4 w-4 mr-2" />
                New Assessment Flow
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {/* Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Users className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Flows</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.total_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Play className="h-6 w-6 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Active</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.active_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <CheckCircle2 className="h-6 w-6 text-purple-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Completed</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.completed_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Users className="h-6 w-6 text-orange-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Apps Assessed</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.total_applications_assessed || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Search and Actions */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Assessment Flows</CardTitle>
                    <div className="flex items-center space-x-2">
                      <Input
                        placeholder="Search flows..."
                        className="w-64"
                        prefix={<Search className="h-4 w-4" />}
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {flowsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                    </div>
                  ) : flows.length === 0 ? (
                    <div className="text-center py-8">
                      <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Assessment Flows</h3>
                      <p className="text-gray-600 mb-4">
                        Start a new assessment flow to begin AI-powered application analysis.
                      </p>
                      <Button onClick={() => navigate('/assessment/initialize')}>
                        <Plus className="h-4 w-4 mr-2" />
                        Start New Assessment Flow
                      </Button>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Flow ID</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Phase</TableHead>
                          <TableHead>Progress</TableHead>
                          <TableHead>Applications</TableHead>
                          <TableHead>Created</TableHead>
                          <TableHead>Updated</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {flows.map((flow) => (
                          <TableRow key={flow.id}>
                            <TableCell className="font-medium">
                              <Link
                                to={`/assessment/${flow.id}/architecture`}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                {flow.id.substring(0, 8)}...
                              </Link>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(flow.status)}
                                {getStatusBadge(flow.status)}
                              </div>
                            </TableCell>
                            <TableCell>{formatPhase(flow.current_phase)}</TableCell>
                            <TableCell>
                              <div className="flex items-center space-x-2">
                                <div className="w-16 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: `${flow.progress}%` }}
                                  />
                                </div>
                                <span className="text-sm text-gray-600">{flow.progress}%</span>
                              </div>
                            </TableCell>
                            <TableCell>{flow.selected_applications}</TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {formatDate(flow.created_at)}
                            </TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {formatDate(flow.updated_at)}
                            </TableCell>
                            <TableCell>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel
                pageContext="assessment-overview"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Assessment overview question answered:', questionId, response);
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection
                pageContext="assessment-overview"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Assessment overview insight action:', insightId, action);
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext="assessment-overview" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentFlowOverview;
