// TypeScript interfaces for Attribute Mapping
export interface AttributeMappingState {
  agenticData: any;
  fieldMappings: any[];
  crewAnalysis: any;
  mappingProgress: any;
  criticalAttributes: any[];
  flowState: any;
  flowId: string | null;
  availableDataImports: any[];
  selectedDataImportId: string | null;
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  agenticError: any;
  flowStateError: any;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: any[];
}

export interface AttributeMappingActions {
  handleTriggerFieldMappingCrew: () => void;
  handleApproveMapping: (mappingId: string) => void;
  handleRejectMapping: (mappingId: string) => void;
  handleMappingChange: (mappingId: string, updates: any) => void;
  handleAttributeUpdate: (attributeId: string, updates: any) => void;
  handleDataImportSelection: (importId: string) => void;
  refetchAgentic: () => void;
  canContinueToDataCleansing: boolean;
}

export interface NavigationState {
  activeTab: 'mappings' | 'data' | 'critical';
  setActiveTab: (tab: 'mappings' | 'data' | 'critical') => void;
}

export interface SessionInfo {
  flowId: string | null;
  availableDataImports: any[];
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
  onMappingChange: (mappingId: string, updates: any) => void;
  onAttributeUpdate: (attributeId: string, updates: any) => void;
  onDataImportSelection: (importId: string) => void;
  onRefetchAgentic: () => void;
  onContinueToDataCleansing: () => void;
}