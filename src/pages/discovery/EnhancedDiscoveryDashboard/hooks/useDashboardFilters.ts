import { useState } from 'react'
import { useMemo, useCallback } from 'react'
import type { FlowSummary, DashboardFilters } from '../types';

interface UseDashboardFiltersReturn {
  filters: DashboardFilters;
  filteredFlows: FlowSummary[];
  availableOptions: {
    statuses: string[];
    flowTypes: string[];
    timeRanges: Array<{ value: string; label: string }>;
  };
  updateFilters: (updates: Partial<DashboardFilters>) => void;
  resetFilters: () => void;
  toggleStatusFilter: (status: string) => void;
  toggleFlowTypeFilter: (flowType: string) => void;
  setSearchQuery: (query: string) => void;
  setTimeRange: (timeRange: string) => void;
}

export const useDashboardFilters = (flows: FlowSummary[] | undefined): UseDashboardFiltersReturn => {
  const [filters, setFilters] = useState<DashboardFilters>({
    timeRange: '24h',
    status: [],
    flowType: [],
    searchQuery: ''
  });

  // Filter flows based on current filters
  const filteredFlows = useMemo(() => {
    // Defensive check: Handle undefined/null flows
    if (!flows || !Array.isArray(flows)) {
      return [];
    }

    return flows.filter(flow => {
      // Status filter
      if (filters.status.length > 0 && !filters.status.includes(flow.status)) {
        return false;
      }

      // Flow type filter
      if (filters.flowType.length > 0 && !filters.flowType.includes(flow.flow_type)) {
        return false;
      }

      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const searchableText = [
          flow.client_name,
          flow.engagement_name,
          flow.current_phase,
          flow.flow_id
        ].join(' ').toLowerCase();

        if (!searchableText.includes(query)) {
          return false;
        }
      }

      // Time range filter
      if (filters.timeRange !== 'all') {
        const now = new Date();
        const flowDate = new Date(flow.started_at);
        const diffHours = (now.getTime() - flowDate.getTime()) / (1000 * 60 * 60);

        switch (filters.timeRange) {
          case '1h':
            if (diffHours > 1) return false;
            break;
          case '6h':
            if (diffHours > 6) return false;
            break;
          case '24h':
            if (diffHours > 24) return false;
            break;
          case '7d':
            if (diffHours > 24 * 7) return false;
            break;
          case '30d':
            if (diffHours > 24 * 30) return false;
            break;
        }
      }

      return true;
    });
  }, [flows, filters]);

  // Update filters
  const updateFilters = useCallback((updates: Partial<DashboardFilters>) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters({
      timeRange: '24h',
      status: [],
      flowType: [],
      searchQuery: ''
    });
  }, []);

  // Toggle status filter
  const toggleStatusFilter = useCallback((status: string) => {
    setFilters(prev => ({
      ...prev,
      status: prev.status.includes(status)
        ? prev.status.filter(s => s !== status)
        : [...prev.status, status]
    }));
  }, []);

  // Toggle flow type filter
  const toggleFlowTypeFilter = useCallback((flowType: string) => {
    setFilters(prev => ({
      ...prev,
      flowType: prev.flowType.includes(flowType)
        ? prev.flowType.filter(t => t !== flowType)
        : [...prev.flowType, flowType]
    }));
  }, []);

  // Set search query
  const setSearchQuery = useCallback((query: string) => {
    setFilters(prev => ({ ...prev, searchQuery: query }));
  }, []);

  // Set time range
  const setTimeRange = useCallback((timeRange: string) => {
    setFilters(prev => ({ ...prev, timeRange }));
  }, []);

  // Get available filter options
  const availableOptions = useMemo(() => {
    // Defensive check: Handle undefined/null flows
    if (!flows || !Array.isArray(flows)) {
      return {
        statuses: [],
        flowTypes: [],
        timeRanges: [
          { value: '1h', label: 'Last Hour' },
          { value: '6h', label: 'Last 6 Hours' },
          { value: '24h', label: 'Last 24 Hours' },
          { value: '7d', label: 'Last 7 Days' },
          { value: '30d', label: 'Last 30 Days' },
          { value: 'all', label: 'All Time' }
        ]
      };
    }

    const statuses = [...new Set(flows.map(f => f.status))];
    const flowTypes = [...new Set(flows.map(f => f.flow_type))];

    return {
      statuses,
      flowTypes,
      timeRanges: [
        { value: '1h', label: 'Last Hour' },
        { value: '6h', label: 'Last 6 Hours' },
        { value: '24h', label: 'Last 24 Hours' },
        { value: '7d', label: 'Last 7 Days' },
        { value: '30d', label: 'Last 30 Days' },
        { value: 'all', label: 'All Time' }
      ]
    };
  }, [flows]);

  return {
    filters,
    filteredFlows,
    availableOptions,
    updateFilters,
    resetFilters,
    toggleStatusFilter,
    toggleFlowTypeFilter,
    setSearchQuery,
    setTimeRange
  };
};
