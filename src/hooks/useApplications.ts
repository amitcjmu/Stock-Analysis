import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall, API_CONFIG } from '@/config/api'
import { SixRApiClient } from '@/lib/api/sixr';
import type { Application } from '@/components/sixr';

/**
 * Interface for raw application data from backend API
 */
interface BackendApplicationData {
  name: string;
  description?: string;
  department?: string;
  business_unit?: string;
  criticality?: string;
  complexity_score?: number;
  techStack?: string;
  technology_stack?: string;
  application_type?: string;
  environment?: string;
  sixr_ready?: boolean;
  migration_complexity?: string;
  original_asset_type?: string;
  asset_id?: string;
  id?: string;
  compliance_requirements?: string[];
  dependencies?: string[];
}

/**
 * Interface for backend applications response
 */
interface BackendApplicationsResponse {
  applications: BackendApplicationData[];
}

interface AssetData {
  asset_type?: string;
  name: string;
  description?: string;
  department?: string;
  business_unit?: string;
  criticality?: string;
  complexity_score?: number;
  techStack?: string;
  technology_stack?: string;
  application_type?: string;
  environment?: string;
  sixr_ready?: boolean;
  migration_complexity?: string;
  original_asset_type?: string;
  asset_id?: string;
  id?: string;
  compliance_requirements?: string[];
  dependencies?: string[];
}

interface AssetsResponse {
  assets?: AssetData[];
}

const loadApplicationsFromBackend = async (contextHeaders: Record<string, string> = {}): Promise<Application[]> => {
  try {
    // Load assets using paginated endpoint with larger page size to get applications
    const assetsResponse = await apiCall<AssetsResponse>('unified-discovery/assets?page_size=100', {
      headers: contextHeaders
    });

    // Filter for application assets - backend returns lowercase
    const applicationAssets = assetsResponse.assets?.filter((asset: AssetData) => {
      const assetType = (asset.asset_type || '').toLowerCase();
      return assetType === 'application';
    }) || [];

    // Transform to match expected format
    const data: BackendApplicationsResponse = {
      applications: applicationAssets
    };

    // Also fetch current 6R analyses to determine status for each application
    // Bug #813 fix: Use string keys (UUIDs) instead of number keys
    const analysisStatusMap: Record<string, {
      status: 'not_analyzed' | 'in_progress' | 'completed' | 'failed',
      recommended_strategy?: string,
      confidence_score?: number
    }> = {};

    try {
      const sixrClient = new SixRApiClient();
      const analysesResponse = await sixrClient.listAnalyses();

      // Fix #633: Backend returns object {analyses: [], total_count, page, page_size}
      // Extract the analyses array from the response
      const analyses = Array.isArray(analysesResponse)
        ? analysesResponse
        : (analysesResponse as any)?.analyses || [];

      // Fix P2: Validate analyses is an array before calling forEach
      if (Array.isArray(analyses)) {
        // Create a map of application ID to analysis status
        analyses.forEach(analysis => {
          if (analysis.applications && Array.isArray(analysis.applications)) {
            analysis.applications.forEach(app => {
              analysisStatusMap[app.id] = {
                status: analysis.status as 'not_analyzed' | 'in_progress' | 'completed' | 'failed',
                recommended_strategy: analysis.recommendation?.recommended_strategy,
                confidence_score: analysis.recommendation?.confidence_score
              };
            });
          }
        });
      } else {
        console.warn('6R analyses response is not an array:', typeof analyses);
      }
    } catch (error) {
      console.warn('Could not fetch 6R analysis status, using default status:', error);
      // Gracefully continue with default 'not_analyzed' status
    }

    // Transform the response to match our Application interface
    return data.applications.map((app: BackendApplicationData) => {
      // Bug #813 fix: Use UUID string IDs from assets table (NOT sequential integers)
      // Backend needs original asset UUIDs to match against assets.id column
      const appId = app.asset_id || app.id; // UUID string
      const analysisInfo = analysisStatusMap[appId] || { status: 'not_analyzed' };

      return {
        // Bug #813 fix: Keep UUID strings for backend compatibility with assets table
        id: appId, // UUID string from assets table
        name: app.name,
        description: app.description || `${app.original_asset_type || 'Application'} - ${app.techStack || 'Unknown Technology'}`,
        department: app.department || 'Unknown',
        business_unit: app.business_unit || app.department || 'Unknown',
        criticality: (app.criticality || 'medium').toLowerCase() as 'low' | 'medium' | 'high' | 'critical',
        complexity_score: app.complexity_score || 5,
        technology_stack: app.techStack ? app.techStack.split(', ') : [app.technology_stack || 'Unknown'],
        application_type: app.application_type || 'custom',
        environment: app.environment || 'Unknown',
        sixr_ready: app.sixr_ready,
        migration_complexity: app.migration_complexity,
        original_asset_type: app.original_asset_type,
        asset_id: appId, // Same as id - UUID string
        analysis_status: analysisInfo.status, // Use actual analysis status from 6R API
        user_count: undefined,
        data_volume: undefined,
        compliance_requirements: app.compliance_requirements || [],
        dependencies: app.dependencies || [],
        last_updated: undefined,
        recommended_strategy: analysisInfo.recommended_strategy,
        confidence_score: analysisInfo.confidence_score
      };
    });
  } catch (error) {
    console.error('Failed to load applications:', error);
    // Return empty array so UI shows no data state instead of crashing
    return [];
  }
};

export const useApplications = (enabled = true): ReturnType<typeof useQuery<Application[]>> & { applications: Application[]; refetchApplications: () => Promise<void> } => {
  const queryClient = useQueryClient();

  const query = useQuery<Application[]>({
    queryKey: ['applications'],
    queryFn: () => loadApplicationsFromBackend({}),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes (cacheTime was renamed to gcTime in v5)
  });

  const refetchApplications = () => {
    return queryClient.invalidateQueries({ queryKey: ['applications'] });
  };

  return {
    ...query,
    applications: query.data || [],
    refetchApplications,
  };
};

// Create a version of the hook that includes context headers
export const useApplicationsWithContext = (contextHeaders: Record<string, string> = {}): ReturnType<typeof useQuery<Application[]>> & { applications: Application[] } => {
  const query = useQuery<Application[]>({
    queryKey: ['applications', contextHeaders],
    queryFn: () => loadApplicationsFromBackend(contextHeaders),
    enabled: !!contextHeaders,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes (cacheTime was renamed to gcTime in v5)
  });

  return {
    ...query,
    applications: query.data || [],
  };
};
