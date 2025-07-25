export interface AnalysisHistoryItem {
  id: number;
  application_name: string;
  application_id: number;
  department: string;
  business_unit?: string;
  analysis_date: Date;
  analyst: string;
  status: 'completed' | 'in_progress' | 'failed' | 'archived';
  recommended_strategy: string;
  confidence_score: number;
  iteration_count: number;
  estimated_effort: string;
  estimated_timeline: string;
  estimated_cost_impact: string;
  parameters: {
    business_value: number;
    technical_complexity: number;
    migration_urgency: number;
    compliance_requirements: number;
    cost_sensitivity: number;
    risk_tolerance: number;
    innovation_priority: number;
    application_type: string;
  };
  key_factors: string[];
  next_steps: string[];
  tags?: string[];
  notes?: string;
}

export interface AnalysisHistoryProps {
  analyses: AnalysisHistoryItem[];
  onExport?: (selectedIds: number[], format: 'csv' | 'pdf' | 'json') => void;
  onDelete?: (analysisId: number) => void;
  onArchive?: (analysisId: number) => void;
  onCompare?: (analysisIds: number[]) => void;
  onViewDetails?: (analysisId: number) => void;
  className?: string;
}

export interface FilterState {
  searchTerm: string;
  statusFilter: string;
  strategyFilter: string;
  departmentFilter: string;
  dateRange: string;
}

export interface AnalyticsData {
  total: number;
  completedRate: number;
  avgConfidence: number;
  strategyDistribution: Record<string, number>;
  effortDistribution: Record<string, number>;
  departmentDistribution: Record<string, number>;
}
