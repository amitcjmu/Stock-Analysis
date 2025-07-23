/**
 * Agent List Overview Component
 * Main dashboard component showing grid of agent performance cards
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react'
import type { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { cn } from '../../lib/utils';
import type { CardHeader, CardTitle } from '@/components/ui/card'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button';
import type { Input } from '@/components/ui/input';
import type { Badge } from '@/components/ui/badge';
import type { Filter } from 'lucide-react'
import { RefreshCw, Search, Grid, List, Settings, Activity, AlertCircle, Users, TrendingUp } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { AgentPerformanceCard, AgentPerformanceCardCompact } from './AgentPerformanceCard';
import { AgentStatusGroup } from './AgentStatusIndicator';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

import type { 
  AgentListOverviewProps,
  AgentCardData,
  AgentListState,
  AgentListFilters,
  LoadingState,
  ErrorState
} from '../../types/api/observability/agent-performance';

// Helper function to filter agents
const filterAgents = (agents: AgentCardData[], filters: AgentListFilters): AgentCardData[] => {
  let filtered = [...agents];

  // Filter by status
  if (filters.status && filters.status.length > 0) {
    filtered = filtered.filter(agent => filters.status.includes(agent.status));
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
      let aValue: string | number = a[filters.sortBy];
      let bValue: string | number = b[filters.sortBy];

      if (filters.sortBy === 'name' || filters.sortBy === 'lastActive') {
        aValue = String(aValue).toLowerCase();
        bValue = String(bValue).toLowerCase();
      }

      if (aValue < bValue) return filters.sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return filters.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }

  return filtered;
};

// Custom hook for agent data management
const useAgentData = (refreshInterval?: number) => {
  const [state, setState] = useState<AgentListState>({
    agents: [],
    filteredAgents: [],
    loading: true,
    error: null,
    selectedAgentId: null,
    filters: {
      sortBy: 'name',
      sortOrder: 'asc'
    },
    refreshing: false
  });

  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    loadingText: 'Loading agents...'
  });

  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false,
    error: null,
    retryCount: 0,
    canRetry: true
  });

  const fetchAgents = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setState(prev => ({ ...prev, refreshing: true }));
      } else {
        setLoadingState({ isLoading: true, loadingText: 'Loading agents...' });
      }

      setErrorState(prev => ({ ...prev, hasError: false, error: null }));

      const summary = await agentObservabilityService.getAllAgentsSummary();
      const agentCards = agentObservabilityService.transformToAgentCardData(summary);

      setState(prev => ({
        ...prev,
        agents: agentCards,
        filteredAgents: filterAgents(agentCards, prev.filters),
        loading: false,
        refreshing: false,
        error: null
      }));

      setLoadingState({ isLoading: false });

    } catch (error) {
      console.error('Failed to fetch agents:', error);
      
      setErrorState(prev => ({
        hasError: true,
        error: error as Error,
        errorMessage: error instanceof Error ? error.message : 'Failed to load agents',
        retryCount: prev.retryCount + 1,
        canRetry: prev.retryCount < 3
      }));

      setState(prev => ({
        ...prev,
        loading: false,
        refreshing: false,
        error: error instanceof Error ? error.message : 'Failed to load agents'
      }));

      setLoadingState({ isLoading: false });
    }
  }, []);

  const updateFilters = useCallback((newFilters: Partial<AgentListFilters>) => {
    setState(prev => {
      const updatedFilters = { ...prev.filters, ...newFilters };
      return {
        ...prev,
        filters: updatedFilters,
        filteredAgents: filterAgents(prev.agents, updatedFilters)
      };
    });
  }, []);

  const selectAgent = useCallback((agentId: string | null) => {
    setState(prev => ({ ...prev, selectedAgentId: agentId }));
  }, []);

  const retryFetch = useCallback(() => {
    if (errorState.canRetry) {
      fetchAgents();
    }
  }, [errorState.canRetry, fetchAgents]);

  // Auto-refresh functionality
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const interval = setInterval(() => {
        fetchAgents(true);
      }, refreshInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchAgents]);

  return {
    ...state,
    loadingState,
    errorState,
    fetchAgents,
    updateFilters,
    selectAgent,
    retryFetch
  };
};

export const AgentListOverview: React.FC<AgentListOverviewProps> = ({
  refreshInterval = 30,
  maxAgents,
  showFilters = true,
  compactView = false,
  onAgentSelect,
  className
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showSettings, setShowSettings] = useState(false);

  const {
    agents,
    filteredAgents,
    loading,
    error,
    selectedAgentId,
    filters,
    refreshing,
    loadingState,
    errorState,
    fetchAgents,
    updateFilters,
    selectAgent,
    retryFetch
  } = useAgentData(refreshInterval);

  const handleAgentSelect = (agent: AgentCardData) => {
    selectAgent(agent.id);
    if (onAgentSelect) {
      onAgentSelect(agent.name);
    }
  };

  const handleRefresh = () => {
    fetchAgents(true);
  };

  // Calculate status distribution
  const statusDistribution = agents.reduce((acc, agent) => {
    acc[agent.status] = (acc[agent.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const statusGroups = [
    { status: 'active' as const, count: statusDistribution.active || 0, label: 'Active' },
    { status: 'idle' as const, count: statusDistribution.idle || 0, label: 'Idle' },
    { status: 'error' as const, count: statusDistribution.error || 0, label: 'Error' },
    { status: 'offline' as const, count: statusDistribution.offline || 0, label: 'Offline' }
  ];

  const displayedAgents = maxAgents ? filteredAgents.slice(0, maxAgents) : filteredAgents;

  if (loadingState.isLoading && !refreshing) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Agent Overview</h3>
          <p className="text-gray-600">{loadingState.loadingText}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Users className="h-6 w-6 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Agent Overview</h2>
            <p className="text-gray-600">
              {agents.length} total agents • {statusDistribution.active || 0} active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <AgentStatusGroup 
            statuses={statusGroups}
            size="sm"
            variant="badge"
          />
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
            <span>Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {errorState.hasError && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <div className="flex items-center justify-between">
              <span>{errorState.errorMessage}</span>
              {errorState.canRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={retryFetch}
                  className="ml-4"
                >
                  Retry
                </Button>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Filters and Controls */}
      {showFilters && (
        <Card>
          <CardContent className="py-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search agents..."
                  value={filters.searchQuery || ''}
                  onChange={(e) => updateFilters({ searchQuery: e.target.value })}
                  className="pl-10"
                />
              </div>

              {/* Status Filter */}
              <Select
                value={filters.status?.[0] || 'all'}
                onValueChange={(value) => 
                  updateFilters({ 
                    status: value === 'all' ? undefined : [value as ('active' | 'idle' | 'error' | 'offline')]
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="idle">Idle</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                  <SelectItem value="offline">Offline</SelectItem>
                </SelectContent>
              </Select>

              {/* Sort By */}
              <Select
                value={filters.sortBy || 'name'}
                onValueChange={(value) => updateFilters({ sortBy: value as 'name' | 'successRate' | 'lastActive' | 'totalTasks' })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="successRate">Success Rate</SelectItem>
                  <SelectItem value="totalTasks">Total Tasks</SelectItem>
                  <SelectItem value="lastActive">Last Active</SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode */}
              <div className="flex items-center space-x-2">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="flex-1"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="flex-1"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Grid/List */}
      {displayedAgents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Activity className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Agents Found</h3>
            <p className="text-gray-600 text-center">
              {filters.searchQuery || filters.status ? 
                'No agents match your current filters.' : 
                'No agents are currently registered.'
              }
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className={cn(
          viewMode === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
            : 'space-y-4'
        )}>
          {displayedAgents.map((agent) => (
            compactView ? (
              <AgentPerformanceCardCompact
                key={agent.id}
                agent={agent}
                onClick={handleAgentSelect}
                className={selectedAgentId === agent.id ? 'ring-2 ring-blue-500' : ''}
              />
            ) : (
              <AgentPerformanceCard
                key={agent.id}
                agent={agent}
                detailed={viewMode === 'list'}
                showChart={viewMode === 'list'}
                onClick={handleAgentSelect}
                className={selectedAgentId === agent.id ? 'ring-2 ring-blue-500' : ''}
              />
            )
          ))}
        </div>
      )}

      {/* Summary Footer */}
      {displayedAgents.length > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>
                Showing {displayedAgents.length} of {filteredAgents.length} agents
                {maxAgents && filteredAgents.length > maxAgents && ` (${maxAgents} max)`}
              </span>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span>
                    {Math.round((statusDistribution.active || 0) / agents.length * 100)}% uptime
                  </span>
                </div>
                
                {refreshing && (
                  <div className="flex items-center space-x-1">
                    <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
                    <span>Refreshing...</span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentListOverview;