/**
 * Types for ClientDetails component
 * Generated with CC for UI modularization
 */

// Client Settings Interface
export interface ClientSettings {
  notifications_enabled?: boolean;
  email_frequency?: 'daily' | 'weekly' | 'monthly' | 'never';
  preferred_timezone?: string;
  language?: string;
  data_retention_days?: number;
  api_access_enabled?: boolean;
  webhook_url?: string;
  custom_integrations?: string[];
}

// Client Branding Interface
export interface ClientBranding {
  primary_color?: string;
  secondary_color?: string;
  logo_url?: string;
  favicon_url?: string;
  custom_domain?: string;
  theme_preference?: 'light' | 'dark' | 'auto';
  custom_css?: string;
  brand_name?: string;
}

// IT Guidelines Interface
export interface ITGuidelines {
  security_requirements?: string[];
  compliance_frameworks?: string[];
  data_classification_levels?: string[];
  approved_technologies?: string[];
  prohibited_technologies?: string[];
  network_policies?: string[];
  access_control_requirements?: string[];
  disaster_recovery_rto?: number; // Recovery Time Objective in hours
  disaster_recovery_rpo?: number; // Recovery Point Objective in hours
}

// Decision Criteria Interface
export interface DecisionCriteria {
  cost_weight?: number; // 0-100
  time_weight?: number; // 0-100
  risk_weight?: number; // 0-100
  quality_weight?: number; // 0-100
  innovation_weight?: number; // 0-100
  minimum_roi?: number; // percentage
  maximum_payback_period?: number; // months
  preferred_vendors?: string[];
  evaluation_factors?: string[];
}

// Agent Preferences Interface
export interface AgentPreferences {
  preferred_agent_types?: string[];
  automation_level?: 'low' | 'medium' | 'high' | 'full';
  approval_required_for?: string[];
  excluded_operations?: string[];
  performance_thresholds?: {
    min_accuracy?: number;
    max_processing_time?: number;
    max_cost_per_operation?: number;
  };
  custom_prompts?: Record<string, string>;
}

// Budget Constraints Interface
export interface BudgetConstraints {
  total_budget?: number;
  budget_currency?: string;
  budget_period?: 'monthly' | 'quarterly' | 'annually';
  cost_centers?: Array<{
    name: string;
    allocation: number;
    department?: string;
  }>;
  spending_limits?: {
    infrastructure?: number;
    services?: number;
    licensing?: number;
    consulting?: number;
  };
  approval_thresholds?: Array<{
    amount: number;
    approver_role: string;
  }>;
}

// Timeline Constraints Interface
export interface TimelineConstraints {
  project_start_date?: string;
  project_end_date?: string;
  blackout_periods?: Array<{
    start_date: string;
    end_date: string;
    reason: string;
  }>;
  milestone_requirements?: Array<{
    name: string;
    due_date: string;
    is_critical: boolean;
  }>;
  working_hours?: {
    timezone: string;
    start_time: string;
    end_time: string;
    working_days: string[];
  };
  sla_requirements?: {
    response_time_hours?: number;
    resolution_time_hours?: number;
    uptime_percentage?: number;
  };
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