/**
 * SummaryCard - Reusable summary metric card component
 *
 * Phase 4: Assessment Architecture Enhancement
 *
 * Displays a metric summary with icon, title, value, and optional description.
 * Used in ReadinessDashboardWidget for displaying readiness summary cards.
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface SummaryCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  description?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, icon, color, description }) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <div className={cn('h-4 w-4', color)}>{icon}</div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
    </CardContent>
  </Card>
);

export default SummaryCard;
