/**
 * Reusable metric display components
 * Common UI patterns for displaying metrics across observability components
 */

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { CardHeader, CardTitle } from '../../ui/card'
import { Card, CardContent } from '../../ui/card'
import { Badge } from '../../ui/badge';
import { formatPercentage, formatDuration, formatMemory, formatNumber } from '../utils/formatters';

export interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  format?: 'number' | 'percentage' | 'duration' | 'memory';
  color?: 'default' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
}

const formatValue = (value: number, format: MetricCardProps['format'], unit: string): string => {
  switch (format) {
    case 'percentage':
      return formatPercentage(value);
    case 'duration':
      return formatDuration(value);
    case 'memory':
      return formatMemory(value);
    case 'number':
      return formatNumber(value);
    default:
      return `${value.toFixed(1)} ${unit}`;
  }
};

const getColorClasses = (color: MetricCardProps['color']) => {
  switch (color) {
    case 'success':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'warning':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'error':
      return 'text-red-600 bg-red-50 border-red-200';
    default:
      return 'text-gray-900';
  }
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  format = 'number',
  color = 'default',
  size = 'md'
}) => {
  const colorClasses = getColorClasses(color);
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  };

  return (
    <Card className={color !== 'default' ? colorClasses : ''}>
      <CardContent className={sizeClasses[size]}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            <p className={`font-bold ${
              size === 'sm' ? 'text-lg' : 
              size === 'md' ? 'text-2xl' : 'text-3xl'
            }`}>
              {formatValue(value, format, unit)}
            </p>
          </div>
          
          {trend && trendValue !== undefined && (
            <div className="flex items-center space-x-1">
              {trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
              {trend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
              <span className={`text-sm font-medium ${
                trend === 'up' ? 'text-green-600' : 
                trend === 'down' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {Math.abs(trendValue).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export interface MetricBadgeProps {
  label: string;
  value: number;
  format?: 'number' | 'percentage' | 'duration' | 'memory';
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
}

export const MetricBadge: React.FC<MetricBadgeProps> = ({
  label,
  value,
  format = 'number',
  variant = 'secondary',
  size = 'md'
}) => {
  const formattedValue = formatValue(value, format, '');

  return (
    <Badge variant={variant as 'default' | 'secondary' | 'destructive' | 'outline'} className={`
      ${size === 'sm' ? 'text-xs px-2 py-1' : 
        size === 'md' ? 'text-sm px-3 py-1' : 'text-base px-4 py-2'}
    `}>
      {label}: {formattedValue}
    </Badge>
  );
};

export interface MetricComparisonProps {
  items: {
    name: string;
    value: number;
    color?: string;
  }[];
  format?: 'number' | 'percentage' | 'duration' | 'memory';
  showRanking?: boolean;
}

export const MetricComparison: React.FC<MetricComparisonProps> = ({
  items,
  format = 'number',
  showRanking = false
}) => {
  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <div key={item.name} className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {showRanking && (
              <span className="text-sm font-medium text-gray-500 w-6">
                #{index + 1}
              </span>
            )}
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: item.color || '#6B7280' }}
            />
            <span className="text-sm font-medium text-gray-900">{item.name}</span>
          </div>
          <span className="text-sm font-bold">
            {formatValue(item.value, format, '')}
          </span>
        </div>
      ))}
    </div>
  );
};