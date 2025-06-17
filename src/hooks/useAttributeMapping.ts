import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '@/config/api';

// Types
export interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
}

export interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
}

export interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  accuracy: number;
}

export interface CriticalAttributeStatus {
  name: string;
  description: string;
  category: string;
  required: boolean;
  status: 'mapped' | 'partially_mapped' | 'unmapped';
  mapped_to: string | null;
  source_field: string | null;
  confidence: number | null;
  quality_score: number;
  completeness_percentage: number;
  mapping_type: string | null;
  ai_suggestion: string | null;
  business_impact: string;
  migration_critical: boolean;
}

export interface CriticalAttributesData {
  attributes: CriticalAttributeStatus[];
  statistics: {
    total_attributes: number;
    mapped_count: number;
    pending_count: number;
    unmapped_count: number;
    migration_critical_count: number;
    migration_critical_mapped: number;
    overall_completeness: number;
    avg_quality_score: number;
    assessment_ready: boolean;
  };
  recommendations: {
    next_priority: string;
    assessment_readiness: string;
    quality_improvement: string;
  };
  agent_status?: {
    discovery_flow_active: boolean;
    field_mapping_crew_status: string;
    learning_system_status: string;
    crew_agents_used?: string[];
    crew_agents_active?: string[];
  };
  crew_insights?: {
    analysis_method: string;
    crew_result_summary: string;
    confidence_level: string;
    learning_applied: boolean;
  };
  analysis_progress?: {
    phase: string;
    estimated_completion: string;
    current_task: string;
  };
  last_updated: string;
}

// Hook to fetch critical attributes status (LEGACY - static heuristics)
export const useCriticalAttributes = () => {
  return useQuery<CriticalAttributesData>({
    queryKey: ['critical-attributes'],
    queryFn: async () => {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS);
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
};

// 🤖 NEW: Hook to fetch AGENTIC critical attributes (agent-driven intelligence)
export const useAgenticCriticalAttributes = () => {
  return useQuery<CriticalAttributesData>({
    queryKey: ['agentic-critical-attributes'],
    queryFn: async () => {
      try {
        // Try the new agentic endpoint first
        const response = await apiCall('/api/v1/data-import/agentic-critical-attributes');
        return response;
      } catch (error) {
        console.warn('Agentic endpoint not available, falling back to legacy endpoint:', error);
        // Fallback to legacy endpoint if agentic is not available
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS);
        return response;
      }
    },
    staleTime: 30 * 1000, // 30 seconds (shorter for agent analysis)
    refetchInterval: (data) => {
      // Auto-refresh if agents are actively analyzing
      if (data?.agent_status?.discovery_flow_active || 
          data?.agent_status?.field_mapping_crew_status === 'analyzing') {
        return 10 * 1000; // 10 seconds
      }
      return false; // No auto-refresh when idle
    },
    refetchOnWindowFocus: true // Refresh when user returns to tab
  });
};

// Hook to manually trigger Field Mapping Crew analysis
export const useTriggerFieldMappingCrew = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const response = await apiCall('/api/v1/data-import/trigger-field-mapping-crew', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response;
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['agentic-critical-attributes'] });
      queryClient.invalidateQueries({ queryKey: ['critical-attributes'] });
    }
  });
};

// Hook to fetch latest imported data
export const useLatestImport = () => {
  return useQuery({
    queryKey: ['latest-import'],
    queryFn: async () => {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
      return response?.data || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
};

// Hook to generate field mappings
export const useGenerateFieldMappings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ columns, sampleData }: { columns: string[], sampleData: any[] }) => {
      // This is a placeholder - replace with actual API call
      const response = await apiCall('data-import/generate-field-mappings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          columns,
          sample_data: sampleData
        })
      });
      return response as FieldMapping[];
    },
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['field-mappings'] });
    }
  });
};

// Hook to update a field mapping
export const useUpdateFieldMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, updates }: { id: string, updates: Partial<FieldMapping> }) => {
      const response = await apiCall(`/api/v1/data-import/field-mappings/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });
      return response as FieldMapping;
    },
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['field-mappings'] });
      queryClient.invalidateQueries({ queryKey: ['critical-attributes'] });
    }
  });
};

// Hook to analyze data with AI
export const useAnalyzeData = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { columns: string[], sampleData: any[] }) => {
      // This is a placeholder - replace with actual API call
      const response = await apiCall('data-import/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      return response as { analysis: CrewAnalysis[], progress: MappingProgress };
    },
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['analysis'] });
      queryClient.invalidateQueries({ queryKey: ['mapping-progress'] });
    }
  });
}; 