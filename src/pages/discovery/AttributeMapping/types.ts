// TypeScript interfaces for Attribute Mapping
export interface AttributeMappingState {
  agenticData: unknown;
  fieldMappings: unknown[];
  crewAnalysis: unknown;
  mappingProgress: unknown;
  criticalAttributes: unknown[];
  flowState: unknown;
  flowId: string | null;
  availableDataImports: unknown[];
  selectedDataImportId: string | null;
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  agenticError: unknown;
  flowStateError: unknown;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: unknown[];
}

export interface AttributeMappingActions {
  handleTriggerFieldMappingCrew: () => void;
  handleApproveMapping: (mappingId: string) => void;
  handleRejectMapping: (mappingId: string) => void;
  handleMappingChange: (mappingId: string, updates: unknown) => void;
  handleAttributeUpdate: (attributeId: string, updates: unknown) => void;
  handleDataImportSelection: (importId: string) => void;
  refetchAgentic: () => void;
  refetchCriticalAttributes: () => void;
  canContinueToDataCleansing: boolean;
}

export interface NavigationState {
  activeTab: 'mappings' | 'data' | 'critical';
  setActiveTab: (tab: 'mappings' | 'data' | 'critical') => void;
}

export interface SessionInfo {
  flowId: string | null;
  availableDataImports: unknown[];
  selectedDataImportId: string | null;
  hasMultipleSessions: boolean;
}

export interface AttributeMappingProps {
  // Computed state props
  isLoading: boolean;
  hasError: boolean;
  errorMessage: string | undefined;
  hasData: boolean;
  isFlowNotFound: boolean;
  hasSessionData: boolean;
  hasUploadedData: boolean;
  sessionInfo: SessionInfo;
  
  // Handlers
  onTriggerAnalysis: () => void;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string) => void;
  onMappingChange: (mappingId: string, updates: unknown) => void;
  onAttributeUpdate: (attributeId: string, updates: unknown) => void;
  onDataImportSelection: (importId: string) => void;
  onRefetchAgentic: () => void;
  onContinueToDataCleansing: () => void;
}