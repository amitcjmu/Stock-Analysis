/**
 * AdminHeader Component
 * Reusable header for admin dashboard pages
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { LucideIcon } from 'lucide-react'
import { RotateCcw } from 'lucide-react'

export interface HeaderAction {
  label: string;
  onClick?: () => void;
  href?: string;
  icon?: LucideIcon;
  variant?: 'default' | 'outline' | 'secondary' | 'destructive';
  badge?: {
    text: string | number;
    variant?: 'default' | 'secondary' | 'destructive' | 'outline';
  };
  disabled?: boolean;
}

export interface AdminHeaderProps {
  title: string;
  description?: string;
  actions?: HeaderAction[];
  onRefresh?: () => void;
  refreshLoading?: boolean;
  className?: string;
}

export const AdminHeader: React.FC<AdminHeaderProps> = ({
  title,
  description,
  actions = [],
  onRefresh,
  refreshLoading = false,
  className = ''
}) => {
  return (
    <div className={`flex justify-between items-start ${className}`}>
      <div>
        <h1 className="text-3xl font-bold">{title}</h1>
        {description && (
          <p className="text-muted-foreground mt-1">
            {description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2">
        {onRefresh && (
          <Button
            onClick={onRefresh}
            variant="outline"
            disabled={refreshLoading}
          >
            <RotateCcw className={`w-4 h-4 mr-2 ${refreshLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        )}

        {actions.map((action) => (
          <Button
            key={action.label}
            variant={action.variant || 'default'}
            onClick={action.onClick}
            disabled={action.disabled}
            {...(action.href && !action.disabled ? { asChild: true } : {})}
          >
            {action.href && !action.disabled ? (
              <a href={action.href} className="flex items-center">
                {action.icon && <action.icon className="w-4 h-4 mr-2" />}
                {action.label}
                {action.badge && (
                  <Badge
                    variant={action.badge.variant || 'secondary'}
                    className="ml-2"
                  >
                    {action.badge.text}
                  </Badge>
                )}
              </a>
            ) : (
              <>
                {action.icon && <action.icon className="w-4 h-4 mr-2" />}
                {action.label}
                {action.badge && (
                  <Badge
                    variant={action.badge.variant || 'secondary'}
                    className="ml-2"
                  >
                    {action.badge.text}
                  </Badge>
                )}
              </>
            )}
          </Button>
        ))}
      </div>
    </div>
  );
};
