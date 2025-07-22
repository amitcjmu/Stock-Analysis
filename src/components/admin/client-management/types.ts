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
  settings?: Record<string, unknown>;
  branding?: Record<string, unknown>;
  slug?: string;
  created_by?: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines?: Record<string, unknown>;
  decision_criteria?: Record<string, unknown>;
  agent_preferences?: Record<string, unknown>;
  budget_constraints?: Record<string, unknown>;
  timeline_constraints?: Record<string, unknown>;
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
  settings: Record<string, unknown>;
  branding: Record<string, unknown>;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines: Record<string, unknown>;
  decision_criteria: Record<string, unknown>;
  agent_preferences: Record<string, unknown>;
  budget_constraints: Record<string, unknown>;
  timeline_constraints: Record<string, unknown>;
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