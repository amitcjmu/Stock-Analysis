/**
 * Shared observability context for state management
 * Provides centralized state for agent data and filters
 */

import React from 'react'
import type { createContext }
import { useContext, useState, ReactNode  } from 'react'
import { useCallback } from 'react'
import type { AgentCardData } from '../../../types/api/observability/agent-performance';
import type { useAgentData } from '../hooks/useAgentData';
import { useAgentFilters } from '../hooks/useAgentFilters';

interface ObservabilityContextValue {
  // Agent data
  agents: AgentCardData[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
  
  // Filters
  filters: {
    searchQuery?: string;
    status?: Array<'active' | 'idle' | 'error' | 'offline'>;
    sortBy?: 'name' | 'successRate' | 'totalTasks' | 'lastActive';
    sortOrder?: 'asc' | 'desc';
  };
  filteredAgents: AgentCardData[];
  updateFilters: (filters: Partial<ObservabilityContextValue['filters']>) => void;
  clearFilters: () => void;
  statusDistribution: Record<string, number>;
  
  // Selected agents
  selectedAgents: string[];
  selectAgent: (agentId: string) => void;
  deselectAgent: (agentId: string) => void;
  toggleAgentSelection: (agentId: string) => void;
  clearSelection: () => void;
  
  // View preferences
  viewMode: 'grid' | 'list';
  setViewMode: (mode: 'grid' | 'list') => void;
  compactView: boolean;
  setCompactView: (compact: boolean) => void;
  
  // Period selection
  period: number;
  setPeriod: (days: number) => void;
}

const ObservabilityContext = createContext<ObservabilityContextValue | undefined>(undefined);

export const useObservability = () => {
  const context = useContext(ObservabilityContext);
  if (!context) {
    throw new Error('useObservability must be used within ObservabilityProvider');
  }
  return context;
};

interface ObservabilityProviderProps {
  children: ReactNode;
  defaultPeriod?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const ObservabilityProvider: React.FC<ObservabilityProviderProps> = ({
  children,
  defaultPeriod = 7,
  autoRefresh = false,
  refreshInterval = 30000
}) => {
  const [period, setPeriod] = useState(defaultPeriod);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [compactView, setCompactView] = useState(false);

  // Use agent data hook
  const { agents, loading, error, refresh, lastUpdated } = useAgentData({
    period,
    autoRefresh,
    refreshInterval
  });

  // Use filters hook
  const {
    filters,
    filteredAgents,
    updateFilters,
    clearFilters,
    statusDistribution
  } = useAgentFilters(agents);

  // Selection management
  const selectAgent = useCallback((agentId: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentId) ? prev : [...prev, agentId]
    );
  }, []);

  const deselectAgent = useCallback((agentId: string) => {
    setSelectedAgents(prev => prev.filter(id => id !== agentId));
  }, []);

  const toggleAgentSelection = useCallback((agentId: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    );
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedAgents([]);
  }, []);

  const value: ObservabilityContextValue = {
    // Agent data
    agents,
    loading,
    error,
    lastUpdated,
    refresh,
    
    // Filters
    filters,
    filteredAgents,
    updateFilters,
    clearFilters,
    statusDistribution,
    
    // Selected agents
    selectedAgents,
    selectAgent,
    deselectAgent,
    toggleAgentSelection,
    clearSelection,
    
    // View preferences
    viewMode,
    setViewMode,
    compactView,
    setCompactView,
    
    // Period selection
    period,
    setPeriod
  };

  return (
    <ObservabilityContext.Provider value={value}>
      {children}
    </ObservabilityContext.Provider>
  );
};

// Convenience hooks for specific parts of the context
export const useAgentSelection = () => {
  const context = useObservability();
  return {
    selectedAgents: context.selectedAgents,
    selectAgent: context.selectAgent,
    deselectAgent: context.deselectAgent,
    toggleAgentSelection: context.toggleAgentSelection,
    clearSelection: context.clearSelection
  };
};

export const useViewPreferences = () => {
  const context = useObservability();
  return {
    viewMode: context.viewMode,
    setViewMode: context.setViewMode,
    compactView: context.compactView,
    setCompactView: context.setCompactView
  };
};