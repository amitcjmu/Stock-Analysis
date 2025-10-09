import { apiCall } from "@/config/api";
import { CollectionFlowClient } from "./client";

/**
 * Validation logic
 * Handles governance requirements, exceptions, approvals, and conflict detection
 */
export class ValidationApi extends CollectionFlowClient {
  // Phase 2: Collection Gaps - Governance & Exceptions
  async getGovernanceRequirements(): Promise<
    Array<{
      id: string;
      title: string;
      description: string;
      category: "security" | "compliance" | "risk" | "policy";
      priority: "low" | "medium" | "high" | "critical";
      status: "active" | "inactive" | "draft";
      applicable_scopes: Array<"tenant" | "application" | "asset">;
      approval_workflow: string[];
      created_at: string;
      updated_at?: string;
    }>
  > {
    return await apiCall(`${this.baseUrl}/governance/requirements`, {
      method: "GET",
    });
  }

  async getMigrationExceptions(): Promise<
    Array<{
      id: string;
      requirement_id: string;
      title: string;
      justification: string;
      business_impact: string;
      mitigation_plan: string;
      scope: "tenant" | "application" | "asset";
      scope_id: string;
      requested_by: string;
      status: "pending" | "approved" | "rejected" | "withdrawn";
      priority: "low" | "medium" | "high" | "critical";
      expiry_date?: string;
      approval_history: Array<{
        approver: string;
        action: "approved" | "rejected" | "requested_changes";
        timestamp: string;
        comments?: string;
      }>;
      created_at: string;
      updated_at?: string;
    }>
  > {
    return await apiCall(`${this.baseUrl}/governance/exceptions`, {
      method: "GET",
    });
  }

  async createMigrationException(data: {
    requirement_id: string;
    title: string;
    justification: string;
    business_impact: string;
    mitigation_plan: string;
    scope: "tenant" | "application" | "asset";
    scope_id: string;
    priority: "low" | "medium" | "high" | "critical";
    expiry_date?: string;
  }): Promise<{
    id: string;
    requirement_id: string;
    title: string;
    justification: string;
    business_impact: string;
    mitigation_plan: string;
    scope: "tenant" | "application" | "asset";
    scope_id: string;
    requested_by: string;
    status: "pending" | "approved" | "rejected" | "withdrawn";
    priority: "low" | "medium" | "high" | "critical";
    expiry_date?: string;
    approval_history: Array<{
      approver: string;
      action: "approved" | "rejected" | "requested_changes";
      timestamp: string;
      comments?: string;
    }>;
    created_at: string;
    updated_at?: string;
  }> {
    return await apiCall(`${this.baseUrl}/governance/exceptions`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getApprovalRequests(): Promise<
    Array<{
      id: string;
      title: string;
      description: string;
      request_type:
        | "policy_exception"
        | "process_deviation"
        | "risk_acceptance"
        | "compliance_waiver";
      scope: "tenant" | "application" | "asset";
      scope_id: string;
      business_justification: string;
      risk_assessment: string;
      mitigation_measures: string;
      requested_by: string;
      status: "pending" | "under_review" | "approved" | "rejected";
      priority: "low" | "medium" | "high" | "critical";
      created_at: string;
      updated_at?: string;
    }>
  > {
    return await apiCall(`${this.baseUrl}/governance/approval-requests`, {
      method: "GET",
    });
  }

  async createApprovalRequest(data: {
    title: string;
    description: string;
    request_type:
      | "policy_exception"
      | "process_deviation"
      | "risk_acceptance"
      | "compliance_waiver";
    scope: "tenant" | "application" | "asset";
    scope_id: string;
    business_justification: string;
    risk_assessment: string;
    mitigation_measures: string;
    priority: "low" | "medium" | "high" | "critical";
  }): Promise<{
    id: string;
    title: string;
    description: string;
    request_type:
      | "policy_exception"
      | "process_deviation"
      | "risk_acceptance"
      | "compliance_waiver";
    scope: "tenant" | "application" | "asset";
    scope_id: string;
    business_justification: string;
    risk_assessment: string;
    mitigation_measures: string;
    requested_by: string;
    status: "pending" | "under_review" | "approved" | "rejected";
    priority: "low" | "medium" | "high" | "critical";
    created_at: string;
    updated_at?: string;
  }> {
    return await apiCall(`${this.baseUrl}/governance/approval-requests`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Phase 2: Collection Gaps - Maintenance Windows Conflicts
  async getMaintenanceConflicts(): Promise<
    Array<{
      window_id: string;
      conflicting_windows: Array<{
        id: string;
        name: string;
        start_time: string;
        end_time: string;
        scope: string;
        impact_level: string;
      }>;
      overlap_duration_minutes: number;
      risk_level: "low" | "medium" | "high" | "critical";
    }>
  > {
    return await apiCall(`${this.baseUrl}/maintenance-windows/conflicts`, {
      method: "GET",
    });
  }

  // Phase 2: Asset-Agnostic Collection Endpoints
  async startAssetCollection(data: {
    scope: "tenant" | "engagement" | "asset";
    scope_id: string;
    asset_type?: string;
  }): Promise<{
    flow_id: string;
    status: string;
  }> {
    return await apiCall(`${this.baseUrl}/assets/start`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAssetConflicts(asset_id: string): Promise<
    Array<{
      id: string;
      asset_id: string;
      field_name: string;
      conflicting_values: Array<{
        value: unknown;
        source: string;
        timestamp: string;
        confidence: number;
      }>;
      resolution_status: "pending" | "auto_resolved" | "manual_resolved";
      resolved_value?: string;
      resolved_by?: string;
      resolution_rationale?: string;
      created_at: string;
      updated_at?: string;
    }>
  > {
    return await apiCall(`${this.baseUrl}/assets/${asset_id}/conflicts`, {
      method: "GET",
    });
  }

  async resolveAssetConflict(
    asset_id: string,
    field_name: string,
    resolution: {
      value: string;
      rationale?: string;
    },
  ): Promise<{
    status: string;
    message?: string;
  }> {
    return await apiCall(
      `${this.baseUrl}/assets/${asset_id}/conflicts/${field_name}/resolve`,
      {
        method: "POST",
        body: JSON.stringify(resolution),
      },
    );
  }
}
