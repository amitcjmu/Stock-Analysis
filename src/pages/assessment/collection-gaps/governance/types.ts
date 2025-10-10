/**
 * TypeScript type definitions for Governance & Exceptions
 * Extracted from governance.tsx for better code organization
 */

export interface GovernanceRequirement {
  id: string;
  title: string;
  description: string;
  category: 'security' | 'compliance' | 'risk' | 'policy';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'inactive' | 'draft';
  applicable_scopes: Array<'tenant' | 'application' | 'asset'>;
  approval_workflow: string[];
  created_at: string;
  updated_at?: string;
}

export interface MigrationException {
  id: string;
  requirement_id: string;
  title: string;
  justification: string;
  business_impact: string;
  mitigation_plan: string;
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  requested_by: string;
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn';
  priority: 'low' | 'medium' | 'high' | 'critical';
  expiry_date?: string;
  approval_history: Array<{
    approver: string;
    action: 'approved' | 'rejected' | 'requested_changes';
    timestamp: string;
    comments?: string;
  }>;
  created_at: string;
  updated_at?: string;
}

export interface ApprovalRequest {
  id: string;
  title: string;
  description: string;
  request_type: 'policy_exception' | 'process_deviation' | 'risk_acceptance' | 'compliance_waiver';
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  business_justification: string;
  risk_assessment: string;
  mitigation_measures: string;
  requested_by: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected';
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  updated_at?: string;
}

export interface ExceptionFormData {
  requirement_id: string;
  title: string;
  justification: string;
  business_impact: string;
  mitigation_plan: string;
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  expiry_date?: string;
}

export interface ApprovalFormData {
  title: string;
  description: string;
  request_type: 'policy_exception' | 'process_deviation' | 'risk_acceptance' | 'compliance_waiver';
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  business_justification: string;
  risk_assessment: string;
  mitigation_measures: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}
