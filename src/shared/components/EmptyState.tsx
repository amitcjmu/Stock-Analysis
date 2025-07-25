/**
 * Reusable EmptyState Component
 * Common pattern for displaying empty states across components
 */

import React from 'react';
import { Button } from '../../components/ui/button';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div className={`text-center py-8 text-gray-500 ${className}`}>
      {Icon && <Icon className="h-12 w-12 mx-auto mb-4 text-gray-300" />}
      <p className="font-medium">{title}</p>
      {description && <p className="text-sm mt-1">{description}</p>}
      {action && (
        <Button
          variant="outline"
          size="sm"
          onClick={action.onClick}
          className="mt-2"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
};
