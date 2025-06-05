export interface CreateEngagementData {
  engagement_name: string;
  client_account_id: string;
  project_manager: string;
  estimated_start_date: string;
  estimated_end_date: string;
  budget: number | string;
  budget_currency: string;
  engagement_status: string;
  phase: string;
  description: string;
  business_objectives: string[];
  target_cloud_provider: string;
  scope_applications: boolean;
  scope_databases: boolean;
  scope_infrastructure: boolean;
  scope_data_migration: boolean;
  risk_level: string;
  compliance_requirements: string[];
}

export interface ClientAccount {
  id: string;
  account_name: string;
  industry: string;
}

export const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' }
];

export const EngagementStatuses = [
  { value: 'planning', label: 'Planning' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'active', label: 'Active' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'completed', label: 'Completed' }
];

export const Phases = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'planning', label: 'Planning' },
  { value: 'execution', label: 'Execution' },
  { value: 'optimization', label: 'Optimization' }
];

export const RiskLevels = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' }
];

export const Currencies = [
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'GBP', label: 'GBP' },
  { value: 'CAD', label: 'CAD' },
  { value: 'AUD', label: 'AUD' }
]; 