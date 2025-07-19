/**
 * Multi-Tenant API Types
 * 
 * Types for multi-tenant context, headers, and tenant-specific operations.
 */

// Multi-tenant context
export interface MultiTenantContext {
  clientAccountId: string;
  engagementId: string;
  userId: string;
  tenantId?: string;
  organizationId?: string;
  workspaceId?: string;
  permissions?: string[];
  roles?: string[];
  scope?: string[];
}

export interface TenantHeaders {
  'X-Client-Account-ID': string;
  'X-Engagement-ID': string;
  'X-User-ID': string;
  'X-Tenant-ID'?: string;
  'X-Organization-ID'?: string;
  'X-Workspace-ID'?: string;
  'X-Request-ID'?: string;
  'X-Correlation-ID'?: string;
  'X-Session-ID'?: string;
  'X-Device-ID'?: string;
  'X-User-Agent'?: string;
  'X-Source'?: string;
  'X-Version'?: string;
}