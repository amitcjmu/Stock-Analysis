/**
 * StatCard Component
 * Reusable statistics card for admin dashboards
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { LucideIcon } from 'lucide-react';

export interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  iconColor?: string;
  change?: {
    value: number;
    label: string;
    type: 'increase' | 'decrease' | 'neutral';
  };
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  iconColor = 'text-muted-foreground',
  change,
  className = ''
}) => {
  const getChangeColor = (type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase': return 'text-green-600';
      case 'decrease': return 'text-red-600';
      case 'neutral': return 'text-muted-foreground';
    }
  };

  const getChangeIcon = (type: 'increase' | 'decrease' | 'neutral') => {
    switch (type) {
      case 'increase': return '↗';
      case 'decrease': return '↘';
      case 'neutral': return '→';
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className={`h-4 w-4 ${iconColor}`} />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
        {change && (
          <div className={`text-xs ${getChangeColor(change.type)} flex items-center gap-1 mt-1`}>
            <span>{getChangeIcon(change.type)}</span>
            <span>{change.value}% {change.label}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
