import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface AssetMetrics {
  total_count: number;
  by_type: Record<string, number>;
  by_environment: Record<string, number>;
  by_criticality: Record<string, number>;
  by_status: Record<string, number>;
}

export interface WorkflowAnalysis {
  discovery: Record<string, number>;
  mapping: Record<string, number>;
  cleanup: Record<string, number>;
  assessment_ready: Record<string, number>;
  completion_percentages: {
    discovery: number;
    mapping: number;
    cleanup: number;
    assessment_ready: number;
  };
}

export interface MissingCriticalData {
  asset_id: string;
  asset_name: string;
  missing_fields: string[];
  completeness: number;
}

export interface DataQuality {
  overall_score: number;
  completeness_by_field: Record<string, number>;
  missing_critical_data: MissingCriticalData[];
}

export interface MigrationReadiness {
  ready_for_assessment: number;
  needs_more_data: number;
  has_dependencies: number;
  needs_modernization: number;
  readiness_by_type: Record<string, {
    ready: number;
    not_ready: number;
    percentage: number;
  }>;
}

export interface DependencyChain {
  chain_id: string;
  assets: string[];
  chain_type: 'circular' | 'deep' | 'branching';
  depth: number;
  critical_path: boolean;
  affected_services: string[];
}

export interface DependencyAnalysis {
  total_dependencies: number;
  application_dependencies: number;
  server_dependencies: number;
  database_dependencies: number;
  complex_dependency_chains: Array<DependencyChain>;
  orphaned_assets: string[];
}

export interface AIInsights {
  available: boolean;
  analysis_result?: unknown;
  confidence_score?: number;
}

export interface Recommendation {
  type: string;
  priority: string;
  title: string;
  description: string;
  action: string;
  affected_assets?: number;
}

export interface AssessmentReadiness {
  ready: boolean;
  overall_score: number;
  criteria: {
    mapping_completion: { current: number; required: number; met: boolean };
    cleanup_completion: { current: number; required: number; met: boolean };
    data_quality: { current: number; required: number; met: boolean };
  };
  next_steps: string[];
}

export interface AssetInventoryData {
  status: string;
  analysis_timestamp: string;
  total_assets: number;
  asset_metrics: AssetMetrics;
  workflow_analysis: WorkflowAnalysis;
  data_quality: DataQuality;
  migration_readiness: MigrationReadiness;
  dependency_analysis: DependencyAnalysis;
  ai_insights: AIInsights;
  recommendations: Recommendation[];
  assessment_ready: AssessmentReadiness;
}

const defaultAssetInventoryData: Partial<AssetInventoryData> = {
  status: 'loading',
  analysis_timestamp: new Date().toISOString(),
  total_assets: 0,
  asset_metrics: {
    total_count: 0,
    by_type: {},
    by_environment: {},
    by_criticality: {},
    by_status: {}
  },
  workflow_analysis: {
    discovery: {},
    mapping: {},
    cleanup: {},
    assessment_ready: {},
    completion_percentages: {
      discovery: 0,
      mapping: 0,
      cleanup: 0,
      assessment_ready: 0
    }
  },
  data_quality: {
    overall_score: 0,
    completeness_by_field: {},
    missing_critical_data: []
  },
  migration_readiness: {
    ready_for_assessment: 0,
    needs_more_data: 0,
    has_dependencies: 0,
    needs_modernization: 0,
    readiness_by_type: {}
  },
  dependency_analysis: {
    total_dependencies: 0,
    application_dependencies: 0,
    server_dependencies: 0,
    database_dependencies: 0,
    complex_dependency_chains: [],
    orphaned_assets: []
  },
  ai_insights: {
    available: false
  },
  recommendations: [],
  assessment_ready: {
    ready: false,
    overall_score: 0,
    criteria: {
      mapping_completion: { current: 0, required: 0, met: false },
      cleanup_completion: { current: 0, required: 0, met: false },
      data_quality: { current: 0, required: 0, met: false }
    },
    next_steps: []
  }
};

export const useAssetInventoryAnalysis = () => {
  const { getContextHeaders } = useAuth();
  
  return useQuery<AssetInventoryData>({
    queryKey: ['asset-inventory-analysis'],
    queryFn: async () => {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS + '/comprehensive-analysis', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response as AssetInventoryData;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    placeholderData: defaultAssetInventoryData as AssetInventoryData
  });
};

export const useRefreshAssetInventory = () => {
  const queryClient = useQueryClient();
  const { getContextHeaders } = useAuth();
  
  return async () => {
    // Invalidate the query to trigger a refetch
    await queryClient.invalidateQueries({ queryKey: ['asset-inventory-analysis'] });
    
    // Optionally force a refetch
    const data = await queryClient.fetchQuery({
      queryKey: ['asset-inventory-analysis'],
      queryFn: async () => {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS + '/comprehensive-analysis', {
          method: 'GET',
          headers: getContextHeaders()
        });
        return response as AssetInventoryData;
      }
    });
    
    return data;
  };
};

// Export the main hook as useAssetInventory for backward compatibility
export const useAssetInventory = useAssetInventoryAnalysis; 