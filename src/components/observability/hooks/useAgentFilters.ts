/**
 * Hook for managing agent filtering and sorting
 * Extracted from ResponsiveAgentListOverview
 */

import { useState, useCallback, useMemo } from 'react';
import type { AgentCardData } from '../../../types/api/observability/agent-performance';

export interface AgentFilters {
  searchQuery?: string;
  status?: ('active' | 'idle' | 'error' | 'offline')[];
  sortBy?: 'name' | 'successRate' | 'totalTasks' | 'lastActive';
  sortOrder?: 'asc' | 'desc';
}

export const useAgentFilters = (agents: AgentCardData[]) => {
  const [filters, setFilters] = useState<AgentFilters>({
    sortBy: 'name',
    sortOrder: 'asc'
  });

  const updateFilters = useCallback((newFilters: Partial<AgentFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const filteredAgents = useMemo(() => {
    let filtered = [...agents];

    // Filter by status
    if (filters.status && filters.status.length > 0) {
      filtered = filtered.filter(agent => filters.status!.includes(agent.status));
    }

    // Filter by search query
    if (filters.searchQuery && filters.searchQuery.trim()) {
      const query = filters.searchQuery.toLowerCase().trim();
      filtered = filtered.filter(agent => 
        agent.name.toLowerCase().includes(query)
      );
    }

    // Sort
    if (filters.sortBy) {
      filtered.sort((a, b) => {
        let aValue: any = a[filters.sortBy!];
        let bValue: any = b[filters.sortBy!];

        if (filters.sortBy === 'name' || filters.sortBy === 'lastActive') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        if (aValue < bValue) return filters.sortOrder === 'asc' ? -1 : 1;
        if (aValue > bValue) return filters.sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [agents, filters]);

  const clearFilters = useCallback(() => {
    setFilters({
      sortBy: 'name',
      sortOrder: 'asc'
    });
  }, []);

  const statusDistribution = useMemo(() => {
    return agents.reduce((acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [agents]);

  return {
    filters,
    filteredAgents,
    updateFilters,
    clearFilters,
    statusDistribution
  };
};