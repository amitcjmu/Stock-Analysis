export interface Engagement {
  id: string;
  engagement_name: string;
  client_account_id: string;
  client_account_name: string;
  migration_scope: string;
  target_cloud_provider: string;
  migration_phase: string;
  engagement_manager: string;
  technical_lead: string;
  start_date: string;
  end_date: string;
  budget: number;
  budget_currency: string;
  completion_percentage: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  total_sessions: number;
  active_sessions: number;
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
  budget: number;
  budget_currency: string;
  team_preferences: Record<string, any>;
  stakeholder_preferences: Record<string, any>;
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
  { value: 'hybrid_cloud', label: 'Hybrid Cloud Setup' }
];

export const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' }
];

export const MigrationPhases = [
  { value: 'planning', label: 'Planning' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'migration', label: 'Migration' },
  { value: 'optimization', label: 'Optimization' },
  { value: 'completed', label: 'Completed' }
];

export const Currencies = [
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
  { value: 'CAD', label: 'Canadian Dollar (CAD)' },
  { value: 'AUD', label: 'Australian Dollar (AUD)' },
  { value: 'JPY', label: 'Japanese Yen (JPY)' },
  { value: 'INR', label: 'Indian Rupee (INR)' }
]; 