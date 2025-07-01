export interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  action?: 'ignore' | 'delete';
}

export interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

export interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
}

export interface RejectionDialogProps {
  isOpen: boolean;
  mappingId: string;
  sourceField: string;
  targetField: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}