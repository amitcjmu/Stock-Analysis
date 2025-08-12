// Re-export all types from individual hooks for centralized type management
export type { FlowDetectionResult } from './useFlowDetection';
export type { FieldMapping, FieldMappingsResult } from './useFieldMappings';
export type { ImportDataResult } from './useImportData';
export type { CriticalAttribute, CriticalAttributesResult } from './useCriticalAttributes';
export type { AttributeMappingActionsResult } from './useAttributeMappingActions';
export type { MappingProgress, AttributeMappingStateResult } from './useAttributeMappingState';
export type { RecoveryProgress } from '../../../services/flow-recovery';

// Additional types for attribute mapping
interface AttributeMappingAttribute {
  id: string;
  name: string;
  type: string;
  required: boolean;
  mapping_status?: 'pending' | 'mapped' | 'approved' | 'rejected';
  target_field?: string;
  confidence?: number;
}

interface CrewAnalysisItem {
  id: string;
  attribute_id: string;
  analysis_type: string;
  result: Record<string, unknown>;
  confidence: number;
  timestamp: string;
}

interface FlowState {
  flow_id: string;
  status: string;
  current_phase: string;
  progress: number;
  metadata?: Record<string, unknown>;
}

interface Flow {
  id: string;
  name: string;
  type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface DataImport {
  id: string;
  name: string;
  status: string;
  created_at: string;
  row_count: number;
  error_count?: number;
}

interface AttributeUpdate {
  name?: string;
  type?: string;
  required?: boolean;
  mapping_status?: string;
  target_field?: string;
}

interface AgentClarification {
  id: string;
  question: string;
  context: string;
  status: 'pending' | 'resolved' | 'dismissed';
  timestamp: string;
  resolution?: string;
}

// Main composition type that matches the original hook's return type
export interface AttributeMappingLogicResult {
  // Data
  agenticData: { attributes: AttributeMappingAttribute[] };
  fieldMappings: FieldMapping[];
  crewAnalysis: CrewAnalysisItem[];
  mappingProgress: MappingProgress;
  criticalAttributes: CriticalAttribute[];

  // Flow state
  flowState: FlowState | null;
  flow: Flow | null;
  flowId: string | null;
  dataImportId: string | null;
  availableDataImports: DataImport[];
  selectedDataImportId: string | null;

  // Auto-detection info
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: Flow[];

  // Loading states
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;

  // Error states
  agenticError: Error | null;
  flowStateError: Error | null;

  // Action handlers
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: AttributeUpdate) => Promise<void>;
  handleDataImportSelection: (importId: string) => Promise<void>;
  refetchAgentic: () => Promise<unknown>;
  refetchCriticalAttributes: () => Promise<unknown>;
  canContinueToDataCleansing: () => boolean;
  checkMappingApprovalStatus: (dataImportId: string) => Promise<{ approved: boolean; total: number; pending: number }>;

  // Flow status
  hasActiveFlow: boolean;
  currentPhase: string;
  flowProgress: number;

  // Agent clarifications
  agentClarifications: AgentClarification[];
  isClarificationsLoading: boolean;
  clarificationsError: Error | null;
  refetchClarifications: () => Promise<void>;

  // Flow recovery state
  isRecovering: boolean;
  recoveryProgress: RecoveryProgress;
  recoveryError: string | null;
  recoveredFlowId: string | null;
  triggerFlowRecovery: (flowId: string) => Promise<boolean>;
  isInterceptingTransition: boolean;
  transitionIntercepted: boolean;
}
