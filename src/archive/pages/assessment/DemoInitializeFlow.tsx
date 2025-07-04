import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';

// Demo applications for testing assessment flow
const demoApplications = [
  {
    id: 'app-1',
    name: 'Customer Portal',
    metadata: {
      business_criticality: 'High',
      technical_stack: ['Java', 'Spring Boot', 'MySQL'],
      last_modified: '2024-01-15'
    }
  },
  {
    id: 'app-2', 
    name: 'Inventory Management System',
    metadata: {
      business_criticality: 'Medium',
      technical_stack: ['.NET', 'SQL Server', 'Angular'],
      last_modified: '2024-01-10'
    }
  },
  {
    id: 'app-3',
    name: 'Payment Processing API',
    metadata: {
      business_criticality: 'Critical',
      technical_stack: ['Node.js', 'PostgreSQL', 'Redis'],
      last_modified: '2024-01-20'
    }
  },
  {
    id: 'app-4',
    name: 'Analytics Dashboard',
    metadata: {
      business_criticality: 'Low',
      technical_stack: ['React', 'Python', 'MongoDB'],
      last_modified: '2024-01-08'
    }
  }
];

const DemoInitializeAssessmentFlow: React.FC = () => {
  const navigate = useNavigate();
  const [selectedApps, setSelectedApps] = useState<string[]>([]);
  const [initializing, setInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectApp = (appId: string) => {
    setSelectedApps(prev => 
      prev.includes(appId) 
        ? prev.filter(id => id !== appId)
        : [...prev, appId]
    );
  };

  const handleSelectAll = () => {
    if (selectedApps.length === demoApplications.length) {
      setSelectedApps([]);
    } else {
      setSelectedApps(demoApplications.map(app => app.id));
    }
  };

  const handleInitialize = async () => {
    if (selectedApps.length === 0) return;
    
    setInitializing(true);
    setError(null);
    
    try {
      // Mock API call to initialize assessment flow
      const response = await fetch('http://localhost:8000/api/v1/assessment-flow/initialize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'X-Client-Account-ID': '55f4a7eb-de00-de00-de00-888ed4f8e05d',
          'X-Engagement-ID': '59e0e675-de00-de00-de00-29245dcbc79f'
        },
        body: JSON.stringify({
          selected_application_ids: selectedApps,
          architecture_captured: false
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize assessment flow: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Assessment flow initialized:', result);
      
      // Navigate to the initialized flow
      if (result.flow_id) {
        navigate(`/assessment/${result.flow_id}/architecture`);
      } else {
        setError('Flow initialized but no flow ID returned');
      }
      
    } catch (err) {
      console.error('Failed to initialize assessment flow:', err);
      setError(err instanceof Error ? err.message : 'Failed to initialize assessment flow');
    } finally {
      setInitializing(false);
    }
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
                <h1 className="text-3xl font-bold text-gray-900">Initialize Assessment Flow</h1>
                <p className="text-gray-600">
                  Select applications to assess and generate migration strategies
                </p>
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    🚀 <strong>Demo Mode:</strong> Using sample applications for testing the assessment flow.
                  </p>
                </div>
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

              <Card>
                <CardHeader>
                  <CardTitle>Select Applications for Assessment</CardTitle>
                  <CardDescription>
                    Choose which applications you want to include in this assessment flow.
                    These are demo applications for testing the assessment flow functionality.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 flex items-center justify-between">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSelectAll}
                    >
                      {selectedApps.length === demoApplications.length 
                        ? 'Deselect All' 
                        : 'Select All'}
                    </Button>
                    <span className="text-sm text-gray-600">
                      {selectedApps.length} of {demoApplications.length} selected
                    </span>
                  </div>

                  <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
                    {demoApplications.map(app => (
                      <div
                        key={app.id}
                        className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50"
                      >
                        <Checkbox
                          checked={selectedApps.includes(app.id)}
                          onCheckedChange={() => handleSelectApp(app.id)}
                        />
                        <div className="flex-1">
                          <div className="font-medium">{app.name}</div>
                          <div className="text-sm text-gray-600">
                            {app.metadata.business_criticality} criticality • 
                            {app.metadata.technical_stack.join(', ')}
                          </div>
                        </div>
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end gap-3">
                    <Button
                      variant="outline"
                      onClick={() => navigate('/assess')}
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

export default DemoInitializeAssessmentFlow;