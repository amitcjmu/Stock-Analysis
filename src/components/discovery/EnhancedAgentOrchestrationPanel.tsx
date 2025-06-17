import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Cpu, Users, MapPin, Database, Crown } from 'lucide-react';

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
}

interface EnhancedAgentOrchestrationPanelProps {
  sessionId: string;
  flowState?: any;
}

const EnhancedAgentOrchestrationPanel: React.FC<EnhancedAgentOrchestrationPanelProps> = ({
  sessionId,
  flowState
}) => {
  const [crews] = useState<CrewProgress[]>([
    {
      name: 'Field Mapping Crew',
      status: 'pending',
      progress: 0,
      agents: [
        { name: 'Field Mapping Manager', role: 'Coordinates field mapping analysis', status: 'idle', isManager: true },
        { name: 'Schema Analysis Expert', role: 'Analyzes data structure semantics', status: 'idle' },
        { name: 'Attribute Mapping Specialist', role: 'Creates precise field mappings', status: 'idle' }
      ],
      description: 'FOUNDATION PHASE: Maps fields to standard migration attributes',
      icon: <MapPin className="h-5 w-5" />
    },
    {
      name: 'Data Cleansing Crew',
      status: 'pending',
      progress: 0,
      agents: [
        { name: 'Data Quality Manager', role: 'Orchestrates data quality assurance', status: 'idle', isManager: true },
        { name: 'Data Validation Expert', role: 'Validates data quality', status: 'idle' },
        { name: 'Data Standardization Specialist', role: 'Standardizes data formats', status: 'idle' }
      ],
      description: 'QUALITY ASSURANCE: Uses field mapping insights for intelligent data cleansing',
      icon: <Database className="h-5 w-5" />
    }
  ]);

  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'completed': return `${baseClasses} bg-green-100 text-green-800`;
      case 'running': case 'active': return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'failed': case 'error': return `${baseClasses} bg-red-100 text-red-800`;
      default: return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl flex items-center">
          <Cpu className="h-6 w-6 mr-2 text-blue-500" />
          Enhanced Agent Orchestration
        </CardTitle>
        <CardDescription>
          Real-time monitoring of hierarchical crew coordination and agent collaboration
        </CardDescription>
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
                  {crews.filter(c => c.status === 'running').length}
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
                  {crews.reduce((total, crew) => total + crew.agents.length, 0)}
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
                  {crews.filter(c => c.status === 'completed').length}
                </div>
                <p className="text-xs text-gray-500">Successfully finished</p>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            {crews.map((crew, idx) => (
              <Card key={idx} className="mb-6">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {crew.icon}
                      <div>
                        <CardTitle className="text-lg">{crew.name}</CardTitle>
                        <CardDescription className="text-sm">{crew.description}</CardDescription>
                      </div>
                    </div>
                    <span className={getStatusBadge(crew.status)}>{crew.status}</span>
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
                        <div key={agentIdx} className={`p-3 rounded border ${agent.isManager ? 'border-orange-200 bg-orange-50' : 'border-gray-200 bg-gray-50'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center space-x-2">
                              {agent.isManager && <Crown className="h-4 w-4 text-orange-500" />}
                              <span className="font-medium text-sm">{agent.name}</span>
                              <span className={getStatusBadge(agent.status)}>{agent.status}</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-600">{agent.role}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default EnhancedAgentOrchestrationPanel; 