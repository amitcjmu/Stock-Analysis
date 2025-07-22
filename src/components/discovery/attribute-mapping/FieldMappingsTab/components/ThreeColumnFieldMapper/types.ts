/**
 * ThreeColumnFieldMapper Types
 * 
 * Type definitions for the field mapping component and its sub-components.
 */

import { TargetField, FieldMapping } from '../../types';

export interface ThreeColumnFieldMapperProps {
  fieldMappings: FieldMapping[];
  availableFields: TargetField[];
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onRefresh?: () => void;
}

export interface MappingBuckets {
  autoMapped: FieldMapping[];
  unmapped: FieldMapping[];
  approved: FieldMapping[];
}

export interface AgentTypeInfo {
  type: string;
  icon: React.ReactNode;
  color: string;
}

export interface ConfidenceDisplayInfo {
  percentage: number;
  colorClass: string;
  icon: React.ReactNode;
}

export interface ProgressInfo {
  total: number;
  approved: number;
  pending: number;
}

export interface CardProps {
  mapping: FieldMapping;
}

export interface ColumnHeaderProps {
  title: string;
  count: number;
  icon: React.ReactNode;
  bgColor: string;
}

export interface BulkOperationResult {
  successful_updates: number;
}

export interface BulkActionsProps {
  buckets: MappingBuckets;
  onBulkApprove: (mappingIds: string[]) => Promise<void>;
  onBulkReject: (mappingIds: string[]) => Promise<void>;
  processingMappings: Set<string>;
  lastBulkOperationTime: number;
  client: unknown;
  engagement: unknown;
}