/**
 * ThreeColumnFieldMapper Types
 * 
 * Type definitions for the field mapping component and its sub-components.
 */

import type { FC, ReactNode, MouseEvent } from 'react';
import type { TargetField, FieldMapping } from '../../types';

export interface ThreeColumnFieldMapperProps {
  fieldMappings: FieldMapping[];
  availableFields: TargetField[];
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => Promise<void> | void;
  onMappingChange?: (mappingId: string, newTarget: string) => Promise<void> | void;
  onRefresh?: () => Promise<void> | void;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  error?: string | null;
  theme?: 'light' | 'dark';
  onError?: (error: Error) => void;
}

export interface MappingBuckets {
  autoMapped: FieldMapping[];
  unmapped: FieldMapping[];
  approved: FieldMapping[];
  rejected?: FieldMapping[];
  processing?: FieldMapping[];
  totalCount: number;
  counts: {
    autoMapped: number;
    unmapped: number;
    approved: number;
    rejected?: number;
    processing?: number;
  };
}

export interface AgentTypeInfo {
  type: string;
  icon: ReactNode;
  color: string;
  description?: string;
}

export interface ConfidenceDisplayInfo {
  percentage: number;
  colorClass: string;
  icon: ReactNode;
  label?: string;
  tooltip?: string;
}

export interface ProgressInfo {
  total: number;
  approved: number;
  pending: number;
}

export interface CardProps {
  mapping: FieldMapping;
  onApprove?: (mappingId: string) => void;
  onReject?: (mappingId: string, reason?: string) => void;
  onEdit?: (mappingId: string) => void;
  processing?: boolean;
  disabled?: boolean;
  className?: string;
  onClick?: (event: MouseEvent<HTMLDivElement>) => void;
  onDoubleClick?: (event: MouseEvent<HTMLDivElement>) => void;
}

export interface ColumnHeaderProps {
  title: string;
  count: number;
  icon: ReactNode;
  bgColor: string;
  onClick?: (event: MouseEvent<HTMLDivElement>) => void;
  sortable?: boolean;
  sortDirection?: 'asc' | 'desc' | null;
  onSort?: (direction: 'asc' | 'desc') => void;
  tooltip?: string;
  className?: string;
}

export interface BulkOperationResult {
  successful_updates: number;
  failed_updates?: number;
  errors?: string[];
  warnings?: string[];
  message?: string;
  total_processed?: number;
}

export interface BulkActionsProps {
  buckets: MappingBuckets;
  onBulkApprove: (mappingIds: string[]) => Promise<void>;
  onBulkReject: (mappingIds: string[]) => Promise<void>;
  processingMappings: Set<string>;
  lastBulkOperationTime: number;
  client: AuthContext['client'];
  engagement: AuthContext['engagement'];
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  maxBulkOperations?: number;
  confirmationRequired?: boolean;
  onConfirmation?: (action: 'approve' | 'reject', count: number) => Promise<boolean>;
}

// Auth context types
export interface AuthContext {
  client: {
    id: string;
    name?: string;
    [key: string]: unknown;
  } | null;
  engagement: {
    id: string;
    name?: string;
    [key: string]: unknown;
  } | null;
}

// API Response types
export interface ApiResponse<T = unknown> {
  data?: T;
  success: boolean;
  message?: string;
  error?: string;
  statusCode?: number;
  timestamp?: string;
}