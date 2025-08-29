// Team Preferences Interface
export interface TeamPreferences {
  preferred_communication_channels?: Array<'email' | 'slack' | 'teams' | 'jira'>;
  meeting_frequency?: 'daily' | 'weekly' | 'bi-weekly' | 'monthly';
  reporting_frequency?: 'daily' | 'weekly' | 'bi-weekly' | 'monthly';
  escalation_matrix?: Array<{
    level: number;
    role: string;
    contact_name: string;
    contact_email: string;
  }>;
  working_hours?: {
    timezone: string;
    start_time: string;
    end_time: string;
    working_days: string[];
  };
  team_size?: number;
  skill_requirements?: string[];
  tool_preferences?: string[];
}

// Agent Configuration Interface
export interface AgentConfiguration {
  enabled_agents?: string[];
  agent_priorities?: Record<string, number>; // agent_name -> priority (1-10)
  automation_rules?: Array<{
    condition: string;
    action: string;
    agent: string;
    parameters?: Record<string, string | number | boolean>;
  }>;
  performance_settings?: {
    parallel_execution?: boolean;
    max_concurrent_agents?: number;
    timeout_seconds?: number;
    retry_attempts?: number;
  };
  custom_configurations?: Record<
    string,
    {
      enabled: boolean;
      settings: Record<string, string | number | boolean>;
    }
  >;
}

// Discovery Preferences Interface
export interface DiscoveryPreferences {
  discovery_methods?: Array<'automated' | 'manual' | 'hybrid'>;
  data_sources?: Array<{
    type: string;
    connection_string?: string;
    credentials_reference?: string;
    enabled: boolean;
  }>;
  scan_frequency?: 'real-time' | 'hourly' | 'daily' | 'weekly' | 'on-demand';
  discovery_scope?: {
    include_patterns?: string[];
    exclude_patterns?: string[];
    depth_limit?: number;
    follow_symlinks?: boolean;
  };
  data_collection_preferences?: {
    collect_performance_metrics?: boolean;
    collect_dependency_data?: boolean;
    collect_configuration_data?: boolean;
    collect_security_data?: boolean;
  };
}

// Assessment Criteria Interface
export interface AssessmentCriteria {
  migration_readiness_weights?: {
    technical_debt?: number; // 0-100
    complexity?: number; // 0-100
    dependencies?: number; // 0-100
    business_criticality?: number; // 0-100
    security_compliance?: number; // 0-100
  };
  risk_thresholds?: {
    low_risk_max?: number;
    medium_risk_max?: number;
    high_risk_min?: number;
  };
  assessment_categories?: Array<{
    name: string;
    weight: number;
    criteria: string[];
  }>;
  custom_scoring_rules?: Array<{
    rule_name: string;
    condition: string;
    score_adjustment: number;
  }>;
  minimum_assessment_score?: number;
  required_assessments?: string[];
}

export interface Engagement {
  id: string;
  engagement_name: string;
  engagement_description?: string;
  client_account_id: string;
  client_account_name?: string; // Made optional
  migration_scope?: string; // Made optional
  target_cloud_provider?: string; // Made optional
  migration_phase?: string; // Made optional
  current_phase?: string;
  engagement_manager?: string; // Made optional
  technical_lead?: string; // Made optional
  start_date?: string; // Made optional
  end_date?: string; // Made optional
  planned_start_date?: string;
  planned_end_date?: string;
  budget?: number; // Made optional
  estimated_budget?: number;
  budget_currency?: string; // Made optional
  completion_percentage?: number; // Made optional
  created_at?: string; // Made optional
  updated_at?: string;
  is_active?: boolean; // Made optional
  total_sessions?: number; // Made optional
  active_sessions?: number; // Made optional
  team_preferences?: TeamPreferences;
  agent_configuration?: AgentConfiguration;
  discovery_preferences?: DiscoveryPreferences;
  assessment_criteria?: AssessmentCriteria;
  // Additional fields that might come from backend
  name?: string; // Backend might send 'name' instead of 'engagement_name'
  status?: string;
  engagement_type?: string;
}

// Stakeholder Preferences Interface
export interface StakeholderPreferences {
  primary_stakeholders?: Array<{
    name: string;
    role: string;
    email: string;
    involvement_level: 'high' | 'medium' | 'low';
  }>;
  communication_preferences?: {
    preferred_channels?: Array<'email' | 'phone' | 'video' | 'in-person'>;
    update_frequency?: 'daily' | 'weekly' | 'bi-weekly' | 'monthly';
    report_format?: 'detailed' | 'summary' | 'executive';
  };
  approval_requirements?: Array<{
    decision_type: string;
    approver_roles: string[];
    sla_hours?: number;
  }>;
  stakeholder_concerns?: string[];
  success_criteria?: string[];
}

export interface EngagementFormData {
  engagement_name: string;
  engagement_description: string;
  client_account_id: string;
  migration_scope: string;
  target_cloud_provider: string;
  migration_phase: string;
  engagement_manager: string;
  technical_lead: string;
  start_date: string;
  end_date: string;
  actual_start_date?: string;
  actual_end_date?: string;
  budget: number;
  budget_currency: string;
  actual_budget?: number;
  estimated_asset_count?: number;
  completion_percentage?: number;
  team_preferences: TeamPreferences;
  stakeholder_preferences: StakeholderPreferences;
}

export interface Client {
  id: string;
  account_name: string;
}

export const MigrationScopes = [
  { value: 'full_datacenter', label: 'Full Datacenter Migration' },
  { value: 'application_portfolio', label: 'Application Portfolio' },
  { value: 'infrastructure_only', label: 'Infrastructure Only' },
  { value: 'selected_applications', label: 'Selected Applications' },
  { value: 'pilot_migration', label: 'Pilot Migration' },
  { value: 'hybrid_cloud', label: 'Hybrid Cloud Setup' },
];

export const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' },
];

export const MigrationPhases = [
  { value: 'planning', label: 'Planning' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'migration', label: 'Migration' },
  { value: 'optimization', label: 'Optimization' },
  { value: 'completed', label: 'Completed' },
];

export const Currencies = [
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
  { value: 'CAD', label: 'Canadian Dollar (CAD)' },
  { value: 'AUD', label: 'Australian Dollar (AUD)' },
  { value: 'JPY', label: 'Japanese Yen (JPY)' },
  { value: 'INR', label: 'Indian Rupee (INR)' },
];
