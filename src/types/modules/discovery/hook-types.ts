/**
 * Discovery Flow - Hook Types Module
 * 
 * React hook interfaces, parameters, and return types for Discovery Flow.
 * Contains attribute mapping, flow detection, field mappings, and data import hooks.
 * 
 * Generated with CC - Code Companion
 */

import type { MappingProgress, FlowState, DiscoveryFlowData, MappingApprovalStatus } from './data-models'
import type { FieldMapping, CriticalAttribute, CrewAnalysis, DataImport, AgentClarification, BulkMappingUpdate } from './data-models'

import type { ValidationResult } from './validation-types';

/**
 * Attribute mapping hook return interface
 */
export interface UseAttributeMappingReturn {
  // Core data
  mappings: FieldMapping[];
  criticalAttributes: CriticalAttribute[];
  crewAnalysis: CrewAnalysis[];
  agenticData: { attributes: unknown[] };
  
  // Flow context
  flowId: string | null;
  flowState: FlowState | null;
  flow: DiscoveryFlowData | null;
  
  // Data imports
  dataImportId: string | null;
  availableDataImports: DataImport[];
  selectedDataImportId: string | null;
  
  // Progress tracking
  mappingProgress: MappingProgress;
  flowProgress: number;
  currentPhase: string;
  
  // Loading states
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  
  // Error states
  agenticError: string | null;
  flowStateError: string | null;
  
  // Actions
  actions: AttributeMappingActions;
  
  // Status checks
  hasActiveFlow: boolean;
  canContinueToDataCleansing: () => boolean;
  
  // Agent interactions
  agentClarifications: AgentClarification[];
  isClarificationsLoading: boolean;
  clarificationsError: string | null;
  refetchClarifications: () => Promise<void>;
}

/**
 * Flow detection hook parameters
 */
export interface UseFlowDetectionParams {
  autoDetect?: boolean;
  fallbackToSession?: boolean;
  requirePhase?: string;
  skipValidation?: boolean;
}

/**
 * Flow detection hook return interface
 */
export interface UseFlowDetectionReturn {
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  emergencyFlowId: string | null;
  finalFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: DiscoveryFlowData[];
  isFlowListLoading: boolean;
  flowListError: string | null;
  pathname: string;
  navigate: (path: string) => void;
}

/**
 * Field mappings hook parameters
 */
export interface UseFieldMappingsParams {
  flowId: string;
  dataImportId?: string;
  autoRefresh?: boolean;
  includeValidation?: boolean;
}

/**
 * Field mappings hook return interface
 */
export interface UseFieldMappingsReturn {
  mappings: FieldMapping[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateMapping: (mappingId: string, updates: Partial<FieldMapping>) => Promise<void>;
  deleteMapping: (mappingId: string) => Promise<void>;
  bulkUpdateMappings: (updates: BulkMappingUpdate[]) => Promise<void>;
}

/**
 * Critical attributes hook parameters
 */
export interface UseCriticalAttributesParams {
  flowId: string;
  autoRefresh?: boolean;
  filterByStatus?: string[];
}

/**
 * Critical attributes hook return interface
 */
export interface UseCriticalAttributesReturn {
  attributes: CriticalAttribute[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateAttribute: (attributeId: string, updates: Partial<CriticalAttribute>) => Promise<void>;
  validateAttribute: (attributeId: string) => Promise<ValidationResult>;
}

/**
 * Import data hook parameters
 */
export interface UseImportDataParams {
  flowId: string;
  includeMetadata?: boolean;
  pageSize?: number;
}

/**
 * Import data hook return interface
 */
export interface UseImportDataReturn {
  imports: DataImport[];
  selectedImport: DataImport | null;
  loading: boolean;
  error: string | null;
  selectImport: (importId: string) => Promise<void>;
  refreshImports: () => Promise<void>;
  uploadFile: (file: File) => Promise<DataImport>;
  deleteImport: (importId: string) => Promise<void>;
}

/**
 * Attribute mapping actions interface
 */
export interface AttributeMappingActions {
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => Promise<void>;
  handleDataImportSelection: (importId: string) => Promise<void>;
  refetchAgentic: () => Promise<void>;
  refetchCriticalAttributes: () => Promise<void>;
  checkMappingApprovalStatus: (dataImportId: string) => Promise<MappingApprovalStatus>;
}