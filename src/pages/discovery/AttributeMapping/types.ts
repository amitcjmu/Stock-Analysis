import type {
  FieldMapping,
  CriticalAttribute,
  MappingAnalytics,
  MappingProgress,
  MappingConflict
} from '../../../types/hooks/discovery/attribute-mapping-hooks';
import type { ApiError } from '../../../types/shared/api-types';

// TypeScript interfaces for Attribute Mapping
export interface AttributeMappingState {
  agenticData: AgenticData | null;
  fieldMappings: FieldMapping[];
  crewAnalysis: CrewAnalysisResult | null;
  mappingProgress: MappingProgress | null;
  criticalAttributes: CriticalAttribute[];
  flowState: FlowState | null;
  flowId: string | null;
  availableDataImports: DataImport[];
  selectedDataImportId: string | null;
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  agenticError: ApiError | null;
  flowStateError: ApiError | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: FlowInfo[];
}

// Supporting interface definitions
export interface AgenticData {
  attributes: AttributeInfo[];
  statistics: AttributeStatistics;
  metadata: Record<string, unknown>;
  confidence: number;
  lastUpdated: string;
}

export interface AttributeInfo {
  id: string;
  name: string;
  type: string;
  isRequired: boolean;
  sampleValues: string[];
  confidence: number;
  metadata: Record<string, unknown>;
}

export interface AttributeStatistics {
  totalAttributes: number;
  requiredAttributes: number;
  optionalAttributes: number;
  mappedAttributes: number;
  unmappedAttributes: number;
}

export interface CrewAnalysisResult {
  mappingRecommendations: MappingRecommendation[];
  confidence: number;
  analysisMetadata: Record<string, unknown>;
  processingTime: number;
  status: 'completed' | 'in_progress' | 'failed';
}

export interface MappingRecommendation {
  sourceField: string;
  targetField: string;
  confidence: number;
  reasoning: string;
  alternatives: AlternativeMapping[];
}

export interface AlternativeMapping {
  targetField: string;
  confidence: number;
  reasoning: string;
}

export interface FlowState {
  id: string;
  phase: string;
  status: 'active' | 'completed' | 'failed' | 'paused';
  field_mappings: FieldMappingData[];
  data_import_completed: boolean;
  metadata: Record<string, unknown>;
  lastUpdated: string;
}

export interface FieldMappingData {
  sourceField: string;
  targetField: string;
  mappingType: string;
  status: string;
  confidence: number;
}

export interface DataImport {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  recordCount: number;
  createdAt: string;
  metadata: Record<string, unknown>;
}

export interface FlowInfo {
  id: string;
  name: string;
  status: string;
  phase: string;
  createdAt: string;
  metadata: Record<string, unknown>;
}

export interface AttributeMappingActions {
  handleTriggerFieldMappingCrew: () => void;
  handleApproveMapping: (mappingId: string) => void;
  handleRejectMapping: (mappingId: string) => void;
  handleMappingChange: (mappingId: string, updates: Partial<FieldMapping>) => void;
  handleAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
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
  availableDataImports: DataImport[];
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
  onMappingChange: (mappingId: string, updates: Partial<FieldMapping>) => void;
  onAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
  onDataImportSelection: (importId: string) => void;
  onRefetchAgentic: () => void;
  onContinueToDataCleansing: () => void;
}