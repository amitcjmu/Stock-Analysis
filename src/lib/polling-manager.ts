/**
 * Global Polling Management System
 * 
 * This module provides centralized control over all polling operations
 * to prevent runaway polling and implement pull-based request patterns.
 */

import React from 'react';

interface PollingConfig {
  id: string;
  component: string;
  endpoint: string;
  interval: number;
  maxRetries: number;
  enabled: boolean;
  lastSuccess?: number;
  consecutiveErrors: number;
  backoffMultiplier: number;
}

interface PollingStats {
  totalPollers: number;
  activePollers: number;
  errorRate: number;
  avgInterval: number;
  topEndpoints: Array<{ endpoint: string; count: number }>;
}

class PollingManager {
  private pollers: Map<string, PollingConfig> = new Map();
  private intervals: Map<string, NodeJS.Timeout> = new Map();
  private globalEnabled = true;
  private maxConcurrentPollers = 5;
  private minInterval = 30000; // 30 seconds minimum
  private maxRetries = 3;

  /**
   * Register a polling operation
   */
  register(config: Omit<PollingConfig, 'consecutiveErrors' | 'lastSuccess'>): boolean {
    // Check if polling is globally disabled
    if (!this.globalEnabled) {
      console.warn(`🚫 Polling globally disabled, rejecting registration for ${config.id}`);
      return false;
    }

    // Check concurrent poller limit
    if (this.getActivePollerCount() >= this.maxConcurrentPollers) {
      console.warn(`🚫 Max concurrent pollers (${this.maxConcurrentPollers}) reached, rejecting ${config.id}`);
      return false;
    }

    // Enforce minimum interval
    const interval = Math.max(config.interval, this.minInterval);
    if (interval !== config.interval) {
      console.warn(`⚠️ Increased polling interval for ${config.id} from ${config.interval}ms to ${interval}ms`);
    }

    const pollerConfig: PollingConfig = {
      ...config,
      interval,
      consecutiveErrors: 0,
      backoffMultiplier: 1.5,
      maxRetries: Math.min(config.maxRetries, this.maxRetries)
    };

    this.pollers.set(config.id, pollerConfig);
    console.log(`✅ Registered poller: ${config.id} (${config.component}) - ${interval}ms interval`);
    
    return true;
  }

  /**
   * Force cleanup of all pollers (emergency stop)
   */
  emergencyStop(): void {
    console.warn('🚨 EMERGENCY STOP: Stopping all polling operations');
    
    for (const pollerId of this.intervals.keys()) {
      this.stop(pollerId);
    }
    
    this.pollers.clear();
    this.intervals.clear();
    this.globalEnabled = false;
  }

  /**
   * Stop polling for a specific poller
   */
  stop(pollerId: string): void {
    const interval = this.intervals.get(pollerId);
    if (interval) {
      clearTimeout(interval);
      this.intervals.delete(pollerId);
      console.log(`⏹️ Stopped poller: ${pollerId}`);
    }
  }

  private getActivePollerCount(): number {
    return Array.from(this.pollers.values()).filter(p => p.enabled).length;
  }
}

// Global instance
export const pollingManager = new PollingManager();

// Console debugging functions (for development)
if (typeof window !== 'undefined') {
  (window as unknown).pollingManager = pollingManager;
  (window as unknown).stopAllPolling = () => pollingManager.emergencyStop();
}

export default pollingManager;
