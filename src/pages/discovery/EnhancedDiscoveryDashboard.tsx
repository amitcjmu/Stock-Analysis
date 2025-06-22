import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Brain, 
  Activity, 
  Users, 
  Target, 
  TrendingUp, 
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Database,
  Network,
  MessageSquare,
  Eye,
  Play,
  Plus,
  Filter,
  RefreshCw,
  ArrowRight,
  BarChart3,
  Lightbulb,
  Shield,
  Layers,
  Settings
} from 'lucide-react';

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '@/config/api';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';

// Flow Management Components
import { 
  useIncompleteFlowDetection, 
  useFlowResumption, 
  useFlowDeletion 
} from '@/hooks/discovery/useIncompleteFlowDetection';
import { IncompleteFlowManager } from '@/components/discovery/IncompleteFlowManager';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface FlowSummary {
  flow_id: string;
  session_id?: string;
  engagement_name: string;
  engagement_id: string;
  client_name: string;
  client_id: string;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'not_found';
  progress: number;
  current_phase: string;
  started_at: string;
  estimated_completion?: string;
  last_updated?: string;
  crew_count: number;
  active_agents: number;
  data_sources: number;
  success_criteria_met: number;
  total_success_criteria: number;
  flow_type: 'discovery' | 'assessment' | 'planning' | 'execution';
}

interface SystemMetrics {
  total_active_flows: number;
  total_agents: number;
  memory_utilization_gb: number;
  total_memory_gb: number;
  collaboration_events_today: number;
  success_rate: number;
  avg_completion_time_hours: number;
  knowledge_bases_loaded: number;
}

interface CrewPerformanceMetrics {
  crew_name: string;
  total_executions: number;
  success_rate: number;
  avg_duration_minutes: number;
  collaboration_score: number;
  efficiency_trend: number;
  current_active: number;
}

interface PlatformAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  flow_id?: string;
  action_required: boolean;
}

const EnhancedDiscoveryDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  
  // Unified discovery flow hook
  const {
    flowState,
    isLoading: flowLoading,
    error: flowError,
    isHealthy,
    refreshFlow
  } = useUnifiedDiscoveryFlow();
  
  const [activeFlows, setActiveFlows] = useState<FlowSummary[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [crewPerformance, setCrewPerformance] = useState<CrewPerformanceMetrics[]>([]);
  const [platformAlerts, setPlatformAlerts] = useState<PlatformAlert[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);

  // Flow Management State
  const { data: incompleteFlowsData } = useIncompleteFlowDetection();
  const flowResumption = useFlowResumption();
  const flowDeletion = useFlowDeletion();
  const [showIncompleteFlowManager, setShowIncompleteFlowManager] = useState(false);
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🔍 Fetching dashboard data for context:', {
        user: user?.id,
        client: client?.id,
        engagement: engagement?.id
      });

      // Fetch real-time active flows from multiple sources
      const [discoveryFlowsResponse, dataImportsResponse] = await Promise.allSettled([
        // Get active Discovery flows
        apiCall('/api/v1/discovery/flow/active', {
          method: 'GET',
          headers: getAuthHeaders()
        }),
        // Get data import sessions (for discovering flows)
        apiCall('/api/v1/data-import/latest-import', {
          method: 'GET',
          headers: getAuthHeaders()
        })
      ]);

      const allFlows: FlowSummary[] = [];

      // Process Discovery flows
      if (discoveryFlowsResponse.status === 'fulfilled' && discoveryFlowsResponse.value) {
        const discoveryData = discoveryFlowsResponse.value;
        console.log('📊 Discovery flows data:', discoveryData);
        console.log('📊 Discovery flows raw response:', JSON.stringify(discoveryData, null, 2));

        if (discoveryData.flow_details && Array.isArray(discoveryData.flow_details)) {
          console.log(`📊 Processing ${discoveryData.flow_details.length} flows...`);
          for (const flow of discoveryData.flow_details) {
            try {
              console.log('📊 Processing flow:', flow);
              allFlows.push({
                flow_id: flow.flow_id,
                session_id: flow.session_id || flow.flow_id,
                engagement_name: flow.engagement_name || `${flow.client_name || 'Unknown'} - Discovery`,
                engagement_id: flow.engagement_id || 'unknown',
                client_name: flow.client_name || 'Unknown Client',
                client_id: flow.client_id || 'unknown',
                status: flow.status || 'running',
                progress: flow.progress || 0,
                current_phase: flow.current_phase || 'initialization',
                started_at: flow.start_time || new Date().toISOString(),
                estimated_completion: flow.estimated_completion,
                last_updated: flow.last_updated || new Date().toISOString(),
                crew_count: 6, // Standard Discovery flow has 6 crews
                active_agents: flow.active_agents || 18,
                data_sources: flow.data_sources || 1,
                success_criteria_met: flow.success_criteria_met || 0,
                total_success_criteria: 18, // Standard Discovery flow criteria
                flow_type: 'discovery'
              });
            } catch (flowError) {
              console.warn('Failed to process flow:', flow, flowError);
            }
          }
        } else {
          console.warn('📊 No flow_details found or not an array:', discoveryData);
        }
      } else {
        console.warn('📊 Discovery flows response failed or empty:', discoveryFlowsResponse);
      }

      // Process Data Import sessions to find additional flows
      if (dataImportsResponse.status === 'fulfilled' && dataImportsResponse.value) {
        const importData = dataImportsResponse.value;
        console.log('📊 Data import data:', importData);

        if (importData.success && importData.data_import) {
          const dataImport = importData.data_import;
          
          // Check if this import has an active discovery flow
          if (dataImport.id && !allFlows.find(f => f.session_id === dataImport.id)) {
            try {
              // Get flow status for this import session
              const flowStatusResponse = await apiCall(`/api/v1/discovery/flow/status?session_id=${dataImport.id}`, {
                method: 'GET',
                headers: getAuthHeaders()
              });

              if (flowStatusResponse && flowStatusResponse.flow_state) {
                const flowState = flowStatusResponse.flow_state;
                
                allFlows.push({
                  flow_id: dataImport.id,
                  session_id: dataImport.id,
                  engagement_name: `${client?.name || 'Current'} - Discovery`,
                  engagement_id: engagement?.id || 'current',
                  client_name: client?.name || 'Current Client',
                  client_id: client?.id || 'current',
                  status: flowState.status === 'completed' ? 'completed' : 'running',
                  progress: flowState.progress_percentage || 0,
                  current_phase: flowState.current_phase || 'field_mapping',
                  started_at: flowState.started_at || dataImport.created_at,
                  last_updated: flowState.updated_at || new Date().toISOString(),
                  crew_count: 6,
                  active_agents: 18,
                  data_sources: 1,
                  success_criteria_met: Object.values(flowState.phase_completion || {}).filter(Boolean).length,
                  total_success_criteria: 6, // 6 phases in discovery
                  flow_type: 'discovery'
                });
              }
            } catch (statusError) {
              console.warn('Failed to get flow status for import:', dataImport.id, statusError);
            }
          }
        }
      }

      setActiveFlows(allFlows);
      console.log('✅ Processed flows:', allFlows);

      // Calculate real system metrics from flows
      const runningFlows = allFlows.filter(f => f.status === 'running');
      const completedFlows = allFlows.filter(f => f.status === 'completed');
      const totalActiveAgents = runningFlows.reduce((sum, flow) => sum + flow.active_agents, 0);
      const successRate = allFlows.length > 0 ? completedFlows.length / allFlows.length : 0;
      
      setSystemMetrics({
        total_active_flows: runningFlows.length,
        total_agents: totalActiveAgents,
        memory_utilization_gb: 4.2, // TODO: Get from monitoring API
        total_memory_gb: 8.0,
        collaboration_events_today: totalActiveAgents * 12, // Estimate based on active agents
        success_rate: successRate,
        avg_completion_time_hours: 3.2, // TODO: Calculate from completed flows
        knowledge_bases_loaded: 12 // TODO: Get from knowledge base API
      });

      // Mock crew performance
      setCrewPerformance([
        {
          crew_name: 'Field Mapping Crew',
          total_executions: 15,
          success_rate: 0.96,
          avg_duration_minutes: 12,
          collaboration_score: 8.7,
          efficiency_trend: 0.15,
          current_active: 2
        },
        {
          crew_name: 'Data Cleansing Crew',
          total_executions: 12,
          success_rate: 0.92,
          avg_duration_minutes: 18,
          collaboration_score: 8.3,
          efficiency_trend: 0.08,
          current_active: 2
        },
        {
          crew_name: 'Inventory Building Crew',
          total_executions: 10,
          success_rate: 0.90,
          avg_duration_minutes: 25,
          collaboration_score: 9.1,
          efficiency_trend: 0.22,
          current_active: 1
        },
        {
          crew_name: 'App-Server Dependency Crew',
          total_executions: 8,
          success_rate: 0.88,
          avg_duration_minutes: 20,
          collaboration_score: 8.9,
          efficiency_trend: 0.12,
          current_active: 1
        },
        {
          crew_name: 'App-App Dependency Crew',
          total_executions: 7,
          success_rate: 0.86,
          avg_duration_minutes: 22,
          collaboration_score: 8.5,
          efficiency_trend: 0.05,
          current_active: 1
        },
        {
          crew_name: 'Technical Debt Crew',
          total_executions: 6,
          success_rate: 0.94,
          avg_duration_minutes: 35,
          collaboration_score: 9.3,
          efficiency_trend: 0.18,
          current_active: 1
        }
      ]);

      // Mock platform alerts
      setPlatformAlerts([
        {
          id: 'alert-001',
          type: 'warning',
          title: 'High Memory Utilization',
          message: 'Memory usage at 75%. Consider optimization.',
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          action_required: true
        },
        {
          id: 'alert-002',
          type: 'success',
          title: 'Flow Completed Successfully',
          message: 'Customer C flow completed with 100% success criteria met.',
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          flow_id: 'flow-003',
          action_required: false
        },
        {
          id: 'alert-003',
          type: 'info',
          title: 'New Knowledge Pattern Identified',
          message: 'Field Mapping Crew discovered new pattern in CMDB data.',
          timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          action_required: false
        }
      ]);

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch dashboard data');
      
      // Set fallback data to prevent UI from breaking
      setActiveFlows([]);
      setSystemMetrics({
        total_active_flows: 0,
        total_agents: 0,
        memory_utilization_gb: 0,
        total_memory_gb: 8.0,
        collaboration_events_today: 0,
        success_rate: 0,
        avg_completion_time_hours: 0,
        knowledge_bases_loaded: 0
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Removed automatic polling - now using manual refresh only
  }, [selectedTimeRange]);

  // Manual refresh function
  const handleManualRefresh = async () => {
    await fetchDashboardData();
    setLastUpdated(new Date());
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'paused':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      running: 'default',
      completed: 'outline',
      failed: 'destructive',
      paused: 'secondary'
    } as const;
    
    const colors = {
      running: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
      paused: 'bg-yellow-100 text-yellow-700'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}
             className={colors[status as keyof typeof colors] || ''}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      default:
        return <Lightbulb className="h-4 w-4 text-blue-500" />;
    }
  };

  const formatTimeAgo = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Dashboard Header with Manual Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Discovery Dashboard</h2>
          <p className="text-sm text-gray-600">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <Button
          onClick={handleManualRefresh}
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {/* Unified Flow Status */}
      {flowState && (
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Brain className="mr-2 h-5 w-5 text-blue-500" />
              Current Unified Discovery Flow
            </CardTitle>
            <CardDescription>
              Session: {flowState.session_id} | Status: {flowState.status}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Progress</span>
                <span className="text-sm text-gray-600">{flowState.progress_percentage}%</span>
              </div>
              <Progress value={flowState.progress_percentage} className="w-full" />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Current Phase:</span>
                  <div className="text-blue-600">{flowState.current_phase}</div>
                </div>
                <div>
                  <span className="font-medium">Completed Phases:</span>
                  <div className="text-green-600">
                    {Object.values(flowState.phase_completion || {}).filter(Boolean).length}/6
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refreshFlow}
                  disabled={flowLoading}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${flowLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/discovery')}
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Details
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Metrics */}
      {systemMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Active Flows
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.total_active_flows}</div>
              <p className="text-xs text-gray-600">{systemMetrics.total_agents} total agents</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Database className="h-4 w-4" />
                Memory Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemMetrics.memory_utilization_gb.toFixed(1)}GB
              </div>
              <p className="text-xs text-gray-600">of {systemMetrics.total_memory_gb}GB</p>
              <Progress 
                value={(systemMetrics.memory_utilization_gb / systemMetrics.total_memory_gb) * 100} 
                className="h-2 mt-2" 
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Collaborations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.collaboration_events_today}</div>
              <p className="text-xs text-gray-600">events today</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Success Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(systemMetrics.success_rate * 100).toFixed(1)}%</div>
              <p className="text-xs text-gray-600">avg completion: {systemMetrics.avg_completion_time_hours.toFixed(1)}h</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Flows */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Active Discovery Flows
            </CardTitle>
            <Button onClick={() => navigate('/discovery/import')}>
              <Plus className="h-4 w-4 mr-2" />
              New Flow
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeFlows.filter(flow => flow.status === 'running').length === 0 ? (
              <div className="text-center py-8">
                <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Discovery Flows</h3>
                <p className="text-gray-600 mb-4">
                  Start a new Discovery Flow by importing your CMDB or asset data.
                </p>
                <Button onClick={() => navigate('/discovery/import')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Import Data & Start Discovery
                </Button>
              </div>
            ) : (
              activeFlows.filter(flow => flow.status === 'running').map((flow) => (
              <div key={flow.flow_id} className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                   onClick={() => navigate(`/discovery/attribute-mapping/${flow.session_id || flow.flow_id}`)}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(flow.status)}
                    <div>
                      <h3 className="font-medium">{flow.engagement_name}</h3>
                      <p className="text-sm text-gray-600">
                        {flow.client_name} • {flow.flow_type.charAt(0).toUpperCase() + flow.flow_type.slice(1)} Flow
                      </p>
                      <p className="text-xs text-gray-500">Session: {flow.session_id || flow.flow_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(flow.status)}
                    <ArrowRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm mb-3">
                  <div>
                    <span className="font-medium">Progress:</span>
                    <div className="text-blue-600">{flow.progress}%</div>
                  </div>
                  <div>
                    <span className="font-medium">Phase:</span>
                    <div>{flow.current_phase}</div>
                  </div>
                  <div>
                    <span className="font-medium">Agents:</span>
                    <div>{flow.active_agents} active</div>
                  </div>
                  <div>
                    <span className="font-medium">Success Criteria:</span>
                    <div>{flow.success_criteria_met}/{flow.total_success_criteria}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Overall Progress</span>
                    <span>ETA: {flow.estimated_completion ? formatTimeAgo(flow.estimated_completion) : 'Calculating...'}</span>
                  </div>
                  <Progress value={flow.progress} className="h-2" />
                </div>
              </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Recent Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {platformAlerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                {getAlertIcon(alert.type)}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm">{alert.title}</h4>
                    <span className="text-xs text-gray-500">{formatTimeAgo(alert.timestamp)}</span>
                  </div>
                  <p className="text-sm text-gray-600">{alert.message}</p>
                  {alert.action_required && (
                    <Badge variant="destructive" className="text-xs mt-2">
                      Action Required
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const PerformanceTab = () => (
    <div className="space-y-6">
      {/* Performance Tab Header with Manual Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Performance Analytics</h2>
          <p className="text-sm text-gray-600">
            Crew performance and system metrics for the last {selectedTimeRange}
          </p>
        </div>
        <Button
          onClick={handleManualRefresh}
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {/* Crew Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Crew Performance Analytics
          </CardTitle>
          <CardDescription>Performance metrics across all crews in the last {selectedTimeRange}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {crewPerformance.map((crew, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium">{crew.crew_name}</h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {crew.current_active} active
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {crew.total_executions} total runs
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Success Rate:</span>
                    <div className="text-green-600">{(crew.success_rate * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <span className="font-medium">Avg Duration:</span>
                    <div>{crew.avg_duration_minutes}m</div>
                  </div>
                  <div>
                    <span className="font-medium">Collaboration:</span>
                    <div>{crew.collaboration_score.toFixed(1)}/10</div>
                  </div>
                  <div>
                    <span className="font-medium">Efficiency Trend:</span>
                    <div className={crew.efficiency_trend > 0 ? 'text-green-600' : 'text-red-600'}>
                      {crew.efficiency_trend > 0 ? '+' : ''}{(crew.efficiency_trend * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="mt-3 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Success Rate</span>
                    <span>{(crew.success_rate * 100).toFixed(1)}%</span>
                  </div>
                  <Progress value={crew.success_rate * 100} className="h-1" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Performance */}
      {systemMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">System Resources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Memory Utilization</span>
                  <span>{((systemMetrics.memory_utilization_gb / systemMetrics.total_memory_gb) * 100).toFixed(1)}%</span>
                </div>
                <Progress value={(systemMetrics.memory_utilization_gb / systemMetrics.total_memory_gb) * 100} className="h-2" />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium">Active Agents</div>
                  <div className="text-xl font-bold">{systemMetrics.total_agents}</div>
                </div>
                <div>
                  <div className="font-medium">Knowledge Bases</div>
                  <div className="text-xl font-bold">{systemMetrics.knowledge_bases_loaded}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Operational Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium">Success Rate</div>
                  <div className="text-xl font-bold text-green-600">{(systemMetrics.success_rate * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="font-medium">Avg Completion</div>
                  <div className="text-xl font-bold">{systemMetrics.avg_completion_time_hours.toFixed(1)}h</div>
                </div>
              </div>
              <div>
                <div className="font-medium mb-2">Collaboration Events Today</div>
                <div className="text-2xl font-bold text-blue-600">{systemMetrics.collaboration_events_today}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced Discovery Dashboard</h1>
              <p className="mt-2 text-gray-600">
                Real-time monitoring of intelligent discovery flows, crew performance, and system analytics
              </p>
            </div>
            <div className="flex items-center gap-4 mt-4 md:mt-0">
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium">Time Range:</label>
                <select 
                  value={selectedTimeRange} 
                  onChange={(e) => setSelectedTimeRange(e.target.value)}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="1h">Last Hour</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                </select>
              </div>
              <Button variant="outline" size="sm" onClick={fetchDashboardData} disabled={isLoading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button onClick={() => navigate('/discovery/import')}>
                <Plus className="h-4 w-4 mr-2" />
                New Discovery Flow
              </Button>
            </div>
          </div>

          {/* Status Indicator */}
          {error ? (
            <div className="mb-6 p-4 bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="font-medium text-red-800">Connection Error</p>
                    <p className="text-sm text-red-600">
                      {error} • Showing fallback data
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={fetchDashboardData}>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div>
                    <p className="font-medium text-green-800">Platform Status: Operational</p>
                    <p className="text-sm text-green-600">
                      All systems running optimally • Last updated: {lastUpdated.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <Badge variant="outline" className="bg-white">
                  <Activity className="h-3 w-3 mr-1" />
                  {systemMetrics?.total_active_flows || 0} active flows
                </Badge>
              </div>
            </div>
          )}

          {/* Incomplete Flows Alert */}
          {hasIncompleteFlows && (
            <div className="mb-6 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <div>
                    <p className="font-medium text-yellow-800">
                      {incompleteFlows.length} Incomplete Discovery Flow{incompleteFlows.length > 1 ? 's' : ''} Found
                    </p>
                    <p className="text-sm text-yellow-700">
                      These flows require attention before new data imports can proceed
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-white text-yellow-700">
                    {incompleteFlows.filter(f => f.status === 'failed').length} failed
                  </Badge>
                  <Badge variant="outline" className="bg-white text-yellow-700">
                    {incompleteFlows.filter(f => f.status === 'paused').length} paused
                  </Badge>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setShowIncompleteFlowManager(true)}
                    className="bg-white hover:bg-yellow-50"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Manage Flows
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Dashboard Tabs */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Performance
              </TabsTrigger>
              <TabsTrigger value="flows" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                All Flows
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <OverviewTab />
            </TabsContent>

            <TabsContent value="performance">
              <PerformanceTab />
            </TabsContent>

            <TabsContent value="flows">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    All Discovery Flows
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {activeFlows.map((flow) => (
                      <div key={flow.flow_id} className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                           onClick={() => navigate(`/discovery/attribute-mapping/${flow.session_id || flow.flow_id}`)}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getStatusIcon(flow.status)}
                            <div>
                              <h3 className="font-medium">{flow.engagement_name}</h3>
                              <p className="text-sm text-gray-600">
                                {flow.client_name} • Started: {formatTimeAgo(flow.started_at)}
                                {flow.estimated_completion && flow.status === 'running' && (
                                  <> • ETA: {formatTimeAgo(flow.estimated_completion)}</>
                                )}
                                {flow.status === 'completed' && flow.estimated_completion && (
                                  <> • Completed: {formatTimeAgo(flow.estimated_completion)}</>
                                )}
                              </p>
                              <p className="text-xs text-gray-500">
                                {flow.flow_type.charAt(0).toUpperCase() + flow.flow_type.slice(1)} Flow • 
                                Session: {flow.session_id || flow.flow_id}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusBadge(flow.status)}
                            <Button variant="outline" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 text-sm">
                          <div>
                            <span className="font-medium">Progress:</span>
                            <div>{flow.progress}%</div>
                          </div>
                          <div>
                            <span className="font-medium">Phase:</span>
                            <div>{flow.current_phase}</div>
                          </div>
                          <div>
                            <span className="font-medium">Crews:</span>
                            <div>{flow.crew_count}</div>
                          </div>
                          <div>
                            <span className="font-medium">Agents:</span>
                            <div>{flow.active_agents}</div>
                          </div>
                          <div>
                            <span className="font-medium">Sources:</span>
                            <div>{flow.data_sources}</div>
                          </div>
                        </div>

                        <div className="mt-3">
                          <Progress value={flow.progress} className="h-2" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Incomplete Flow Management Modal */}
      <Dialog open={showIncompleteFlowManager} onOpenChange={setShowIncompleteFlowManager}>
        <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Incomplete Discovery Flows</DialogTitle>
          </DialogHeader>
          <IncompleteFlowManager 
            flows={incompleteFlows}
            onContinueFlow={(sessionId) => flowResumption.mutate(sessionId)}
            onDeleteFlow={(sessionId) => flowDeletion.mutate(sessionId)}
            onBatchDelete={(sessionIds) => {
              // Batch delete logic
              sessionIds.forEach(id => flowDeletion.mutate(id));
            }}
            onViewDetails={(sessionId, phase) => {
              const phaseRoutes = {
                'field_mapping': `/discovery/attribute-mapping/${sessionId}`,
                'data_cleansing': `/discovery/data-cleansing/${sessionId}`,
                'asset_inventory': `/discovery/asset-inventory/${sessionId}`,
                'dependency_analysis': `/discovery/dependencies/${sessionId}`,
                'tech_debt_analysis': `/discovery/technical-debt/${sessionId}`
              };
              const route = phaseRoutes[phase as keyof typeof phaseRoutes] || `/discovery/enhanced-dashboard`;
              navigate(route);
            }}
            isLoading={flowResumption.isPending || flowDeletion.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EnhancedDiscoveryDashboard; 