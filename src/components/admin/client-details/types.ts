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
  settings?: Record<string, any>;
  branding?: Record<string, any>;
  slug?: string;
  created_by?: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines?: Record<string, any>;
  decision_criteria?: Record<string, any>;
  agent_preferences?: Record<string, any>;
  budget_constraints?: Record<string, any>;
  timeline_constraints?: Record<string, any>;
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
}

export const INDUSTRIES = [
  'Technology', 
  'Healthcare', 
  'Finance', 
  'Manufacturing', 
  'Retail', 
  'Education', 
  'Government', 
  'Energy', 
  'Transportation', 
  'Other'
];

export const COMPANY_SIZES = [
  'Small (1-100)', 
  'Medium (101-1000)', 
  'Large (1001-5000)', 
  'Enterprise (5000+)'
];

export const SUBSCRIPTION_TIERS = [
  { value: 'basic', label: 'Basic' },
  { value: 'pro', label: 'Pro' },
  { value: 'enterprise', label: 'Enterprise' },
  { value: 'custom', label: 'Custom' }
];

export const PROVIDER_MAP: Record<string, string> = {
  'aws': 'Amazon Web Services (AWS)',
  'azure': 'Microsoft Azure',
  'gcp': 'Google Cloud Platform (GCP)',
  'multi_cloud': 'Multi-Cloud Strategy',
  'hybrid': 'Hybrid Cloud',
  'private_cloud': 'Private Cloud'
};

export const PRIORITY_MAP: Record<string, string> = {
  'cost_reduction': 'Cost Reduction',
  'agility_speed': 'Agility & Speed',
  'security_compliance': 'Security & Compliance',
  'innovation': 'Innovation',
  'scalability': 'Scalability',
  'reliability': 'Reliability'
}; 