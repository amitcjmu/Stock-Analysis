/**
 * Polling Controls Component
 * 
 * Provides emergency stop functionality and manual refresh controls
 * to replace automatic polling with pull-based requests.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  RefreshCw, 
  Square, 
  Activity,
  Clock,
  Zap
} from 'lucide-react';
import { apiCall } from '@/lib/api';

interface PollingControlsProps {
  onManualRefresh?: () => Promise<void>;
  refreshLabel?: string;
  showEmergencyStop?: boolean;
  className?: string;
}

export function PollingControls({
  onManualRefresh,
  refreshLabel = 'Refresh Data',
  showEmergencyStop = true,
  className = ''
}: PollingControlsProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const handleManualRefresh = async () => {
    if (!onManualRefresh) return;
    
    setIsRefreshing(true);
    try {
      await onManualRefresh();
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Manual refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleEmergencyStop = async () => {
    try {
      // Stop frontend polling
      if (typeof window !== 'undefined' && (window as any).stopAllPolling) {
        (window as any).stopAllPolling();
      }
      
      // Stop backend polling
      await apiCall('/api/v1/observability/polling/emergency-stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',
          'X-Engagement-Id': '22222222-2222-2222-2222-222222222222'
        }
      });
      
      console.log('🚨 EMERGENCY STOP: All polling operations halted');
      
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Activity className="h-5 w-5" />
            Data Refresh Controls
          </CardTitle>
          <CardDescription>
            Manual refresh controls for pull-based data updates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button 
                onClick={handleManualRefresh}
                disabled={isRefreshing}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Refreshing...' : refreshLabel}
              </Button>
              
              {lastRefresh && (
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  Last: {lastRefresh.toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>

          {showEmergencyStop && (
            <div className="flex gap-2 pt-2 border-t">
              <Button
                onClick={handleEmergencyStop}
                variant="destructive"
                size="sm"
              >
                <Square className="h-4 w-4 mr-2" />
                Emergency Stop All Polling
              </Button>
            </div>
          )}

          <div className="text-xs text-muted-foreground space-y-1">
            <p>• Use manual refresh to get the latest data</p>
            <p>• Emergency stop disables all automatic polling</p>
            <p>• Pull-based requests reduce server load and log spam</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Simplified refresh button for inline use
 */
export function RefreshButton({
  onRefresh,
  isLoading = false,
  label = 'Refresh',
  size = 'sm',
  variant = 'outline'
}: {
  onRefresh: () => Promise<void>;
  isLoading?: boolean;
  label?: string;
  size?: 'sm' | 'default' | 'lg';
  variant?: 'default' | 'outline' | 'secondary';
}) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Button
      onClick={handleRefresh}
      disabled={refreshing || isLoading}
      variant={variant}
      size={size}
    >
      <RefreshCw className={`h-4 w-4 mr-2 ${refreshing || isLoading ? 'animate-spin' : ''}`} />
      {refreshing ? 'Refreshing...' : label}
    </Button>
  );
}

/**
 * Emergency stop button for critical situations
 */
export function EmergencyStopButton({ className = '' }: { className?: string }) {
  const handleEmergencyStop = async () => {
    try {
      // Stop all frontend polling
      if (typeof window !== 'undefined' && (window as any).stopAllPolling) {
        (window as any).stopAllPolling();
      }
      
      // Stop backend polling
      await apiCall('/api/v1/observability/polling/emergency-stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',
          'X-Engagement-Id': '22222222-2222-2222-2222-222222222222'
        }
      });
      
      console.log('🚨 Emergency stop executed successfully');
      
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  };

  return (
    <Button
      onClick={handleEmergencyStop}
      variant="destructive"
      size="sm"
      className={className}
    >
      <Zap className="h-4 w-4 mr-2" />
      Stop All Polling
    </Button>
  );
}
