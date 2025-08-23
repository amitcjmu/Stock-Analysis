// Import standardized FieldMapping interface
import type { FieldMapping } from '@/types/api/discovery/field-mapping-types';

// Import TargetField type from the context to ensure consistency
export type { TargetField } from '../../../../contexts/FieldOptionsContext';

export interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onRefresh?: () => void;
}

export interface RejectionDialogProps {
  isOpen: boolean;
  mappingId: string;
  source_field: string;
  target_field: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}
