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

interface FlowSummary {
  flow_id: string;
  engagement_name: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
  current_phase: string;
  started_at: string;
  estimated_completion: string;
  crew_count: number;
  active_agents: number;
  data_sources: number;
  success_criteria_met: number;
  total_success_criteria: number;
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
  const [activeFlows, setActiveFlows] = useState<FlowSummary[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [crewPerformance, setCrewPerformance] = useState<CrewPerformanceMetrics[]>([]);
  const [platformAlerts, setPlatformAlerts] = useState<PlatformAlert[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      // In real implementation, these would be separate API calls
      // For now, using mock data

      // Mock active flows
      setActiveFlows([
        {
          flow_id: 'flow-001',
          engagement_name: 'Customer A - CMDB Migration',
          status: 'running',
          progress: 65,
          current_phase: 'Inventory Building',
          started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          estimated_completion: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(),
          crew_count: 6,
          active_agents: 18,
          data_sources: 4,
          success_criteria_met: 12,
          total_success_criteria: 18
        },
        {
          flow_id: 'flow-002',
          engagement_name: 'Customer B - App Discovery',
          status: 'running',
          progress: 30,
          current_phase: 'Data Cleansing',
          started_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          estimated_completion: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
          crew_count: 6,
          active_agents: 18,
          data_sources: 2,
          success_criteria_met: 6,
          total_success_criteria: 18
        },
        {
          flow_id: 'flow-003',
          engagement_name: 'Customer C - Infrastructure Assessment',
          status: 'completed',
          progress: 100,
          current_phase: 'Completed',
          started_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          estimated_completion: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          crew_count: 6,
          active_agents: 0,
          data_sources: 6,
          success_criteria_met: 18,
          total_success_criteria: 18
        }
      ]);

      // Mock system metrics
      setSystemMetrics({
        total_active_flows: 2,
        total_agents: 36,
        memory_utilization_gb: 4.2,
        total_memory_gb: 8.0,
        collaboration_events_today: 247,
        success_rate: 0.94,
        avg_completion_time_hours: 3.2,
        knowledge_bases_loaded: 12
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
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [selectedTimeRange]);

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
            <Button onClick={() => navigate('/discovery/enhanced-import')}>
              <Plus className="h-4 w-4 mr-2" />
              New Flow
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeFlows.filter(flow => flow.status === 'running').map((flow) => (
              <div key={flow.flow_id} className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                   onClick={() => navigate(`/discovery/flow/${flow.flow_id}`)}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(flow.status)}
                    <div>
                      <h3 className="font-medium">{flow.engagement_name}</h3>
                      <p className="text-sm text-gray-600">Flow ID: {flow.flow_id}</p>
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
                    <span>ETA: {formatTimeAgo(flow.estimated_completion)}</span>
                  </div>
                  <Progress value={flow.progress} className="h-2" />
                </div>
              </div>
            ))}
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
              <Button onClick={() => navigate('/discovery/enhanced-import')}>
                <Plus className="h-4 w-4 mr-2" />
                New Discovery Flow
              </Button>
            </div>
          </div>

          {/* Status Indicator */}
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
                           onClick={() => navigate(`/discovery/flow/${flow.flow_id}`)}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getStatusIcon(flow.status)}
                            <div>
                              <h3 className="font-medium">{flow.engagement_name}</h3>
                              <p className="text-sm text-gray-600">
                                Started: {formatTimeAgo(flow.started_at)} • 
                                {flow.status === 'running' ? ' ETA: ' + formatTimeAgo(flow.estimated_completion) : ' Completed: ' + formatTimeAgo(flow.estimated_completion)}
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
    </div>
  );
};

export default EnhancedDiscoveryDashboard; 