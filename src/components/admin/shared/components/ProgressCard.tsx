/**
 * ProgressCard Component  
 * Reusable progress display card for admin dashboards
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { safePercentage } from '../utils/adminFormatters';

export interface ProgressItemData {
  label: string;
  value: number;
  total?: number;
  color?: string;
}

export interface ProgressCardProps {
  title: string;
  description?: string;
  items: ProgressItemData[];
  totalItems?: number;
  showPercentage?: boolean;
  showCounts?: boolean;
  className?: string;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  title,
  description,
  items,
  totalItems,
  showPercentage = true,
  showCounts = true,
  className = ''
}) => {
  const maxTotal = totalItems || Math.max(...items.map(item => item.total || item.value));

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4">
        {items.length > 0 ? (
          items.map((item) => {
            const percentage = showPercentage ? safePercentage(item.value, item.total || maxTotal) : 0;
            return (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm font-medium">{item.label}</span>
                <div className="flex items-center gap-2">
                  {showPercentage && (
                    <Progress 
                      value={percentage} 
                      className="w-20 h-2"
                      style={{
                        // @ts-expect-error - Custom CSS properties for progress color
                        '--progress-background': item.color || 'hsl(var(--primary))'
                      }}
                    />
                  )}
                  {showCounts && (
                    <span className="text-sm text-muted-foreground w-8 text-right">
                      {item.value}
                    </span>
                  )}
                  {showPercentage && (
                    <span className="text-xs text-muted-foreground w-12 text-right">
                      {percentage}%
                    </span>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center text-muted-foreground py-4">
            No data available
          </div>
        )}
      </CardContent>
    </Card>
  );
};