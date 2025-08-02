export const strategyColors = {
  // Migration Lift and Shift
  rehost: 'bg-blue-100 text-blue-800',
  
  // Legacy Modernization Treatments  
  replatform: 'bg-yellow-100 text-yellow-800',
  refactor: 'bg-yellow-100 text-yellow-800',
  rearchitect: 'bg-yellow-100 text-yellow-800',
  
  // Cloud Native
  replace: 'bg-purple-100 text-purple-800',
  rewrite: 'bg-purple-100 text-purple-800'
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

export const strategyLabels: Record<string, string> = {
  // Migration Lift and Shift
  rehost: 'REHOST',
  
  // Legacy Modernization Treatments
  replatform: 'REPLATFORM',
  refactor: 'REFACTOR',  
  rearchitect: 'RE-ARCHITECT',
  
  // Cloud Native
  replace: 'REPLACE',
  rewrite: 'RE-WRITE'
};

export const dateRangeOptions = [
  { value: 'all', label: 'All Time' },
  { value: 'week', label: 'Last 7 Days' },
  { value: 'month', label: 'Last 30 Days' },
  { value: 'quarter', label: 'Last 90 Days' }
];
