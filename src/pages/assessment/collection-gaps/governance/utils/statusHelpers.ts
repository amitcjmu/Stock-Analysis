/**
 * Status and Priority Badge Helpers
 * Utility functions for formatting status and priority badges
 */

export type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline';

/**
 * Get badge variant for status values
 */
export function getStatusBadgeVariant(status: string): BadgeVariant {
  switch (status) {
    case 'approved':
      return 'default';
    case 'pending':
    case 'under_review':
      return 'secondary';
    case 'rejected':
    case 'withdrawn':
      return 'destructive';
    case 'active':
      return 'default';
    case 'inactive':
      return 'secondary';
    default:
      return 'outline';
  }
}

/**
 * Get badge variant for priority values
 */
export function getPriorityBadgeVariant(priority: string): BadgeVariant {
  switch (priority) {
    case 'critical':
      return 'destructive';
    case 'high':
      return 'destructive';
    case 'medium':
      return 'secondary';
    case 'low':
      return 'outline';
    default:
      return 'outline';
  }
}
