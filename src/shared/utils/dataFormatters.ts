/**
 * Reusable Data Formatting Utilities
 * Common formatting functions used across components
 */

/**
 * Format numbers with locale-specific formatting
 */
export const formatNumber = (value: number, options?: Intl.NumberFormatOptions): string => {
  return new Intl.NumberFormat('en-US', options).format(value);
};

/**
 * Format percentages
 */
export const formatPercentage = (value: number, decimals = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format currency values
 */
export const formatCurrency = (value: number, currency = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(value);
};

/**
 * Format file sizes
 */
export const formatFileSize = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';

  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

/**
 * Format duration in seconds to human readable format
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
};

/**
 * Format dates consistently across components
 */
export const formatDate = (date: string | Date, format: 'short' | 'long' | 'relative' = 'short'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'long':
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    case 'relative':
      return formatRelativeTime(dateObj);
    default:
      return dateObj.toLocaleDateString('en-US');
  }
};

/**
 * Format relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return formatDate(date, 'short');
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

/**
 * Convert camelCase/snake_case to human readable format
 */
export const humanizeString = (str: string): string => {
  return str
    .replace(/([A-Z])/g, ' $1') // Add space before uppercase letters
    .replace(/_/g, ' ') // Replace underscores with spaces
    .replace(/^./, char => char.toUpperCase()) // Capitalize first letter
    .trim();
};

/**
 * Get status color based on common status patterns
 */
export const getStatusColor = (status: string): string => {
  const statusColors: Record<string, string> = {
    // Success states
    'completed': 'text-green-600 bg-green-100',
    'success': 'text-green-600 bg-green-100',
    'active': 'text-green-600 bg-green-100',
    'online': 'text-green-600 bg-green-100',

    // Warning states
    'pending': 'text-yellow-600 bg-yellow-100',
    'warning': 'text-yellow-600 bg-yellow-100',
    'in_progress': 'text-blue-600 bg-blue-100',

    // Error states
    'failed': 'text-red-600 bg-red-100',
    'error': 'text-red-600 bg-red-100',
    'offline': 'text-red-600 bg-red-100',

    // Neutral states
    'idle': 'text-gray-600 bg-gray-100',
    'paused': 'text-gray-600 bg-gray-100',
    'not_analyzed': 'text-gray-600 bg-gray-100'
  };

  return statusColors[status.toLowerCase()] || 'text-gray-600 bg-gray-100';
};
