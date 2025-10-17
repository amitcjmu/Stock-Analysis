// 6R Strategy Constants - Updated October 2025 for canonical strategy alignment
// Note: "replace" consolidates both COTS replacement (formerly "repurchase")
// and custom rewrites (formerly "rewrite")
export const strategyColors = {
  // Lift and Shift
  rehost: 'bg-green-100 text-green-800',

  // Modernization Treatments
  replatform: 'bg-blue-100 text-blue-800',
  refactor: 'bg-purple-100 text-purple-800',
  rearchitect: 'bg-indigo-100 text-indigo-800',

  // Replacement and Decommissioning
  replace: 'bg-orange-100 text-orange-800', // Consolidates rewrite/repurchase
  retire: 'bg-gray-100 text-gray-800',

  // Backward compatibility - deprecated strategies map to canonical ones
  rewrite: 'bg-orange-100 text-orange-800', // → replace
  repurchase: 'bg-orange-100 text-orange-800', // → replace
  retain: 'bg-green-100 text-green-800' // → rehost (fallback)
};

export const statusColors = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
  archived: 'bg-gray-100 text-gray-800'
};

export const effortColors = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  very_high: 'bg-red-100 text-red-800'
};

// Strategy labels - Canonical 6R strategies
export const strategyLabels: Record<string, string> = {
  // 6R Canonical Strategies
  rehost: 'REHOST',
  replatform: 'REPLATFORM',
  refactor: 'REFACTOR',
  rearchitect: 'REARCHITECT',
  replace: 'REPLACE', // Consolidates rewrite/repurchase
  retire: 'RETIRE',

  // Backward compatibility - deprecated strategies
  rewrite: 'REPLACE (Rewrite)', // Deprecated - use replace
  repurchase: 'REPLACE (COTS)', // Deprecated - use replace
  retain: 'REHOST (Retain)' // Deprecated - use rehost
};

export const dateRangeOptions = [
  { value: 'all', label: 'All Time' },
  { value: 'week', label: 'Last 7 Days' },
  { value: 'month', label: 'Last 30 Days' },
  { value: 'quarter', label: 'Last 90 Days' }
];
