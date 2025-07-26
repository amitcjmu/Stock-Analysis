/**
 * Get the color class for a readiness score
 * @param value - The readiness score (0-100)
 * @returns Tailwind CSS color class
 */
export const getReadinessColor = (value: number): string => {
  if (value >= 80) return 'text-green-600';
  if (value >= 60) return 'text-yellow-600';
  if (value >= 40) return 'text-orange-600';
  return 'text-red-600';
};

/**
 * Get the badge variant based on readiness state
 * @param state - The readiness state
 * @returns Tailwind CSS variant class
 */
export const getReadinessBadgeVariant = (state: string): any => {
  switch (state?.toLowerCase()) {
    case 'ready':
      return 'bg-green-100 text-green-800';
    case 'in-progress':
      return 'bg-yellow-100 text-yellow-800';
    case 'needs-attention':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

type BadgeVariant = 'default' | 'destructive' | 'outline' | 'secondary';

/**
 * Get the color class for a risk level
 * @param riskLevel - The risk level (high/medium/low)
 * @returns Tailwind CSS color class
 */
export const getRiskColor = (riskLevel: string): string => {
  switch (riskLevel?.toLowerCase()) {
    case 'high':
      return 'text-red-600';
    case 'medium':
      return 'text-yellow-600';
    case 'low':
      return 'text-green-600';
    default:
      return 'text-gray-600';
  }
};

/**
 * Get the Badge variant for a risk level
 * @param riskLevel - The risk level (high/medium/low)
 * @returns A valid Badge variant
 */
export const getRiskBadgeVariant = (riskLevel: string): BadgeVariant => {
  switch (riskLevel?.toLowerCase()) {
    case 'high':
      return 'destructive';
    case 'medium':
      return 'outline';
    case 'low':
      return 'default';
    default:
      return 'secondary';
  }
};

// All utilities are exported above
