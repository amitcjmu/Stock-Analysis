import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useToast } from '../use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';
import { useDiscoveryFlowState } from '../useDiscoveryFlowState';

// Types
interface AssetInventory {
  id?: string;
  asset_name?: string;
  asset_type?: string;
  environment?: string;
  department?: string;
  criticality?: string;
  discovery_status?: string;
  migration_readiness?: number;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

interface InventoryProgress {
  total_assets: number;
  classified_assets: number;
  servers: number;
  applications: number;
  devices: number;
  databases: number;
  unknown: number;
  classification_accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

interface InventorySummary {
  total: number;
  filtered: number;
  applications: number;
  servers: number;
  databases: number;
  devices: number;
  unknown: number;
  discovered: number;
  pending: number;
  device_breakdown: {
    network: number;
    storage: number;
    security: number;
    infrastructure: number;
    virtualization: number;
  };
}

interface PaginationData {
  current_page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface FilterParams {
  asset_type?: string;
  environment?: string;
  department?: string;
  criticality?: string;
  search?: string;
}

export const useInventoryLogic = () => {
  const location = useLocation();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state
  const [assets, setAssets] = useState<AssetInventory[]>([]);
  const [summary, setSummary] = useState<InventorySummary>({
    total: 0,
    filtered: 0,
    applications: 0,
    servers: 0,
    databases: 0,
    devices: 0,
    unknown: 0,
    discovered: 0,
    pending: 0,
    device_breakdown: {
      network: 0,
      storage: 0,
      security: 0,
      infrastructure: 0,
      virtualization: 0
    }
  });
  const [pagination, setPagination] = useState<PaginationData>({
    current_page: 1,
    page_size: 50,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_previous: false
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const uploadProcessedRef = useRef(false);

  // Filtering state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [filters, setFilters] = useState<FilterParams>({});
  const [searchTerm, setSearchTerm] = useState('');

  // Selection state
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  // Discovery Flow integration
  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executePhase
  } = useDiscoveryFlowState();

  // Initialize from navigation state (from Data Cleansing)
  useEffect(() => {
    const handleNavigationFromDataCleansing = async () => {
      if (!client || !engagement) return;
      
      const state = location.state as any;
      
      if (state?.from_phase === 'data_cleansing' && state?.flow_session_id && !uploadProcessedRef.current) {
        uploadProcessedRef.current = true;
        
        try {
          setIsAnalyzing(true);
          
          toast({
            title: "🚀 Asset Inventory Phase Started",
            description: "Initializing Inventory Manager and Classification Specialists...",
          });

          if (state.flow_session_id) {
            await executePhase('inventory_building', { 
              session_id: state.flow_session_id,
              previous_phase: 'data_cleansing',
              cleansing_progress: state.cleansing_progress,
              client_account_id: client.id,
              engagement_id: engagement.id
            });
          }

          setTimeout(() => {
            fetchAssets();
          }, 2000);

          toast({
            title: "✅ Inventory Building Started",
            description: "Crew is analyzing assets and building comprehensive inventory.",
          });

        } catch (error) {
          console.error('❌ Failed to initialize Inventory Building phase:', error);
          toast({
            title: "❌ Phase Initialization Failed",
            description: "Could not start Inventory Building phase. Please try manually triggering analysis.",
            variant: "destructive"
          });
        } finally {
          setIsAnalyzing(false);
        }
      }
    };
    
    handleNavigationFromDataCleansing();
  }, [client, engagement, executePhase, toast, location.state]);

  // Fetch assets from API
  const fetchAssets = useCallback(async (page = 1, filterParams: FilterParams = {}) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const contextHeaders = getAuthHeaders();
      
      // Build query parameters
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      
      if (filterParams.asset_type && filterParams.asset_type !== 'all') {
        params.append('asset_type', filterParams.asset_type);
      }
      if (filterParams.environment && filterParams.environment !== 'all') {
        params.append('environment', filterParams.environment);
      }
      if (filterParams.department && filterParams.department !== 'all') {
        params.append('department', filterParams.department);
      }
      if (filterParams.criticality && filterParams.criticality !== 'all') {
        params.append('criticality', filterParams.criticality);
      }
      if (filterParams.search) {
        params.append('search', filterParams.search);
      }
      
      console.log('🔍 Fetching assets from API:', `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${params}`);
      
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${params}`, {
        headers: contextHeaders
      });
      
      console.log('📊 Asset API response:', response);
      
      // Process response
      let assetsData: AssetInventory[] = [];
      let paginationData = pagination;
      let summaryData = summary;
      
      if (Array.isArray(response)) {
        assetsData = response;
      } else if (response.assets && Array.isArray(response.assets)) {
        assetsData = response.assets;
        paginationData = response.pagination || pagination;
      } else if (response.data && Array.isArray(response.data)) {
        assetsData = response.data;
      }
      
      // Process summary
      if (response.summary && typeof response.summary === 'object') {
        const backendSummary = response.summary;
        summaryData = {
          total: backendSummary.total || 0,
          filtered: backendSummary.total || 0,
          applications: backendSummary.by_type?.Application || 0,
          servers: backendSummary.by_type?.Server || 0,
          databases: backendSummary.by_type?.Database || 0,
          devices: (backendSummary.by_type?.['Infrastructure Device'] || 0) + 
                  (backendSummary.by_type?.['Security Device'] || 0) + 
                  (backendSummary.by_type?.['Storage Device'] || 0),
          unknown: backendSummary.by_type?.Unknown || 0,
          discovered: backendSummary.total || 0,
          pending: 0,
          device_breakdown: {
            network: 0,
            storage: backendSummary.by_type?.['Storage Device'] || 0,
            security: backendSummary.by_type?.['Security Device'] || 0,
            infrastructure: backendSummary.by_type?.['Infrastructure Device'] || 0,
            virtualization: 0
          }
        };
      }
      
      setAssets(assetsData);
      setPagination(paginationData);
      setSummary(summaryData);
      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('❌ Error fetching assets:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch assets');
      toast({
        title: "❌ Error",
        description: "Failed to fetch asset inventory. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  }, [getAuthHeaders, pageSize, toast]);

  // Trigger inventory building crew
  const handleTriggerInventoryBuildingCrew = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Triggering Inventory Building Analysis",
        description: "Starting comprehensive asset inventory building and classification...",
      });

      if (!flowState?.session_id && !assets?.length) {
        const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
        const rawData = latestImportResponse?.data || [];
        
        if (rawData.length === 0) {
          toast({
            title: "❌ No Data Available",
            description: "Please complete data cleansing first before running inventory building.",
            variant: "destructive"
          });
          return;
        }

        await initializeFlow.mutateAsync({
          client_account_id: client!.id,
          engagement_id: engagement!.id,
          user_id: user?.id || 'anonymous',
          raw_data: rawData,
          metadata: {
            source: 'inventory_building_manual_trigger',
            previous_phase: 'data_cleansing'
          },
          configuration: {
            enable_field_mapping: false,
            enable_data_cleansing: false,
            enable_inventory_building: true,
            enable_dependency_analysis: false,
            enable_technical_debt_analysis: false,
            confidence_threshold: 0.7
          }
        });
      }

      await fetchAssets();
      toast({
        title: "✅ Analysis Complete", 
        description: "Inventory building analysis has been completed.",
      });
    } catch (error) {
      console.error('Failed to trigger inventory building analysis:', error);
      toast({
        title: "❌ Analysis Failed",
        description: "Inventory building analysis encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [fetchAssets, toast, flowState, assets, initializeFlow, client, engagement, user]);

  // Asset management functions
  const handleBulkUpdate = useCallback(async (updateData: any) => {
    if (selectedAssets.length === 0) return;

    try {
      const contextHeaders = getAuthHeaders();
      
      await apiCall('/api/v1/discovery/assets/bulk-update', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          asset_ids: selectedAssets,
          updates: updateData
        })
      });

      toast({
        title: "✅ Bulk Update Complete",
        description: `Updated ${selectedAssets.length} assets successfully.`
      });

      setSelectedAssets([]);
      await fetchAssets(currentPage, filters);
      
    } catch (error) {
      console.error('❌ Error in bulk update:', error);
      toast({
        title: "❌ Bulk Update Failed",
        description: "Failed to update assets. Please try again.",
        variant: "destructive"
      });
    }
  }, [selectedAssets, getAuthHeaders, toast, currentPage, filters, fetchAssets]);

  const handleAssetClassificationUpdate = useCallback(async (assetId: string, newClassification: string) => {
    try {
      const contextHeaders = getAuthHeaders();
      
      await apiCall(`/api/v1/discovery/assets/${assetId}/classify`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          asset_type: newClassification,
          source: 'user_correction'
        })
      });

      // Update local state
      setAssets(prev => prev.map(asset => 
        asset.id === assetId 
          ? { ...asset, asset_type: newClassification }
          : asset
      ));

      toast({
        title: "✅ Classification Updated",
        description: `Asset reclassified as ${newClassification}.`
      });

    } catch (error) {
      console.error('❌ Error updating classification:', error);
      toast({
        title: "❌ Update Failed",
        description: "Failed to update asset classification.",
        variant: "destructive"
      });
    }
  }, [getAuthHeaders, toast]);

  // Derived data
  const inventoryProgress = useMemo((): InventoryProgress => {
    return {
      total_assets: summary.total,
      classified_assets: summary.total - summary.unknown,
      servers: summary.servers,
      applications: summary.applications,
      devices: summary.devices,
      databases: summary.databases,
      unknown: summary.unknown,
      classification_accuracy: summary.total > 0 ? ((summary.total - summary.unknown) / summary.total) * 100 : 0,
      crew_completion_status: {
        inventory_building: (summary.total > 0 && summary.unknown < summary.total * 0.1)
      }
    };
  }, [summary]);

  // Filter functions
  const handleFilterChange = useCallback((filterType: string, value: string) => {
    const newFilters = { ...filters, [filterType]: value };
    setFilters(newFilters);
    setCurrentPage(1);
    fetchAssets(1, newFilters);
  }, [filters, fetchAssets]);

  const handleSearchChange = useCallback((search: string) => {
    setSearchTerm(search);
    const newFilters = { ...filters, search };
    setFilters(newFilters);
    setCurrentPage(1);
    fetchAssets(1, newFilters);
  }, [filters, fetchAssets]);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    fetchAssets(page, filters);
  }, [filters, fetchAssets]);

  // Asset selection
  const toggleAssetSelection = useCallback((assetId: string) => {
    setSelectedAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  }, []);

  const selectAllAssets = useCallback(() => {
    const allAssetIds = assets.map(asset => asset.id).filter(Boolean) as string[];
    setSelectedAssets(allAssetIds);
  }, [assets]);

  const clearSelection = useCallback(() => {
    setSelectedAssets([]);
  }, []);

  // Navigation helpers
  const canContinueToAppServerDependencies = () => {
    return flowState?.phase_completion?.inventory_building || 
           (inventoryProgress.classification_accuracy >= 80 && inventoryProgress.total_assets > 0);
  };

  // Initial load
  useEffect(() => {
    fetchAssets();
  }, []);

  return {
    // Data
    assets,
    summary,
    pagination,
    inventoryProgress,
    flowState,
    
    // Loading states
    isLoading,
    isFlowStateLoading,
    isAnalyzing,
    lastUpdated,
    
    // Errors
    error,
    flowStateError,
    
    // Filters and search
    currentPage,
    pageSize,
    filters,
    searchTerm,
    
    // Selection
    selectedAssets,
    
    // Actions
    handleTriggerInventoryBuildingCrew,
    handleBulkUpdate,
    handleAssetClassificationUpdate,
    handleFilterChange,
    handleSearchChange,
    handlePageChange,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
    fetchAssets: () => fetchAssets(currentPage, filters),
    canContinueToAppServerDependencies,
  };
}; 