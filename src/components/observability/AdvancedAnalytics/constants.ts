/**
 * Constants for Advanced Analytics Component
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import { MetricConfig } from './types';

export const METRIC_CONFIGS: MetricConfig[] = [
  {
    key: 'successRate',
    label: 'Success Rate',
    color: '#10b981',
    unit: '%',
    format: (value) => `${(value * 100).toFixed(1)}%`
  },
  {
    key: 'avgDuration',
    label: 'Avg Duration',
    color: '#3b82f6',
    unit: 's',
    format: (value) => `${value.toFixed(1)}s`
  },
  {
    key: 'throughput',
    label: 'Throughput',
    color: '#8b5cf6',
    unit: 'tasks/hr',
    format: (value) => `${value.toFixed(1)}`
  },
  {
    key: 'memoryUsage',
    label: 'Memory Usage',
    color: '#f59e0b',
    unit: 'MB',
    format: (value) => `${value.toFixed(0)} MB`
  },
  {
    key: 'confidence',
    label: 'Confidence',
    color: '#ef4444',
    unit: '%',
    format: (value) => `${(value * 100).toFixed(1)}%`
  }
];