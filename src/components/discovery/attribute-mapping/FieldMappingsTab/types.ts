// Import standardized FieldMapping interface
import type { FieldMapping } from '@/types/api/discovery/field-mapping-types';

// Import TargetField type from the context to ensure consistency
export type { TargetField } from '../../../../contexts/FieldOptionsContext';

import type {
  FieldMappingLearningApprovalRequest,
  FieldMappingLearningRejectionRequest,
  BulkFieldMappingLearningRequest
} from '../../../../services/api/discoveryFlowService';

export interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onRemoveMapping?: (mappingId: string) => Promise<void>;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onRefresh?: () => void;
  // New learning-related props
  onApproveMappingWithLearning?: (mappingId: string, request: FieldMappingLearningApprovalRequest) => Promise<void>;
  onRejectMappingWithLearning?: (mappingId: string, request: FieldMappingLearningRejectionRequest) => Promise<void>;
  onBulkLearnMappings?: (request: BulkFieldMappingLearningRequest) => Promise<void>;
  learnedMappings?: Set<string>;
  clientAccountId?: string;
  engagementId?: string;
  // Continue to data cleansing props
  canContinueToDataCleansing?: boolean;
  onContinueToDataCleansing?: () => void;
}

export interface RejectionDialogProps {
  isOpen: boolean;
  mappingId: string;
  source_field: string;
  target_field: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}
