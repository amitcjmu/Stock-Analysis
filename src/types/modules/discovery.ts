/**
 * Discovery Flow Module Namespace
 * 
 * TypeScript module boundaries for Discovery Flow components, hooks, and API types.
 * Provides clear architectural boundaries with enhanced type safety.
 */

import { ReactNode } from 'react';

// Base types for the Discovery module
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
}

export interface MultiTenantContext {
  clientAccountId: string;
  engagementId: string;
  userId: string;
}

export interface ResponseMetadata {
  timestamp: string;
  requestId: string;
  version: string;
  totalCount?: number;
  pageSize?: number;
  currentPage?: number;
}

// Discovery Flow namespace declaration
declare namespace DiscoveryFlow {
  // Component namespace
  namespace Components {
    // Field Mappings component types
    interface FieldMappingsTabProps extends BaseComponentProps {
      flowId: string;
      onMappingUpdate?: (mapping: FieldMapping) => void;
      showAdvanced?: boolean;
      readonly?: boolean;
    }

    interface MappingFiltersProps extends BaseComponentProps {
      filters: MappingFilter[];
      onFilterChange: (filters: MappingFilter[]) => void;
      availableFields: string[];
      searchTerm?: string;
      onSearchChange?: (term: string) => void;
    }

    interface AttributeMappingTableProps extends BaseComponentProps {
      mappings: FieldMapping[];
      onMappingChange: (mappingId: string, newTarget: string) => void;
      onApproveMapping: (mappingId: string) => void;
      onRejectMapping: (mappingId: string, reason?: string) => void;
      loading?: boolean;
      error?: string | null;
    }

    interface CriticalAttributesTabProps extends BaseComponentProps {
      attributes: CriticalAttribute[];
      onAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
      flowId: string;
      readonly?: boolean;
    }

    interface NavigationTabsProps extends BaseComponentProps {
      activeTab: string;
      onTabChange: (tab: string) => void;
      tabs: TabDefinition[];
      disabled?: boolean;
    }

    interface CrewAnalysisPanelProps extends BaseComponentProps {
      analysis: CrewAnalysis[];
      onTriggerAnalysis: () => void;
      loading?: boolean;
      error?: string | null;
    }

    interface TrainingProgressTabProps extends BaseComponentProps {
      progress: TrainingProgress;
      onProgressUpdate: (updates: Partial<TrainingProgress>) => void;
      flowId: string;
    }

    // Navigation components
    interface NavigationSidebarProps extends BaseComponentProps {
      currentRoute: string;
      onNavigate: (route: string) => void;
      collapsed?: boolean;
      onToggleCollapse?: () => void;
    }

    interface FlowBreadcrumbsProps extends BaseComponentProps {
      flowId: string;
      currentPhase: string;
      phases: PhaseDefinition[];
      onPhaseSelect?: (phase: string) => void;
    }

    // Data components
    interface DataImportSelectorProps extends BaseComponentProps {
      availableImports: DataImport[];
      selectedImportId: string | null;
      onImportSelect: (importId: string) => void;
      loading?: boolean;
      error?: string | null;
    }

    interface FileUploadAreaProps extends BaseComponentProps {
      onFileUpload: (files: File[]) => void;
      acceptedTypes?: string[];
      maxFileSize?: number;
      multiple?: boolean;
      disabled?: boolean;
    }

    interface RawDataTableProps extends BaseComponentProps {
      data: any[];
      columns: ColumnDefinition[];
      loading?: boolean;
      error?: string | null;
      onRowSelect?: (row: any) => void;
      selectable?: boolean;
    }
  }

  // Hook namespace
  namespace Hooks {
    interface UseAttributeMappingReturn {
      // Core data
      mappings: FieldMapping[];
      criticalAttributes: CriticalAttribute[];
      crewAnalysis: CrewAnalysis[];
      agenticData: { attributes: any[] };
      
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

    interface UseFlowDetectionParams {
      autoDetect?: boolean;
      fallbackToSession?: boolean;
      requirePhase?: string;
      skipValidation?: boolean;
    }

    interface UseFlowDetectionReturn {
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

    interface UseFieldMappingsParams {
      flowId: string;
      dataImportId?: string;
      autoRefresh?: boolean;
      includeValidation?: boolean;
    }

    interface UseFieldMappingsReturn {
      mappings: FieldMapping[];
      loading: boolean;
      error: string | null;
      refetch: () => Promise<void>;
      updateMapping: (mappingId: string, updates: Partial<FieldMapping>) => Promise<void>;
      deleteMapping: (mappingId: string) => Promise<void>;
      bulkUpdateMappings: (updates: BulkMappingUpdate[]) => Promise<void>;
    }

    interface UseCriticalAttributesParams {
      flowId: string;
      autoRefresh?: boolean;
      filterByStatus?: string[];
    }

    interface UseCriticalAttributesReturn {
      attributes: CriticalAttribute[];
      loading: boolean;
      error: string | null;
      refetch: () => Promise<void>;
      updateAttribute: (attributeId: string, updates: Partial<CriticalAttribute>) => Promise<void>;
      validateAttribute: (attributeId: string) => Promise<ValidationResult>;
    }

    interface UseImportDataParams {
      flowId: string;
      includeMetadata?: boolean;
      pageSize?: number;
    }

    interface UseImportDataReturn {
      imports: DataImport[];
      selectedImport: DataImport | null;
      loading: boolean;
      error: string | null;
      selectImport: (importId: string) => Promise<void>;
      refreshImports: () => Promise<void>;
      uploadFile: (file: File) => Promise<DataImport>;
      deleteImport: (importId: string) => Promise<void>;
    }

    interface AttributeMappingActions {
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
  }

  // API namespace
  namespace API {
    interface FieldMappingRequest {
      flowId: string;
      mappings: FieldMappingInput[];
      context: MultiTenantContext;
      validation?: ValidationOptions;
    }

    interface FieldMappingResponse {
      success: boolean;
      data: FieldMapping[];
      metadata: ResponseMetadata;
      validationResults?: ValidationResult[];
    }

    interface FlowInitializationRequest {
      flowName: string;
      flowDescription?: string;
      context: MultiTenantContext;
      configuration?: FlowConfiguration;
    }

    interface FlowInitializationResponse {
      success: boolean;
      flowId: string;
      initialState: FlowState;
      metadata: ResponseMetadata;
    }

    interface FlowStatusRequest {
      flowId: string;
      context: MultiTenantContext;
      includeDetails?: boolean;
    }

    interface FlowStatusResponse {
      flowId: string;
      status: FlowStatus;
      progress: number;
      currentPhase: string;
      nextPhase?: string;
      phaseCompletion: Record<string, boolean>;
      agentInsights?: AgentInsight[];
      errors?: string[];
      warnings?: string[];
      metadata: ResponseMetadata;
    }

    interface DataImportRequest {
      flowId: string;
      file: File;
      context: MultiTenantContext;
      options?: ImportOptions;
    }

    interface DataImportResponse {
      success: boolean;
      importId: string;
      recordsProcessed: number;
      recordsValid: number;
      errors?: ImportError[];
      metadata: ResponseMetadata;
    }

    interface CriticalAttributesRequest {
      flowId: string;
      context: MultiTenantContext;
      includeValidation?: boolean;
    }

    interface CriticalAttributesResponse {
      success: boolean;
      attributes: CriticalAttribute[];
      validationResults?: ValidationResult[];
      metadata: ResponseMetadata;
    }

    interface CrewAnalysisRequest {
      flowId: string;
      context: MultiTenantContext;
      analysisType: 'mapping' | 'validation' | 'optimization';
      parameters?: Record<string, any>;
    }

    interface CrewAnalysisResponse {
      success: boolean;
      analysis: CrewAnalysis[];
      recommendations?: string[];
      metadata: ResponseMetadata;
    }
  }

  // Data Models namespace
  namespace Models {
    interface FieldMapping {
      id: string;
      sourceField: string;
      targetField: string;
      mappingType: 'direct' | 'transformed' | 'calculated' | 'conditional';
      transformationLogic?: string;
      validationRules?: ValidationRule[];
      confidence: number;
      status: 'pending' | 'approved' | 'rejected' | 'in_review';
      createdAt: string;
      updatedAt: string;
      createdBy: string;
      reviewedBy?: string;
      rejectionReason?: string;
    }

    interface CriticalAttribute {
      id: string;
      name: string;
      description: string;
      dataType: string;
      isRequired: boolean;
      defaultValue?: any;
      validationRules: ValidationRule[];
      mappingStatus: 'mapped' | 'unmapped' | 'partially_mapped';
      sourceFields: string[];
      targetField?: string;
      businessRules?: BusinessRule[];
      priority: 'critical' | 'high' | 'medium' | 'low';
      category: string;
      tags: string[];
      metadata: Record<string, any>;
    }

    interface CrewAnalysis {
      id: string;
      analysisType: string;
      findings: AnalysisFinding[];
      recommendations: string[];
      confidence: number;
      executedAt: string;
      executedBy: string;
      status: 'completed' | 'in_progress' | 'failed';
      metadata: Record<string, any>;
    }

    interface MappingProgress {
      totalMappings: number;
      completedMappings: number;
      pendingMappings: number;
      approvedMappings: number;
      rejectedMappings: number;
      progressPercentage: number;
      lastUpdated: string;
    }

    interface FlowState {
      flowId: string;
      currentPhase: string;
      nextPhase?: string;
      previousPhase?: string;
      phaseCompletion: Record<string, boolean>;
      phaseData: Record<string, any>;
      agentInsights: Record<string, AgentInsight[]>;
      agentProgress: Record<string, number>;
      agentStatus: Record<string, string>;
      createdAt: string;
      updatedAt: string;
    }

    interface DiscoveryFlowData {
      id: string;
      flowId: string;
      clientAccountId: string;
      engagementId: string;
      userId: string;
      flowName: string;
      flowDescription?: string;
      status: FlowStatus;
      progress: number;
      phases: PhaseCompletion;
      currentPhase: string;
      nextPhase?: string;
      createdAt: string;
      updatedAt: string;
      completedAt?: string;
    }

    interface DataImport {
      id: string;
      flowId: string;
      fileName: string;
      fileSize: number;
      fileType: string;
      recordsTotal: number;
      recordsProcessed: number;
      recordsValid: number;
      recordsInvalid: number;
      status: 'uploading' | 'processing' | 'completed' | 'failed';
      errors?: ImportError[];
      uploadedAt: string;
      processedAt?: string;
      uploadedBy: string;
    }

    interface AgentClarification {
      id: string;
      agentId: string;
      question: string;
      context: string;
      priority: 'high' | 'medium' | 'low';
      status: 'pending' | 'answered' | 'dismissed';
      response?: string;
      createdAt: string;
      answeredAt?: string;
    }

    interface ValidationResult {
      isValid: boolean;
      errors: ValidationError[];
      warnings: ValidationWarning[];
      score: number;
      details: Record<string, any>;
    }

    interface TabDefinition {
      id: string;
      label: string;
      icon?: string;
      disabled?: boolean;
      badge?: string | number;
    }

    interface PhaseDefinition {
      id: string;
      name: string;
      description: string;
      order: number;
      dependencies: string[];
      estimatedDuration: number;
      status: 'not_started' | 'in_progress' | 'completed' | 'failed';
    }

    interface ColumnDefinition {
      id: string;
      header: string;
      accessor: string;
      type: 'text' | 'number' | 'boolean' | 'date' | 'custom';
      sortable?: boolean;
      filterable?: boolean;
      width?: number;
      render?: (value: any, row: any) => ReactNode;
    }

    // Supporting types
    interface MappingFilter {
      field: string;
      operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith';
      value: any;
    }

    interface FieldMappingInput {
      sourceField: string;
      targetField: string;
      mappingType: string;
      transformationLogic?: string;
      validationRules?: ValidationRule[];
    }

    interface ValidationOptions {
      strict?: boolean;
      includeWarnings?: boolean;
      validateTransformations?: boolean;
    }

    interface FlowConfiguration {
      autoAdvance?: boolean;
      validationLevel?: 'strict' | 'normal' | 'lenient';
      parallelProcessing?: boolean;
      notificationSettings?: NotificationSettings;
    }

    interface ImportOptions {
      skipValidation?: boolean;
      batchSize?: number;
      delimiter?: string;
      encoding?: string;
    }

    interface ImportError {
      row: number;
      column: string;
      message: string;
      severity: 'error' | 'warning';
    }

    interface ValidationRule {
      type: string;
      parameters: Record<string, any>;
      message: string;
    }

    interface BusinessRule {
      id: string;
      name: string;
      description: string;
      logic: string;
      priority: number;
    }

    interface AnalysisFinding {
      type: string;
      description: string;
      severity: 'critical' | 'high' | 'medium' | 'low';
      recommendation: string;
      impact: string;
    }

    interface AgentInsight {
      agentId: string;
      insight: string;
      confidence: number;
      timestamp: string;
      context: Record<string, any>;
    }

    interface PhaseCompletion {
      dataImportCompleted: boolean;
      attributeMappingCompleted: boolean;
      dataCleansingCompleted: boolean;
      inventoryCompleted: boolean;
      dependenciesCompleted: boolean;
      techDebtCompleted: boolean;
    }

    interface ValidationError {
      field: string;
      message: string;
      code: string;
      severity: 'error' | 'warning';
    }

    interface ValidationWarning {
      field: string;
      message: string;
      code: string;
      suggestion?: string;
    }

    interface NotificationSettings {
      emailEnabled: boolean;
      slackEnabled: boolean;
      webhookUrl?: string;
    }

    interface BulkMappingUpdate {
      mappingId: string;
      updates: Partial<FieldMapping>;
    }

    interface MappingApprovalStatus {
      total: number;
      approved: number;
      rejected: number;
      pending: number;
      canProceed: boolean;
    }

    interface TrainingProgress {
      totalSamples: number;
      processedSamples: number;
      accuracy: number;
      lastTrainingRun: string;
      modelVersion: string;
    }

    type FlowStatus = 'active' | 'completed' | 'failed' | 'paused' | 'waiting_for_user' | 'migrated';
  }
}

// Export the namespace for external use
export { DiscoveryFlow };

// Export individual types for convenience
export type {
  BaseComponentProps,
  MultiTenantContext,
  ResponseMetadata
};

// Re-export Models for easier access
export namespace DiscoveryFlowTypes {
  export import Models = DiscoveryFlow.Models;
  export import Components = DiscoveryFlow.Components;
  export import Hooks = DiscoveryFlow.Hooks;
  export import API = DiscoveryFlow.API;
}