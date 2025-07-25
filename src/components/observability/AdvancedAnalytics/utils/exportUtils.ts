/**
 * Export Utilities for Advanced Analytics
 * Handles data export functionality
 */

import { format } from 'date-fns';
import type { AnalyticsData } from '../types';

export const handleExportData = (
  analyticsData: AnalyticsData | null,
  timeRange: number,
  agentNames: string[]
) => {
  if (!analyticsData) return;

  const exportData = {
    timestamp: new Date().toISOString(),
    timeRange: `${timeRange} days`,
    agents: agentNames,
    analytics: analyticsData
  };

  const dataStr = JSON.stringify(exportData, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `advanced-analytics-${format(new Date(), 'yyyy-MM-dd')}.json`;
  link.click();
  URL.revokeObjectURL(url);
};
