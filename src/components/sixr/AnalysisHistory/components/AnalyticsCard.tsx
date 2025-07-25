import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../ui/card';
import type { LucideIcon } from 'lucide-react';

interface AnalyticsCardProps {
  title: string;
  description?: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendColor?: string;
  children?: React.ReactNode;
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title,
  description,
  value,
  icon: Icon,
  trend,
  trendColor = 'text-green-600',
  children
}) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <CardDescription className="text-xs text-muted-foreground">
            {description}
          </CardDescription>
        )}
        {trend && (
          <p className={`text-xs ${trendColor} mt-1`}>
            {trend}
          </p>
        )}
        {children}
      </CardContent>
    </Card>
  );
};
