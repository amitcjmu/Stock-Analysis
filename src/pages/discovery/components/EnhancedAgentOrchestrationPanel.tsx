import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Users, 
  Database, 
  Search, 
  MapPin, 
  Shield,
  Activity,
  Brain,
  Zap,
  Target,
  Crown,
  Link,
  TrendingUp,
  Lightbulb,
  Network,
  BarChart3,
  Settings,
  MessageSquare,
  Eye,
  Timer,
  Cpu
} from 'lucide-react';

interface AgentInfo {
  name: string;
  role: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  isManager?: boolean;
  collaborations?: string[];
  currentTask?: string;
  performance?: {
    tasks_completed: number;
    success_rate: number;
    avg_duration: number;
  };
}

interface CrewProgress {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  agents: AgentInfo[];
  description: string;
  icon: React.ReactNode;
  results?: any;
  currentTask?: string;
  manager?: string;
  collaboration_status?: {
    intra_crew: number;
    cross_crew: number;
    memory_sharing: boolean;
    knowledge_utilization: number;
  };
  planning_status?: {
    strategy: string;
    coordination_score: number;
    adaptive_triggers: string[];
  };
}

interface CollaborationData {
  total_collaborations: number;
  active_collaborations: number;
  cross_crew_insights: number;
  memory_utilization: number;
  knowledge_sharing_score: number;
}

interface PlanningData {
  coordination_strategy: string;
  success_criteria_met: number;
  adaptive_adjustments: number;
  optimization_score: number;
  predicted_completion: string;
}

interface EnhancedAgentOrchestrationPanelProps {
  sessionId: string;
  flowState: any;
  onStatusUpdate?: (status: any) => void;
}

const EnhancedAgentOrchestrationPanel: React.FC<EnhancedAgentOrchestrationPanelProps> = ({
  sessionId,
  flowState,
  onStatusUpdate
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [collaborationData, setCollaborationData] = useState<CollaborationData | null>(null);
  const [planningData, setPlanningData] = useState<PlanningData | null>(null);
  const [memoryAnalytics, setMemoryAnalytics] = useState<any>(null);
  
  const [crews, setCrews] = useState<CrewProgress[]>([
    {
      name: 'Field Mapping Crew',
      status: 'pending',
      progress: 0,
      manager: 'Field Mapping Manager',
      agents: [
        {
          name: 'Field Mapping Manager',
          role: 'Coordinates field mapping analysis with hierarchical oversight',
          status: 'idle',
          isManager: true,
          collaborations: ['Schema Analysis Expert', 'Attribute Mapping Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Schema Analysis Expert',
          role: 'Analyzes data structure semantics and field relationships',
          status: 'idle',
          collaborations: ['Field Mapping Manager', 'Attribute Mapping Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Attribute Mapping Specialist',
          role: 'Creates precise field mappings with confidence scoring',
          status: 'idle',
          collaborations: ['Field Mapping Manager', 'Schema Analysis Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'FOUNDATION PHASE: Uses hierarchical coordination and shared memory to map fields to standard migration attributes',
      icon: <MapPin className="h-5 w-5" />,
      currentTask: 'Ready to analyze data structure...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'hierarchical_with_memory',
        coordination_score: 0,
        adaptive_triggers: []
      }
    },
    {
      name: 'Data Cleansing Crew',
      status: 'pending',
      progress: 0,
      manager: 'Data Quality Manager',
      agents: [
        {
          name: 'Data Quality Manager',
          role: 'Orchestrates comprehensive data quality assurance',
          status: 'idle',
          isManager: true,
          collaborations: ['Data Validation Expert', 'Data Standardization Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Data Validation Expert',
          role: 'Validates data quality using field mapping insights',
          status: 'idle',
          collaborations: ['Data Quality Manager', 'Data Standardization Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Data Standardization Specialist',
          role: 'Standardizes data formats with field-aware processing',
          status: 'idle',
          collaborations: ['Data Quality Manager', 'Data Validation Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'QUALITY ASSURANCE: Uses field mapping insights from shared memory for intelligent data cleansing and validation',
      icon: <Database className="h-5 w-5" />,
      currentTask: 'Waiting for field mapping completion...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'memory_enhanced_validation',
        coordination_score: 0,
        adaptive_triggers: []
      }
    },
    {
      name: 'Inventory Building Crew',
      status: 'pending', 
      progress: 0,
      manager: 'Inventory Manager',
      agents: [
        {
          name: 'Inventory Manager',
          role: 'Coordinates multi-domain asset classification strategy',
          status: 'idle',
          isManager: true,
          collaborations: ['Server Expert', 'Application Expert', 'Device Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Server Classification Expert',
          role: 'Classifies server infrastructure with cross-domain insights',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Application Expert', 'Device Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Discovery Expert',
          role: 'Identifies applications using field and cleansing insights',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Server Expert', 'Device Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Device Classification Expert',
          role: 'Classifies network devices with domain collaboration',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Server Expert', 'Application Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'MULTI-DOMAIN CLASSIFICATION: Cross-domain collaboration and shared memory enable comprehensive asset intelligence',
      icon: <Search className="h-5 w-5" />,
      currentTask: 'Waiting for data cleansing...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'cross_domain_intelligence',
        coordination_score: 0,
        adaptive_triggers: []
      }
    },
    {
      name: 'App-Server Dependency Crew',
      status: 'pending',
      progress: 0,
      manager: 'Dependency Manager',
      agents: [
        {
          name: 'Dependency Manager',
          role: 'Orchestrates hosting relationship analysis strategy',
          status: 'idle',
          isManager: true,
          collaborations: ['Topology Expert', 'Relationship Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Topology Expert',
          role: 'Maps application hosting using inventory intelligence',
          status: 'idle',
          collaborations: ['Dependency Manager', 'Relationship Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Infrastructure Relationship Analyst',
          role: 'Analyzes server-application relationships with shared insights',
          status: 'idle',
          collaborations: ['Dependency Manager', 'Topology Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'HOSTING RELATIONSHIPS: Leverages asset inventory intelligence to map application-to-server hosting dependencies',
      icon: <Activity className="h-5 w-5" />,
      currentTask: 'Waiting for inventory building...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'inventory_intelligent_hosting',
        coordination_score: 0,
        adaptive_triggers: []
      }
    },
    {
      name: 'App-App Dependency Crew',
      status: 'pending',
      progress: 0,
      manager: 'Integration Manager',
      agents: [
        {
          name: 'Integration Manager',
          role: 'Coordinates application integration dependency analysis',
          status: 'idle',
          isManager: true,
          collaborations: ['Integration Expert', 'API Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Integration Expert',
          role: 'Maps communication patterns using hosting intelligence',
          status: 'idle',
          collaborations: ['Integration Manager', 'API Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'API Dependency Analyst',
          role: 'Analyzes service dependencies with integration intelligence',
          status: 'idle',
          collaborations: ['Integration Manager', 'Integration Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'INTEGRATION ANALYSIS: Uses hosting relationship intelligence for comprehensive application integration mapping',
      icon: <Zap className="h-5 w-5" />,
      currentTask: 'Waiting for app-server dependencies...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'integration_intelligent',
        coordination_score: 0,
        adaptive_triggers: []
      }
    },
    {
      name: 'Technical Debt Crew',
      status: 'pending',
      progress: 0,
      manager: 'Technical Debt Manager',
      agents: [
        {
          name: 'Technical Debt Manager',
          role: 'Coordinates comprehensive 6R strategy preparation',
          status: 'idle',
          isManager: true,
          collaborations: ['Legacy Analyst', 'Modernization Expert', 'Risk Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Legacy Technology Analyst',
          role: 'Assesses technology stack using all previous insights',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Modernization Expert', 'Risk Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Modernization Strategy Expert',
          role: 'Recommends 6R strategies using comprehensive intelligence',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Legacy Analyst', 'Risk Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Risk Assessment Specialist',
          role: 'Evaluates migration risks with full dependency intelligence',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Legacy Analyst', 'Modernization Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: '6R PREPARATION: Synthesizes all crew insights for comprehensive 6R migration strategy with complete risk intelligence',
      icon: <Target className="h-5 w-5" />,
      currentTask: 'Waiting for dependency analysis...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'comprehensive_synthesis',
        coordination_score: 0,
        adaptive_triggers: []
      }
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('Initializing...');

  // Fetch enhanced monitoring data
  useEffect(() => {
    const fetchEnhancedData = async () => {
      if (!flowState?.flow_id) return;

      try {
        // Fetch collaboration analytics
        const collaborationResponse = await fetch(`/api/v1/discovery/flow/collaboration/analytics/${flowState.flow_id}`);
        if (collaborationResponse.ok) {
          const collaborationData = await collaborationResponse.json();
          setCollaborationData({
            total_collaborations: collaborationData.agent_collaboration?.total_events || 0,
            active_collaborations: collaborationData.agent_collaboration?.active_collaborations || 0,
            cross_crew_insights: collaborationData.cross_crew_sharing?.shared_insights || 0,
            memory_utilization: collaborationData.cross_crew_sharing?.memory_utilization || 0,
            knowledge_sharing_score: collaborationData.knowledge_utilization?.effectiveness_score || 0
          });
        }

        // Fetch planning intelligence
        const planningResponse = await fetch(`/api/v1/discovery/flow/planning/intelligence/${flowState.flow_id}`);
        if (planningResponse.ok) {
          const planningData = await planningResponse.json();
          setPlanningData({
            coordination_strategy: planningData.coordination_plan?.strategy || 'Not set',
            success_criteria_met: planningData.coordination_plan?.success_criteria_met || 0,
            adaptive_adjustments: planningData.dynamic_planning?.adjustments_count || 0,
            optimization_score: planningData.planning_intelligence?.optimization_score || 0,
            predicted_completion: planningData.planning_intelligence?.predicted_completion || 'Unknown'
          });
        }

        // Fetch memory analytics
        const memoryResponse = await fetch(`/api/v1/discovery/flow/memory/analytics/${flowState.flow_id}?report_type=summary`);
        if (memoryResponse.ok) {
          const memoryData = await memoryResponse.json();
          setMemoryAnalytics(memoryData);
        }

        // Fetch detailed crew monitoring
        const crewResponse = await fetch(`/api/v1/discovery/flow/crews/monitoring/${flowState.flow_id}`);
        if (crewResponse.ok) {
          const crewData = await crewResponse.json();
          updateCrewsWithMonitoringData(crewData);
        }
      } catch (error) {
        console.error('Failed to fetch enhanced monitoring data:', error);
      }
    };

    fetchEnhancedData();
    const interval = setInterval(fetchEnhancedData, 5000);
    return () => clearInterval(interval);
  }, [flowState?.flow_id]);

  const updateCrewsWithMonitoringData = (monitoringData: any) => {
    const updatedCrews = crews.map(crew => {
      const crewKey = crew.name.toLowerCase().replace(' crew', '').replace(/[\s-]/g, '_');
      const crewMonitoring = monitoringData.crews?.[crewKey];
      
      if (crewMonitoring) {
        return {
          ...crew,
          status: crewMonitoring.status === 'completed' ? 'completed' : 
                 crewMonitoring.status === 'failed' ? 'failed' :
                 crewMonitoring.progress > 0 ? 'running' : 'pending',
          progress: crewMonitoring.progress || 0,
          currentTask: crewMonitoring.current_task || crew.currentTask,
          agents: crew.agents.map((agent, index) => ({
            ...agent,
            status: crewMonitoring.agents?.[index]?.status || agent.status,
            currentTask: crewMonitoring.agents?.[index]?.current_task || agent.currentTask,
            performance: crewMonitoring.agents?.[index]?.performance || agent.performance
          })),
          collaboration_status: {
            intra_crew: crewMonitoring.performance_metrics?.collaboration_score || 0,
            cross_crew: crewMonitoring.performance_metrics?.cross_crew_score || 0,
            memory_sharing: crewMonitoring.performance_metrics?.memory_sharing || false,
            knowledge_utilization: crewMonitoring.performance_metrics?.knowledge_score || 0
          }
        };
      }
      return crew;
    });
    
    setCrews(updatedCrews);
    setOverallProgress(monitoringData.overall_progress || 0);
    setCurrentPhase(monitoringData.current_phase || 'Initializing...');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'secondary',
      running: 'default',
      completed: 'success',
      failed: 'destructive'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const AgentCard: React.FC<{ agent: AgentInfo; isManager?: boolean }> = ({ agent, isManager }) => (
    <div className={`p-3 rounded-lg border ${isManager ? 'border-yellow-200 bg-yellow-50' : 'border-gray-200 bg-gray-50'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isManager && <Crown className="h-4 w-4 text-yellow-600" />}
          <span className="font-medium text-sm">{agent.name}</span>
          {getStatusIcon(agent.status)}
        </div>
        <Badge variant="outline" className="text-xs">
          {agent.collaborations?.length || 0} collaborations
        </Badge>
      </div>
      <p className="text-xs text-gray-600 mb-2">{agent.role}</p>
      {agent.currentTask && (
        <p className="text-xs text-blue-600 italic">{agent.currentTask}</p>
      )}
      {agent.performance && (
        <div className="flex gap-2 mt-2 text-xs">
          <span>Success: {(agent.performance.success_rate * 100).toFixed(0)}%</span>
          <span>Tasks: {agent.performance.tasks_completed}</span>
        </div>
      )}
    </div>
  );

  const CrewCard: React.FC<{ crew: CrewProgress }> = ({ crew }) => (
    <Card className={`transition-all duration-300 ${
      crew.status === 'running' ? 'border-blue-500 shadow-lg' : 
      crew.status === 'completed' ? 'border-green-500' :
      crew.status === 'failed' ? 'border-red-500' : ''
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              crew.status === 'running' ? 'bg-blue-100 text-blue-600' :
              crew.status === 'completed' ? 'bg-green-100 text-green-600' :
              crew.status === 'failed' ? 'bg-red-100 text-red-600' :
              'bg-gray-100 text-gray-600'
            }`}>
              {crew.icon}
            </div>
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {crew.name}
                {crew.manager && <Badge variant="outline" className="text-xs">Manager: {crew.manager}</Badge>}
              </CardTitle>
              <CardDescription className="text-sm mt-1">
                {crew.description}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(crew.status)}
            {getStatusBadge(crew.status)}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Progress</span>
              <span>{crew.progress}%</span>
            </div>
            <Progress value={crew.progress} className="h-2" />
          </div>

          {/* Current Task */}
          {crew.currentTask && (
            <div className="text-sm">
              <span className="font-medium">Current Task: </span>
              <span className="text-blue-600">{crew.currentTask}</span>
            </div>
          )}

          {/* Collaboration Status */}
          {crew.collaboration_status && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span>Intra-crew: {crew.collaboration_status.intra_crew}/10</span>
              </div>
              <div className="flex items-center gap-1">
                <Network className="h-3 w-3" />
                <span>Cross-crew: {crew.collaboration_status.cross_crew}/10</span>
              </div>
              <div className="flex items-center gap-1">
                <Brain className="h-3 w-3" />
                <span>Memory: {crew.collaboration_status.memory_sharing ? 'Active' : 'Inactive'}</span>
              </div>
              <div className="flex items-center gap-1">
                <Lightbulb className="h-3 w-3" />
                <span>Knowledge: {crew.collaboration_status.knowledge_utilization}/10</span>
              </div>
            </div>
          )}

          {/* Agents */}
          <div>
            <div className="font-medium text-sm mb-2 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Agents ({crew.agents.length})
            </div>
            <div className="space-y-2">
              {crew.agents.map((agent, index) => (
                <AgentCard key={index} agent={agent} isManager={agent.isManager} />
              ))}
            </div>
          </div>

          {/* Planning Status */}
          {crew.planning_status && (
            <div className="text-xs bg-blue-50 p-2 rounded">
              <div className="font-medium mb-1">Planning Strategy: {crew.planning_status.strategy}</div>
              <div>Coordination Score: {crew.planning_status.coordination_score}/10</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const CollaborationOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Active Collaborations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{collaborationData?.active_collaborations || 0}</div>
          <p className="text-xs text-gray-600">Total: {collaborationData?.total_collaborations || 0}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Memory Utilization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{Math.round((collaborationData?.memory_utilization || 0) * 100)}%</div>
          <Progress value={(collaborationData?.memory_utilization || 0) * 100} className="h-2 mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            Cross-Crew Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{collaborationData?.cross_crew_insights || 0}</div>
          <p className="text-xs text-gray-600">Knowledge Score: {(collaborationData?.knowledge_sharing_score || 0).toFixed(1)}/10</p>
        </CardContent>
      </Card>
    </div>
  );

  const PlanningOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Coordination Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-lg font-medium">{planningData?.coordination_strategy || 'Not set'}</div>
          <p className="text-xs text-gray-600">Adaptive adjustments: {planningData?.adaptive_adjustments || 0}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Target className="h-4 w-4" />
            Success Criteria
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{planningData?.success_criteria_met || 0}/6</div>
          <Progress value={((planningData?.success_criteria_met || 0) / 6) * 100} className="h-2 mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Optimization Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(planningData?.optimization_score || 0).toFixed(1)}/10</div>
          <p className="text-xs text-gray-600">ETA: {planningData?.predicted_completion || 'Unknown'}</p>
        </CardContent>
      </Card>
    </div>
  );

  const MemoryAnalytics = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Memory Analytics
        </CardTitle>
      </CardHeader>
      <CardContent>
        {memoryAnalytics ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium">Memory Usage</div>
                <div className="text-2xl font-bold">{memoryAnalytics.memory_usage || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Learning Effectiveness</div>
                <div className="text-2xl font-bold">{memoryAnalytics.learning_effectiveness || 'N/A'}</div>
              </div>
            </div>
            {memoryAnalytics.cross_crew_insights && (
              <div>
                <div className="text-sm font-medium mb-2">Cross-Crew Insights</div>
                <div className="text-xs text-gray-600">
                  {JSON.stringify(memoryAnalytics.cross_crew_insights, null, 2)}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-gray-500">Loading memory analytics...</div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Enhanced Agent Orchestration
              </CardTitle>
              <CardDescription>
                Hierarchical crews with collaborative intelligence and planning coordination
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-lg px-3 py-1">
              {overallProgress}% Complete
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Progress</span>
                <span>{currentPhase}</span>
              </div>
              <Progress value={overallProgress} className="h-3" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for different views */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="crews">Crews</TabsTrigger>
          <TabsTrigger value="collaboration">Collaboration</TabsTrigger>
          <TabsTrigger value="planning">Planning</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {crews.slice(0, 4).map((crew, index) => (
              <CrewCard key={index} crew={crew} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {crews.map((crew, index) => (
              <CrewCard key={index} crew={crew} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="collaboration" className="space-y-4">
          <CollaborationOverview />
        </TabsContent>

        <TabsContent value="planning" className="space-y-4">
          <PlanningOverview />
        </TabsContent>

        <TabsContent value="memory" className="space-y-4">
          <MemoryAnalytics />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedAgentOrchestrationPanel; 