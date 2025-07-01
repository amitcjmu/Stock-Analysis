import { MapPin, Database, Search, Shield, Users, Link, TrendingUp } from 'lucide-react';
import { CrewProgress } from './types';

export const INITIAL_CREWS: CrewProgress[] = [
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
        role: 'Oversees data cleaning operations with collaborative planning',
        status: 'idle',
        isManager: true,
        collaborations: ['Data Validation Agent', 'Data Transformation Agent']
      },
      {
        name: 'Data Validation Agent',
        role: 'Identifies data quality issues and validation rules',
        status: 'idle',
        collaborations: ['Data Quality Manager', 'Data Transformation Agent']
      },
      {
        name: 'Data Transformation Agent',
        role: 'Applies cleaning rules with memory persistence',
        status: 'idle',
        collaborations: ['Data Quality Manager', 'Data Validation Agent']
      }
    ],
    description: 'Collaboratively cleanses and standardizes data across assets',
    icon: <Database className="h-5 w-5" />,
    currentTask: 'Waiting for field mapping completion...'
  },
  {
    name: 'Asset Intelligence Crew',
    status: 'pending',
    progress: 0,
    manager: 'Asset Intelligence Coordinator',
    agents: [
      {
        name: 'Asset Intelligence Coordinator',
        role: 'Coordinates multi-agent asset classification',
        status: 'idle',
        isManager: true,
        collaborations: ['Asset Discovery Agent', 'Asset Classifier Agent']
      },
      {
        name: 'Asset Discovery Agent',
        role: 'Discovers and catalogs IT assets',
        status: 'idle',
        collaborations: ['Asset Intelligence Coordinator', 'Asset Classifier Agent']
      },
      {
        name: 'Asset Classifier Agent',
        role: 'Classifies assets with shared knowledge',
        status: 'idle',
        collaborations: ['Asset Intelligence Coordinator', 'Asset Discovery Agent']
      }
    ],
    description: 'Discovers and classifies IT assets using distributed intelligence',
    icon: <Search className="h-5 w-5" />,
    currentTask: 'Awaiting cleansed data...'
  },
  {
    name: 'Risk Assessment Crew',
    status: 'pending',
    progress: 0,
    manager: 'Risk Manager',
    agents: [
      {
        name: 'Risk Manager',
        role: 'Manages collaborative risk assessment',
        status: 'idle',
        isManager: true,
        collaborations: ['Security Risk Analyst', 'Compliance Risk Analyst']
      },
      {
        name: 'Security Risk Analyst',
        role: 'Analyzes security risks with memory-based learning',
        status: 'idle',
        collaborations: ['Risk Manager', 'Compliance Risk Analyst']
      },
      {
        name: 'Compliance Risk Analyst',
        role: 'Evaluates compliance risks across assets',
        status: 'idle',
        collaborations: ['Risk Manager', 'Security Risk Analyst']
      }
    ],
    description: 'Performs collaborative risk assessment with knowledge sharing',
    icon: <Shield className="h-5 w-5" />,
    currentTask: 'Pending asset classification...'
  },
  {
    name: 'Application Discovery Crew',
    status: 'pending',
    progress: 0,
    manager: 'Application Intelligence Lead',
    agents: [
      {
        name: 'Application Intelligence Lead',
        role: 'Leads collaborative application discovery',
        status: 'idle',
        isManager: true,
        collaborations: ['Application Analyzer', 'Component Mapper']
      },
      {
        name: 'Application Analyzer',
        role: 'Analyzes application patterns and relationships',
        status: 'idle',
        collaborations: ['Application Intelligence Lead', 'Component Mapper']
      },
      {
        name: 'Component Mapper',
        role: 'Maps application components with shared context',
        status: 'idle',
        collaborations: ['Application Intelligence Lead', 'Application Analyzer']
      }
    ],
    description: 'DISCOVERY PHASE: Discovers applications through collaborative analysis',
    icon: <Users className="h-5 w-5" />,
    currentTask: 'Awaiting asset intelligence...'
  },
  {
    name: 'Dependency Mapping Crew',
    status: 'pending',
    progress: 0,
    manager: 'Dependency Coordinator',
    agents: [
      {
        name: 'Dependency Coordinator',
        role: 'Coordinates dependency discovery across crews',
        status: 'idle',
        isManager: true,
        collaborations: ['Network Dependency Mapper', 'Service Dependency Analyzer']
      },
      {
        name: 'Network Dependency Mapper',
        role: 'Maps network dependencies with cross-crew insights',
        status: 'idle',
        collaborations: ['Dependency Coordinator', 'Service Dependency Analyzer']
      },
      {
        name: 'Service Dependency Analyzer',
        role: 'Analyzes service dependencies',
        status: 'idle',
        collaborations: ['Dependency Coordinator', 'Network Dependency Mapper']
      }
    ],
    description: 'Maps dependencies using cross-crew collaboration',
    icon: <Link className="h-5 w-5" />,
    currentTask: 'Awaiting application discovery...'
  },
  {
    name: 'Migration Planning Crew',
    status: 'pending',
    progress: 0,
    manager: 'Migration Strategy Director',
    agents: [
      {
        name: 'Migration Strategy Director',
        role: 'Directs collaborative migration planning',
        status: 'idle',
        isManager: true,
        collaborations: ['Wave Planning Specialist', 'Migration Risk Assessor']
      },
      {
        name: 'Wave Planning Specialist',
        role: 'Plans migration waves with adaptive learning',
        status: 'idle',
        collaborations: ['Migration Strategy Director', 'Migration Risk Assessor']
      },
      {
        name: 'Migration Risk Assessor',
        role: 'Assesses migration risks across waves',
        status: 'idle',
        collaborations: ['Migration Strategy Director', 'Wave Planning Specialist']
      }
    ],
    description: 'PLANNING PHASE: Creates adaptive migration strategy',
    icon: <TrendingUp className="h-5 w-5" />,
    currentTask: 'Awaiting dependency analysis...'
  }
];

export const TAB_ITEMS = [
  { value: 'overview', label: 'Overview' },
  { value: 'crews', label: 'Crews' },
  { value: 'collaboration', label: 'Collaboration' },
  { value: 'planning', label: 'Planning' },
  { value: 'memory', label: 'Memory' }
];