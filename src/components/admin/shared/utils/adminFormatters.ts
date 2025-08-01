/**
 * Shared Admin Formatting Utilities
 * Common formatting functions used across admin dashboard components
 */

/**
 * Format date string to localized format
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Format currency values
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

/**
 * Get color classes for access levels
 */
export const getAccessLevelColor = (level: string): string => {
  switch (level) {
    case 'admin':
      return 'bg-red-100 text-red-800 hover:bg-red-200';
    case 'read_write':
      return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
    case 'read_only':
      return 'bg-green-100 text-green-800 hover:bg-green-200';
    default:
      return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
  }
};

/**
 * Get color classes for item types
 */
export const getItemTypeColor = (itemType: string): string => {
  switch (itemType) {
    case 'client_account':
      return 'bg-red-100 text-red-800';
    case 'engagement':
      return 'bg-blue-100 text-blue-800';
    case 'data_import_session':
      return 'bg-green-100 text-green-800';
    case 'user_profile':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Format item type labels
 */
export const getItemTypeLabel = (itemType: string): string => {
  return itemType.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Format phase labels
 */
export const getPhaseLabel = (phase: string): string => {
  const labels: Record<string, string> = {
    planning: 'Planning',
    discovery: 'Discovery',
    assessment: 'Assessment',
    migration: 'Migration',
    optimization: 'Optimization',
    completed: 'Completed',
  };
  return labels[phase] || phase;
};

/**
 * Format cloud provider labels
 */
export const getProviderLabel = (provider: string): string => {
  const labels: Record<string, string> = {
    aws: 'AWS',
    azure: 'Azure',
    gcp: 'GCP',
    multi_cloud: 'Multi-Cloud',
    hybrid: 'Hybrid',
    private_cloud: 'Private Cloud',
  };
  return labels[provider] || provider.toUpperCase();
};

/**
 * Calculate percentage with safe division
 */
export const safePercentage = (value: number, total: number, decimals = 1): number => {
  if (total === 0) return 0;
  return Math.round((value / total) * 100 * Math.pow(10, decimals)) / Math.pow(10, decimals);
};

/**
 * Format time duration from date
 */
export const getTimeSince = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffDays > 0) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } else if (diffHours > 0) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else {
    return 'Less than 1 hour ago';
  }
};
