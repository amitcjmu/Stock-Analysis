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
  agenticData: { attributes: any[] };
  fieldMappings: FieldMapping[];
  crewAnalysis: any[];
  mappingProgress: MappingProgress;
  criticalAttributes: CriticalAttribute[];
  
  // Flow state
  flowState: any;
  flow: any;
  flowId: string | null;
  dataImportId: string | null;
  availableDataImports: any[];
  selectedDataImportId: string | null;
  
  // Auto-detection info
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: any[];
  
  // Loading states
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  
  // Error states
  agenticError: any;
  flowStateError: any;
  
  // Action handlers
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: any) => Promise<void>;
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
  agentClarifications: any[];
  isClarificationsLoading: boolean;
  clarificationsError: any;
  refetchClarifications: () => Promise<void>;
}