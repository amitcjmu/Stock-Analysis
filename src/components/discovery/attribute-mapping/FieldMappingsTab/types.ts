export interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string | null;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual' | 'ai_suggested' | 'unmapped';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning?: string;
  action?: 'ignore' | 'delete';
}

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
  sourceField: string;
  targetField: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}