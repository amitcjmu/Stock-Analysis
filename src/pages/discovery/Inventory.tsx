import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import ApplicationDiscoveryPanel from '../../components/discovery/application-discovery/ApplicationDiscoveryPanel';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Download, Filter, Database, Server, HardDrive, RefreshCw, Router, Shield, Cpu, Cloud, Zap,
  ChevronLeft, ChevronRight, Search, Plus, Trash2, Eye, ArrowUpDown, Users, Brain,
  CheckCircle, AlertCircle
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';
import { useAuth } from '@/contexts/AuthContext';

const Inventory = () => {
  const { getAuthHeaders, client, engagement, session } = useAuth();
  
  // Filtering and pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedDept, setSelectedDept] = useState('all');
  const [selectedEnv, setSelectedEnv] = useState('all');
  const [selectedCriticality, setSelectedCriticality] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Data state
  const [assets, setAssets] = useState([]);
  const [summary, setSummary] = useState({
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
  const [pagination, setPagination] = useState({
    current_page: 1,
    page_size: 50,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_previous: false
  });
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('test');
  const [suggestedHeaders, setSuggestedHeaders] = useState([]);
  const [activeTab, setActiveTab] = useState('assets');
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);
  
  // Bulk operations state
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [showBulkEditDialog, setShowBulkEditDialog] = useState(false);
  const [bulkEditData, setBulkEditData] = useState({
    environment: '',
    department: '',
    criticality: '',
    asset_type: ''
  });
  const [isBulkOperating, setIsBulkOperating] = useState(false);
  
  // App-to-server mapping state
  const [showAppMapping, setShowAppMapping] = useState(false);
  const [appMappings, setAppMappings] = useState([]);
  const [selectedApp, setSelectedApp] = useState('');
  const [mappingLoading, setMappingLoading] = useState(false);
  
  // Unlinked assets state
  const [unlinkedAssets, setUnlinkedAssets] = useState([]);
  const [unlinkedSummary, setUnlinkedSummary] = useState({
    total_unlinked: 0,
    by_type: {},
    by_environment: {},
    by_criticality: {},
    migration_impact: 'none'
  });
  const [unlinkedLoading, setUnlinkedLoading] = useState(false);
  


  // Define filter interface
  interface FilterParams {
    asset_type?: string;
    environment?: string;
    department?: string;
    criticality?: string;
    search?: string;
  }

  // Fetch assets from API with pagination and filtering
  const fetchAssets = async (page = 1, filters: FilterParams = {}) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const contextHeaders = getAuthHeaders();
      
      // Build query parameters for both assets and summary requests
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      
      const summaryParams = new URLSearchParams();
      
      if (filters.asset_type && filters.asset_type !== 'all') {
        params.append('asset_type', filters.asset_type);
        summaryParams.append('asset_type', filters.asset_type);
      }
      if (filters.environment && filters.environment !== 'all') {
        params.append('environment', filters.environment);
        summaryParams.append('environment', filters.environment);
      }
      if (filters.department && filters.department !== 'all') {
        params.append('department', filters.department);
        summaryParams.append('department', filters.department);
      }
      if (filters.criticality && filters.criticality !== 'all') {
        params.append('criticality', filters.criticality);
        summaryParams.append('criticality', filters.criticality);
      }
      if (filters.search) {
        params.append('search', filters.search);
        summaryParams.append('search', filters.search);
      }
      
      console.log('🔍 Fetching assets from API:', `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${params}`);
      console.log('🔒 Using context headers:', contextHeaders);
      
      // Fetch assets (includes summary data in response)
      const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${params}`, {
        headers: contextHeaders
      });
      
      console.log('📊 Asset API response:', assetsResponse);
      
      // Process the assets response
      let assetsData = [];
      let paginationData = pagination;
      
      if (Array.isArray(assetsResponse)) {
        assetsData = assetsResponse;
      } else if (assetsResponse.assets && Array.isArray(assetsResponse.assets)) {
        assetsData = assetsResponse.assets;
        paginationData = assetsResponse.pagination || pagination;
      } else if (assetsResponse.data && Array.isArray(assetsResponse.data)) {
        assetsData = assetsResponse.data;
      }
      
      // Use summary from assets response
      let summaryData = summary;
      if (assetsResponse.summary && typeof assetsResponse.summary === 'object') {
        // Transform backend summary to match frontend expected format
        const backendSummary = assetsResponse.summary;
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
        console.log('✅ Using summary from assets response:', summaryData);
      }
      
      console.log('🎯 Processed data:', {
        assetsCount: assetsData.length,
        summaryTotal: summaryData.total,
        paginationInfo: paginationData
      });
      
      // Check if we got real assets data or an empty response
      if (assetsData.length > 0 || (summaryData && summaryData.total > 0)) {
        console.log('✅ Found real data, using live data');
        setAssets(assetsData);
        setDataSource('live');
        
        // Use the accurate summary from the dedicated endpoint
        setSummary(summaryData);
        
        // Update pagination using data from backend
        setPagination(paginationData || {
          current_page: page,
          page_size: pageSize,
          total_items: summaryData.total || 0,
          total_pages: Math.ceil((summaryData.total || 0) / pageSize),
          has_next: page * pageSize < (summaryData.total || 0),
          has_previous: page > 1
        });
        
        console.log('✅ Using live data with accurate summary:', summaryData);
        console.log('📊 Updated pagination info:', paginationData);
      } else {
        // Check if this might be a valid empty response or if we should try demo data
        console.log('⚠️ API returned empty assets array. Response details:', {
          hasAssetsProperty: assetsResponse.hasOwnProperty('assets'),
          assetsLength: assetsResponse.assets?.length,
          hasPagination: assetsResponse.hasOwnProperty('pagination'),
          hasFilters: assetsResponse.hasOwnProperty('filters_ap'),
          isEmptyResult: assetsResponse.assets && Array.isArray(assetsResponse.assets) && assetsResponse.assets.length === 0
        });
        
        // If it's a structured response with empty assets array, it means no data in database
        if (assetsResponse.assets && Array.isArray(assetsResponse.assets) && assetsResponse.assets.length === 0) {
          console.log('📊 Database has no assets, showing empty state');
          setAssets([]);
          setSummary({
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
          setDataSource('empty');
        } else {
          // Fallback to demo data only if we got an unexpected response
          console.log('🎭 Using demo data as fallback for development');
          const demoAssets = [
            {
              id: 'asset_001',
              asset_name: 'web-server-01',
              hostname: 'web-server-01',
              asset_type: 'Server',
              ci_type: 'Server',
              status: 'Active',
              department: 'IT',
              business_owner: 'IT Operations',
              environment: 'Production',
              operating_system: 'Windows Server 2019',
              os_type: 'Windows Server 2019',
              application_name: 'IIS',
              business_criticality: 'High',
              criticality: 'High',
              ip_address: '192.168.1.10',
              location: 'DC1',
              datacenter: 'DC1',
              cpu_cores: 4,
              memory_gb: 16,
              ram_gb: 16,
              storage_gb: 500,
              last_scan: '2024-06-01T10:30:00Z',
              confidence_score: 0.95
            },
            {
              id: 'asset_002',
              asset_name: 'db-server-01',
              hostname: 'db-server-01',
              asset_type: 'Database',
              ci_type: 'Database',
              status: 'Active',
              department: 'IT',
              business_owner: 'Database Team',
              environment: 'Production',
              operating_system: 'Linux',
              os_type: 'Linux',
              application_name: 'PostgreSQL',
              business_criticality: 'Critical',
              criticality: 'Critical',
              ip_address: '192.168.1.20',
              location: 'DC1',
              datacenter: 'DC1',
              cpu_cores: 8,
              memory_gb: 32,
              ram_gb: 32,
              storage_gb: 2000,
              last_scan: '2024-06-01T10:30:00Z',
              confidence_score: 0.92
            },
            {
              id: 'asset_003',
              asset_name: 'app-server-01',
              hostname: 'app-server-01',
              asset_type: 'Server',
              ci_type: 'Server',
              status: 'Active',
              department: 'Engineering',
              business_owner: 'Development Team',
              environment: 'Production',
              operating_system: 'Ubuntu 20.04',
              os_type: 'Ubuntu 20.04',
              application_name: 'Node.js',
              business_criticality: 'Medium',
              criticality: 'Medium',
              ip_address: '192.168.1.30',
              location: 'DC1',
              datacenter: 'DC1',
              cpu_cores: 4,
              memory_gb: 8,
              ram_gb: 8,
              storage_gb: 250,
              last_scan: '2024-06-01T10:30:00Z',
              confidence_score: 0.88
            }
          ];
          
          setAssets(demoAssets);
          setSummary({
            total: 3,
            filtered: 3,
            applications: 0,
            servers: 2,
            databases: 1,
            devices: 0,
            unknown: 0,
            discovered: 3,
            pending: 0,
            device_breakdown: {
              network: 0,
              storage: 0,
              security: 0,
              infrastructure: 0,
              virtualization: 0
            }
          });
          setDataSource('demo');
        }
        
        setPagination({
          current_page: 1,
          page_size: pageSize,
          total_items: dataSource === 'empty' ? 0 : 3,
          total_pages: dataSource === 'empty' ? 0 : 1,
          has_next: false,
          has_previous: false
        });
      }
      
      setLastUpdated(new Date().toISOString());
      
      // Trigger agent analysis for asset inventory context if we have real data
      if (assetsData.length > 0 && page === 1) {
        try {
          await triggerAgentAnalysis(assetsData);
        } catch (agentError) {
          console.warn('Agent analysis failed for asset inventory:', agentError);
          // Non-critical, continue without agent analysis
        }
      }
      
      // Cache the successful response
      const cacheKey = getCacheKey(page, filters);
      saveToCache(cacheKey, {
        assets: assetsData,
        summary: summaryData,
        pagination: paginationData,
        lastUpdated: new Date().toISOString(),
        dataSource: assetsData.length > 0 ? 'live' : 'demo'
      });
      
    } catch (error) {
      console.error('Failed to fetch assets:', error);
      setError(`Failed to load assets: ${error.message}`);
      setDataSource('error');
      
      // Set empty state for error case
      setAssets([]);
      setSummary({
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
      setPagination({
        current_page: 1,
        page_size: pageSize,
        total_items: 0,
        total_pages: 0,
        has_next: false,
        has_previous: false
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch app-to-server mappings
  const fetchAppMappings = async () => {
    try {
      setMappingLoading(true);
      const contextHeaders = getAuthHeaders();
      console.log('Fetching app mappings from:', API_CONFIG.ENDPOINTS.DISCOVERY.APP_MAPPINGS);
      
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APP_MAPPINGS, {
        headers: contextHeaders
      });
      
      console.log('App mappings response:', response);
      console.log('Applications found:', response.applications?.length || 0);
      
      if (response.applications && Array.isArray(response.applications)) {
        setAppMappings(response.applications);
        console.log('Successfully set app mappings:', response.applications.map(app => ({ id: app.id, name: app.name })));
      } else {
        console.warn('No applications array in response:', response);
        setAppMappings([]);
      }
    } catch (error) {
      console.error('Failed to fetch app mappings:', error);
      setAppMappings([]);
    } finally {
      setMappingLoading(false);
    }
  };

  // Fetch applications count for summary - separate from app mappings
  const fetchApplicationsCount = async () => {
    try {
      const contextHeaders = getAuthHeaders();
      console.log('🔍 Fetching applications count from:', API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS);
      
      // Try the applications endpoint
      const applicationsResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS, {
        headers: contextHeaders
      });
      console.log('📊 Applications API response:', applicationsResponse);
      
      let applicationsCount = 0;
      
      if (Array.isArray(applicationsResponse)) {
        applicationsCount = applicationsResponse.length;
      } else if (applicationsResponse.applications && Array.isArray(applicationsResponse.applications)) {
        applicationsCount = applicationsResponse.applications.length;
      } else if (applicationsResponse.data && Array.isArray(applicationsResponse.data)) {
        applicationsCount = applicationsResponse.data.length;
      }
      
      console.log('✅ Found applications count:', applicationsCount);
      
      // Update the summary with real applications count
      setSummary(prevSummary => ({
        ...prevSummary,
        applications: applicationsCount
      }));
      
      return applicationsCount;
      
    } catch (error) {
      console.error('Failed to fetch applications count:', error);
      
      // Try the application portfolio endpoint as backup
      try {
        console.log('🔄 Trying application portfolio endpoint as backup');
        const portfolioResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATION_PORTFOLIO, {
          headers: contextHeaders
        });
        console.log('📊 Application portfolio response:', portfolioResponse);
        
        let portfolioCount = 0;
        
        if (portfolioResponse.application_portfolio?.applications) {
          portfolioCount = portfolioResponse.application_portfolio.applications.length;
          console.log('✅ Found applications in portfolio:', portfolioCount);
          
          setSummary(prevSummary => ({
            ...prevSummary,
            applications: portfolioCount
          }));
          
          return portfolioCount;
        }
      } catch (portfolioError) {
        console.error('Failed to fetch from application portfolio endpoint:', portfolioError);
      }
      
      return 0;
    }
  };

  // Fetch unlinked assets - assets not tied to any application
  const fetchUnlinkedAssets = async () => {
    try {
      setUnlinkedLoading(true);
      const contextHeaders = getAuthHeaders();
      
      console.log('🔍 Fetching unlinked assets from API');
      console.log('🔒 Using context headers:', contextHeaders);
      
      const response = await apiCall('discovery/assets/unlinked', {
        headers: contextHeaders
      });
      
      console.log('📊 Unlinked assets API response:', response);
      
      if (response && response.unlinked_assets) {
        setUnlinkedAssets(response.unlinked_assets);
        setUnlinkedSummary(response.summary);
        console.log(`✅ Found ${response.unlinked_assets.length} unlinked assets`);
      } else {
        console.log('⚠️ No unlinked assets found in response');
        setUnlinkedAssets([]);
        setUnlinkedSummary({
          total_unlinked: 0,
          by_type: {},
          by_environment: {},
          by_criticality: {},
          migration_impact: 'none'
        });
      }
    } catch (err) {
      console.error('❌ Error fetching unlinked assets:', err);
      setUnlinkedAssets([]);
    } finally {
      setUnlinkedLoading(false);
    }
  };

  // Trigger agent analysis for asset inventory context
  const triggerAgentAnalysis = async (assetsData: any[]) => {
    try {
      const contextHeaders = getAuthHeaders();
      console.log('Triggering agent analysis for asset-inventory context');
      
      // Prepare data for agent analysis
      const agentAnalysisRequest = {
        data_source: {
          file_data: assetsData.slice(0, 20), // Send sample of assets for analysis
          columns: assetsData.length > 0 ? Object.keys(assetsData[0]) : [],
          sample_data: assetsData.slice(0, 10), // Keep for backward compatibility
          metadata: {
            source: "asset-inventory-page",
            file_name: "asset_inventory_analysis.csv",
            total_records: assetsData.length,
            context: "asset_inventory_analysis",
            mapping_context: "asset-inventory"
          }
        },
        analysis_type: "data_source_analysis",
        page_context: "asset-inventory"
      };

      // Trigger agent analysis
      const agentResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify(agentAnalysisRequest)
      });

      if (agentResponse) {
        console.log('✅ Agent analysis completed for asset-inventory context');
        // Trigger agent panel refresh
        setAgentRefreshTrigger(prev => prev + 1);
      }
      
    } catch (error) {
      console.error('Failed to trigger agent analysis for asset inventory:', error);
    }
  };

  // Load assets on component mount and when filters change
  useEffect(() => {
    const filters = {
      asset_type: selectedFilter,
      environment: selectedEnv,
      department: selectedDept,
      criticality: selectedCriticality,
      search: searchTerm
    };
    
    // Try to load from cache first, then fetch from API
    loadAssetsWithCache(currentPage, filters);
    
    // Also fetch applications count for accurate summary
    fetchApplicationsCount();
  }, [currentPage, pageSize, selectedFilter, selectedEnv, selectedDept, selectedCriticality, searchTerm]);

  // Refetch data when context changes (client/engagement/session)
  useEffect(() => {
    if (context.client && context.engagement) {
      const filters = {
        asset_type: selectedFilter,
        environment: selectedEnv,
        department: selectedDept,
        criticality: selectedCriticality,
        search: searchTerm
      };
      
      console.log('🔄 Context changed, refetching inventory data for:', {
        client: context.client.name,
        engagement: context.engagement.name,
        session: context.session?.session_display_name || 'None'
      });
      
      // Force reload from API when context changes (bypass cache)
      fetchAssets(currentPage, filters);
      fetchApplicationsCount();
    }
  }, [context.client, context.engagement, context.session, context.viewMode]);

  // Trigger initial agent panel refresh on component mount
  useEffect(() => {
    // Small delay to ensure components are mounted before triggering refresh
    const timer = setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []); // Only run once on mount

  // Load app mappings when app mapping view is shown
  useEffect(() => {
    if (showAppMapping) {
      fetchAppMappings();
    }
  }, [showAppMapping]);

  // Load unlinked assets when unlinked tab is selected
  useEffect(() => {
    if (activeTab === 'unlinked') {
      fetchUnlinkedAssets();
      fetchAppMappings(); // Also load app mappings for linking functionality
    }
  }, [activeTab, context.client, context.engagement, context.session]);

  // Add persistence helper functions
  const getCacheKey = (page: number, filters: FilterParams) => {
    return `inventory_cache_${page}_${pageSize}_${JSON.stringify(filters)}`;
  };

  const loadFromCache = (cacheKey: string) => {
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        // Cache expires after 5 minutes
        if (Date.now() - timestamp < 5 * 60 * 1000) {
          return data;
        }
      }
    } catch (error) {
      console.warn('Failed to load from cache:', error);
    }
    return null;
  };

  const saveToCache = (cacheKey: string, data: any) => {
    try {
      const cacheData = {
        data,
        timestamp: Date.now()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Failed to save to cache:', error);
    }
  };

  const loadAssetsWithCache = async (page = 1, filters: FilterParams = {}) => {
    const cacheKey = getCacheKey(page, filters);
    const cachedData = loadFromCache(cacheKey);
    
    if (cachedData && !isLoading) {
      // Load from cache immediately
      setAssets(cachedData.assets || []);
      setSummary(cachedData.summary || summary);
      setPagination(cachedData.pagination || pagination);
      setLastUpdated(cachedData.lastUpdated);
      setDataSource(cachedData.dataSource || 'cached');
      setSuggestedHeaders(cachedData.suggestedHeaders || []);
    }
    
    // Always fetch fresh data in background
    try {
      await fetchAssets(page, filters);
    } catch (error) {
      // If API fails and we have cached data, continue using cache
      if (!cachedData) {
        console.error('No cached data available and API failed:', error);
      }
    }
  };

  // Handle page changes
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  // Handle filter changes
  const handleFilterChange = (filterType, value) => {
    setCurrentPage(1); // Reset to first page when filtering
    switch (filterType) {
      case 'type':
        setSelectedFilter(value);
        break;
      case 'department':
        setSelectedDept(value);
        break;
      case 'environment':
        setSelectedEnv(value);
        break;
      case 'criticality':
        setSelectedCriticality(value);
        break;
      case 'search':
        setSearchTerm(value);
        break;
    }
  };

  // Get unique values for filter dropdowns
  const getUniqueValues = (field) => {
    return [...new Set(assets.map(asset => asset[field]).filter(value => value && value !== 'Unknown'))];
  };

  const getTypeIcon = (type) => {
    const iconClass = "h-5 w-5";
    switch (type) {
      case 'Application': return <Database className={iconClass} />;
      case 'Server': return <Server className={iconClass} />;
      case 'Database': return <HardDrive className={iconClass} />;
      case 'Network Device': return <Router className={iconClass} />;
      case 'Storage Device': return <HardDrive className={iconClass} />;
      case 'Security Device': return <Shield className={iconClass} />;
      case 'Infrastructure Device': return <Cpu className={iconClass} />;
      case 'Virtualization Platform': return <Cloud className={iconClass} />;
      case 'Unknown': return <Zap className={iconClass} />;
      default: return <Database className={iconClass} />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'Application': return 'text-blue-500';
      case 'Server': return 'text-green-500';
      case 'Database': return 'text-purple-500';
      case 'Network Device': return 'text-orange-500';
      case 'Storage Device': return 'text-yellow-500';
      case 'Security Device': return 'text-red-500';
      case 'Infrastructure Device': return 'text-gray-500';
      case 'Virtualization Platform': return 'text-indigo-500';
      case 'Unknown': return 'text-gray-400';
      default: return 'text-gray-500';
    }
  };

  // Calculate migration readiness confidence percentage
  const calculateReadinessConfidence = (asset) => {
    let confidence = 0;
    let factors = [];

    // Basic asset info (20%)
    if (asset.name && asset.type !== 'Unknown') {
      confidence += 20;
      factors.push('Basic info');
    }

    // Application mapping (25%)
    if (asset.applicationMapped || asset.application_name) {
      confidence += 25;
      factors.push('App mapped');
    }

    // Environment and location (15%)
    if (asset.environment && asset.environment !== 'Unknown' && 
        asset.location && asset.location !== 'Unknown') {
      confidence += 15;
      factors.push('Environment');
    }

    // Technical details (20%)
    if ((asset.ipAddress || asset.operatingSystem || asset.cpuCores || asset.memoryGb)) {
      confidence += 20;
      factors.push('Tech specs');
    }

    // Owner and criticality (10%)
    if (asset.owner && asset.owner !== 'Unknown' && asset.criticality) {
      confidence += 10;
      factors.push('Ownership');
    }

    // Dependencies analyzed (10%) - placeholder for future implementation
    if (asset.dependencies_analyzed) {
      confidence += 10;
      factors.push('Dependencies');
    }

    return { confidence: Math.min(confidence, 100), factors };
  };

  // Get readiness color based on confidence percentage
  const getReadinessColor = (confidence) => {
    if (confidence >= 80) return 'bg-green-100 text-green-800';
    if (confidence >= 60) return 'bg-yellow-100 text-yellow-800';
    if (confidence >= 40) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  // Export to CSV function
  const exportToCSV = () => {
    const headers = [
      'ID', 'Type', 'Name', 'Tech Stack', 'Department', 'Environment', 
      'Criticality', 'IP Address', 'Operating System', 'OS Version',
      'CPU Cores', 'Memory (GB)', 'Storage (GB)', 'Application Mapped', 
      'Workload Type', 'Location', 'Vendor', 'Model', 'Serial Number'
    ];
    
    const csvContent = [
      headers.join(','),
      ...assets.map(asset => [
        asset.id,
        asset.type,
        `"${asset.name}"`,
        `"${asset.techStack}"`,
        asset.department,
        asset.environment,
        asset.criticality,
        asset.ipAddress || '',
        asset.operatingSystem || '',
        asset.osVersion || '',
        asset.cpuCores || '',
        asset.memoryGb || '',
        asset.storageGb || '',
        asset.applicationMapped || '',
        asset.workloadType || '',
        asset.location || '',
        asset.vendor || '',
        asset.model || '',
        asset.serialNumber || ''
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asset-inventory-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Bulk operations
  const toggleAssetSelection = (assetId: string) => {
    setSelectedAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  };

  const selectAllAssets = () => {
    setSelectedAssets(assets.map(asset => asset.id));
  };

  const clearSelection = () => {
    setSelectedAssets([]);
  };

  const bulkUpdateAssets = async () => {
    if (selectedAssets.length === 0) return;
    
    try {
      setIsBulkOperating(true);
      const contextHeaders = getAuthHeaders();
      
      // Filter out empty values from bulkEditData
      const updates = Object.fromEntries(
        Object.entries(bulkEditData).filter(([_, value]) => value !== '')
      );
      
      if (Object.keys(updates).length === 0) {
        alert('Please select at least one field to update');
        return;
      }
      
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_BULK, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          asset_ids: selectedAssets,
          updates: updates
        })
      });
      
      // Refresh the assets list
      const filters = {
        asset_type: selectedFilter,
        environment: selectedEnv,
        department: selectedDept,
        criticality: selectedCriticality,
        search: searchTerm
      };
      await fetchAssets(currentPage, filters);
      
      // Clear selection and close dialog
      clearSelection();
      setShowBulkEditDialog(false);
      setBulkEditData({
        environment: '',
        department: '',
        criticality: '',
        asset_type: ''
      });
      
      alert(`Successfully updated ${selectedAssets.length} assets`);
      
    } catch (error) {
      console.error('Failed to bulk update:', error);
      alert('Failed to update assets: ' + error.message);
    } finally {
      setIsBulkOperating(false);
    }
  };

  const bulkDeleteAssets = async () => {
    if (selectedAssets.length === 0) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedAssets.length} selected assets? This action cannot be undone.`
    );
    
    if (!confirmed) return;
    
    try {
      setIsBulkOperating(true);
      const contextHeaders = getAuthHeaders();
      
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_BULK, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          asset_ids: selectedAssets
        })
      });
      
      // Refresh the assets list
      const filters = {
        asset_type: selectedFilter,
        environment: selectedEnv,
        department: selectedDept,
        criticality: selectedCriticality,
        search: searchTerm
      };
      await fetchAssets(currentPage, filters);
      
      // Clear selection
      clearSelection();
      
      alert(`Successfully deleted ${selectedAssets.length} assets`);
      
    } catch (error) {
      console.error('Failed to bulk delete:', error);
      alert('Failed to delete assets: ' + error.message);
    } finally {
      setIsBulkOperating(false);
    }
  };

  const cleanupDuplicates = async () => {
    const confirmed = window.confirm(
      'This will remove duplicate assets from your inventory. Do you want to continue?'
    );
    
    if (!confirmed) return;
    
    try {
      setIsBulkOperating(true);
      const contextHeaders = getAuthHeaders();
      
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_CLEANUP, {
        method: 'POST',
        headers: contextHeaders
      });
      
      // Refresh the assets list
      const filters = {
        asset_type: selectedFilter,
        environment: selectedEnv,
        department: selectedDept,
        criticality: selectedCriticality,
        search: searchTerm
      };
      await fetchAssets(currentPage, filters);
      
      alert(`Successfully removed ${result.removed_count} duplicate assets`);
      
    } catch (error) {
      console.error('Failed to cleanup duplicates:', error);
      alert('Failed to cleanup duplicates: ' + error.message);
    } finally {
      setIsBulkOperating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <div className="flex h-full">
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            <main className="p-8">
              <div className="max-w-5xl mx-auto">
            {/* Header with Breadcrumbs */}
            <div className="mb-8">
              <div className="mb-4">
                <ContextBreadcrumbs showContextSelector={true} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Asset Inventory</h1>
                  <p className="text-lg text-gray-600">
                    Comprehensive inventory of discovered IT assets
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  {selectedAssets.length > 0 && (
                    <>
                      <button
                        onClick={() => setShowBulkEditDialog(true)}
                        disabled={isBulkOperating}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                      >
                        <Database className="h-5 w-5" />
                        <span>Edit {selectedAssets.length}</span>
                      </button>
                      <button
                        onClick={bulkDeleteAssets}
                        disabled={isBulkOperating}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                      >
                        <Trash2 className="h-5 w-5" />
                        <span>Delete {selectedAssets.length}</span>
                      </button>
                      <button
                        onClick={clearSelection}
                        className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2"
                      >
                        <Eye className="h-5 w-5" />
                        <span>Clear</span>
                      </button>
                    </>
                  )}
                  <button
                    onClick={cleanupDuplicates}
                    disabled={isBulkOperating}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <ArrowUpDown className="h-5 w-5" />
                    <span>De-dupe</span>
                  </button>
                  <button 
                    onClick={() => setShowAppMapping(!showAppMapping)}
                    className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                      showAppMapping 
                        ? 'bg-purple-600 text-white hover:bg-purple-700' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    <Database className="h-5 w-5" />
                    <span>App Dependencies</span>
                  </button>
                  <button 
                    onClick={() => {
                      // Clear cache and force fresh fetch
                      const filters = {
                        asset_type: selectedFilter,
                        environment: selectedEnv,
                        department: selectedDept,
                        criticality: selectedCriticality,
                        search: searchTerm
                      };
                      const cacheKey = getCacheKey(currentPage, filters);
                      localStorage.removeItem(cacheKey);
                      fetchAssets(currentPage, filters);
                    }}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                  <button 
                    onClick={exportToCSV}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                  >
                    <Download className="h-5 w-5" />
                    <span>Export CSV</span>
                  </button>
                </div>
              </div>

              {/* Status Bar */}
              <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-700">
                    {error ? (
                      <span className="text-red-600">
                        <strong>Error:</strong> {error} - Unable to load data
                      </span>
                    ) : dataSource === 'live' ? (
                      <span className="text-green-600">
                        <strong>Live Data:</strong> Showing {summary.filtered || 0} of {summary.total || 0} processed assets from CMDB import
                      </span>
                    ) : dataSource === 'cached' ? (
                      <span className="text-blue-600">
                        <strong>Cached Data:</strong> Showing {summary.filtered || 0} of {summary.total || 0} assets (refreshing in background)
                      </span>
                    ) : dataSource === 'empty' ? (
                      <span className="text-orange-600">
                        <strong>No Data:</strong> Database is empty - import CMDB data to see assets here
                      </span>
                    ) : (
                      <span className="text-blue-600">
                        <strong>Demo Data:</strong> Showing sample data for development and testing
                      </span>
                    )}
                  </p>
                  {lastUpdated && (
                    <p className="text-sm text-gray-500">
                      Last updated: {new Date(lastUpdated).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Tab Navigation */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-6">
                <TabsTrigger value="assets" className="flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Asset Inventory
                </TabsTrigger>
                <TabsTrigger value="applications" className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Application Portfolio
                </TabsTrigger>
                <TabsTrigger value="unlinked" className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Unlinked Assets
                </TabsTrigger>
              </TabsList>

              <TabsContent value="assets" className="space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-6 gap-6 mb-8">
              {[
                { key: 'applications', label: 'Applications', icon: Database, color: 'bg-blue-500' },
                { key: 'servers', label: 'Servers', icon: Server, color: 'bg-green-500' },
                { key: 'databases', label: 'Databases', icon: HardDrive, color: 'bg-purple-500' },
                { key: 'devices', label: 'Devices', icon: Router, color: 'bg-orange-500' },
                { key: 'unknown', label: 'Unknown', icon: Zap, color: 'bg-gray-500' },
                { key: 'total', label: 'Total', icon: Server, color: 'bg-indigo-500' }
              ].map(({ key, label, icon: Icon, color }) => (
                <div key={key} className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className={`${color} rounded-md p-3`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">{label}</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {summary[key] || 0}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Search and Filters */}
            <div className="bg-white rounded-lg shadow mb-6 p-6">
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                {/* Search */}
                <div className="md:col-span-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                    <input
                      type="text"
                      placeholder="Search assets..."
                      value={searchTerm}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                      className="pl-10 w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Type Filter */}
                <div>
                  <select
                    value={selectedFilter}
                    onChange={(e) => handleFilterChange('type', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Types</option>
                    <option value="application">Applications</option>
                    <option value="server">Servers</option>
                    <option value="database">Databases</option>
                    <option value="network device">Network Devices</option>
                    <option value="storage device">Storage Devices</option>
                    <option value="security device">Security Devices</option>
                    <option value="infrastructure device">Infrastructure Devices</option>
                    <option value="unknown">Unknown Devices</option>
                    <option value="unlinked">Unlinked Assets</option>
                  </select>
                </div>

                {/* Environment Filter */}
                <div>
                  <select
                    value={selectedEnv}
                    onChange={(e) => handleFilterChange('environment', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Environments</option>
                    <option value="production">Production</option>
                    <option value="test">Test</option>
                    <option value="dev">Development</option>
                    <option value="staging">Staging</option>
                  </select>
                </div>

                {/* Department Filter */}
                <div>
                  <select
                    value={selectedDept}
                    onChange={(e) => handleFilterChange('department', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Departments</option>
                    {getUniqueValues('department').map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>

                {/* Page Size */}
                <div>
                  <select
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={10}>10 per page</option>
                    <option value={25}>25 per page</option>
                    <option value={50}>50 per page</option>
                    <option value={100}>100 per page</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Asset Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="min-w-full">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={selectedAssets.length === assets.length && assets.length > 0}
                            onChange={() => selectedAssets.length === assets.length ? clearSelection() : selectAllAssets()}
                            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span>Select</span>
                        </div>
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Environment</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <div className="flex items-center space-x-1">
                          <span>Readiness</span>
                          <div className="group relative">
                            <span className="text-blue-500 cursor-help">ⓘ</span>
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                              Migration readiness: mapped, cleansed, dependencies analyzed
                            </div>
                          </div>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {isLoading ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center">
                          <div className="flex items-center justify-center">
                            <RefreshCw className="animate-spin h-5 w-5 text-gray-400 mr-2" />
                            <span className="text-gray-500">Loading assets...</span>
                          </div>
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center text-red-600">
                          <p>Error loading assets: {error}</p>
                        </td>
                      </tr>
                    ) : assets.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center">
                          <div className="text-gray-500">
                            <Database className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                            <h3 className="text-lg font-medium mb-2">No assets found</h3>
                            <p className="text-sm">
                              {dataSource === 'live' 
                                ? "No assets match your current filters. Try adjusting the search criteria."
                                : "Upload and process CMDB data to see your assets here."
                              }
                            </p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      assets.map((asset) => {
                        // Map asset data to display fields
                        const displayAsset = {
                          id: asset.id || asset.ci_id || asset.asset_id,
                          name: asset.asset_name || asset.hostname || asset.name || 'Unknown Asset',
                          type: asset.asset_type || asset.ci_type || asset.type || 'Unknown',
                          environment: asset.environment || 'Unknown',
                          owner: asset.business_owner || asset.owner || 'Unknown',
                          location: asset.location || asset.datacenter || 'Unknown',
                          status: asset.status || 'Unknown',
                          // Additional fields for display
                          ipAddress: asset.ip_address || asset.ipAddress,
                          operatingSystem: asset.operating_system || asset.os_type,
                          cpuCores: asset.cpu_cores || asset.cpuCores,
                          memoryGb: asset.memory_gb || asset.ram_gb || asset.memoryGb,
                          storageGb: asset.storage_gb || asset.storageGb,
                          applicationMapped: asset.application_name || asset.application || asset.applicationMapped,
                          criticality: asset.business_criticality || asset.criticality
                        };
                        
                        return (
                          <tr key={displayAsset.id} className={`hover:bg-gray-50 ${selectedAssets.includes(displayAsset.id) ? 'bg-blue-50' : ''}`}>
                            {/* Selection Checkbox */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <input
                                type="checkbox"
                                checked={selectedAssets.includes(displayAsset.id)}
                                onChange={() => toggleAssetSelection(displayAsset.id)}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                              />
                            </td>
                            
                            {/* Asset Info */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className={`mr-3 ${getTypeColor(displayAsset.type)}`}>
                                  {getTypeIcon(displayAsset.type)}
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{displayAsset.name}</div>
                                  {displayAsset.ipAddress && (
                                    <div className="text-sm text-gray-500">{displayAsset.ipAddress}</div>
                                  )}
                                </div>
                              </div>
                            </td>

                            {/* Type */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">{displayAsset.type}</div>
                              {displayAsset.operatingSystem && (
                                <div className="text-sm text-gray-500">{displayAsset.operatingSystem}</div>
                              )}
                            </td>

                            {/* Environment */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                displayAsset.environment === 'Production' ? 'bg-red-100 text-red-800' :
                                displayAsset.environment === 'Test' ? 'bg-yellow-100 text-yellow-800' :
                                displayAsset.environment === 'Development' ? 'bg-green-100 text-green-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {displayAsset.environment}
                              </span>
                            </td>

                            {/* Owner */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">{displayAsset.owner}</div>
                            </td>

                            {/* Location */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">{displayAsset.location}</div>
                            </td>

                            {/* Readiness Confidence */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              {(() => {
                                const { confidence, factors } = calculateReadinessConfidence(displayAsset);
                                return (
                                  <div className="group relative">
                                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getReadinessColor(confidence)}`}>
                                      {confidence}%
                                    </span>
                                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded py-2 px-3 whitespace-nowrap z-10">
                                      <div className="font-medium mb-1">Readiness Factors:</div>
                                      {factors.length > 0 ? (
                                        <div className="space-y-1">
                                          {factors.map((factor, idx) => (
                                            <div key={idx}>✓ {factor}</div>
                                          ))}
                                        </div>
                                      ) : (
                                        <div>No factors complete</div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })()}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {!isLoading && !error && assets.length > 0 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-4 rounded-lg shadow">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => handlePageChange(pagination.current_page - 1)}
                    disabled={!pagination.has_previous}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.current_page + 1)}
                    disabled={!pagination.has_next}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">
                        {((pagination.current_page - 1) * pagination.page_size) + 1}
                      </span>{' '}
                      to{' '}
                      <span className="font-medium">
                        {Math.min(pagination.current_page * pagination.page_size, pagination.total_items)}
                      </span>{' '}
                      of{' '}
                      <span className="font-medium">{pagination.total_items}</span> results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => handlePageChange(pagination.current_page - 1)}
                        disabled={!pagination.has_previous}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <ChevronLeft className="h-5 w-5" />
                      </button>
                      
                      {/* Page numbers */}
                      {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                        const pageNum = i + 1;
                        const isCurrentPage = pageNum === pagination.current_page;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              isCurrentPage
                                ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      
                      <button
                        onClick={() => handlePageChange(pagination.current_page + 1)}
                        disabled={!pagination.has_next}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}

            {/* App-to-Server Mapping Section */}
            {showAppMapping && (
              <div className="mt-8 bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Application Dependencies</h3>
                  <p className="text-sm text-gray-500 mt-1">View and manage application to server mappings</p>
                </div>
                
                <div className="p-6">
                  {mappingLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <RefreshCw className="animate-spin h-5 w-5 text-gray-400 mr-2" />
                      <span className="text-gray-500">Loading app mappings...</span>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* App Selector */}
                      <div className="flex items-center space-x-4">
                        <label className="text-sm font-medium text-gray-700">Select Application:</label>
                        <select
                          value={selectedApp}
                          onChange={(e) => setSelectedApp(e.target.value)}
                          className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Choose an application...</option>
                          {appMappings.map(app => (
                            <option key={app.id} value={app.id}>{app.name}</option>
                          ))}
                        </select>
                        <button
                          onClick={fetchAppMappings}
                          disabled={mappingLoading}
                          className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                          title="Refresh application list"
                        >
                          <RefreshCw className={`h-4 w-4 ${mappingLoading ? 'animate-spin' : ''}`} />
                          <span>Refresh</span>
                        </button>
                        {appMappings.length === 0 && !mappingLoading && (
                          <span className="text-sm text-orange-600">
                            No applications found. Try refreshing or check if assets are properly mapped.
                          </span>
                        )}
                      </div>

                      {/* Selected App Details */}
                      {selectedApp && (
                        <div className="border border-gray-200 rounded-lg p-4">
                          {(() => {
                            const app = appMappings.find(a => a.id === selectedApp);
                            if (!app) return null;
                            
                            return (
                              <div>
                                <div className="mb-4">
                                  <h4 className="text-lg font-medium text-gray-900">{app.name}</h4>
                                  <p className="text-sm text-gray-600">{app.description}</p>
                                </div>
                                
                                {app.servers && app.servers.length > 0 ? (
                                  <div>
                                    <h5 className="text-sm font-medium text-gray-700 mb-3">
                                      Associated Servers ({app.servers.length})
                                    </h5>
                                    <div className="overflow-x-auto">
                                      <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                          <tr>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Server</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">OS</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Specs</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Environment</th>
                                          </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                          {app.servers.map(server => (
                                            <tr key={server.id} className="hover:bg-gray-50">
                                              <td className="px-4 py-3 text-sm font-medium text-gray-900">{server.name}</td>
                                              <td className="px-4 py-3 text-sm text-gray-500">{server.type}</td>
                                              <td className="px-4 py-3 text-sm text-gray-500">{server.ipAddress || '-'}</td>
                                              <td className="px-4 py-3 text-sm text-gray-500">{server.operatingSystem || '-'}</td>
                                              <td className="px-4 py-3 text-sm text-gray-500">
                                                {server.cpuCores && server.memoryGb ? 
                                                  `${server.cpuCores} cores, ${server.memoryGb}GB` : '-'
                                                }
                                              </td>
                                              <td className="px-4 py-3">
                                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                                  server.environment === 'Production' ? 'bg-red-100 text-red-800' :
                                                  server.environment === 'Test' ? 'bg-yellow-100 text-yellow-800' :
                                                  server.environment === 'Dev' ? 'bg-green-100 text-green-800' :
                                                  'bg-gray-100 text-gray-800'
                                                }`}>
                                                  {server.environment}
                                                </span>
                                              </td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  </div>
                                ) : (
                                  <p className="text-sm text-gray-500">No servers mapped to this application.</p>
                                )}
                              </div>
                            );
                          })()}
                        </div>
                      )}

                      {/* Summary */}
                      {appMappings.length > 0 && (
                        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">
                              {appMappings.length}
                            </div>
                            <div className="text-sm text-gray-600">Applications</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">
                              {appMappings.reduce((total, app) => total + (app.servers ? app.servers.length : 0), 0)}
                            </div>
                            <div className="text-sm text-gray-600">Mapped Servers</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-orange-600">
                              {assets.filter(asset => 
                                ['Server', 'Database'].includes(asset.type) && !asset.applicationMapped
                              ).length}
                            </div>
                            <div className="text-sm text-gray-600">Unmapped Servers</div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
              </TabsContent>

              <TabsContent value="applications" className="space-y-6">
                <ApplicationDiscoveryPanel 
                  onApplicationSelect={(application) => {
                    console.log('Application selected:', application);
                  }}
                  onValidationSubmit={(applicationId, validation) => {
                    console.log('Application validation submitted:', applicationId, validation);
                  }}
                />
              </TabsContent>

              <TabsContent value="unlinked" className="space-y-6">
                {/* Unlinked Assets Header */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                        <Shield className="h-5 w-5 text-orange-600" />
                        Unlinked Assets
                      </h2>
                      <p className="text-gray-600 mt-1">
                        Assets not tied to any application - critical for migration planning
                      </p>
                    </div>
                    <button
                      onClick={fetchUnlinkedAssets}
                      disabled={unlinkedLoading}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                    >
                      <RefreshCw className={`h-4 w-4 ${unlinkedLoading ? 'animate-spin' : ''}`} />
                      <span>Refresh</span>
                    </button>
                  </div>

                  {/* Migration Impact Alert */}
                  {unlinkedSummary.migration_impact !== 'none' && (
                    <div className={`p-4 rounded-lg border-2 mb-4 ${
                      unlinkedSummary.migration_impact === 'high' 
                        ? 'bg-red-50 border-red-200 text-red-800'
                        : unlinkedSummary.migration_impact === 'medium'
                        ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                        : 'bg-blue-50 border-blue-200 text-blue-800'
                    }`}>
                      <div className="flex items-center">
                        <AlertCircle className="h-5 w-5 mr-2" />
                        <div>
                          <h3 className="font-medium">
                            {unlinkedSummary.migration_impact === 'high' ? 'High Migration Impact' :
                             unlinkedSummary.migration_impact === 'medium' ? 'Medium Migration Impact' :
                             'Low Migration Impact'}
                          </h3>
                          <p className="text-sm mt-1">
                            {unlinkedSummary.migration_impact === 'high' 
                              ? 'These unlinked assets may significantly impact migration planning. Review and map to applications.'
                              : unlinkedSummary.migration_impact === 'medium'
                              ? 'Some unlinked assets require attention for migration planning.'
                              : 'Unlinked assets have minimal impact on migration planning.'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Summary Cards */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <Shield className="h-8 w-8 text-orange-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-600">Total Unlinked</p>
                          <p className="text-2xl font-bold text-gray-900">{unlinkedSummary.total_unlinked}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <Server className="h-8 w-8 text-blue-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-600">Servers</p>
                          <p className="text-2xl font-bold text-gray-900">{unlinkedSummary.by_type?.Server || 0}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <Database className="h-8 w-8 text-purple-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-600">Databases</p>
                          <p className="text-2xl font-bold text-gray-900">{unlinkedSummary.by_type?.Database || 0}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <Router className="h-8 w-8 text-green-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-600">Infrastructure</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {(unlinkedSummary.by_type?.['Infrastructure Device'] || 0) + 
                             (unlinkedSummary.by_type?.['Network Device'] || 0) + 
                             (unlinkedSummary.by_type?.['Storage Device'] || 0)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Unlinked Assets Table */}
                {unlinkedLoading ? (
                  <div className="bg-white rounded-lg shadow p-8">
                    <div className="flex items-center justify-center">
                      <RefreshCw className="animate-spin h-8 w-8 text-gray-400 mr-3" />
                      <span className="text-gray-600">Loading unlinked assets...</span>
                    </div>
                  </div>
                ) : unlinkedAssets.length === 0 ? (
                  <div className="bg-white rounded-lg shadow p-8">
                    <div className="text-center">
                      <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">All Assets Linked!</h3>
                      <p className="text-gray-600">
                        Great! All assets are properly linked to applications. This will make migration planning much easier.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h3 className="text-lg font-medium text-gray-900">
                        Unlinked Assets ({unlinkedAssets.length})
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        These assets need to be mapped to applications for proper migration planning
                      </p>
                    </div>
                    
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Asset
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Type
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Environment
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Criticality
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Migration Consideration
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Details
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {unlinkedAssets.map((asset) => (
                            <tr key={asset.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  {getTypeIcon(asset.type)}
                                  <div className="ml-3">
                                    <div className="text-sm font-medium text-gray-900">{asset.name}</div>
                                    {asset.hostname && (
                                      <div className="text-sm text-gray-500">{asset.hostname}</div>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(asset.type)}`}>
                                  {asset.type}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  asset.environment === 'Production' ? 'bg-red-100 text-red-800' :
                                  asset.environment === 'Test' ? 'bg-yellow-100 text-yellow-800' :
                                  asset.environment === 'Development' ? 'bg-green-100 text-green-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {asset.environment}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  asset.criticality === 'High' ? 'bg-red-100 text-red-800' :
                                  asset.criticality === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-green-100 text-green-800'
                                }`}>
                                  {asset.criticality}
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-gray-900 max-w-xs">
                                  {asset.migration_consideration}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <div className="space-y-1">
                                  {asset.ip_address && (
                                    <div>IP: {asset.ip_address}</div>
                                  )}
                                  {asset.operating_system && (
                                    <div>OS: {asset.operating_system}</div>
                                  )}
                                  {asset.memory_gb && (
                                    <div>RAM: {asset.memory_gb}GB</div>
                                  )}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex space-x-2">
                                  <select
                                    className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    defaultValue=""
                                    onChange={(e) => {
                                      if (e.target.value) {
                                        // TODO: Implement link asset to application
                                        console.log('Link asset', asset.id, 'to app', e.target.value);
                                        alert(`Will link ${asset.name} to application ${e.target.value}`);
                                      }
                                    }}
                                  >
                                    <option value="">Link to App...</option>
                                    {appMappings.map(app => (
                                      <option key={app.id} value={app.id}>{app.name}</option>
                                    ))}
                                  </select>
                                  <button
                                    className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 transition-colors"
                                    onClick={() => {
                                      // Switch to Application Portfolio tab
                                      setActiveTab('applications');
                                    }}
                                    title="Go to Application Portfolio"
                                  >
                                    View Apps
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>
              </div>
            </main>
          </div>

          {/* Agent Interaction Sidebar */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="asset-inventory"
                refreshTrigger={agentRefreshTrigger}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Inventory question answered:', questionId, response);
                  // Trigger asset re-analysis or asset updates based on agent learning
                  const filters = {
                    asset_type: selectedFilter,
                    environment: selectedEnv,
                    department: selectedDept,
                    criticality: selectedCriticality,
                    search: searchTerm
                  };
                  fetchAssets(currentPage, filters);
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="asset-inventory"
                refreshTrigger={agentRefreshTrigger}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Asset classification updated:', itemId, newClassification);
                  // Update local asset data quality classification
                  setAssets(prev => prev.map(asset => 
                    asset.id === itemId 
                      ? { ...asset, dataQuality: newClassification }
                      : asset
                  ));
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="asset-inventory"
                refreshTrigger={agentRefreshTrigger}
                onInsightAction={(insightId, action) => {
                  console.log('Inventory insight action:', insightId, action);
                  // Apply agent insights for inventory optimization
                  if (action === 'apply_insight') {
                    // Trigger bulk updates or asset categorization improvements
                    console.log('Applying agent inventory insights');
                  }
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard 
                pageContext="asset-inventory"
                triggerElement={
                  <div className="bg-white rounded-lg shadow p-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      Agent Planning
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      View and manage agent workflow plans for asset analysis.
                    </p>
                    <Button className="w-full">
                      <Brain className="h-4 w-4 mr-2" />
                      Open Planning Dashboard
                    </Button>
                  </div>
                }
                onPlanApproval={(planId, approved) => {
                  console.log('Inventory plan approval:', planId, approved);
                  // Handle plan approval for asset inventory
                }}
                onTaskFeedback={(taskId, feedback) => {
                  console.log('Task feedback:', taskId, feedback);
                  // Handle task feedback
                }}
                onHumanInput={(taskId, input) => {
                  console.log('Human input provided:', taskId, input);
                  // Handle human input for agent tasks
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bulk Edit Dialog */}
      {showBulkEditDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Bulk Edit {selectedAssets.length} Assets
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Asset Type
                </label>
                <select
                  value={bulkEditData.asset_type}
                  onChange={(e) => setBulkEditData(prev => ({ ...prev, asset_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Keep current values</option>
                  <option value="Application">Application</option>
                  <option value="Server">Server</option>
                  <option value="Database">Database</option>
                  <option value="Network Device">Network Device</option>
                  <option value="Storage Device">Storage Device</option>
                  <option value="Security Device">Security Device</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Environment
                </label>
                <select
                  value={bulkEditData.environment}
                  onChange={(e) => setBulkEditData(prev => ({ ...prev, environment: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Keep current values</option>
                  <option value="Production">Production</option>
                  <option value="Test">Test</option>
                  <option value="Development">Development</option>
                  <option value="Staging">Staging</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Department
                </label>
                <input
                  type="text"
                  value={bulkEditData.department}
                  onChange={(e) => setBulkEditData(prev => ({ ...prev, department: e.target.value }))}
                  placeholder="Leave empty to keep current values"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Criticality
                </label>
                <select
                  value={bulkEditData.criticality}
                  onChange={(e) => setBulkEditData(prev => ({ ...prev, criticality: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Keep current values</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowBulkEditDialog(false);
                  setBulkEditData({
                    environment: '',
                    department: '',
                    criticality: '',
                    asset_type: ''
                  });
                }}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={bulkUpdateAssets}
                disabled={isBulkOperating}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isBulkOperating ? 'Updating...' : `Update ${selectedAssets.length} Assets`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
