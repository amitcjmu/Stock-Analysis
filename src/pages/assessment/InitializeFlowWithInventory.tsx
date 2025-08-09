import React from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Filter } from 'lucide-react'
import { Loader2, CheckCircle2, AlertCircle, Search } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '../../config/api';

interface Application {
  id: string;
  name: string;
  type: string;
  business_criticality?: string;
  technical_stack?: string[];
  last_modified?: string;
  ready_for_assessment?: boolean;
  metadata?: {
    business_criticality?: string;
    technical_stack?: string[];
    environment?: string;
    owner?: string;
  };
}

const InitializeAssessmentFlowWithInventory: React.FC = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const [selectedApps, setSelectedApps] = useState<string[]>([]);
  const [initializing, setInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState<string>('');

  // Fetch applications from inventory
  const { data: applications = [], isLoading: appsLoading, error: appsError } = useQuery<Application[]>({
    queryKey: ['assessment-applications'],
    queryFn: async () => {
      const headers = getAuthHeaders();

      try {
        // Try to get applications from asset inventory
        const response = await apiCall('assets/list/paginated', {
          headers,
          method: 'GET'
        });

        if (response?.assets) {
          // Filter for applications and format them
          return response.assets
            .filter((asset: unknown) => asset.type === 'Application')
            .map((asset: unknown) => ({
              id: asset.id,
              name: asset.name || asset.hostname || `App-${asset.id}`,
              type: 'Application',
              business_criticality: asset.metadata?.business_criticality || asset.business_criticality || 'Medium',
              technical_stack: asset.metadata?.technical_stack || asset.technical_stack || ['Unknown'],
              last_modified: asset.last_modified || asset.updated_at,
              ready_for_assessment: asset.ready_for_assessment !== false, // Default to true
              metadata: {
                business_criticality: asset.metadata?.business_criticality || asset.business_criticality || 'Medium',
                technical_stack: asset.metadata?.technical_stack || asset.technical_stack || ['Unknown'],
                environment: asset.metadata?.environment || asset.environment || 'Production',
                owner: asset.metadata?.owner || asset.owner || 'Unknown'
              }
            }));
        }

        // Fallback to discovery applications if available
        try {
          const discoveryResponse = await apiCall('discovery/applications', { headers });
          if (discoveryResponse?.applications) {
            return discoveryResponse.applications.map((app: unknown) => ({
              id: app.id,
              name: app.name || app.application_name,
              type: 'Application',
              business_criticality: app.business_criticality || 'Medium',
              technical_stack: app.technical_stack || ['Unknown'],
              ready_for_assessment: true,
              metadata: {
                business_criticality: app.business_criticality || 'Medium',
                technical_stack: app.technical_stack || ['Unknown'],
                environment: app.environment || 'Production',
                owner: app.owner || 'Unknown'
              }
            }));
          }
        } catch (discoveryError) {
          console.log('Discovery applications not available:', discoveryError);
        }

        // Return empty array if no applications found
        return [];

      } catch (error) {
        console.error('Failed to fetch applications:', error);
        throw new Error('Failed to load applications from inventory');
      }
    },
    retry: 2
  });

  // Filter applications based on search and criticality
  const filteredApplications = applications.filter(app => {
    const matchesSearch = !searchTerm ||
      app.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (app.metadata?.technical_stack?.some(tech =>
        tech.toLowerCase().includes(searchTerm.toLowerCase())
      ));

    const matchesCriticality = !criticalityFilter ||
      app.metadata?.business_criticality === criticalityFilter;

    return matchesSearch && matchesCriticality;
  });

  // Only show applications ready for assessment
  const readyApplications = filteredApplications.filter(app => app.ready_for_assessment);

  const handleSelectApp = (appId: string): void => {
    setSelectedApps(prev =>
      prev.includes(appId)
        ? prev.filter(id => id !== appId)
        : [...prev, appId]
    );
  };

  const handleSelectAll = (): void => {
    if (selectedApps.length === readyApplications.length) {
      setSelectedApps([]);
    } else {
      setSelectedApps(readyApplications.map(app => app.id));
    }
  };

  const handleInitialize = async (): Promise<void> => {
    if (selectedApps.length === 0) return;

    setInitializing(true);
    setError(null);

    try {
      const headers = getAuthHeaders();
      const result = await apiCall('/assessment-flow/initialize', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          selected_application_ids: selectedApps,
          architecture_captured: false
        })
      });

      const flowId = result && typeof result === 'object' ? (result as any).flow_id : undefined;
      if (flowId) {
        navigate(`/assessment/${flowId}/architecture`);
      } else {
        throw new Error('Flow initialization returned no flow_id');
      }

    } catch (err) {
      console.error('Failed to initialize assessment flow:', err);
      setError(err instanceof Error ? err.message : 'Failed to initialize assessment flow');
    } finally {
      setInitializing(false);
    }
  };

  const getCriticalityColor = (criticality: string): unknown => {
    switch (criticality?.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (appsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

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
                <h1 className="text-3xl font-bold text-gray-900">Initialize Assessment Flow</h1>
                <p className="text-gray-600">
                  Select applications from your inventory to assess and generate migration strategies
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {error && (
                <Alert variant="destructive" className="mb-6">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {appsError && (
                <Alert variant="destructive" className="mb-6">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Failed to load applications from inventory. Please check your data sources.
                  </AlertDescription>
                </Alert>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>Select Applications for Assessment</CardTitle>
                  <CardDescription>
                    Choose applications from your inventory to include in this assessment flow.
                    Only applications marked as ready for assessment are shown.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Search and Filter Controls */}
                  <div className="mb-6 space-y-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex-1">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <Input
                            placeholder="Search applications..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10"
                          />
                        </div>
                      </div>
                      <select
                        value={criticalityFilter}
                        onChange={(e) => setCriticalityFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">All Criticality</option>
                        <option value="Critical">Critical</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                      </select>
                    </div>
                  </div>

                  {readyApplications.length === 0 ? (
                    <div className="text-center py-8">
                      <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 mb-4">
                        {applications.length === 0
                          ? "No applications found in your inventory."
                          : "No applications are ready for assessment."
                        }
                      </p>
                      <Button
                        variant="outline"
                        onClick={() => navigate('/discovery/inventory')}
                      >
                        Go to Inventory
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div className="mb-4 flex items-center justify-between">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleSelectAll}
                        >
                          {selectedApps.length === readyApplications.length
                            ? 'Deselect All'
                            : 'Select All'}
                        </Button>
                        <span className="text-sm text-gray-600">
                          {selectedApps.length} of {readyApplications.length} selected
                        </span>
                      </div>

                      <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
                        {readyApplications.map(app => (
                          <div
                            key={app.id}
                            className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50"
                          >
                            <Checkbox
                              checked={selectedApps.includes(app.id)}
                              onCheckedChange={() => handleSelectApp(app.id)}
                            />
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <div className="font-medium">{app.name}</div>
                                <Badge
                                  variant="outline"
                                  className={getCriticalityColor(app.metadata?.business_criticality || 'Medium')}
                                >
                                  {app.metadata?.business_criticality || 'Medium'}
                                </Badge>
                              </div>
                              <div className="text-sm text-gray-600">
                                {app.metadata?.technical_stack?.join(', ') || 'Unknown stack'} •
                                {app.metadata?.environment || 'Unknown environment'}
                              </div>
                            </div>
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          </div>
                        ))}
                      </div>

                      <div className="flex justify-end gap-3">
                        <Button
                          variant="outline"
                          onClick={() => navigate('/assessment')}
                          disabled={initializing}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={handleInitialize}
                          disabled={selectedApps.length === 0 || initializing}
                        >
                          {initializing ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Initializing...
                            </>
                          ) : (
                            `Start Assessment (${selectedApps.length} apps)`
                          )}
                        </Button>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel
                pageContext="assessment-initialization"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Assessment initialization question answered:', questionId, response);
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection
                pageContext="assessment-initialization"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Assessment initialization insight action:', insightId, action);
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext="assessment-initialization" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InitializeAssessmentFlowWithInventory;
