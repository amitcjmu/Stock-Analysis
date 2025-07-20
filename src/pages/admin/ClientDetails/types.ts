/**
 * Types for ClientDetails component
 * Generated with CC for UI modularization
 */

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
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
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
] as const;

export const COMPANY_SIZES = [
  'Small (1-100)',
  'Medium (101-1000)',
  'Large (1001-5000)',
  'Enterprise (5000+)'
] as const;

export const SUBSCRIPTION_TIERS = [
  'basic',
  'pro', 
  'enterprise',
  'custom'
] as const;