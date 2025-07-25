/**
 * Shared constants for observability components
 */

export const REFRESH_INTERVALS = {
  FAST: 5000,    // 5 seconds
  NORMAL: 30000, // 30 seconds
  SLOW: 60000,   // 1 minute
  MANUAL: 0      // No auto-refresh
} as const;

export const PERIOD_OPTIONS = [
  { value: 1, label: 'Last day' },
  { value: 7, label: 'Last week' },
  { value: 30, label: 'Last month' },
  { value: 90, label: 'Last 3 months' }
] as const;

export const AGENT_STATUS_COLORS = {
  active: {
    bg: 'bg-green-100',
    text: 'text-green-700',
    icon: 'text-green-500'
  },
  idle: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-700',
    icon: 'text-yellow-500'
  },
  error: {
    bg: 'bg-red-100',
    text: 'text-red-700',
    icon: 'text-red-500'
  },
  offline: {
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    icon: 'text-gray-500'
  }
} as const;

export const PRIORITY_CONFIG = {
  high: {
    color: 'border-l-red-500 bg-red-50',
    label: 'High Priority',
    weight: 3
  },
  medium: {
    color: 'border-l-yellow-500 bg-yellow-50',
    label: 'Medium Priority',
    weight: 2
  },
  low: {
    color: 'border-l-blue-500 bg-blue-50',
    label: 'Low Priority',
    weight: 1
  }
} as const;

export const IMPACT_CONFIG = {
  high: {
    color: 'text-green-600 bg-green-100',
    label: 'High Impact'
  },
  medium: {
    color: 'text-yellow-600 bg-yellow-100',
    label: 'Medium Impact'
  },
  low: {
    color: 'text-blue-600 bg-blue-100',
    label: 'Low Impact'
  }
} as const;

export const EFFORT_CONFIG = {
  low: {
    color: 'text-green-600 bg-green-100',
    label: 'Low Effort'
  },
  medium: {
    color: 'text-yellow-600 bg-yellow-100',
    label: 'Medium Effort'
  },
  high: {
    color: 'text-red-600 bg-red-100',
    label: 'High Effort'
  }
} as const;

export const COMPARISON_METRICS = [
  {
    key: 'successRate' as const,
    label: 'Success Rate',
    unit: '%',
    higherIsBetter: true,
    format: (value: number) => `${(value * 100).toFixed(1)}%`
  },
  {
    key: 'avgDuration' as const,
    label: 'Avg Duration',
    unit: 's',
    higherIsBetter: false,
    format: (value: number) => `${value.toFixed(1)}s`
  },
  {
    key: 'avgConfidence' as const,
    label: 'Avg Confidence',
    unit: '%',
    higherIsBetter: true,
    format: (value: number) => `${(value * 100).toFixed(1)}%`
  },
  {
    key: 'totalTasks' as const,
    label: 'Total Tasks',
    unit: '',
    higherIsBetter: true,
    format: (value: number) => value.toString()
  },
  {
    key: 'throughput' as const,
    label: 'Throughput',
    unit: 'tasks/hr',
    higherIsBetter: true,
    format: (value: number) => `${value.toFixed(1)}/hr`
  },
  {
    key: 'memoryUsage' as const,
    label: 'Memory Usage',
    unit: 'MB',
    higherIsBetter: false,
    format: (value: number) => `${value.toFixed(1)} MB`
  },
  {
    key: 'errorRate' as const,
    label: 'Error Rate',
    unit: '%',
    higherIsBetter: false,
    format: (value: number) => `${(value * 100).toFixed(1)}%`
  }
] as const;

export const RECOMMENDATION_CATEGORIES = {
  performance: {
    icon: 'TrendingUp',
    color: 'text-blue-500',
    label: 'Performance'
  },
  reliability: {
    icon: 'CheckCircle',
    color: 'text-green-500',
    label: 'Reliability'
  },
  efficiency: {
    icon: 'Zap',
    color: 'text-purple-500',
    label: 'Efficiency'
  },
  resource: {
    icon: 'Target',
    color: 'text-orange-500',
    label: 'Resource'
  },
  configuration: {
    icon: 'Brain',
    color: 'text-indigo-500',
    label: 'Configuration'
  }
} as const;
