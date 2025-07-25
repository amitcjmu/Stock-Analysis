/**
 * Discovery Flow - Component Types Module
 *
 * React component prop interfaces for all Discovery Flow UI components.
 * Includes field mappings, navigation, data import, and analysis components.
 *
 * Generated with CC - Code Companion
 */

import type { BaseComponentProps } from './base-types'
import type { ColumnDefinition, TabDefinition, PhaseDefinition } from './base-types'

import type { MappingFilter } from './data-models'
import type { FieldMapping, CriticalAttribute, CrewAnalysis, TrainingProgress, DataImport } from './data-models'

// Field Mappings component types
export interface FieldMappingsTabProps extends BaseComponentProps {
  flowId: string;
  onMappingUpdate?: (mapping: FieldMapping) => void;
  showAdvanced?: boolean;
  readonly?: boolean;
}

export interface MappingFiltersProps extends BaseComponentProps {
  filters: MappingFilter[];
  onFilterChange: (filters: MappingFilter[]) => void;
  availableFields: string[];
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
}

export interface AttributeMappingTableProps extends BaseComponentProps {
  mappings: FieldMapping[];
  onMappingChange: (mappingId: string, newTarget: string) => void;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, reason?: string) => void;
  loading?: boolean;
  error?: string | null;
}

export interface CriticalAttributesTabProps extends BaseComponentProps {
  attributes: CriticalAttribute[];
  onAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
  flowId: string;
  readonly?: boolean;
}

export interface NavigationTabsProps extends BaseComponentProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: TabDefinition[];
  disabled?: boolean;
}

export interface CrewAnalysisPanelProps extends BaseComponentProps {
  analysis: CrewAnalysis[];
  onTriggerAnalysis: () => void;
  loading?: boolean;
  error?: string | null;
}

export interface TrainingProgressTabProps extends BaseComponentProps {
  progress: TrainingProgress;
  onProgressUpdate: (updates: Partial<TrainingProgress>) => void;
  flowId: string;
}

// Navigation components
export interface NavigationSidebarProps extends BaseComponentProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export interface FlowBreadcrumbsProps extends BaseComponentProps {
  flowId: string;
  currentPhase: string;
  phases: PhaseDefinition[];
  onPhaseSelect?: (phase: string) => void;
}

// Data components
export interface DataImportSelectorProps extends BaseComponentProps {
  availableImports: DataImport[];
  selectedImportId: string | null;
  onImportSelect: (importId: string) => void;
  loading?: boolean;
  error?: string | null;
}

export interface FileUploadAreaProps extends BaseComponentProps {
  onFileUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  multiple?: boolean;
  disabled?: boolean;
}

export interface RawDataTableProps<T = Record<string, unknown>> extends BaseComponentProps {
  data: T[];
  columns: ColumnDefinition[];
  loading?: boolean;
  error?: string | null;
  onRowSelect?: (row: T) => void;
  selectable?: boolean;
}
