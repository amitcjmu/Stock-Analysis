/**
 * Enhanced Polling Controls Component
 * 
 * Provides centralized control over all polling operations in the application
 * to replace automatic polling with pull-based requests and manage errors.
 */

import React, { useState } from 'react'
import { useEffect, useCallback } from 'react'

// CC: Global window extensions for polling control
declare global {
  interface Window {
    stopAllPolling?: () => void;
  }
}
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, StopCircle, CheckCircle, XCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { toast } from 'sonner';

interface PollingStatus {
  totalActivePollers: number;
  errorRate: number;
  consecutiveErrors: number;
  lastSuccessfulFetch: number;
  problematicEndpoints: string[];
}

interface PollingControlsProps {
  flowId?: string;
  onEmergencyStop?: () => void;
  onRefresh?: () => void;
  showDetailedStatus?: boolean;
}

export function PollingControls({
  flowId,
  onEmergencyStop,
  onRefresh,
  showDetailedStatus = false
}: PollingControlsProps) {
  const queryClient = useQueryClient();
  const [pollingStatus, setPollingStatus] = useState<PollingStatus>({
    totalActivePollers: 0,
    errorRate: 0,
    consecutiveErrors: 0,
    lastSuccessfulFetch: Date.now(),
    problematicEndpoints: []
  });
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);

  // Monitor polling status
  useEffect(() => {
    const checkPollingStatus = () => {
      // Get query cache and analyze error patterns
      const queryCache = queryClient.getQueryCache();
      const queries = queryCache.getAll();
      
      let totalQueries = 0;
      let errorQueries = 0;
      const consecutiveErrors = 0;
      const problematicEndpoints: string[] = [];
      
      queries.forEach(query => {
        if (query.state.status === 'error') {
          errorQueries++;
          if (query.queryKey[0] && typeof query.queryKey[0] === 'string') {
            problematicEndpoints.push(query.queryKey[0]);
          }
        }
        totalQueries++;
      });

      // Check for consecutive errors across all queries
      const recentErrors = queries.filter(q => 
        q.state.error && 
        q.state.errorUpdateCount > 2
      ).length;

      setPollingStatus({
        totalActivePollers: totalQueries,
        errorRate: totalQueries > 0 ? (errorQueries / totalQueries) * 100 : 0,
        consecutiveErrors: recentErrors,
        lastSuccessfulFetch: Date.now(),
        problematicEndpoints: [...new Set(problematicEndpoints)]
      });

      // Auto-trigger emergency stop if error rate is too high
      if (errorQueries > 5 && (errorQueries / totalQueries) > 0.5) {
        console.warn('🚨 High error rate detected, triggering emergency stop');
        handleEmergencyStop();
      }
    };

    // Only check polling status once on mount and on manual refresh
    checkPollingStatus(); // Initial check

    // No auto-polling - user must manually refresh
    return () => {};
  }, [queryClient]);

  const handleEmergencyStop = async () => {
    try {
      setIsEmergencyActive(true);
      
      // Stop all frontend polling
      if (typeof window !== 'undefined' && window.stopAllPolling) {
        window.stopAllPolling();
      }

      // Clear all query cache to stop React Query polling
      queryClient.clear();

      // Stop backend polling
      await apiCall('/api/v1/observability/polling/emergency-stop', {
        method: 'POST',
        body: JSON.stringify({ 
          reason: 'User triggered emergency stop',
          flow_id: flowId 
        })
      });

      onEmergencyStop?.();
      console.log('🚨 EMERGENCY STOP: All polling operations halted');
      toast.success('Emergency stop activated - all polling stopped');
    } catch (error) {
      console.error('Failed to execute emergency stop:', error);
      toast.error('Failed to stop all polling operations');
    }
  };

  const handleRefreshAll = async () => {
    try {
      // Invalidate all queries to trigger fresh fetches
      await queryClient.invalidateQueries();
      
      // Reset error states
      setPollingStatus(prev => ({
        ...prev,
        consecutiveErrors: 0,
        errorRate: 0,
        problematicEndpoints: []
      }));
      
      onRefresh?.();
      toast.success('All data refreshed');
    } catch (error) {
      console.error('Failed to refresh data:', error);
      toast.error('Failed to refresh data');
    }
  };

  const handleResetErrorState = async () => {
    try {
      // Clear error states in React Query
      queryClient.resetQueries({ type: 'all' });
      
      // Reset local error tracking
      setPollingStatus(prev => ({
        ...prev,
        consecutiveErrors: 0,
        errorRate: 0,
        problematicEndpoints: []
      }));
      
      setIsEmergencyActive(false);
      
      toast.success('Error state reset - polling can resume');
    } catch (error) {
      console.error('Failed to reset error state:', error);
      toast.error('Failed to reset error state');
    }
  };

  const handleStopFlowPolling = async () => {
    if (!flowId) return;
    
    try {
      // Stop polling for specific flow
      await queryClient.cancelQueries({ 
        queryKey: ['discoveryFlowV2', flowId] 
      });
      await queryClient.cancelQueries({ 
        queryKey: ['real-time-processing', flowId] 
      });
      await queryClient.cancelQueries({ 
        queryKey: ['flow-escalation-status', flowId] 
      });
      
      // Stop all frontend polling for this flow
      if (typeof window !== 'undefined' && window.stopAllPolling) {
        window.stopAllPolling();
      }

      // Stop backend polling for this flow
      await apiCall('/api/v1/observability/polling/emergency-stop', {
        method: 'POST',
        body: JSON.stringify({ 
          reason: 'Flow-specific polling stop',
          flow_id: flowId 
        })
      });

      toast.success(`Stopped all polling for flow ${flowId}`);
    } catch (error) {
      console.error('Failed to stop flow polling:', error);
      toast.error('Failed to stop flow polling');
    }
  };

  const getStatusColor = () => {
    if (isEmergencyActive) return 'destructive';
    if (pollingStatus.consecutiveErrors > 3) return 'destructive';
    if (pollingStatus.errorRate > 25) return 'secondary';
    return 'default';
  };

  const getStatusIcon = () => {
    if (isEmergencyActive) return <StopCircle className="h-4 w-4" />;
    if (pollingStatus.consecutiveErrors > 3) return <XCircle className="h-4 w-4" />;
    if (pollingStatus.errorRate > 25) return <AlertTriangle className="h-4 w-4" />;
    return <CheckCircle className="h-4 w-4" />;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getStatusIcon()}
          Polling Control Center
          <Badge variant={getStatusColor()}>
            {isEmergencyActive ? 'STOPPED' : 
             pollingStatus.consecutiveErrors > 3 ? 'ERROR' :
             pollingStatus.errorRate > 25 ? 'WARNING' : 'ACTIVE'}
          </Badge>
        </CardTitle>
        <CardDescription>
          Manage all polling operations and handle errors
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{pollingStatus.totalActivePollers}</div>
            <div className="text-sm text-muted-foreground">Active Queries</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{pollingStatus.errorRate.toFixed(1)}%</div>
            <div className="text-sm text-muted-foreground">Error Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{pollingStatus.consecutiveErrors}</div>
            <div className="text-sm text-muted-foreground">Consecutive Errors</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {Math.round((Date.now() - pollingStatus.lastSuccessfulFetch) / 1000)}s
            </div>
            <div className="text-sm text-muted-foreground">Last Success</div>
          </div>
        </div>

        {/* Error Alerts */}
        {pollingStatus.consecutiveErrors > 3 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              High error rate detected! {pollingStatus.consecutiveErrors} consecutive errors.
              Consider using Emergency Stop to halt all polling.
            </AlertDescription>
          </Alert>
        )}

        {pollingStatus.problematicEndpoints.length > 0 && showDetailedStatus && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Problematic endpoints: {pollingStatus.problematicEndpoints.join(', ')}
            </AlertDescription>
          </Alert>
        )}

        {/* Control Buttons */}
        <div className="flex flex-wrap gap-2">
          <Button 
            onClick={handleEmergencyStop}
            variant="destructive"
            size="sm"
            disabled={isEmergencyActive}
          >
            <StopCircle className="h-4 w-4 mr-2" />
            Emergency Stop All Polling
          </Button>

          {flowId && (
            <Button 
              onClick={handleStopFlowPolling}
              variant="outline"
              size="sm"
            >
              <StopCircle className="h-4 w-4 mr-2" />
              Stop Flow Polling
            </Button>
          )}

          <Button 
            onClick={handleRefreshAll}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh All Data
          </Button>

          <Button 
            onClick={handleResetErrorState}
            variant="outline"
            size="sm"
            disabled={!isEmergencyActive && pollingStatus.consecutiveErrors === 0}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Reset Error State
          </Button>
        </div>

        {/* Instructions */}
        <div className="text-sm text-muted-foreground space-y-1">
          <p>• Emergency stop disables all automatic polling</p>
          <p>• Use refresh to manually fetch latest data</p>
          <p>• Reset error state to re-enable polling after issues</p>
          {flowId && <p>• Flow-specific stop only affects current flow</p>}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact Polling Status Indicator
 * For use in headers or toolbars
 */
export function PollingStatusIndicator({ flowId }: { flowId?: string }) {
  const queryClient = useQueryClient();
  const [errorCount, setErrorCount] = useState(0);
  const [lastChecked, setLastChecked] = useState(new Date());

  // Check errors on mount and provide manual refresh
  const checkErrors = useCallback(() => {
    const queries = queryClient.getQueryCache().getAll();
    const errors = queries.filter(q => q.state.status === 'error').length;
    setErrorCount(errors);
    setLastChecked(new Date());
  }, [queryClient]);

  // Check once on mount
  useEffect(() => {
    checkErrors();
  }, [checkErrors]);

  const handleQuickStop = async () => {
    try {
      // Stop all frontend polling
      if (typeof window !== 'undefined' && window.stopAllPolling) {
        window.stopAllPolling();
      }

      // Stop backend polling
      await apiCall('/api/v1/observability/polling/emergency-stop', {
        method: 'POST',
        body: JSON.stringify({ 
          reason: 'Quick stop from indicator',
          flow_id: flowId 
        })
      });

      toast.success('Polling stopped');
    } catch (error) {
      console.error('Failed to stop polling:', error);
      toast.error('Failed to stop polling');
    }
  };

  if (errorCount === 0) {
    return (
      <Badge 
        variant="default" 
        className="cursor-pointer hover:bg-gray-200" 
        onClick={checkErrors}
        title={`Last checked: ${lastChecked.toLocaleTimeString()}`}
      >
        <RefreshCw className="h-3 w-3 mr-1" />
        Status OK
      </Badge>
    );
  }

  return (
    <Badge 
      variant="destructive" 
      className="cursor-pointer"
      onClick={handleQuickStop}
      title={`${errorCount} errors detected - Click to stop all polling`}
    >
      <XCircle className="h-3 w-3 mr-1" />
      {errorCount} Errors
    </Badge>
  );
}
