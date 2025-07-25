/**
 * Reusable status display components
 * Common UI patterns for displaying status across observability components
 */

import React from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { AGENT_STATUS_COLORS } from '../utils/constants';

export type StatusType = 'active' | 'idle' | 'error' | 'offline';

export interface StatusBadgeProps {
  status: StatusType;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'badge' | 'dot' | 'icon';
  showText?: boolean;
}

const statusIcons = {
  active: <CheckCircle className="w-4 h-4" />,
  idle: <Clock className="w-4 h-4" />,
  error: <XCircle className="w-4 h-4" />,
  offline: <AlertTriangle className="w-4 h-4" />
};

const statusLabels = {
  active: 'Active',
  idle: 'Idle',
  error: 'Error',
  offline: 'Offline'
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  variant = 'badge',
  showText = true
}) => {
  const colors = AGENT_STATUS_COLORS[status];

  if (variant === 'dot') {
    const dotSize = size === 'sm' ? 'w-2 h-2' : size === 'md' ? 'w-3 h-3' : 'w-4 h-4';
    return (
      <div
        className={`${dotSize} rounded-full ${colors.bg.replace('100', '500')}`}
        title={statusLabels[status]}
      />
    );
  }

  if (variant === 'icon') {
    const iconSize = size === 'sm' ? 'w-3 h-3' : size === 'md' ? 'w-4 h-4' : 'w-5 h-5';
    return (
      <div className={`${colors.icon} ${iconSize}`}>
        {statusIcons[status]}
      </div>
    );
  }

  return (
    <Badge
      className={`${colors.bg} ${colors.text} ${
        size === 'sm' ? 'text-xs px-2 py-1' :
        size === 'md' ? 'text-sm px-3 py-1' : 'text-base px-4 py-2'
      }`}
    >
      <div className="flex items-center space-x-1">
        <div className={`${colors.icon} ${
          size === 'sm' ? 'w-3 h-3' : size === 'md' ? 'w-4 h-4' : 'w-5 h-5'
        }`}>
          {statusIcons[status]}
        </div>
        {showText && <span>{statusLabels[status]}</span>}
      </div>
    </Badge>
  );
};

export interface StatusGroupProps {
  statuses: Array<{
    status: StatusType;
    count: number;
    label: string;
  }>;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'badge' | 'horizontal' | 'vertical';
  className?: string;
}

export const StatusGroup: React.FC<StatusGroupProps> = ({
  statuses,
  size = 'md',
  variant = 'badge',
  className = ''
}) => {
  if (variant === 'horizontal') {
    return (
      <div className={`flex items-center space-x-4 ${className}`}>
        {statuses.map(({ status, count, label }) => (
          <div key={status} className="flex items-center space-x-2">
            <StatusBadge status={status} size={size} variant="dot" showText={false} />
            <span className="text-sm text-gray-600">
              {label}: {count}
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'vertical') {
    return (
      <div className={`space-y-2 ${className}`}>
        {statuses.map(({ status, count, label }) => (
          <div key={status} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <StatusBadge status={status} size={size} variant="dot" showText={false} />
              <span className="text-sm font-medium">{label}</span>
            </div>
            <span className="text-sm text-gray-600">{count}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {statuses.map(({ status, count, label }) => (
        <Badge key={status} variant="secondary" className="flex items-center space-x-1">
          <StatusBadge status={status} size="sm" variant="dot" showText={false} />
          <span>{label}: {count}</span>
        </Badge>
      ))}
    </div>
  );
};
