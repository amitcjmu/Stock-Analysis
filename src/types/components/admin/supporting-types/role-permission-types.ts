/**
 * Role and Permission Types
 *
 * Role-based access control (RBAC) type definitions including roles,
 * permissions, conditions, and scopes.
 */

export interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: RoleType;
  permissions: Permission[];
  hierarchy: number;
  isDefault: boolean;
  isSystem: boolean;
  isActive: boolean;
  conditions?: RoleCondition[];
  metadata?: Record<string, string | number | boolean | null>;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  resource: string;
  action: string;
  scope?: PermissionScope;
  conditions?: PermissionCondition[];
  granted: boolean;
  inherited?: boolean;
  source?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface RoleCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: unknown;
  description?: string;
}

export interface PermissionCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: unknown;
  description?: string;
}

export interface PermissionScope {
  type: ScopeType;
  value: string;
  description?: string;
}

// Enum and union types
export type RoleType = 'system' | 'custom' | 'temporary' | 'inherited';
export type ConditionType = 'time' | 'location' | 'device' | 'ip' | 'attribute' | 'custom';
export type ConditionOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'between';
export type ScopeType = 'global' | 'organization' | 'department' | 'team' | 'personal' | 'resource';
