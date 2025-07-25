/**
 * Utility Functions
 *
 * Helper functions for styling and status management.
 */

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed': return 'text-green-600 bg-green-100';
    case 'in_progress': return 'text-blue-600 bg-blue-100';
    case 'planned': return 'text-gray-600 bg-gray-100';
    case 'blocked': return 'text-red-600 bg-red-100';
    case 'failed': return 'text-red-600 bg-red-200';
    default: return 'text-gray-600 bg-gray-100';
  }
};

export const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'critical': return 'text-red-600 bg-red-100';
    case 'high': return 'text-orange-600 bg-orange-100';
    case 'medium': return 'text-yellow-600 bg-yellow-100';
    case 'low': return 'text-green-600 bg-green-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};
