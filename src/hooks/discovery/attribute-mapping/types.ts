// Re-export all types from individual hooks for centralized type management
export type { FlowDetectionResult } from './useFlowDetection';
export type { FieldMapping, FieldMappingsResult } from './useFieldMappings';
export type { ImportDataResult } from './useImportData';
export type { CriticalAttribute, CriticalAttributesResult } from './useCriticalAttributes';
export type { AttributeMappingActionsResult } from './useAttributeMappingActions';
export type { MappingProgress, AttributeMappingStateResult } from './useAttributeMappingState';

// Main composition type that matches the original hook's return type
export interface AttributeMappingLogicResult {
  // Data
  agenticData: { attributes: unknown[] };
  fieldMappings: FieldMapping[];
  crewAnalysis: unknown[];
  mappingProgress: MappingProgress;
  criticalAttributes: CriticalAttribute[];
  
  // Flow state
  flowState: unknown;
  flow: unknown;
  flowId: string | null;
  dataImportId: string | null;
  availableDataImports: unknown[];
  selectedDataImportId: string | null;
  
  // Auto-detection info
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: unknown[];
  
  // Loading states
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  
  // Error states
  agenticError: unknown;
  flowStateError: unknown;
  
  // Action handlers
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: unknown) => Promise<void>;
  handleDataImportSelection: (importId: string) => Promise<void>;
  refetchAgentic: () => Promise<any>;
  refetchCriticalAttributes: () => Promise<any>;
  canContinueToDataCleansing: () => boolean;
  checkMappingApprovalStatus: (dataImportId: string) => Promise<any>;
  
  // Flow status
  hasActiveFlow: boolean;
  currentPhase: string;
  flowProgress: number;
  
  // Agent clarifications
  agentClarifications: unknown[];
  isClarificationsLoading: boolean;
  clarificationsError: unknown;
  refetchClarifications: () => Promise<void>;
}