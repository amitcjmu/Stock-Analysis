import { apiCall } from '@/config/api';
import { getAuthHeaders } from '../../../../utils/contextUtils';
import type { FlowSummary, SystemMetrics, CrewPerformanceMetrics, PlatformAlert } from '../types';

export interface DashboardData {
  activeFlows: FlowSummary[];
  systemMetrics: SystemMetrics;
  crewPerformance: CrewPerformanceMetrics[];
  platformAlerts: PlatformAlert[];
}

// Debouncing and caching for rate limiting
let lastFetchTime = 0;
let cachedResponse: DashboardData | null = null;
let pendingFetch: Promise<DashboardData> | null = null;
const CACHE_DURATION = 30000; // 30 seconds
const DEBOUNCE_DELAY = 500; // 500ms debounce

// Exponential backoff for 429 errors
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const makeApiCallWithRetry = async (url: string, options: any, maxRetries = 3): Promise<any> => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall(url, options);
    } catch (error: any) {
      if (error.status === 429 && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
        console.log(`🕐 Rate limited (429), retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
};

export class DashboardService {
  
  async fetchDashboardData(user: any, client: any, engagement: any): Promise<DashboardData> {
    const now = Date.now();
    
    // Return cached response if still valid
    if (cachedResponse && (now - lastFetchTime) < CACHE_DURATION) {
      console.log('📊 Returning cached dashboard data');
      return cachedResponse;
    }
    
    // Return pending fetch if one is already in progress (deduplication)
    if (pendingFetch) {
      console.log('📊 Dashboard fetch already in progress, waiting for result');
      return pendingFetch;
    }
    
    // Debouncing - wait if too soon after last fetch
    const timeSinceLastFetch = now - lastFetchTime;
    if (timeSinceLastFetch < DEBOUNCE_DELAY) {
      const waitTime = DEBOUNCE_DELAY - timeSinceLastFetch;
      console.log(`📊 Debouncing dashboard fetch for ${waitTime}ms`);
      await sleep(waitTime);
    }
    
    console.log('🔍 Fetching dashboard data for context:', {
      user: user?.id,
      client: client?.id,
      engagement: engagement?.id
    });

    // Create the fetch promise and store it to prevent duplicate calls
    pendingFetch = this._performDashboardFetch(user, client, engagement);
    
    try {
      const result = await pendingFetch;
      lastFetchTime = Date.now();
      cachedResponse = result;
      return result;
    } finally {
      pendingFetch = null;
    }
  }
  
  private async _performDashboardFetch(user: any, client: any, engagement: any): Promise<DashboardData> {
    // Fetch real-time active flows from multiple sources with retry logic
    const [discoveryFlowsResponse, dataImportsResponse] = await Promise.allSettled([
      // Get active Discovery flows - try the discovery flows endpoint first
      makeApiCallWithRetry('/api/v1/discovery/flows/active', {
        method: 'GET',
        headers: getAuthHeaders({ user, client, engagement })
      }),
      // Get data import sessions (for discovering flows)
      makeApiCallWithRetry('/api/v1/data-import/latest-import', {
        method: 'GET',
        headers: getAuthHeaders({ user, client, engagement })
      })
    ]);

    const allFlows: FlowSummary[] = [];

    // Process Discovery flows
    if (discoveryFlowsResponse.status === 'fulfilled' && discoveryFlowsResponse.value) {
      const discoveryData = discoveryFlowsResponse.value;
      console.log('📊 Discovery flows data:', discoveryData);

      // Handle both array response and object with flows array
      let flowsToProcess = [];
      
      if (Array.isArray(discoveryData)) {
        // Direct array response from /api/v1/discovery/flows/active
        flowsToProcess = discoveryData;
        console.log(`📊 Processing ${flowsToProcess.length} flows from discovery API (array response)...`);
      } else if (discoveryData.flows && Array.isArray(discoveryData.flows)) {
        // Object with flows array from unified discovery API
        flowsToProcess = discoveryData.flows;
        console.log(`📊 Processing ${flowsToProcess.length} flows from discovery API (object.flows response)...`);
      } else if (discoveryData.flow_details && Array.isArray(discoveryData.flow_details)) {
        // Legacy structure if exists
        flowsToProcess = discoveryData.flow_details;
        console.log(`📊 Processing ${flowsToProcess.length} flows from discovery API (legacy flow_details)...`);
      }

      // Process all flows with consistent handling
      for (const flow of flowsToProcess) {
        try {
          console.log('📊 Processing flow:', flow);
          
          // Extract metadata if it exists
          const metadata = flow.metadata || {};
          
          allFlows.push({
            flow_id: flow.flow_id,
            engagement_name: metadata.engagement_name || flow.engagement_name || `${client?.name || 'Unknown'} - Discovery`,
            engagement_id: flow.engagement_id || engagement?.id || 'unknown',
            client_name: metadata.client_name || flow.client_name || client?.name || 'Unknown Client',
            client_id: flow.client_account_id || flow.client_id || client?.id || 'unknown',
            status: flow.status === 'active' ? 'active' : (flow.status || 'running'),
            progress: metadata.progress_percentage || flow.progress_percentage || flow.progress || 0,
            current_phase: metadata.current_phase || flow.current_phase || 'initialization',
            started_at: flow.created_at || flow.start_time || new Date().toISOString(),
            estimated_completion: flow.estimated_completion,
            last_updated: flow.updated_at || flow.last_updated || new Date().toISOString(),
            crew_count: 6, // Standard Discovery flow has 6 crews
            active_agents: metadata.active_agents || flow.active_agents || 18,
            data_sources: metadata.data_sources || flow.data_sources || 1,
            success_criteria_met: metadata.success_criteria_met || flow.success_criteria_met || Object.values(flow.phases || metadata.phases || {}).filter(Boolean).length || 0,
            total_success_criteria: 6, // 6 phases in discovery
            flow_type: flow.type || 'discovery'
          });
        } catch (flowError) {
          console.warn('Failed to process flow:', flow, flowError);
        }
      }

      if (flowsToProcess.length === 0) {
        console.warn('📊 No flows found in response:', discoveryData);
      }
    } else {
      console.warn('📊 Discovery flows response failed or empty:', discoveryFlowsResponse);
    }

    // Process Data Import sessions to find additional flows
    if (dataImportsResponse.status === 'fulfilled' && dataImportsResponse.value) {
      const importData = dataImportsResponse.value;
      console.log('📊 Data import data:', importData);

      if (importData.success && importData.data_import) {
        const dataImport = importData.data_import;
        
        // Check if this import has an active discovery flow
        if (dataImport.id && !allFlows.find(f => f.flow_id === dataImport.id)) {
          try {
            // Get flow status for this import session with retry logic
            const flowStatusResponse = await makeApiCallWithRetry(`/api/v1/discovery/flows/${dataImport.id}/status`, {
              method: 'GET',
              headers: getAuthHeaders({ user, client, engagement })
            });

            if (flowStatusResponse && flowStatusResponse.flow_state) {
              const flowState = flowStatusResponse.flow_state;
              
              allFlows.push({
                flow_id: dataImport.id,
                engagement_name: `${client?.name || 'Current'} - Discovery`,
                engagement_id: engagement?.id || 'current',
                client_name: client?.name || 'Current Client',
                client_id: client?.id || 'current',
                status: flowState.status === 'completed' ? 'completed' : 'running',
                progress: flowState.progress_percentage || 0,
                current_phase: flowState.current_phase || 'field_mapping',
                started_at: flowState.started_at || dataImport.created_at,
                last_updated: flowState.updated_at || new Date().toISOString(),
                crew_count: 6,
                active_agents: 18,
                data_sources: 1,
                success_criteria_met: Object.values(flowState.phases || {}).filter(Boolean).length,
                total_success_criteria: 6, // 6 phases in discovery
                flow_type: 'discovery'
              });
            }
          } catch (statusError) {
            console.warn('Failed to get flow status for import:', dataImport.id, statusError);
          }
        }
      }
    }

    console.log('✅ Processed flows:', allFlows);

    // Calculate real system metrics from flows
    const runningFlows = allFlows.filter(f => f.status === 'running' || f.status === 'active');
    const completedFlows = allFlows.filter(f => f.status === 'completed');
    const totalActiveAgents = runningFlows.reduce((sum, flow) => sum + flow.active_agents, 0);
    const successRate = allFlows.length > 0 ? completedFlows.length / allFlows.length : 0;
    
    const systemMetrics: SystemMetrics = {
      total_active_flows: runningFlows.length,
      total_agents: totalActiveAgents,
      memory_utilization_gb: 4.2, // TODO: Get from monitoring API
      total_memory_gb: 8.0,
      collaboration_events_today: totalActiveAgents * 12, // Estimate based on active agents
      success_rate: successRate,
      avg_completion_time_hours: 3.2, // TODO: Calculate from completed flows
      knowledge_bases_loaded: 12 // TODO: Get from knowledge base API
    };

    // Mock crew performance data
    const crewPerformance: CrewPerformanceMetrics[] = [
      {
        crew_name: 'Field Mapping Crew',
        total_executions: 15,
        success_rate: 0.96,
        avg_duration_minutes: 12,
        collaboration_score: 8.7,
        efficiency_trend: 0.15,
        current_active: 2
      },
      {
        crew_name: 'Data Cleansing Crew',
        total_executions: 22,
        success_rate: 0.89,
        avg_duration_minutes: 18,
        collaboration_score: 7.9,
        efficiency_trend: 0.08,
        current_active: 1
      },
      {
        crew_name: 'Inventory Building Crew',
        total_executions: 18,
        success_rate: 0.94,
        avg_duration_minutes: 25,
        collaboration_score: 8.2,
        efficiency_trend: 0.12,
        current_active: 3
      }
    ];

    // Mock platform alerts
    const platformAlerts: PlatformAlert[] = [
      {
        id: '1',
        type: 'info',
        title: 'Discovery Flow Completed',
        message: 'Asset inventory has been successfully completed for Client ABC.',
        timestamp: new Date().toISOString(),
        action_required: false
      }
    ];

    return {
      activeFlows: allFlows,
      systemMetrics,
      crewPerformance,
      platformAlerts
    };
  }
}

export const dashboardService = new DashboardService();