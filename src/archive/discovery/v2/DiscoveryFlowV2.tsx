/**
 * Discovery Flow V2 Page
 * Main page for managing Discovery Flow V2 with flow selection and dashboard
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  Plus, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle,
  Clock,
  Database,
  FileText,
  Settings
} from 'lucide-react';
import { DiscoveryFlowV2Dashboard } from '../../components/discovery/DiscoveryFlowV2Dashboard';
import { useDiscoveryFlowList, useDiscoveryFlowHealth } from '../../hooks/discovery/useDiscoveryFlowV2';
import { discoveryFlowV2Service, DiscoveryFlowV2Utils } from '../../services/discoveryFlowV2Service';
import { toast } from 'sonner';

export function DiscoveryFlowV2Page() {
  const [selectedFlowId, setSelectedFlowId] = useState<string | null>(null);
  const [showCreateFlow, setShowCreateFlow] = useState(false);

  const { data: flows = [], isLoading: flowsLoading, refetch: refetchFlows } = useDiscoveryFlowList();
  const { data: health, isLoading: healthLoading } = useDiscoveryFlowHealth();

  const handleCreateFlow = async () => {
    try {
      // Demo flow creation
      const demoFlowData = {
        flow_id: `flow_${Date.now()}`,
        raw_data: [
          {
            name: 'Demo Server 1',
            type: 'server',
            environment: 'production',
            os: 'Windows Server 2019',
            cpu_cores: 8,
            memory_gb: 32,
            applications: ['IIS', 'SQL Server']
          },
          {
            name: 'Demo Database 1',
            type: 'database',
            engine: 'SQL Server',
            version: '2019',
            size_gb: 500,
            connections: 50
          },
          {
            name: 'Demo Application 1',
            type: 'application',
            framework: '.NET Framework 4.8',
            language: 'C#',
            dependencies: ['SQL Server', 'IIS']
          }
        ],
        metadata: {
          source: 'demo_data',
          created_by: 'demo_user',
          description: 'Demo discovery flow for testing V2 functionality'
        }
      };

      const newFlow = await discoveryFlowV2Service.createFlow(demoFlowData);
      setSelectedFlowId(newFlow.flow_id);
      refetchFlows();
      setShowCreateFlow(false);
      toast.success('Demo discovery flow created successfully');
    } catch (error) {
      toast.error('Failed to create discovery flow');
    }
  };

  const handleFlowComplete = (flowId: string) => {
    toast.success(`Flow ${flowId} completed successfully`);
    refetchFlows();
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Discovery Flow V2</h1>
          <p className="text-muted-foreground">
            Next-generation discovery flows with CrewAI integration and real-time progress tracking
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetchFlows()} disabled={flowsLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${flowsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleCreateFlow}>
            <Plus className="h-4 w-4 mr-2" />
            Create Demo Flow
          </Button>
        </div>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          {healthLoading ? (
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Checking system health...</span>
            </div>
          ) : health ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <div className="font-medium">API Status</div>
                  <div className="text-sm text-muted-foreground">{health.status}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="font-medium">Database</div>
                  <div className="text-sm text-muted-foreground">
                    {health.database_connected ? 'Connected' : 'Disconnected'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-600" />
                <div>
                  <div className="font-medium">API Version</div>
                  <div className="text-sm text-muted-foreground">{health.api_version}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-orange-600" />
                <div>
                  <div className="font-medium">Last Check</div>
                  <div className="text-sm text-muted-foreground">
                    {new Date(health.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Unable to connect to Discovery Flow V2 API. Please check system status.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="flows" className="space-y-4">
        <TabsList>
          <TabsTrigger value="flows">Flow Management</TabsTrigger>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
        </TabsList>

        {/* Flow Management Tab */}
        <TabsContent value="flows" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Discovery Flows</CardTitle>
              <CardDescription>
                Manage and monitor your discovery flows
              </CardDescription>
            </CardHeader>
            <CardContent>
              {flowsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin" />
                  <span className="ml-2">Loading flows...</span>
                </div>
              ) : flows.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-semibold mb-2">No Discovery Flows</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first discovery flow to get started with V2 functionality.
                  </p>
                  <Button onClick={handleCreateFlow}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Demo Flow
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid gap-4">
                    {flows.map((flow: any) => (
                      <div
                        key={flow.flow_id}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${
                          selectedFlowId === flow.flow_id ? 'border-blue-500 bg-blue-50' : ''
                        }`}
                        onClick={() => setSelectedFlowId(flow.flow_id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div>
                              <div className="font-medium">{flow.flow_name}</div>
                              <div className="text-sm text-muted-foreground">
                                Flow ID: {flow.flow_id}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={
                              flow.status === 'completed' ? 'default' : 
                              flow.status === 'in_progress' ? 'secondary' : 'outline'
                            }>
                              {flow.status}
                            </Badge>
                            <div className="text-sm text-muted-foreground">
                              {flow.progress_percentage}%
                            </div>
                            {flow.is_complete && <CheckCircle className="h-4 w-4 text-green-600" />}
                          </div>
                        </div>
                        
                        <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                          <span>
                            Readiness Score: {flow.migration_readiness_score}%
                          </span>
                          <span>
                            Assessment Ready: {flow.assessment_ready ? 'Yes' : 'No'}
                          </span>
                          <span>
                            Created: {new Date(flow.created_at).toLocaleDateString()}
                          </span>
                        </div>

                        {flow.next_phase && (
                          <div className="mt-2">
                            <Badge variant="outline" className="text-xs">
                              Next: {DiscoveryFlowV2Utils.formatPhaseDisplayName(flow.next_phase)}
                            </Badge>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {selectedFlowId && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Selected flow: <strong>{selectedFlowId}</strong>. 
                        Switch to the Dashboard tab to manage this flow.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-4">
          {selectedFlowId ? (
            <DiscoveryFlowV2Dashboard
              flowId={selectedFlowId}
              enableRealTimeUpdates={true}
              onFlowComplete={handleFlowComplete}
            />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Flow Selected</h3>
                <p className="text-muted-foreground">
                  Select a discovery flow from the Flow Management tab to view its dashboard.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
} 