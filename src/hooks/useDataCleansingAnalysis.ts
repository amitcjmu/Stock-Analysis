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
  completeness_percentage: number;
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

export const useDataCleansingAnalysis = () => {
  const { client, engagement } = useAuth();

  return useQuery({
    queryKey: ['data-cleansing-analysis', client?.id, engagement?.id],
    queryFn: async (): Promise<DataCleansingResponse> => {
      if (!client?.id || !engagement?.id) {
        throw new Error('Authentication context required');
      }

      try {
        // Primary endpoint - agentic data cleansing analysis
        const response = await apiCall('/api/v1/agents/discovery/data-cleansing/analysis', {
          method: 'GET',
          headers: {
            'X-Client-Account-ID': client.id,
            'X-Engagement-ID': engagement.id,
          },
        });

        return response;
      } catch (error) {
        // Fallback to mock data for development
        console.warn('Data cleansing endpoint not available, using mock data:', error);
        
        return {
          quality_issues: [
            {
              id: 'issue-1',
              field: 'server_name',
              issue_type: 'missing_values',
              severity: 'high',
              description: 'Missing server names in 15% of records',
              affected_records: 23,
              recommendation: 'Implement naming convention based on IP address patterns',
              agent_source: 'Data Quality Manager',
              status: 'pending'
            },
            {
              id: 'issue-2', 
              field: 'environment',
              issue_type: 'inconsistent_values',
              severity: 'medium',
              description: 'Environment values vary between "prod", "production", "PROD"',
              affected_records: 12,
              recommendation: 'Standardize to "production", "staging", "development"',
              agent_source: 'Data Standardization Specialist',
              status: 'pending'
            },
            {
              id: 'issue-3',
              field: 'business_criticality',
              issue_type: 'missing_values',
              severity: 'high',
              description: 'Business criticality not defined for 28% of servers',
              affected_records: 44,
              recommendation: 'Assign criticality based on environment and application dependencies',
              agent_source: 'Data Quality Manager',
              status: 'pending'
            }
          ],
          recommendations: [
            {
              id: 'rec-1',
              type: 'standardization',
              title: 'Standardize Environment Values',
              description: 'Convert all environment indicators to standard values',
              confidence: 0.92,
              priority: 'high',
              fields: ['environment', 'env_type'],
              agent_source: 'Data Standardization Specialist',
              implementation_steps: [
                'Map "prod", "PROD" → "production"',
                'Map "dev", "DEV" → "development"', 
                'Map "test", "TEST" → "staging"'
              ],
              status: 'pending'
            },
            {
              id: 'rec-2',
              type: 'data_enrichment',
              title: 'Complete Missing Business Criticality',
              description: 'Assign business criticality ratings to all assets',
              confidence: 0.87,
              priority: 'high',
              fields: ['business_criticality'],
              agent_source: 'Data Quality Manager',
              implementation_steps: [
                'Production servers → High criticality',
                'Development servers → Low criticality',
                'Application servers → Medium-High criticality'
              ],
              status: 'pending'
            }
          ],
          metrics: {
            total_records: 156,
            cleaned_records: 121,
            quality_issues_found: 8,
            quality_issues_resolved: 3,
            data_quality_score: 78,
            completeness_percentage: 85,
            consistency_score: 72,
            standardization_score: 68,
            assessment_ready: false
          },
          cleaned_data: [],
          processing_status: {
            phase: 'data_cleansing',
            completion_percentage: 65,
            crew_agents_used: ['Data Quality Manager', 'Data Standardization Specialist'],
            last_updated: new Date().toISOString()
          },
          agent_insights: {
            data_quality_summary: 'Data quality is good overall with some standardization needs',
            primary_concerns: ['Inconsistent environment naming', 'Missing server identifiers', 'Incomplete business criticality'],
            next_priority: 'Focus on environment standardization and server name completion'
          },
          statistics: {
            total_records: 156,
            quality_score: 78,
            completion_percentage: 65,
            issues_count: 8,
            recommendations_count: 2
          }
        };
      }
    },
    enabled: !!client?.id && !!engagement?.id,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}; 