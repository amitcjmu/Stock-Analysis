import { useState } from 'react';
import { 
  MapPin, 
  Database, 
  Search, 
  Activity, 
  Zap, 
  Target 
} from 'lucide-react';
import { CrewProgress, CollaborationData, PlanningData } from './types';

export const useAgentOrchestrationState = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [collaborationData, setCollaborationData] = useState<CollaborationData | null>(null);
  const [planningData, setPlanningData] = useState<PlanningData | null>(null);
  const [overallProgress, setOverallProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('Initializing...');

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

  return {
    activeTab,
    setActiveTab,
    collaborationData,
    setCollaborationData,
    planningData,
    setPlanningData,
    crews,
    setCrews,
    overallProgress,
    setOverallProgress,
    currentPhase,
    setCurrentPhase
  };
};