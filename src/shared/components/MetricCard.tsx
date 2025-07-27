/**
 * Reusable MetricCard Component
 * Common pattern for displaying metrics across components
 */

import React from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  iconColor?: string;
  progress?: number;
  trend?: 'up' | 'down' | 'stable';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-gray-500',
  progress,
  trend,
  className = ''
}) => {
  const getTrendColor = (): unknown => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-2xl font-bold ${getTrendColor()}`}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          </div>
          {Icon && <Icon className={`w-8 h-8 ${iconColor}`} />}
        </div>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-2">{subtitle}</p>
        )}
        {progress !== undefined && (
          <Progress value={progress} className="mt-2" />
        )}
      </CardContent>
    </Card>
  );
};
