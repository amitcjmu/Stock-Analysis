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
    const assetsResponse = await apiCall<AssetsResponse>('assets/list/paginated?page_size=100', {
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
    const analysisStatusMap: Record<number, {
      status: 'not_analyzed' | 'in_progress' | 'completed' | 'failed',
      recommended_strategy?: string,
      confidence_score?: number
    }> = {};

    try {
      const sixrClient = new SixRApiClient();
      const analyses = await sixrClient.listAnalyses();

      // Create a map of application ID to analysis status
      analyses.forEach(analysis => {
        analysis.applications.forEach(app => {
          analysisStatusMap[app.id] = {
            status: analysis.status as 'not_analyzed' | 'in_progress' | 'completed' | 'failed',
            recommended_strategy: analysis.recommendation?.recommended_strategy,
            confidence_score: analysis.recommendation?.confidence_score
          };
        });
      });
    } catch (error) {
      console.warn('Could not fetch 6R analysis status, using default status:', error);
      // Gracefully continue with default 'not_analyzed' status
    }

    // Transform the response to match our Application interface
    return data.applications.map((app: BackendApplicationData, index: number) => {
      const appId = index + 1;
      const analysisInfo = analysisStatusMap[appId] || { status: 'not_analyzed' };

      return {
        // Convert string IDs to integers for 6R backend compatibility
        id: appId, // Use sequential integers starting from 1
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
        asset_id: app.asset_id || app.id, // Keep original string ID as reference
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
