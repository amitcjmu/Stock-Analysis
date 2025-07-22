import type { Crew, Agent, DiscoveryFlow, CrewStatus, AgentStatus } from '../types';

interface RawCrewData {
  crews?: unknown[];
}

export const transformCrewData = (crewData: RawCrewData): Crew[] => {
  if (!crewData || !crewData.crews) {
    return [];
  }

  return crewData.crews.map((crew: unknown): Crew => {
    const c = crew as Record<string, unknown>;
    return {
    id: (c.id as string) || `crew_${Date.now()}_${Math.random()}`,
    name: (c.name as string) || 'Unknown Crew',
    manager: (c.manager as string) || 'AI Crew Manager',
    status: (c.status as CrewStatus) || 'pending',
    progress: (c.progress as number) || 0,
    current_phase: (c.current_phase as string) || 'initialization',
    started_at: (c.started_at as string) || new Date().toISOString(),
    estimated_completion: c.estimated_completion as string,
    agents: (c.agents as unknown[])?.map((agent: unknown): Agent => {
      const a = agent as Record<string, unknown>;
      const perf = a.performance as Record<string, unknown> | undefined;
      const collab = a.collaboration as Record<string, unknown> | undefined;
      return {
      id: (a.id as string) || `agent_${Date.now()}_${Math.random()}`,
      name: (a.name as string) || 'Unknown Agent',
      role: (a.role as string) || 'AI Agent',
      status: (a.status as AgentStatus) || 'idle',
      current_task: (a.current_task as string) || 'Awaiting tasks',
      performance: {
        success_rate: (perf?.success_rate as number) || 0,
        tasks_completed: (perf?.tasks_completed as number) || 0,
        avg_response_time: (perf?.avg_response_time as number) || 0
      },
      collaboration: {
        is_collaborating: (collab?.is_collaborating as boolean) || false,
        collaboration_partner: collab?.collaboration_partner as string,
        shared_memory_access: (collab?.shared_memory_access as boolean) || false
      },
      last_activity: (a.last_activity as string) || new Date().toISOString()
      };
    }) || [],
    collaboration_metrics: {
      internal_effectiveness: ((c.collaboration_metrics as Record<string, unknown>)?.internal_effectiveness as number) || 0,
      cross_crew_sharing: ((c.collaboration_metrics as Record<string, unknown>)?.cross_crew_sharing as number) || 0,
      memory_utilization: ((c.collaboration_metrics as Record<string, unknown>)?.memory_utilization as number) || 0
    }
    };
  });
};

export const createAllAvailableCrews = (agentRegistryData: unknown): Crew[] => {
  // Create standardized crews for Discovery Flow
  const standardCrews = [
    {
      name: 'Field Mapping Crew',
      manager: 'Field Mapping Manager',
      phase: 'field_mapping',
      agents: [
        'CMDB Data Analyst',
        'Schema Analysis Agent',
        'Data Quality Validator'
      ]
    },
    {
      name: 'Data Cleansing Crew',
      manager: 'Data Cleansing Manager', 
      phase: 'data_cleansing',
      agents: [
        'Data Cleansing Agent',
        'Duplicate Detection Agent',
        'Data Standardization Agent'
      ]
    },
    {
      name: 'Inventory Building Crew',
      manager: 'Asset Inventory Manager',
      phase: 'asset_inventory',
      agents: [
        'Asset Intelligence Agent',
        'Configuration Item Agent',
        'Inventory Validation Agent'
      ]
    },
    {
      name: 'Application Dependencies Crew',
      manager: 'Dependency Analysis Manager',
      phase: 'dependency_analysis',
      agents: [
        'Dependency Intelligence Agent',
        'Application Discovery Agent',
        'Service Mapping Agent'
      ]
    },
    {
      name: 'Server Dependencies Crew',
      manager: 'Infrastructure Manager',
      phase: 'infrastructure_analysis',
      agents: [
        'Server Analysis Agent',
        'Network Topology Agent',
        'Infrastructure Mapping Agent'
      ]
    },
    {
      name: 'Technical Debt Analysis Crew',
      manager: 'Technical Debt Manager',
      phase: 'tech_debt_analysis',
      agents: [
        'Technical Debt Agent',
        'Code Quality Agent',
        'Risk Assessment Agent'
      ]
    }
  ];

  return standardCrews.map((crewTemplate, index): Crew => ({
    id: `crew_${crewTemplate.phase}_${index}`,
    name: crewTemplate.name,
    manager: crewTemplate.manager,
    status: 'pending' as CrewStatus,
    progress: 0,
    current_phase: crewTemplate.phase,
    started_at: new Date().toISOString(),
    agents: crewTemplate.agents.map((agentName, agentIndex): Agent => ({
      id: `agent_${crewTemplate.phase}_${agentIndex}`,
      name: agentName,
      role: agentName,
      status: 'idle' as AgentStatus,
      current_task: 'Awaiting workflow initiation',
      performance: {
        success_rate: 0.95 + (Math.random() * 0.05), // 95-100%
        tasks_completed: Math.floor(Math.random() * 50),
        avg_response_time: 1.2 + (Math.random() * 0.8) // 1.2-2.0 seconds
      },
      collaboration: {
        is_collaborating: false,
        shared_memory_access: true
      },
      last_activity: new Date().toISOString()
    })),
    collaboration_metrics: {
      internal_effectiveness: 0.85 + (Math.random() * 0.1),
      cross_crew_sharing: 0.75 + (Math.random() * 0.15),
      memory_utilization: 0.60 + (Math.random() * 0.25)
    }
  }));
};

export const createCompleteFlowView = (activeFlows: DiscoveryFlow[], agentRegistryData: unknown): DiscoveryFlow[] => {
  // If we have active flows, return them
  if (activeFlows.length > 0) {
    return activeFlows;
  }

  // Otherwise, create a default view showing all available crews
  const defaultFlow: DiscoveryFlow = {
    flow_id: 'discovery_flow_default',
    status: 'pending',
    current_phase: 'initialization',
    progress: 0,
    crews: createAllAvailableCrews(agentRegistryData),
    started_at: new Date().toISOString(),
    performance_metrics: {
      overall_efficiency: 0,
      crew_coordination: 0,
      agent_collaboration: 0
    },
    events_count: 0,
    last_event: 'System initialized'
  };

  return [defaultFlow];
};

export const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
    case 'running':
      return '🟢';
    case 'completed':
      return '✅';
    case 'failed':
    case 'error':
      return '❌';
    case 'paused':
      return '⏸️';
    case 'pending':
    case 'idle':
      return '⏳';
    default:
      return '⚪';
  }
};

export const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
    case 'running':
      return 'text-green-600 bg-green-100';
    case 'completed':
      return 'text-blue-600 bg-blue-100';
    case 'failed':
    case 'error':
      return 'text-red-600 bg-red-100';
    case 'paused':
      return 'text-yellow-600 bg-yellow-100';
    case 'pending':
    case 'idle':
      return 'text-gray-600 bg-gray-100';
    default:
      return 'text-gray-400 bg-gray-50';
  }
};

export const formatDuration = (timestamp: string) => {
  const now = new Date();
  const start = new Date(timestamp);
  const diffMs = now.getTime() - start.getTime();
  
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

export const calculateAverageMetrics = (crews: Crew[]) => {
  if (crews.length === 0) {
    return {
      avgEfficiency: 0,
      avgCollaboration: 0,
      avgMemoryUtilization: 0,
      totalAgents: 0,
      activeAgents: 0
    };
  }

  const totalAgents = crews.reduce((sum, crew) => sum + crew.agents.length, 0);
  const activeAgents = crews.reduce((sum, crew) => 
    sum + crew.agents.filter(agent => agent.status === 'active').length, 0
  );

  const avgEfficiency = crews.reduce((sum, crew) => 
    sum + crew.collaboration_metrics.internal_effectiveness, 0
  ) / crews.length;

  const avgCollaboration = crews.reduce((sum, crew) => 
    sum + crew.collaboration_metrics.cross_crew_sharing, 0
  ) / crews.length;

  const avgMemoryUtilization = crews.reduce((sum, crew) => 
    sum + crew.collaboration_metrics.memory_utilization, 0
  ) / crews.length;

  return {
    avgEfficiency,
    avgCollaboration,
    avgMemoryUtilization,
    totalAgents,
    activeAgents
  };
};