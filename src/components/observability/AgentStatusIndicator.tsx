/**
 * Agent Status Indicator Component
 * Visual status indicator for agents with different variants and states
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { Badge } from '@/components/ui/badge';
import { Activity, AlertCircle, Clock, Wifi, WifiOff } from 'lucide-react';
import type { StatusIndicatorProps } from '../../types/api/observability/agent-performance';

const statusConfig = {
  active: {
    color: 'bg-green-500',
    badgeVariant: 'default' as const,
    badgeClass: 'bg-green-100 text-green-800 hover:bg-green-200',
    icon: Activity,
    label: 'Active',
    description: 'Agent is currently processing tasks'
  },
  idle: {
    color: 'bg-yellow-500',
    badgeVariant: 'secondary' as const,
    badgeClass: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    icon: Clock,
    label: 'Idle',
    description: 'Agent is online but not processing tasks'
  },
  inactive: {
    color: 'bg-slate-400',
    badgeVariant: 'secondary' as const,
    badgeClass: 'bg-slate-100 text-slate-600 hover:bg-slate-200',
    icon: Wifi,
    label: 'Inactive',
    description: 'Agent is registered but not currently active'
  },
  error: {
    color: 'bg-red-500',
    badgeVariant: 'destructive' as const,
    badgeClass: 'bg-red-100 text-red-800 hover:bg-red-200',
    icon: AlertCircle,
    label: 'Error',
    description: 'Agent encountered an error'
  },
  offline: {
    color: 'bg-gray-400',
    badgeVariant: 'outline' as const,
    badgeClass: 'bg-gray-100 text-gray-600 hover:bg-gray-200',
    icon: WifiOff,
    label: 'Offline',
    description: 'Agent is not responding'
  }
};

const sizeConfig = {
  sm: {
    dot: 'w-2 h-2',
    badge: 'text-xs px-2 py-1',
    icon: 'w-3 h-3'
  },
  md: {
    dot: 'w-3 h-3',
    badge: 'text-sm px-3 py-1',
    icon: 'w-4 h-4'
  },
  lg: {
    dot: 'w-4 h-4',
    badge: 'text-base px-4 py-2',
    icon: 'w-5 h-5'
  }
};

export const AgentStatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  variant = 'dot',
  showLabel = false,
  size = 'md',
  pulse = false,
  className,
  onClick
}) => {
  const config = statusConfig[status] || statusConfig['offline']; // Fallback to offline for unknown statuses
  const sizes = sizeConfig[size];
  const IconComponent = config.icon;

  const baseClasses = cn(
    'inline-flex items-center',
    onClick && 'cursor-pointer',
    className
  );

  const dotClasses = cn(
    sizes.dot,
    config.color,
    'rounded-full',
    pulse && 'animate-pulse',
    'transition-all duration-200'
  );

  const badgeClasses = cn(
    sizes.badge,
    config.badgeClass,
    'transition-all duration-200',
    'border-0'
  );

  if (variant === 'dot') {
    return (
      <div
        className={baseClasses}
        onClick={onClick}
        title={config.description}
      >
        <div className={dotClasses} />
        {showLabel && (
          <span className="ml-2 text-sm text-gray-700">
            {config.label}
          </span>
        )}
      </div>
    );
  }

  if (variant === 'badge') {
    return (
      <Badge
        variant={config.badgeVariant}
        className={cn(badgeClasses, baseClasses)}
        onClick={onClick}
        title={config.description}
      >
        <div className={cn(sizes.dot, config.color, 'rounded-full mr-2')} />
        {config.label}
      </Badge>
    );
  }

  if (variant === 'icon') {
    return (
      <div
        className={baseClasses}
        onClick={onClick}
        title={config.description}
      >
        <IconComponent
          className={cn(
            sizes.icon,
            status === 'active' && 'text-green-600',
            status === 'idle' && 'text-yellow-600',
            status === 'error' && 'text-red-600',
            status === 'offline' && 'text-gray-400',
            pulse && 'animate-pulse'
          )}
        />
        {showLabel && (
          <span className={cn(
            'ml-2 text-sm',
            status === 'active' && 'text-green-700',
            status === 'idle' && 'text-yellow-700',
            status === 'error' && 'text-red-700',
            status === 'offline' && 'text-gray-500'
          )}>
            {config.label}
          </span>
        )}
      </div>
    );
  }

  return null;
};

// Helper component for online/offline status
export const AgentOnlineIndicator: React.FC<{
  isOnline: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}> = ({ isOnline, size = 'md', showLabel = false, className }) => {
  return (
    <AgentStatusIndicator
      status={isOnline ? 'active' : 'offline'}
      variant="icon"
      size={size}
      showLabel={showLabel}
      className={className}
    />
  );
};

// Component for showing multiple status indicators
export const AgentStatusGroup: React.FC<{
  statuses: Array<{
    status: 'active' | 'idle' | 'error' | 'offline';
    count: number;
    label?: string;
  }>;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'dot' | 'badge' | 'icon';
  className?: string;
}> = ({ statuses, size = 'md', variant = 'badge', className }) => {
  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {statuses.map((item, index) => (
        item.count > 0 && (
          <div key={index} className="flex items-center space-x-1">
            <AgentStatusIndicator
              status={item.status}
              variant={variant}
              size={size}
              showLabel={false}
            />
            <span className={cn(
              'text-sm font-medium',
              size === 'sm' && 'text-xs',
              size === 'lg' && 'text-base'
            )}>
              {item.count}
            </span>
            {item.label && (
              <span className={cn(
                'text-xs text-gray-500',
                size === 'lg' && 'text-sm'
              )}>
                {item.label}
              </span>
            )}
          </div>
        )
      ))}
    </div>
  );
};

export default AgentStatusIndicator;
