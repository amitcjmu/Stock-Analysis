/**
 * Responsive Agent List Overview Component
 * Enhanced version with responsive design and comprehensive error handling
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react'
import { useState, useMemo } from 'react'
import { useEffect, useCallback } from 'react'
import { cn } from '../../lib/utils';
import { CardHeader, CardTitle } from '../ui/card'
import { Card, CardContent } from '../ui/card'
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Filter, Activity } from 'lucide-react'
import { RefreshCw, Search, Grid, List, Settings, AlertCircle, Users, TrendingUp, Wifi, WifiOff } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';

// Import our components
import { AgentPerformanceCard, AgentPerformanceCardCompact } from './AgentPerformanceCard';
import { AgentStatusGroup } from './AgentStatusIndicator';
import { LoadingError, NetworkError } from './ErrorBoundary'
import { ObservabilityErrorBoundary } from './ErrorBoundary'
import { AgentOverviewLoading, AgentListSkeleton, EmptyState } from './LoadingStates'
import { LoadingSpinner, ProgressiveLoader } from './LoadingStates'
import { useComponentVisibility, useGridLayout } from './hooks/useResponsiveLayout'
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

import type {
  AgentListOverviewProps,
  AgentCardData,
  AgentListState,
  AgentListFilters,
  LoadingState,
  ErrorState
} from '../../types/api/observability/agent-performance';

// Enhanced filtering function
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

// Enhanced hook with better error handling and retry logic
const useAgentData = (refreshInterval?: number): JSX.Element => {
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

  const [connectionState, setConnectionState] = useState({
    isOnline: navigator.onLine,
    lastSuccessfulFetch: null as Date | null
  });

  const [progressStage, setProgressStage] = useState(0);
  const loadingStages = useMemo(() => [
    'Connecting to monitoring service...',
    'Fetching agent registry...',
    'Loading performance data...',
    'Processing metrics...'
  ], []);

  const fetchAgents = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setState(prev => ({ ...prev, refreshing: true }));
      } else {
        setLoadingState({ isLoading: true, loadingText: 'Loading agents...' });
        setProgressStage(0);
      }

      setErrorState(prev => ({ ...prev, hasError: false, error: null }));

      // Simulate progressive loading stages
      if (!isRefresh) {
        for (let i = 0; i < loadingStages.length; i++) {
          setProgressStage(i);
          setLoadingState({
            isLoading: true,
            loadingText: loadingStages[i]
          });
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      }

      // Check connectivity
      if (!navigator.onLine) {
        throw new Error('No internet connection');
      }

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
      setConnectionState({
        isOnline: true,
        lastSuccessfulFetch: new Date()
      });

      // Reset error count on successful fetch
      setErrorState(prev => ({ ...prev, retryCount: 0 }));

    } catch (error) {
      console.error('Failed to fetch agents:', error);

      const errorMessage = error instanceof Error ? error.message : 'Failed to load agents';
      const isNetworkError = errorMessage.includes('fetch') ||
                           errorMessage.includes('network') ||
                           errorMessage.includes('connection') ||
                           !navigator.onLine;

      setErrorState(prev => ({
        hasError: true,
        error: error as Error,
        errorMessage,
        retryCount: prev.retryCount + 1,
        canRetry: prev.retryCount < 3
      }));

      setState(prev => ({
        ...prev,
        loading: false,
        refreshing: false,
        error: errorMessage
      }));

      setLoadingState({ isLoading: false });

      if (isNetworkError) {
        setConnectionState(prev => ({ ...prev, isOnline: false }));
      }
    }
  }, [loadingStages]);

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
    if (errorState.canRetry || !navigator.onLine) {
      fetchAgents();
    }
  }, [errorState.canRetry, fetchAgents]);

  // Connection status monitoring
  useEffect(() => {
    const handleOnline = (): void => {
      setConnectionState(prev => ({ ...prev, isOnline: true }));
      if (errorState.hasError) {
        retryFetch();
      }
    };

    const handleOffline = (): void => {
      setConnectionState(prev => ({ ...prev, isOnline: false }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [errorState.hasError, retryFetch]);

  // Auto-refresh functionality
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (refreshInterval && refreshInterval > 0 && connectionState.isOnline) {
      const interval = setInterval(() => {
        fetchAgents(true);
      }, refreshInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchAgents, connectionState.isOnline]);

  return {
    ...state,
    loadingState,
    errorState,
    connectionState,
    progressStage,
    loadingStages,
    fetchAgents,
    updateFilters,
    selectAgent,
    retryFetch
  };
};

export const ResponsiveAgentListOverview: React.FC<AgentListOverviewProps> = ({
  refreshInterval = 30,
  maxAgents,
  showFilters = true,
  compactView = false,
  onAgentSelect,
  className
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showSettings, setShowSettings] = useState(false);

  const { columns, gridClass, isMobile, isTablet } = useGridLayout(4);
  const {
    showFilters: showFiltersResponsive,
    compactMode,
    stackedLayout
  } = useComponentVisibility();

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
    connectionState,
    progressStage,
    loadingStages,
    fetchAgents,
    updateFilters,
    selectAgent,
    retryFetch
  } = useAgentData(refreshInterval);

  const handleAgentSelect = (agent: AgentCardData): void => {
    selectAgent(agent.id);
    if (onAgentSelect) {
      onAgentSelect(agent);
    }
  };

  const handleRefresh = (): void => {
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
  const effectiveShowFilters = showFilters && showFiltersResponsive;
  const effectiveCompactView = compactView || compactMode;

  // Loading states
  if (loadingState.isLoading && !refreshing) {
    if (isMobile) {
      return (
        <div className={cn('space-y-4', className)}>
          <LoadingSpinner text={loadingState.loadingText} />
        </div>
      );
    }

    return (
      <ProgressiveLoader
        stages={loadingStages}
        currentStage={progressStage}
        className={className}
      />
    );
  }

  // Error states
  if (errorState.hasError && !connectionState.isOnline) {
    return (
      <NetworkError onRetry={retryFetch} />
    );
  }

  if (errorState.hasError && !errorState.canRetry) {
    return (
      <LoadingError
        error={errorState.errorMessage || 'Unknown error occurred'}
        onRetry={retryFetch}
        canRetry={false}
      />
    );
  }

  return (
    <ObservabilityErrorBoundary showDetails={!isMobile}>
      <div className={cn('space-y-6', className)}>
        {/* Header */}
        <div className={cn(
          'flex items-center justify-between',
          stackedLayout && 'flex-col space-y-4 items-stretch'
        )}>
          <div className="flex items-center space-x-3">
            <Users className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className={cn(
                'font-bold text-gray-900',
                isMobile ? 'text-xl' : 'text-2xl'
              )}>
                Agent Overview
              </h2>
              <p className={cn(
                'text-gray-600',
                isMobile && 'text-sm'
              )}>
                {agents.length} total agents • {statusDistribution.active || 0} active
              </p>
            </div>
          </div>

          <div className={cn(
            'flex items-center space-x-3',
            stackedLayout && 'w-full justify-between'
          )}>
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {connectionState.isOnline ? (
                <Wifi className="h-4 w-4 text-green-500" title="Connected" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" title="Offline" />
              )}
            </div>

            {!isMobile && (
              <AgentStatusGroup
                statuses={statusGroups}
                size="sm"
                variant="badge"
              />
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing || !connectionState.isOnline}
              className="flex items-center space-x-2"
            >
              <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
              {!isMobile && <span>Refresh</span>}
            </Button>

            {!isMobile && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
                className="flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Button>
            )}
          </div>
        </div>

        {/* Mobile Status Groups */}
        {isMobile && (
          <AgentStatusGroup
            statuses={statusGroups}
            size="sm"
            variant="badge"
            className="justify-center"
          />
        )}

        {/* Error Display */}
        {errorState.hasError && (
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <div className={cn(
                'flex items-center justify-between',
                isMobile && 'flex-col space-y-2 items-start'
              )}>
                <span>{errorState.errorMessage}</span>
                {errorState.canRetry && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={retryFetch}
                    className={isMobile ? 'w-full' : 'ml-4'}
                  >
                    Retry
                  </Button>
                )}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Filters and Controls */}
        {effectiveShowFilters && (
          <Card>
            <CardContent className="py-4">
              <div className={cn(
                'grid gap-4',
                isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-4'
              )}>
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
                {!isMobile && (
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
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading State During Refresh */}
        {refreshing && (
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-center space-x-2">
                <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
                <span className="text-sm text-gray-600">Refreshing agent data...</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Agent Grid/List */}
        {displayedAgents.length === 0 ? (
          <EmptyState
            title="No Agents Found"
            description={
              filters.searchQuery || filters.status ?
                'No agents match your current filters.' :
                'No agents are currently registered.'
            }
            action={
              (filters.searchQuery || filters.status) && (
                <Button
                  variant="outline"
                  onClick={() => updateFilters({ searchQuery: '', status: undefined })}
                >
                  Clear Filters
                </Button>
              )
            }
          />
        ) : (
          <div className={cn(
            isMobile
              ? 'space-y-4'
              : viewMode === 'grid'
                ? gridClass + ' gap-6'
                : 'space-y-4'
          )}>
            {displayedAgents.map((agent) => (
              effectiveCompactView ? (
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
                  detailed={viewMode === 'list' && !isMobile}
                  showChart={viewMode === 'list' && !isMobile}
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
              <div className={cn(
                'flex items-center justify-between text-sm text-gray-600',
                isMobile && 'flex-col space-y-2 items-start'
              )}>
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

                  {connectionState.lastSuccessfulFetch && (
                    <div className="text-xs text-gray-500">
                      Last updated: {connectionState.lastSuccessfulFetch.toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ObservabilityErrorBoundary>
  );
};

export default ResponsiveAgentListOverview;
