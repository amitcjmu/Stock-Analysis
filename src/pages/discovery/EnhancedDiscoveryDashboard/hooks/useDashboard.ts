import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext';
import { dashboardService } from '../services/dashboardService';
import type { DashboardState } from '../types';

export const useDashboard = (): JSX.Element => {
  const { user, client, engagement } = useAuth();

  const [state, setState] = useState<DashboardState>({
    currentFlow: null,
    flowLoading: false,
    flowError: null,
    isHealthy: true,
    activeFlows: [],
    systemMetrics: null,
    crewPerformance: [],
    platformAlerts: [],
    selectedTimeRange: '24h',
    isLoading: false,
    lastUpdated: new Date(),
    error: null,
    showIncompleteFlowManager: false,
    selectedFlowForStatus: null
  });

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const data = await dashboardService.fetchDashboardData(user, client, engagement);

      setState(prev => ({
        ...prev,
        activeFlows: data.activeFlows,
        systemMetrics: data.systemMetrics,
        crewPerformance: data.crewPerformance,
        platformAlerts: data.platformAlerts,
        lastUpdated: new Date(),
        isLoading: false
      }));
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to fetch dashboard data',
        isLoading: false
      }));
    }
  }, [user, client, engagement]);

  // Refresh flow data
  const refreshFlow = useCallback(async () => {
    setState(prev => ({ ...prev, flowLoading: true }));
    try {
      await fetchDashboardData();
    } catch (error) {
      setState(prev => ({ ...prev, flowError: error }));
    } finally {
      setState(prev => ({ ...prev, flowLoading: false }));
    }
  }, [fetchDashboardData]);

  // Update specific state values
  const updateState = useCallback((updates: Partial<DashboardState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Set time range filter
  const setSelectedTimeRange = useCallback((timeRange: string) => {
    setState(prev => ({ ...prev, selectedTimeRange: timeRange }));
  }, []);

  // Toggle flow manager dialog
  const toggleFlowManager = useCallback((show?: boolean) => {
    setState(prev => ({
      ...prev,
      showIncompleteFlowManager: show !== undefined ? show : !prev.showIncompleteFlowManager
    }));
  }, []);

  // Set selected flow for status monitoring
  const setSelectedFlowForStatus = useCallback((flowId: string | null) => {
    setState(prev => ({ ...prev, selectedFlowForStatus: flowId }));
  }, []);

  // Load data on mount and when context changes
  useEffect(() => {
    if (user && client && engagement) {
      fetchDashboardData();
    }
  }, [fetchDashboardData, user, client, engagement]);

  return {
    // State
    ...state,

    // Actions
    fetchDashboardData,
    refreshFlow,
    updateState,
    setSelectedTimeRange,
    toggleFlowManager,
    setSelectedFlowForStatus
  };
};
