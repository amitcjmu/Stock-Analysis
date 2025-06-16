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
  Target
} from 'lucide-react';

interface CrewProgress {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  agents: string[];
  description: string;
  icon: React.ReactNode;
  results?: any;
  currentTask?: string;
}

interface AgentOrchestrationPanelProps {
  sessionId: string;
  flowState: any;
  onStatusUpdate?: (status: any) => void;
}

const AgentOrchestrationPanel: React.FC<AgentOrchestrationPanelProps> = ({
  sessionId,
  flowState,
  onStatusUpdate
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [crews, setCrews] = useState<CrewProgress[]>([
    {
      name: 'Field Mapping Crew',
      status: 'pending',
      progress: 0,
      agents: ['Field Mapping Manager', 'Schema Analysis Expert', 'Attribute Mapping Specialist'],
      description: 'FOUNDATION PHASE: Analyzes data structure and maps fields to standard migration attributes',
      icon: <MapPin className="h-5 w-5" />,
      currentTask: 'Ready to analyze data structure...'
    },
    {
      name: 'Data Cleansing Crew',
      status: 'pending',
      progress: 0,
      agents: ['Data Quality Manager', 'Data Validation Expert', 'Data Standardization Specialist'],
      description: 'QUALITY ASSURANCE: Cleanses and standardizes data using field mapping insights',
      icon: <Database className="h-5 w-5" />,
      currentTask: 'Waiting for field mapping completion...'
    },
    {
      name: 'Inventory Building Crew',
      status: 'pending', 
      progress: 0,
      agents: ['Inventory Manager', 'Server Classification Expert', 'Application Discovery Expert', 'Device Classification Expert'],
      description: 'MULTI-DOMAIN CLASSIFICATION: Classifies assets across servers, applications, and devices',
      icon: <Search className="h-5 w-5" />,
      currentTask: 'Waiting for data cleansing...'
    },
    {
      name: 'App-Server Dependency Crew',
      status: 'pending',
      progress: 0,
      agents: ['Dependency Manager', 'Application Topology Expert', 'Infrastructure Relationship Analyst'],
      description: 'HOSTING RELATIONSHIPS: Maps application-to-server hosting dependencies',
      icon: <Activity className="h-5 w-5" />,
      currentTask: 'Waiting for inventory building...'
    },
    {
      name: 'App-App Dependency Crew',
      status: 'pending',
      progress: 0,
      agents: ['Integration Manager', 'Application Integration Expert', 'API Dependency Analyst'],
      description: 'INTEGRATION ANALYSIS: Maps application-to-application communication patterns',
      icon: <Zap className="h-5 w-5" />,
      currentTask: 'Waiting for app-server dependencies...'
    },
    {
      name: 'Technical Debt Crew',
      status: 'pending',
      progress: 0,
      agents: ['Technical Debt Manager', 'Legacy Technology Analyst', 'Modernization Strategy Expert', 'Risk Assessment Specialist'],
      description: '6R PREPARATION: Assesses technical debt and prepares 6R migration strategies',
      icon: <Target className="h-5 w-5" />,
      currentTask: 'Waiting for dependency analysis...'
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('Initializing...');

  // Update crews based on flow state
  useEffect(() => {
    if (flowState?.phase_progress) {
      const updatedCrews = crews.map(crew => {
        const phaseKey = crew.name.toLowerCase().replace(' crew', '').replace(' ', '_');
        const phaseData = flowState.phase_progress[phaseKey];
        
        if (phaseData) {
          return {
            ...crew,
            status: phaseData.status === 'completed' ? 'completed' : 
                   phaseData.status === 'failed' ? 'failed' :
                   phaseData.progress > 0 ? 'running' : 'pending',
            progress: phaseData.progress || 0,
            currentTask: phaseData.status === 'completed' ? 'Completed successfully' :
                        phaseData.status === 'running' ? 'Processing...' :
                        phaseData.status === 'failed' ? 'Failed - see errors' :
                        'Waiting...',
            results: phaseData
          };
        }
        return crew;
      });
      
      setCrews(updatedCrews);
      setOverallProgress(flowState.overall_progress || 0);
      setCurrentPhase(flowState.current_phase || 'Initializing...');
    }
  }, [flowState]);

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
                  {agent}
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
                Session: {sessionId?.substring(0, 8)}...
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