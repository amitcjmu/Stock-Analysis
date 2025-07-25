/**
 * Custom Hook for Analytics Data Management
 * Handles data loading, caching, and refresh logic
 */

import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { subDays } from 'date-fns';
import type { AnalyticsData } from '../types';
import type { generateAnalyticsData } from '../utils';

interface UseAnalyticsDataProps {
  agentNames: string[];
  timeRange: number;
  refreshInterval: number;
}

export const useAnalyticsData = ({
  agentNames,
  timeRange,
  refreshInterval
}: UseAnalyticsDataProps) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataGenerationInProgress, setDataGenerationInProgress] = useState(false);
  const [dataCache, setDataCache] = useState<Map<string, AnalyticsData>>(new Map());
  const [dateRange, setDateRange] = useState<{ from: Date; to: Date }>({
    from: subDays(new Date(), timeRange),
    to: new Date()
  });

  const loadAnalyticsData = useCallback(async () => {
    // Prevent multiple simultaneous data generations
    if (dataGenerationInProgress) return;

    // Check cache first
    const cacheKey = `${agentNames.join(',')}-${timeRange}-${dateRange.from.getTime()}-${dateRange.to.getTime()}`;
    const cachedData = dataCache.get(cacheKey);

    if (cachedData) {
      setAnalyticsData(cachedData);
      return;
    }

    setDataGenerationInProgress(true);
    setLoading(true);
    setError(null);

    try {
      // Generate comprehensive analytics data
      const data = await generateAnalyticsData(agentNames, dateRange);
      setAnalyticsData(data);

      // Cache the result
      setDataCache(prev => new Map(prev.set(cacheKey, data)));
    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
      setDataGenerationInProgress(false);
    }
  }, [agentNames, timeRange, dateRange, dataGenerationInProgress, dataCache]);

  // Update date range when time range changes
  useEffect(() => {
    setDateRange({
      from: subDays(new Date(), timeRange),
      to: new Date()
    });
  }, [timeRange]);

  // Load data on mount and when dependencies change
  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  // Set up refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(loadAnalyticsData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, loadAnalyticsData]);

  return {
    analyticsData,
    loading,
    error,
    refresh: loadAnalyticsData,
    dateRange
  };
};
