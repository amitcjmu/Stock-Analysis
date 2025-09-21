/**
 * Completeness Dashboard Component
 *
 * Shows category badges for lifecycle, resilience, operations with last-checked timestamps
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { CheckCircle, AlertCircle, XCircle, Clock, Info, Activity, Shield, Settings, Calendar, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { CompletenessMetrics, CompletenessCategory } from '../types';

interface CompletenessDashboardProps {
  metrics: CompletenessMetrics;
  className?: string;
  onCategoryClick?: (categoryId: string) => void;
}

export const CompletenessDashboard: React.FC<CompletenessDashboardProps> = ({
  metrics,
  className,
  onCategoryClick
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'partial':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'missing':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'missing':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (categoryId: string) => {
    switch (categoryId) {
      case 'lifecycle':
        return <Calendar className="h-5 w-5" />;
      case 'resilience':
        return <Shield className="h-5 w-5" />;
      case 'operations':
        return <Settings className="h-5 w-5" />;
      case 'compliance':
        return <Activity className="h-5 w-5" />;
      case 'technical':
        return <Zap className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const formatLastChecked = (dateStr?: string) => {
    if (!dateStr) return 'Never';

    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMinutes = Math.floor(diffMs / (1000 * 60));

      if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else {
        return date.toLocaleDateString();
      }
    } catch {
      return 'Unknown';
    }
  };

  const getOverallStatus = () => {
    if (metrics.overall_completion >= 95) return 'complete';
    if (metrics.overall_completion >= 70) return 'partial';
    if (metrics.overall_completion > 0) return 'partial';
    return 'missing';
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall Completion Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Collection Completeness
            </div>
            <Badge className={getStatusColor(getOverallStatus())}>
              {Math.round(metrics.overall_completion)}% Complete
            </Badge>
          </CardTitle>
          <CardDescription>
            Data collection progress across all categories • Last updated {formatLastChecked(metrics.last_updated)}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>Overall Progress</span>
              <span>{metrics.completed_fields} / {metrics.total_fields} fields completed</span>
            </div>
            <Progress value={metrics.overall_completion} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Category Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.categories.map((category) => (
          <Card
            key={category.id}
            className={cn(
              'cursor-pointer transition-all duration-200 hover:shadow-md',
              onCategoryClick && 'hover:border-primary'
            )}
            onClick={() => onCategoryClick?.(category.id)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getCategoryIcon(category.id)}
                  <CardTitle className="text-base capitalize">
                    {category.name}
                  </CardTitle>
                </div>
                {getStatusIcon(category.status)}
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Progress */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Progress</span>
                  <span className="font-medium">
                    {Math.round(category.completion_percentage)}%
                  </span>
                </div>
                <Progress value={category.completion_percentage} className="h-1.5" />
              </div>

              {/* Field Counts */}
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  {category.completed_fields.length} / {category.required_fields.length} fields
                </span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatLastChecked(category.last_checked)}</span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="space-y-1">
                        <p className="font-medium">Last checked: {category.last_checked ? new Date(category.last_checked).toLocaleString() : 'Never'}</p>
                        <p className="text-xs">{category.description}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Status Badge */}
              <Badge
                variant="outline"
                className={cn('w-full justify-center', getStatusColor(category.status))}
              >
                {category.status.charAt(0).toUpperCase() + category.status.slice(1)}
              </Badge>

              {/* Missing Fields Preview */}
              {category.status !== 'complete' && (
                <div className="text-xs text-muted-foreground">
                  {category.required_fields.length - category.completed_fields.length} fields remaining
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Phase 1 Focus Areas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Phase 1 Focus Areas</CardTitle>
          <CardDescription>
            Priority collection categories for immediate migration planning
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Lifecycle */}
            {metrics.categories.find(c => c.id === 'lifecycle') && (
              <div className="p-3 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">Lifecycle Dates</span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  End-of-Life and End-of-Support dates for migration urgency
                </p>
                <Badge className={getStatusColor(metrics.categories.find(c => c.id === 'lifecycle')?.status || 'missing')}>
                  {Math.round(metrics.categories.find(c => c.id === 'lifecycle')?.completion_percentage || 0)}% Complete
                </Badge>
              </div>
            )}

            {/* Resilience */}
            {metrics.categories.find(c => c.id === 'resilience') && (
              <div className="p-3 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  <span className="font-medium">RTO/RPO</span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  Recovery objectives for availability planning
                </p>
                <Badge className={getStatusColor(metrics.categories.find(c => c.id === 'resilience')?.status || 'missing')}>
                  {Math.round(metrics.categories.find(c => c.id === 'resilience')?.completion_percentage || 0)}% Complete
                </Badge>
              </div>
            )}

            {/* Operations */}
            {metrics.categories.find(c => c.id === 'operations') && (
              <div className="p-3 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Settings className="h-4 w-4 text-orange-600" />
                  <span className="font-medium">Maintenance Windows</span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  Operational constraints for migration scheduling
                </p>
                <Badge className={getStatusColor(metrics.categories.find(c => c.id === 'operations')?.status || 'missing')}>
                  {Math.round(metrics.categories.find(c => c.id === 'operations')?.completion_percentage || 0)}% Complete
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};