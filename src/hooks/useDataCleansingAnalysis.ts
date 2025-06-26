import { useQuery } from '@tanstack/react-query';
import { apiCall } from '../config/api';
import { useAuth } from '../contexts/AuthContext';

interface DataCleansingQualityIssue {
  id: string;
  field: string;
  issue_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_records: number;
  recommendation: string;
  agent_source: string;
  status: 'pending' | 'resolved' | 'ignored';
}

interface DataCleansingRecommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  fields: string[];
  agent_source: string;
  implementation_steps: string[];
  status: 'pending' | 'applied' | 'rejected';
}

interface DataCleansingMetrics {
  total_records: number;
  cleaned_records: number;
  quality_issues_found: number;
  quality_issues_resolved: number;
  data_quality_score: number;
  quality_score: number; // Add for compatibility
  completeness_percentage: number;
  completion_percentage: number; // Add for compatibility
  consistency_score: number;
  standardization_score: number;
  assessment_ready: boolean;
}

interface DataCleansingResponse {
  quality_issues: DataCleansingQualityIssue[];
  recommendations: DataCleansingRecommendation[];
  metrics: DataCleansingMetrics;
  cleaned_data: any[];
  processing_status: {
    phase: string;
    completion_percentage: number;
    crew_agents_used: string[];
    last_updated: string;
  };
  agent_insights: {
    data_quality_summary: string;
    primary_concerns: string[];
    next_priority: string;
  };
  statistics: {
    total_records: number;
    quality_score: number;
    completion_percentage: number;
    issues_count: number;
    recommendations_count: number;
  };
}

export const useDataCleansingAnalysis = (flowId?: string) => {
  const { client, engagement, user } = useAuth();

  return useQuery({
    queryKey: ['data-cleansing-analysis', client?.id, engagement?.id, flowId],
    queryFn: async (): Promise<DataCleansingResponse> => {
      if (!client?.id || !engagement?.id) {
        throw new Error('Authentication context required');
      }

      // If a specific flow ID is provided, get data cleansing results from that flow
      if (flowId) {
        try {
          const flowStatusResponse = await apiCall(`/discovery/flow/status/${flowId}`, {
            method: 'GET',
            headers: {
              'X-Client-Account-Id': client.id.toString(),
              'X-Engagement-Id': engagement.id.toString(),
              'X-User-Id': user.id.toString()
            }
          });

          if (flowStatusResponse && flowStatusResponse.flow_id) {
            const cleansingResults = flowStatusResponse.data_cleansing_results || flowStatusResponse.results?.data_cleansing;
            
            if (cleansingResults) {
              console.log('✅ Found data cleansing results for flow:', flowId);
              // Transform the real flow data to match the expected interface
              return {
                quality_issues: cleansingResults.quality_issues || [],
                recommendations: cleansingResults.recommendations || [],
                metrics: {
                  total_records: cleansingResults.metadata?.original_records || flowStatusResponse.raw_data?.length || 0,
                  cleaned_records: cleansingResults.metadata?.cleaned_records || 0,
                  quality_issues_found: cleansingResults.quality_issues?.length || 0,
                  quality_issues_resolved: 0,
                  data_quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  completeness_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  consistency_score: 0,
                  standardization_score: 0,
                  assessment_ready: true
                },
                cleaned_data: cleansingResults.cleaned_data || [],
                processing_status: {
                  phase: 'data_cleansing',
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  crew_agents_used: ['Data Cleansing Agent'],
                  last_updated: flowStatusResponse.updated_at || new Date().toISOString()
                },
                agent_insights: {
                  data_quality_summary: 'Real data cleansing analysis from CrewAI Flow',
                  primary_concerns: [],
                  next_priority: 'Review cleansing results'
                },
                statistics: {
                  total_records: cleansingResults.metadata?.original_records || flowStatusResponse.raw_data?.length || 0,
                  quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  issues_count: cleansingResults.quality_issues?.length || 0,
                  recommendations_count: cleansingResults.recommendations?.length || 0
                }
              };
            }
          }
        } catch (error) {
          console.error(`Failed to fetch data cleansing results for flow ${flowId}:`, error);
        }
      }

      // Fallback: try to get the data cleansing results from the active discovery flows
      try {
        const flowResponse = await apiCall('/discovery/flows/active', {
          method: 'GET',
          headers: {
            'X-Client-Account-Id': client.id.toString(),
            'X-Engagement-Id': engagement.id.toString(),
            'X-User-Id': user.id.toString()
          }
        });

        if (flowResponse.success && flowResponse.flow_details && flowResponse.flow_details.length > 0) {
          // Find the most recent flow with data cleansing results
          const flowsWithCleansing = flowResponse.flow_details.filter(flow => 
            flow.phase_completion?.data_cleansing === true || 
            flow.results?.data_cleansing ||
            flow.data_cleansing_results
          );

          if (flowsWithCleansing.length > 0) {
            // Sort by updated_at and get the most recent
            const latestFlow = flowsWithCleansing.sort((a, b) => 
              new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
            )[0];

            const cleansingResults = latestFlow.data_cleansing_results || latestFlow.results?.data_cleansing;
            
            if (cleansingResults) {
              // Transform the real flow data to match the expected interface
              return {
                quality_issues: cleansingResults.quality_issues || [],
                recommendations: cleansingResults.recommendations || [],
                metrics: {
                  total_records: cleansingResults.metadata?.original_records || latestFlow.raw_data?.length || 0,
                  cleaned_records: cleansingResults.metadata?.cleaned_records || 0,
                  quality_issues_found: cleansingResults.quality_issues?.length || 0,
                  quality_issues_resolved: 0,
                  data_quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  completeness_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  consistency_score: 0,
                  standardization_score: 0,
                  assessment_ready: true
                },
                cleaned_data: cleansingResults.cleaned_data || [],
                processing_status: {
                  phase: 'data_cleansing',
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  crew_agents_used: ['Data Cleansing Agent'],
                  last_updated: latestFlow.updated_at || new Date().toISOString()
                },
                agent_insights: {
                  data_quality_summary: 'Real data cleansing analysis from CrewAI Flow',
                  primary_concerns: [],
                  next_priority: 'Review cleansing results'
                },
                statistics: {
                  total_records: cleansingResults.metadata?.original_records || latestFlow.raw_data?.length || 0,
                  quality_score: cleansingResults.data_quality_metrics?.overall_improvement?.quality_score || 0,
                  completion_percentage: cleansingResults.data_quality_metrics?.overall_improvement?.completeness_improvement || 0,
                  issues_count: cleansingResults.quality_issues?.length || 0,
                  recommendations_count: cleansingResults.recommendations?.length || 0
                }
              };
            }
          }
        }
      } catch (error) {
        console.error('Failed to fetch data cleansing results from flow:', error);
      }

      // If no data cleansing results are found, return initial empty state instead of throwing error
      console.log('No data cleansing results found, returning initial state');
      return {
        quality_issues: [],
        recommendations: [],
        metrics: {
          total_records: 0,
          cleaned_records: 0,
          quality_issues_found: 0,
          quality_issues_resolved: 0,
          data_quality_score: 0,
          quality_score: 0,
          completeness_percentage: 0,
          completion_percentage: 0,
          consistency_score: 0,
          standardization_score: 0,
          assessment_ready: false
        },
        cleaned_data: [],
        processing_status: {
          phase: 'pending',
          completion_percentage: 0,
          crew_agents_used: [],
          last_updated: new Date().toISOString()
        },
        agent_insights: {
          data_quality_summary: 'Data cleansing analysis not yet started',
          primary_concerns: [],
          next_priority: 'Start data cleansing analysis'
        },
        statistics: {
          total_records: 0,
          quality_score: 0,
          completion_percentage: 0,
          issues_count: 0,
          recommendations_count: 0
        }
      };
    },
    enabled: !!client?.id && !!engagement?.id,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    retry: 1
  });
}; 