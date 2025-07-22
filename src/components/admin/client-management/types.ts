// CC: Client configuration interfaces for type safety
interface ClientSettings {
  notifications_enabled?: boolean;
  auto_backup?: boolean;
  data_retention_days?: number;
  [key: string]: unknown;
}

interface ClientBranding {
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  custom_css?: string;
  [key: string]: unknown;
}

interface ITGuidelines {
  security_level?: string;
  compliance_frameworks?: string[];
  data_governance_rules?: string[];
  [key: string]: unknown;
}

interface DecisionCriteria {
  cost_weight?: number;
  performance_weight?: number;
  security_weight?: number;
  timeline_weight?: number;
  [key: string]: unknown;
}

interface AgentPreferences {
  automation_level?: string;
  human_approval_required?: boolean;
  preferred_communication_style?: string;
  [key: string]: unknown;
}

interface BudgetConstraints {
  max_monthly_spend?: number;
  currency?: string;
  cost_center?: string;
  [key: string]: unknown;
}

interface TimelineConstraints {
  target_completion_date?: string;
  critical_milestones?: string[];
  business_deadlines?: string[];
  [key: string]: unknown;
}

export interface Client {
  id: string;
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone?: string;
  description?: string;
  subscription_tier?: string;
  billing_contact_email?: string;
  settings?: ClientSettings;
  branding?: ClientBranding;
  slug?: string;
  created_by?: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines?: ITGuidelines;
  decision_criteria?: DecisionCriteria;
  agent_preferences?: AgentPreferences;
  budget_constraints?: BudgetConstraints;
  timeline_constraints?: TimelineConstraints;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  total_engagements: number;
  active_engagements: number;
}

export interface ClientFormData {
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone: string;
  description: string;
  subscription_tier: string;
  billing_contact_email: string;
  settings?: ClientSettings;
  branding?: ClientBranding;
  business_objectives?: string[];
  target_cloud_providers?: string[];
  business_priorities?: string[];
  compliance_requirements?: string[];
  it_guidelines?: ITGuidelines;
  decision_criteria?: DecisionCriteria;
  agent_preferences?: AgentPreferences;
  budget_constraints?: BudgetConstraints;
  timeline_constraints?: TimelineConstraints;
}

export const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' }
];

export const BusinessPriorities = [
  { value: 'cost_reduction', label: 'Cost Reduction' },
  { value: 'agility_speed', label: 'Agility & Speed' },
  { value: 'security_compliance', label: 'Security & Compliance' },
  { value: 'innovation', label: 'Innovation' },
  { value: 'scalability', label: 'Scalability' },
  { value: 'reliability', label: 'Reliability' }
];

export const Industries = [
  'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
  'Education', 'Government', 'Energy', 'Transportation', 'Other'
];

export const CompanySizes = [
  'Small (1-100)', 'Medium (101-1000)', 'Large (1001-5000)', 'Enterprise (5000+)'
];

export const SubscriptionTiers = [
  { value: 'basic', label: 'Basic' },
  { value: 'professional', label: 'Professional' },
  { value: 'enterprise', label: 'Enterprise' },
  { value: 'premium', label: 'Premium' }
]; 