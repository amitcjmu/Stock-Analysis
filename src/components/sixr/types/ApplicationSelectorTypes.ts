/**
 * Types for ApplicationSelector functionality
 * Extracted from ApplicationSelector.tsx for modularization
 */

// Bug #813 fix: Changed id from number to string (UUID) for backend compatibility
export interface Application {
  id: string; // UUID from assets table
  name: string;
  description?: string;
  technology_stack: string[];
  department: string;
  business_unit?: string;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  complexity_score?: number;
  user_count?: number;
  data_volume?: string;
  compliance_requirements?: string[];
  dependencies?: string[];
  last_updated?: Date;
  analysis_status?: 'not_analyzed' | 'in_progress' | 'completed' | 'failed';
  recommended_strategy?: string;
  confidence_score?: number;
}

// Bug #813 fix: Changed applications from number[] to string[] (UUIDs)
export interface AnalysisQueue {
  id: string;
  name: string;
  applications: string[]; // UUID strings
  status: 'pending' | 'in_progress' | 'completed' | 'paused';
  created_at: Date;
  priority: number;
  estimated_duration?: number;
}

// Bug #813 fix: Changed all number[] to string[] (UUIDs)
export interface ApplicationSelectorProps {
  applications: Application[];
  selectedApplications: string[]; // UUID strings
  onSelectionChange: (selectedIds: string[]) => void;
  onStartAnalysis: (applicationIds: string[], queueName?: string) => void;
  analysisQueues?: AnalysisQueue[];
  onQueueAction?: (queueId: string, action: 'start' | 'pause' | 'cancel') => void;
  maxSelections?: number;
  showQueue?: boolean;
  className?: string;
}

export interface ApplicationFilters {
  searchTerm: string;
  departmentFilter: string;
  criticalityFilter: string;
  statusFilter: string;
  technologyFilter: string;
}

export interface FilteredApplicationsResult {
  filteredApplications: Application[];
  departments: string[];
  technologies: string[];
}

// Bug #813 fix: Changed selectedApplications and appId from number to string (UUID)
export interface ApplicationTableProps {
  applications: Application[];
  selectedApplications: string[]; // UUID strings
  onSelectApplication: (appId: string) => void;
  onSelectAll: () => void;
}

export interface QueueManagementProps {
  analysisQueues: AnalysisQueue[];
  applications: Application[];
  onQueueAction?: (queueId: string, action: 'start' | 'pause' | 'cancel') => void;
}

export interface FilterPanelProps {
  filters: ApplicationFilters;
  onFiltersChange: (filters: Partial<ApplicationFilters>) => void;
  departments: string[];
  technologies: string[];
  showAdvanced: boolean;
  onToggleAdvanced: () => void;
  onClearFilters: () => void;
}
