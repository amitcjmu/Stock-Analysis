import {
  CheckCircle2,
  Activity,
  AlertCircle,
  Clock
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { CrewStatus, BadgeVariant } from './types';

export const getStatusIcon = (status: string): unknown => {
  switch (status) {
    case 'completed':
      return CheckCircle2;
    case 'running':
      return Activity;
    case 'failed':
      return AlertCircle;
    default:
      return Clock;
  }
};

export const getStatusIconWithStyles = (status: string): JSX.Element => {
  const IconComponent = getStatusIcon(status);

  switch (status) {
    case 'completed':
      return <IconComponent className="h-4 w-4 text-green-500" />;
    case 'running':
      return <IconComponent className="h-4 w-4 text-blue-500 animate-pulse" />;
    case 'failed':
      return <IconComponent className="h-4 w-4 text-red-500" />;
    default:
      return <IconComponent className="h-4 w-4 text-gray-400" />;
  }
};

export const getStatusBadgeVariant = (status: CrewStatus): BadgeVariant => {
  const variants: Record<CrewStatus, BadgeVariant> = {
    pending: 'secondary',
    running: 'default',
    completed: 'success',
    failed: 'destructive'
  };

  return variants[status] || 'secondary';
};

export const getCrewStatusStyles = (status: CrewStatus): unknown => {
  switch (status) {
    case 'running':
      return 'border-blue-500 shadow-lg';
    case 'completed':
      return 'border-green-500';
    case 'failed':
      return 'border-red-500';
    default:
      return '';
  }
};

export const getIconContainerStyles = (status: CrewStatus): unknown => {
  switch (status) {
    case 'running':
      return 'bg-blue-100 text-blue-600';
    case 'completed':
      return 'bg-green-100 text-green-600';
    case 'failed':
      return 'bg-red-100 text-red-600';
    default:
      return 'bg-gray-100 text-gray-600';
  }
};

export const formatStatusText = (status: string): string => {
  return status.charAt(0).toUpperCase() + status.slice(1);
};
