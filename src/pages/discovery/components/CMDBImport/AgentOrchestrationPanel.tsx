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
  MessageSquare
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

interface AgentOrchestrationPanelProps {
  flowId: string;
  flowState: any;
  onStatusUpdate?: (status: any) => void;
}

const AgentOrchestrationPanel: React.FC<AgentOrchestrationPanelProps> = ({
  flowId,
  flowState,
  onStatusUpdate
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [collaborationData, setCollaborationData] = useState<any>(null);
  const [planningData, setPlanningData] = useState<any>(null);
  const [crews, setCrews] = useState<CrewProgress[]>([
    {
      name: 'Field Mapping Crew',
      status: 'pending',
      progress: 0,
      manager: 'Field Mapping Manager',
      agents: [
        {
          name: 'Field Mapping Manager',
          role: 'Coordinates field mapping analysis',
          status: 'idle',
          isManager: true,
          collaborations: ['Schema Analysis Expert', 'Attribute Mapping Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Schema Analysis Expert',
          role: 'Analyzes data structure semantics',
          status: 'idle',
          collaborations: ['Field Mapping Manager', 'Attribute Mapping Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Attribute Mapping Specialist',
          role: 'Creates precise field mappings',
          status: 'idle',
          collaborations: ['Field Mapping Manager', 'Schema Analysis Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'FOUNDATION PHASE: Analyzes data structure and maps fields to standard migration attributes using hierarchical coordination',
      icon: <MapPin className="h-5 w-5" />,
      currentTask: 'Ready to analyze data structure...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'hierarchical',
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
          role: 'Ensures comprehensive data quality',
          status: 'idle',
          isManager: true,
          collaborations: ['Data Validation Expert', 'Data Standardization Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Data Validation Expert',
          role: 'Validates data using field mappings',
          status: 'idle',
          collaborations: ['Data Quality Manager', 'Data Standardization Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Data Standardization Specialist',
          role: 'Standardizes data formats',
          status: 'idle',
          collaborations: ['Data Quality Manager', 'Data Validation Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'QUALITY ASSURANCE: Cleanses and standardizes data using field mapping insights with memory-enhanced validation',
      icon: <Database className="h-5 w-5" />,
      currentTask: 'Waiting for field mapping completion...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'memory_enhanced',
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
          role: 'Coordinates multi-domain classification',
          status: 'idle',
          isManager: true,
          collaborations: ['Server Expert', 'Application Expert', 'Device Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Server Classification Expert',
          role: 'Classifies server infrastructure',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Application Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Discovery Expert',
          role: 'Identifies application assets',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Server Expert', 'Device Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Device Classification Expert',
          role: 'Classifies network devices',
          status: 'idle',
          collaborations: ['Inventory Manager', 'Application Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'MULTI-DOMAIN CLASSIFICATION: Cross-domain collaboration for comprehensive asset classification with shared insights',
      icon: <Search className="h-5 w-5" />,
      currentTask: 'Waiting for data cleansing...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'cross_domain_collaboration',
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
          role: 'Orchestrates hosting relationship mapping',
          status: 'idle',
          isManager: true,
          collaborations: ['Topology Expert', 'Relationship Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Topology Expert',
          role: 'Maps application hosting patterns',
          status: 'idle',
          collaborations: ['Dependency Manager', 'Relationship Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Infrastructure Relationship Analyst',
          role: 'Analyzes server-app relationships',
          status: 'idle',
          collaborations: ['Dependency Manager', 'Topology Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'HOSTING RELATIONSHIPS: Maps application-to-server hosting dependencies with topology intelligence',
      icon: <Activity className="h-5 w-5" />,
      currentTask: 'Waiting for inventory building...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'topology_intelligent',
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
          role: 'Coordinates integration dependency analysis',
          status: 'idle',
          isManager: true,
          collaborations: ['Integration Expert', 'API Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Application Integration Expert',
          role: 'Maps communication patterns',
          status: 'idle',
          collaborations: ['Integration Manager', 'API Analyst'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'API Dependency Analyst',
          role: 'Analyzes service dependencies',
          status: 'idle',
          collaborations: ['Integration Manager', 'Integration Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: 'INTEGRATION ANALYSIS: Maps application-to-application communication patterns with API intelligence',
      icon: <Zap className="h-5 w-5" />,
      currentTask: 'Waiting for app-server dependencies...',
      collaboration_status: {
        intra_crew: 0,
        cross_crew: 0,
        memory_sharing: false,
        knowledge_utilization: 0
      },
      planning_status: {
        strategy: 'api_intelligent',
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
          role: 'Coordinates 6R strategy preparation',
          status: 'idle',
          isManager: true,
          collaborations: ['Legacy Analyst', 'Modernization Expert', 'Risk Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Legacy Technology Analyst',
          role: 'Assesses technology stack age',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Modernization Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Modernization Strategy Expert',
          role: 'Recommends 6R strategies',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Legacy Analyst', 'Risk Specialist'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        },
        {
          name: 'Risk Assessment Specialist',
          role: 'Evaluates migration risks',
          status: 'idle',
          collaborations: ['Technical Debt Manager', 'Modernization Expert'],
          performance: { tasks_completed: 0, success_rate: 0, avg_duration: 0 }
        }
      ],
      description: '6R PREPARATION: Synthesizes all insights for comprehensive 6R migration strategy with risk intelligence',
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

  // Removed legacy API calls - data now comes from props or flow state


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
              <CardTitle className="text-lg">{crew.name}</CardTitle>
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
          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">Current Task:</p>
            <p className="text-sm text-gray-600">{crew.currentTask}</p>
          </div>
          
          {/* Agents */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Agents:</p>
            <div className="flex flex-wrap gap-2">
              {crew.agents.map((agent, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  <Users className="h-3 w-3 mr-1" />
                  {agent.name}
                </Badge>
              ))}
            </div>
          </div>
          
          {/* Results (if available) */}
          {crew.results && crew.status === 'completed' && (
            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
              <p className="text-sm font-medium text-green-800 mb-1">Results:</p>
              <div className="text-sm text-green-700 space-y-1">
                {crew.results.records_processed && (
                  <p>• Records processed: {crew.results.records_processed}</p>
                )}
                {crew.results.assets_classified && (
                  <p>• Assets classified: {crew.results.assets_classified}</p>
                )}
                {crew.results.fields_mapped && (
                  <p>• Fields mapped: {crew.results.fields_mapped}</p>
                )}
                {crew.results.quality_score && (
                  <p>• Quality score: {(crew.results.quality_score * 100).toFixed(1)}%</p>
                )}
              </div>
            </div>
          )}
          
          {/* Error (if failed) */}
          {crew.status === 'failed' && crew.results?.error && (
            <div className="bg-red-50 p-3 rounded-lg border border-red-200">
              <p className="text-sm font-medium text-red-800 mb-1">Error:</p>
              <p className="text-sm text-red-700">{crew.results.error}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Overall Progress Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-blue-600" />
                CrewAI Discovery Orchestration
              </CardTitle>
              <CardDescription>
                Multiple specialized crews working collaboratively on your data
              </CardDescription>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-blue-600">{overallProgress.toFixed(0)}%</p>
              <p className="text-sm text-gray-600">Overall Progress</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Progress value={overallProgress} className="h-3" />
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-orange-500" />
                Current Phase: {currentPhase}
              </span>
              <span className="text-gray-600">
                Flow: {flowId?.substring(0, 8)}...
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Crew Orchestration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">
            <Target className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="crews">
            <Users className="h-4 w-4 mr-2" />
            Crews
          </TabsTrigger>
          <TabsTrigger value="results">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Results
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {crews.map((crew, idx) => (
              <div key={idx} className="flex items-center gap-4 p-4 border rounded-lg">
                <div className={`p-2 rounded-lg ${
                  crew.status === 'running' ? 'bg-blue-100 text-blue-600' :
                  crew.status === 'completed' ? 'bg-green-100 text-green-600' :
                  crew.status === 'failed' ? 'bg-red-100 text-red-600' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {crew.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium">{crew.name}</h4>
                  <p className="text-sm text-gray-600">{crew.currentTask}</p>
                  <Progress value={crew.progress} className="h-1 mt-2" />
                </div>
                {getStatusIcon(crew.status)}
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {crews.map((crew, idx) => (
              <CrewCard key={idx} crew={crew} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {flowState?.processing_summary ? (
            <Card>
              <CardHeader>
                <CardTitle>Processing Summary</CardTitle>
                <CardDescription>Complete results from all crews</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {flowState.processing_summary.total_records_processed || 0}
                    </p>
                    <p className="text-sm text-gray-600">Records Processed</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {flowState.processing_summary.assets_created || 0}
                    </p>
                    <p className="text-sm text-gray-600">Assets Created</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {((flowState.processing_summary.data_quality_score || 0) * 100).toFixed(1)}%
                    </p>
                    <p className="text-sm text-gray-600">Quality Score</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {flowState.processing_summary.crews_executed || 0}
                    </p>
                    <p className="text-sm text-gray-600">Crews Executed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Clock className="h-8 w-8 mx-auto mb-2" />
                  <p>Results will appear here once crews complete their work</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentOrchestrationPanel; 