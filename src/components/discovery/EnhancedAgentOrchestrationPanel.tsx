import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Cpu, Users, MapPin, Database, Crown, CheckCircle, Clock, AlertCircle, Network, Zap, BarChart3 } from 'lucide-react';

interface AgentInfo {
  name: string;
  role: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  isManager?: boolean;
}

interface CrewProgress {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  agents: AgentInfo[];
  description: string;
  icon: React.ReactNode;
  key_metrics?: unknown;
}

interface EnhancedAgentOrchestrationPanelProps {
  flowId: string;
  flowState?: unknown;
}

const EnhancedAgentOrchestrationPanel: React.FC<EnhancedAgentOrchestrationPanelProps> = ({
  flowId,
  flowState
}) => {
  const [crews, setCrews] = useState<CrewProgress[]>([]);

  // Update crews based on real flow state
  useEffect(() => {
    console.log('🔍 Updating crew state with:', { flowId, flowState });

    const DISCOVERY_FLOW_CREWS = [
      {
        id: 'field_mapping',
        name: 'Field Mapping Crew',
        description: 'FOUNDATION PHASE: Maps fields to standard migration attributes',
        icon: <MapPin className="h-5 w-5" />,
        agents: [
          { name: 'Field Mapping Manager', role: 'Coordinates field mapping analysis', isManager: true },
          { name: 'Schema Analysis Expert', role: 'Analyzes data structure semantics' },
          { name: 'Attribute Mapping Specialist', role: 'Creates precise field mappings' }
        ]
      },
      {
        id: 'data_cleansing',
        name: 'Data Cleansing Crew',
        description: 'QUALITY ASSURANCE: Uses field mapping insights for intelligent data cleansing',
        icon: <Database className="h-5 w-5" />,
        agents: [
          { name: 'Data Quality Manager', role: 'Orchestrates data quality assurance', isManager: true },
          { name: 'Data Validation Expert', role: 'Validates data quality' },
          { name: 'Data Standardization Specialist', role: 'Standardizes data formats' }
        ]
      },
      {
        id: 'inventory_building',
        name: 'Inventory Building Crew',
        description: 'CLASSIFICATION: Multi-domain asset inventory with cross-collaboration',
        icon: <BarChart3 className="h-5 w-5" />,
        agents: [
          { name: 'Inventory Manager', role: 'Coordinates multi-domain classification', isManager: true },
          { name: 'Server Classification Expert', role: 'Classifies server and infrastructure assets' },
          { name: 'Application Discovery Expert', role: 'Identifies and categorizes applications' },
          { name: 'Device Classification Expert', role: 'Classifies network devices and components' }
        ]
      },
      {
        id: 'app_server_dependencies',
        name: 'App-Server Dependency Crew',
        description: 'HOSTING RELATIONSHIPS: Maps application-to-server hosting relationships',
        icon: <Network className="h-5 w-5" />,
        agents: [
          { name: 'Dependency Manager', role: 'Orchestrates hosting relationship mapping', isManager: true },
          { name: 'Application Topology Expert', role: 'Maps applications to hosting infrastructure' },
          { name: 'Infrastructure Relationship Analyst', role: 'Analyzes server-application relationships' }
        ]
      },
      {
        id: 'app_app_dependencies',
        name: 'App-App Dependency Crew',
        description: 'INTEGRATION ANALYSIS: Maps application communication patterns and API dependencies',
        icon: <Network className="h-5 w-5" />,
        agents: [
          { name: 'Integration Manager', role: 'Coordinates application integration analysis', isManager: true },
          { name: 'Application Integration Expert', role: 'Maps application communication patterns' },
          { name: 'API Dependency Analyst', role: 'Analyzes service-to-service dependencies' }
        ]
      },
      {
        id: 'technical_debt',
        name: 'Technical Debt Crew',
        description: '6R STRATEGY PREPARATION: Evaluates technical debt for migration strategy',
        icon: <Zap className="h-5 w-5" />,
        agents: [
          { name: 'Technical Debt Manager', role: 'Coordinates technical debt assessment', isManager: true },
          { name: 'Legacy Technology Analyst', role: 'Assesses technology stack age and needs' },
          { name: 'Modernization Strategy Expert', role: 'Recommends 6R strategies' },
          { name: 'Risk Assessment Specialist', role: 'Evaluates migration risks and complexity' }
        ]
      }
    ];

    // Map flow state to crew progress
    const updatedCrews = DISCOVERY_FLOW_CREWS.map(crew => {
      const crewStatus = flowState?.crew_status?.[crew.id];
      const isCompleted = flowState?.phase_completion?.[crew.id] === true;

      // Determine status from flow state or backend logs pattern
      let status: 'pending' | 'running' | 'completed' | 'failed' = 'pending';
      let progress = 0;

      if (flowState?.overall_status === 'completed' || crewStatus?.status === 'completed' || isCompleted) {
        status = 'completed';
        progress = 100;
      } else if (crewStatus?.status === 'running' || crewStatus?.status === 'active') {
        status = 'running';
        progress = crewStatus?.progress || 50;
      } else if (crewStatus?.status === 'failed' || crewStatus?.status === 'error') {
        status = 'failed';
        progress = 0;
      } else if (flowState?.overall_status === 'in_progress' || flowState?.overall_status === 'completed') {
        // If flow shows as in_progress or completed, mark early crews as completed
        const crewOrder = ['field_mapping', 'data_cleansing', 'inventory_building', 'app_server_dependencies', 'app_app_dependencies', 'technical_debt'];
        const currentPhaseIndex = crewOrder.indexOf(flowState?.current_phase || 'field_mapping');
        const thisCrewIndex = crewOrder.indexOf(crew.id);

        if (thisCrewIndex < currentPhaseIndex || flowState?.overall_status === 'completed') {
          status = 'completed';
          progress = 100;
        } else if (thisCrewIndex === currentPhaseIndex) {
          status = 'running';
          progress = flowState?.completion_percentage || 50;
        }
      }

      // Update agent statuses based on crew status
      const updatedAgents = crew.agents.map(agent => ({
        ...agent,
        status: status === 'completed' ? 'completed' :
               status === 'running' ? 'active' :
               status === 'failed' ? 'error' : 'idle'
      }));

      return {
        name: crew.name,
        status,
        progress,
        agents: updatedAgents,
        description: crew.description,
        icon: crew.icon,
        key_metrics: crewStatus?.key_metrics || {}
      };
    });

    setCrews(updatedCrews);
  }, [flowId, flowState]);

  const getStatusBadge = (status: string): JSX.Element => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1";
    switch (status) {
      case 'completed': return (
        <span className={`${baseClasses} bg-green-100 text-green-800`}>
          <CheckCircle className="h-3 w-3" />
          <span>completed</span>
        </span>
      );
      case 'running': case 'active': return (
        <span className={`${baseClasses} bg-blue-100 text-blue-800`}>
          <Clock className="h-3 w-3 animate-pulse" />
          <span>running</span>
        </span>
      );
      case 'failed': case 'error': return (
        <span className={`${baseClasses} bg-red-100 text-red-800`}>
          <AlertCircle className="h-3 w-3" />
          <span>failed</span>
        </span>
      );
      default: return (
        <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
          <Clock className="h-3 w-3" />
          <span>pending</span>
        </span>
      );
    }
  };

  const getOverallProgress = (): any => {
    if (crews.length === 0) return 0;
    const totalProgress = crews.reduce((sum, crew) => sum + crew.progress, 0);
    return Math.round(totalProgress / crews.length);
  };

  const completedCrews = crews.filter(c => c.status === 'completed').length;
  const activeCrews = crews.filter(c => c.status === 'running').length;
  const totalAgents = crews.reduce((total, crew) => total + crew.agents.length, 0);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl flex items-center">
          <Cpu className="h-6 w-6 mr-2 text-blue-500" />
          Discovery Flow Crew Progress
        </CardTitle>
        <CardDescription>
          Real-time monitoring of the 6-phase CrewAI Discovery Flow execution
        </CardDescription>

        {/* Overall Progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium">Overall Progress</span>
            <span className="text-blue-600 font-bold">{getOverallProgress()}%</span>
          </div>
          <Progress value={getOverallProgress()} className="h-3" />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Flow: {flowId.substring(0, 8)}...</span>
            <span>Status: {flowState?.overall_status || 'initializing'}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Active Crews</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {activeCrews}
                </div>
                <p className="text-xs text-gray-500">Currently executing</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Total Agents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">
                  {totalAgents}
                </div>
                <p className="text-xs text-gray-500">Specialized agents</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Completed</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {completedCrews}
                </div>
                <p className="text-xs text-gray-500">Successfully finished</p>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            {crews.map((crew, idx) => (
              <Card key={idx} className={`mb-6 ${crew.status === 'completed' ? 'border-green-200 bg-green-50' :
                                                   crew.status === 'running' ? 'border-blue-200 bg-blue-50' : ''}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {crew.icon}
                      <div>
                        <CardTitle className="text-lg">{crew.name}</CardTitle>
                        <CardDescription className="text-sm">{crew.description}</CardDescription>
                      </div>
                    </div>
                    {getStatusBadge(crew.status)}
                  </div>

                  <div className="mt-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{crew.progress}%</span>
                    </div>
                    <Progress value={crew.progress} className="h-2" />
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="mb-4">
                    <div className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                      <Users className="h-4 w-4 text-blue-500 mr-1" />
                      Agents ({crew.agents.length})
                    </div>

                    <div className="space-y-2">
                      {crew.agents.map((agent, agentIdx) => (
                        <div key={agentIdx} className={`p-3 rounded border ${
                          agent.isManager ? 'border-orange-200 bg-orange-50' : 'border-gray-200 bg-gray-50'
                        }`}>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center space-x-2">
                              {agent.isManager && <Crown className="h-4 w-4 text-orange-500" />}
                              <span className="font-medium text-sm">{agent.name}</span>
                              {getStatusBadge(agent.status)}
                            </div>
                          </div>
                          <p className="text-xs text-gray-600">{agent.role}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Show completion message for completed crews */}
                  {crew.status === 'completed' && (
                    <div className="mt-3 p-2 bg-green-100 border border-green-200 rounded text-sm text-green-800">
                      ✅ Crew completed successfully - Results available for next phase
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Navigation hint when flow is completed */}
          {flowState?.overall_status === 'completed' || completedCrews >= 3 && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="text-center">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-green-800 mb-2">
                    Discovery Flow Data Ready!
                  </h3>
                  <p className="text-sm text-green-700 mb-4">
                    Field mappings and asset data have been processed by the crews. You can now proceed to the Attribute Mapping page.
                  </p>
                  <Badge className="bg-green-600 text-white">
                    Ready for Attribute Mapping →
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default EnhancedAgentOrchestrationPanel;
