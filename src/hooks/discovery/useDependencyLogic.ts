import { useState, useMemo, useEffect } from 'react'
import { useCallback } from 'react'
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { useAuth } from '../../contexts/AuthContext';
import { ApiClient } from '../../services/ApiClient';

export const useDependencyLogic = (flowId?: string): {
  dependencyData: {
    servers: unknown[];
    applications: unknown[];
    databases: unknown[];
    totalAssets: number;
  };
  isLoading: boolean;
  error: string | null;
  isAnalyzing: boolean;
  analyzeDependencies: () => Promise<void>;
  activeView: string;
  setActiveView: (view: string) => void;
  canContinueToNextPhase: boolean;
  canAccessDependencyPhase: boolean;
  prerequisitePhases: string[];
  isDependencyAnalysisComplete: boolean;
  inventoryData: {
    servers: unknown[];
    applications: unknown[];
    databases: unknown[];
    totalAssets: number;
  };
  flowState: unknown;
  refreshDependencies: () => Promise<void>;
} => {
  const { client, engagement } = useAuth();

  // Use the unified discovery flow
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh,
    isPhaseComplete,
    canProceedToPhase
  } = useUnifiedDiscoveryFlow(flowId);

  // Local UI state
  const [activeView, setActiveView] = useState<'app-server' | 'app-app'>('app-server');
  const [additionalAssets, setAdditionalAssets] = useState<{servers: unknown[], applications: unknown[], databases: unknown[]}>({
    servers: [],
    applications: [],
    databases: []
  });

  // Check if user can access dependency analysis phase
  const canAccessDependencyPhase = useMemo(() => {
    return canProceedToPhase('dependency_analysis');
  }, [canProceedToPhase]);

  // Check what phase should be completed before dependency analysis
  const prerequisitePhases = useMemo(() => {
    const phases = ['data_import', 'field_mapping', 'data_cleansing', 'asset_inventory'];
    return phases.filter(phase => !isPhaseComplete(phase));
  }, [isPhaseComplete]);

  // Check if dependency analysis has been completed
  const isDependencyAnalysisComplete = useMemo(() => {
    return isPhaseComplete('dependency_analysis');
  }, [isPhaseComplete]);

  // Extract inventory data for dropdowns even if dependency analysis isn't complete
  const inventoryData = useMemo(() => {
    const assetInventory = flow?.asset_inventory || flow?.results?.asset_inventory || {};

    // Extract servers and applications from inventory
    const servers = [];
    const applications = [];
    const databases = [];

    // Check if asset inventory has structured data
    if (assetInventory.servers) {
      servers.push(...assetInventory.servers);
    }
    if (assetInventory.applications) {
      applications.push(...assetInventory.applications);
    }
    if (assetInventory.databases) {
      databases.push(...assetInventory.databases);
    }

    // Also check if asset inventory is stored as a flat object with assets
    if (assetInventory.assets) {
      for (const asset of assetInventory.assets) {
        if (asset.type === 'server' || asset.asset_type === 'server') servers.push(asset);
        else if (asset.type === 'application' || asset.asset_type === 'application') applications.push(asset);
        else if (asset.type === 'database' || asset.asset_type === 'database') databases.push(asset);
      }
    }

    // CRITICAL FIX: If no structured inventory data, fetch from flow state assets directly
    if (servers.length === 0 && applications.length === 0 && databases.length === 0) {
      // Try to extract from any assets data in the flow state
      const allAssets = flow?.assets || flow?.results?.assets || [];
      for (const asset of Array.isArray(allAssets) ? allAssets : []) {
        const assetType = asset.asset_type || asset.type;
        if (assetType === 'server') servers.push(asset);
        else if (assetType === 'application') applications.push(asset);
        else if (assetType === 'database') databases.push(asset);
      }
    }

    // CRITICAL FIX: Use additional assets from direct API as fallback
    if (servers.length === 0 && applications.length === 0 && databases.length === 0) {
      servers.push(...additionalAssets.servers);
      applications.push(...additionalAssets.applications);
      databases.push(...additionalAssets.databases);
    }

    // Debug logging
    if (servers.length > 0 || applications.length > 0) {
      console.log('✅ Assets loaded for dependencies:', {
        servers: servers.length,
        applications: applications.length,
        databases: databases.length,
        totalAssets: servers.length + applications.length + databases.length
      });
    }

    return {
      servers,
      applications,
      databases,
      totalAssets: servers.length + applications.length + databases.length
    };
  }, [flow, additionalAssets]);

  // State for persisted dependencies
  const [persistedDependencies, setPersistedDependencies] = useState<{
    app_server_mapping: unknown[];
    cross_application_mapping: unknown[];
  }>({
    app_server_mapping: [],
    cross_application_mapping: []
  });

  // Fetch assets directly if they're not available in flow state
  useEffect(() => {
    const fetchAssetsDirectly = async () => {
      if (!client?.id || !engagement?.id) return;

      // Only fetch if we don't already have assets
      if (additionalAssets.servers.length > 0 || additionalAssets.applications.length > 0) {
        return;
      }

      try {
        // Use the same apiCall method that inventory uses - it handles auth context properly
        const { apiCall } = await import('@/config/api');
        const response = await apiCall('/assets/list/paginated?page=1&page_size=50');

        if (response.assets) {
          const servers = response.assets.filter((asset: { asset_type: string }) => asset.asset_type === 'server');
          const applications = response.assets.filter((asset: { asset_type: string }) => asset.asset_type === 'application');
          const databases = response.assets.filter((asset: { asset_type: string }) => asset.asset_type === 'database');

          console.log('✅ Fetched assets for dependencies:', {
            servers: servers.length,
            applications: applications.length,
            databases: databases.length
          });

          setAdditionalAssets({ servers, applications, databases });
        }
      } catch (error) {
        console.warn('Failed to fetch assets for dependencies:', error);
      }
    };

    fetchAssetsDirectly();
  }, [client?.id, engagement?.id, flow, additionalAssets.applications.length, additionalAssets.servers.length]);

  // Function to fetch persisted dependencies
  const fetchPersistedDependencies = useCallback(async () => {
    if (!client?.id || !engagement?.id) return;

    try {
      const { apiCall } = await import('@/config/api');
      const response = await apiCall('/unified-discovery/dependencies/analysis');  // Updated to unified-discovery endpoint as part of API migration

      if (response) {
        console.log('✅ Fetched persisted dependencies from database:', response);
        setPersistedDependencies(response);
      }
    } catch (error) {
      console.error('Failed to fetch persisted dependencies:', error);
      // Set empty state to prevent infinite loading
      setPersistedDependencies({
        app_server_mapping: [],
        cross_application_mapping: []
      });
      throw error; // Re-throw to allow caller to handle
    }
  }, [client?.id, engagement?.id]);

  // Fetch persisted dependencies from database
  useEffect(() => {
    fetchPersistedDependencies();
  }, [fetchPersistedDependencies, flow?.flow_id]);


  // Extract dependency analysis data from flow state AND persisted dependencies
  const dependencyData = {
    // CRITICAL FIX: Maintain nested structure that UI components expect
    cross_application_mapping: {
      cross_app_dependencies: persistedDependencies?.cross_application_mapping?.cross_app_dependencies ||
        flow?.results?.dependency_analysis?.cross_application_mapping ||
        flow?.dependency_analysis?.cross_application_mapping || [],
      available_applications: persistedDependencies?.cross_application_mapping?.available_applications || inventoryData.applications,
      dependency_graph: persistedDependencies?.cross_application_mapping?.dependency_graph || { nodes: [], edges: [] }
    },
    app_server_mapping: {
      hosting_relationships: persistedDependencies?.app_server_mapping?.hosting_relationships ||
        flow?.results?.dependency_analysis?.app_server_mapping ||
        flow?.dependency_analysis?.app_server_mapping || [],
      available_applications: persistedDependencies?.app_server_mapping?.available_applications || inventoryData.applications,
      available_servers: persistedDependencies?.app_server_mapping?.available_servers || inventoryData.servers
    },
    flow_id: flow?.flow_id,
    crew_completion_status: flow?.phase_completion || {},
    analysis_progress: {
      total_applications: flow?.results?.dependency_analysis?.total_applications || flow?.dependency_analysis?.total_applications || inventoryData.applications.length,
      mapped_dependencies: (persistedDependencies?.app_server_mapping?.hosting_relationships?.length || 0) +
                        (persistedDependencies?.cross_application_mapping?.cross_app_dependencies?.length || 0) ||
                        flow?.results?.dependency_analysis?.mapped_dependencies ||
                        flow?.dependency_analysis?.mapped_dependencies || 0,
      completion_percentage: flow?.progress_percentage || 0
    },
    // Add additional dependency data from flow state
    dependency_relationships: flow?.results?.dependency_analysis?.dependency_relationships || flow?.dependency_analysis?.dependency_relationships || [],
    dependency_matrix: flow?.results?.dependency_analysis?.dependency_matrix || flow?.dependency_analysis?.dependency_matrix || {},
    critical_dependencies: flow?.results?.dependency_analysis?.critical_dependencies || flow?.dependency_analysis?.critical_dependencies || [],
    orphaned_assets: flow?.results?.dependency_analysis?.orphaned_assets || flow?.dependency_analysis?.orphaned_assets || [],
    dependency_complexity_score: flow?.results?.dependency_analysis?.complexity_score || flow?.dependency_analysis?.complexity_score || 0,
    recommendations: flow?.results?.dependency_analysis?.recommendations || flow?.dependency_analysis?.recommendations || [],
    // CRITICAL: Include inventory data for dropdowns (maintained for backward compatibility)
    available_servers: persistedDependencies?.app_server_mapping?.available_servers || inventoryData.servers,
    available_applications: persistedDependencies?.app_server_mapping?.available_applications || inventoryData.applications,
    available_databases: inventoryData.databases,
    total_inventory_assets: inventoryData.totalAssets
  };


  // Loading and analyzing states
  const isAnalyzing = isLoading;

  // Action handlers
  const analyzeDependencies = useCallback(async () => {
    if (flow?.flow_id) {
      await updatePhase('dependency_analysis', { trigger_analysis: true });
    }
  }, [flow, updatePhase]);

  const canContinueToNextPhase = useCallback(() => {
    return isDependencyAnalysisComplete;
  }, [isDependencyAnalysisComplete]);

  // Combined refresh function that refreshes both flow and persisted dependencies
  const refreshAllDependencies = useCallback(async () => {
    console.log('🔄 Refreshing all dependencies...');
    try {
      // Refresh flow state
      await refresh();
      // Refresh persisted dependencies
      await fetchPersistedDependencies();
      console.log('✅ Successfully refreshed all dependencies');
    } catch (error) {
      console.error('❌ Failed to refresh dependencies:', error);
      // Don't re-throw to prevent component crashes
    }
  }, [refresh, fetchPersistedDependencies]);

  return {
    dependencyData,
    isLoading,
    error,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase,
    // CRITICAL: Add phase progression logic
    canAccessDependencyPhase,
    prerequisitePhases,
    isDependencyAnalysisComplete,
    inventoryData,
    flowState: flow,
    refreshDependencies: refreshAllDependencies
  };
};
