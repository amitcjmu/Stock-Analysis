/**
 * Discovery Flow - Base Types Module
 * 
 * Foundational types and interfaces shared across the Discovery Flow module.
 * Contains base component props, multi-tenant context, and response metadata.
 * 
 * Generated with CC - Code Companion
 */

import { ReactNode } from 'react';

/**
 * Base props interface for all Discovery Flow components
 */
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
}

/**
 * Multi-tenant context for all Discovery Flow operations
 */
export interface MultiTenantContext {
  clientAccountId: string;
  engagementId: string;
  userId: string;
}

/**
 * Standard response metadata structure for API responses
 */
export interface ResponseMetadata {
  timestamp: string;
  requestId: string;
  version: string;
  totalCount?: number;
  pageSize?: number;
  currentPage?: number;
}

/**
 * Flow status enumeration
 */
export type FlowStatus = 'active' | 'completed' | 'failed' | 'paused' | 'waiting_for_user' | 'migrated';

/**
 * Phase completion tracking interface
 */
export interface PhaseCompletion {
  dataImportCompleted: boolean;
  attributeMappingCompleted: boolean;
  dataCleansingCompleted: boolean;
  inventoryCompleted: boolean;
  dependenciesCompleted: boolean;
  techDebtCompleted: boolean;
}

/**
 * Column definition for data tables
 */
export interface ColumnDefinition {
  id: string;
  header: string;
  accessor: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'custom';
  sortable?: boolean;
  filterable?: boolean;
  width?: number;
  render?: (value: any, row: any) => ReactNode;
}

/**
 * Tab definition for navigation components
 */
export interface TabDefinition {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  badge?: string | number;
}

/**
 * Phase definition for flow management
 */
export interface PhaseDefinition {
  id: string;
  name: string;
  description: string;
  order: number;
  dependencies: string[];
  estimatedDuration: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed';
}