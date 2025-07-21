/**
 * Types for ApplicationSelector functionality
 * Extracted from ApplicationSelector.tsx for modularization
 */

export interface Application {
  id: number;
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

export interface AnalysisQueue {
  id: string;
  name: string;
  applications: number[];
  status: 'pending' | 'in_progress' | 'completed' | 'paused';
  created_at: Date;
  priority: number;
  estimated_duration?: number;
}

export interface ApplicationSelectorProps {
  applications: Application[];
  selectedApplications: number[];
  onSelectionChange: (selectedIds: number[]) => void;
  onStartAnalysis: (applicationIds: number[], queueName?: string) => void;
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

export interface ApplicationTableProps {
  applications: Application[];
  selectedApplications: number[];
  onSelectApplication: (appId: number) => void;
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