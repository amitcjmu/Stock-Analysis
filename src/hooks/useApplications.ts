import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall, API_CONFIG } from '@/config/api'

// Note: Phase 5 - SixRApiClient and Application type removed (from deleted sixr components)
// Application type is now defined locally below

/**
 * Application interface (previously imported from @/components/sixr)
 */
export interface Application {
  id: string;
  name: string;
  description?: string;
  department?: string;
  business_unit?: string;
  criticality?: 'low' | 'medium' | 'high' | 'critical';
  complexity_score?: number;
  technology_stack?: string[];
  application_type?: string;
  environment?: string;
  sixr_ready?: boolean;
  migration_complexity?: string;
  sixr_status?: 'not_analyzed' | 'in_progress' | 'completed' | 'failed';
  recommended_strategy?: string;
  confidence_score?: number;
  compliance_requirements?: string[];
  dependencies?: string[];
}

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

    // Note: Phase 5 - 6R analysis status code removed (deprecated SixRApiClient)
    // 6R analysis status should now be fetched from Assessment Flow API if needed

    // Transform the response to match our Application interface
    return data.applications.map((app: BackendApplicationData) => {
      // Bug #813 fix: Use UUID string IDs from assets table (NOT sequential integers)
      // Backend needs original asset UUIDs to match against assets.id column
      const appId = app.asset_id || app.id; // UUID string

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
        compliance_requirements: app.compliance_requirements || [],
        dependencies: app.dependencies || [],
        // Note: Phase 5 - analysis_status, recommended_strategy, confidence_score removed
        // These should be fetched from Assessment Flow API if needed
        sixr_status: 'not_analyzed' as const,
        recommended_strategy: undefined,
        confidence_score: undefined
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
