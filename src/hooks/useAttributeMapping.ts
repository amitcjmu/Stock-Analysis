import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../config/api';
import { useAuth } from '../contexts/AuthContext';

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
  const { user, client, engagement } = useAuth();
  
  return useQuery<CriticalAttributesData>({
    queryKey: ['agentic-critical-attributes', client?.id, engagement?.id],
    queryFn: async () => {
      // 🚨 MULTI-TENANCY FIX: Ensure context is available before API call
      if (!client?.id || !engagement?.id) {
        console.warn('⚠️ Skipping agentic API call - missing context:', { 
          client: client?.id, 
          engagement: engagement?.id 
        });
        throw new Error('Context not available - client or engagement missing');
      }
      
      console.log('🤖 Making agentic API call with context:', { 
        client: client.id, 
        engagement: engagement.id 
      });
      
      try {
        // Create a timeout promise
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), 15000); // 15 second timeout
        });

        // Try the new agentic endpoint first with timeout
        const apiCallPromise = apiCall('/api/v1/data-import/agentic-critical-attributes');
        
        const response = await Promise.race([apiCallPromise, timeoutPromise]);
        return response;
      } catch (error) {
        console.warn('Agentic endpoint failed or timed out, falling back to basic analysis:', error);
        
        // Quick fallback to prevent indefinite loading
        try {
          const fallbackResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS);
          return fallbackResponse;
        } catch (fallbackError) {
          console.warn('Fallback also failed, returning empty state:', fallbackError);
          
          // Return minimal data to unblock the UI
          return {
            attributes: [],
            statistics: {
              total_attributes: 0,
              mapped_count: 0,
              pending_count: 0,
              unmapped_count: 0,
              migration_critical_count: 0,
              migration_critical_mapped: 0,
              overall_completeness: 0,
              avg_quality_score: 0,
              assessment_ready: false,
            },
            recommendations: {
              next_priority: "Upload data to enable analysis",
              assessment_readiness: "No data available for analysis",
              quality_improvement: "Import CMDB data to get started"
            },
            last_updated: new Date().toISOString()
          };
        }
      }
    },
    // 🚨 CRITICAL: Only enable query when context is available
    enabled: !!(client?.id && engagement?.id),
    staleTime: Infinity, // Never automatically consider data stale
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
    refetchInterval: false, // DISABLED: No automatic polling
    refetchOnWindowFocus: false, // DISABLED: No refetch on focus
    refetchOnMount: false, // DISABLED: No refetch on mount after initial load
    refetchOnReconnect: false, // DISABLED: No refetch on network reconnect
    retry: 1, // Minimal retries
    retryDelay: 2000 // 2 second delay between retries
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