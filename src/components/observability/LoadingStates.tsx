/**
 * Loading States Components
 * Comprehensive loading states for observability components
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { Activity, BarChart3 } from 'lucide-react'
import { RefreshCw, Users } from 'lucide-react'

// Skeleton Loader Components
export const AgentCardSkeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Skeleton className="w-3 h-3 rounded-full" />
              <Skeleton className="h-6 w-32" />
            </div>
            <Skeleton className="w-4 h-4" />
          </div>
        </div>
        <Skeleton className="h-4 w-24" />
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Skeleton className="w-4 h-4" />
                <Skeleton className="h-4 w-20" />
              </div>
              <div className="flex items-center space-x-2">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="w-3 h-3" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Skeleton className="w-4 h-4" />
                <Skeleton className="h-4 w-16" />
              </div>
              <div className="flex items-center space-x-2">
                <Skeleton className="h-8 w-12" />
                <Skeleton className="h-5 w-12" />
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <Skeleton className="h-10 w-full rounded-md" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const AgentListSkeleton: React.FC<{ count?: number; className?: string }> = ({
  count = 6,
  className
}) => {
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6', className)}>
      {Array.from({ length: count }, (_, i) => (
        <AgentCardSkeleton key={i} />
      ))}
    </div>
  );
};

export const MetricsChartSkeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <Card className={cn('w-full', className)}>
      <CardContent className="p-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <div className="flex items-center space-x-1">
              <Skeleton className="w-3 h-3" />
              <Skeleton className="h-3 w-8" />
            </div>
          </div>
          <div className="relative h-16">
            <div className="flex items-end justify-between h-full space-x-1">
              {Array.from({ length: 12 }, (_, i) => (
                <Skeleton
                  key={i}
                  className="flex-1"
                  style={{ height: `${Math.random() * 80 + 20}%` }}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-between">
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 w-8" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Animated Loading Components
export const PulsingLoader: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ size = 'md', className }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className={cn('animate-spin', sizeClasses[size], className)}>
      <RefreshCw className="w-full h-full text-blue-600" />
    </div>
  );
};

export const LoadingSpinner: React.FC<{
  text?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ text = 'Loading...', size = 'md', className }) => {
  return (
    <div className={cn('flex flex-col items-center justify-center space-y-4', className)}>
      <PulsingLoader size={size} />
      {text && (
        <p className={cn(
          'text-gray-600',
          size === 'sm' && 'text-sm',
          size === 'lg' && 'text-lg'
        )}>
          {text}
        </p>
      )}
    </div>
  );
};

// Full Page Loading States
export const AgentOverviewLoading: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Skeleton className="w-6 h-6" />
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-6 w-16" />
            ))}
          </div>
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-20" />
        </div>
      </div>

      {/* Filters Skeleton */}
      <Card>
        <CardContent className="py-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <div className="flex items-center space-x-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent Cards Skeleton */}
      <AgentListSkeleton count={8} />

      {/* Summary Footer Skeleton */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-48" />
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <Skeleton className="w-4 h-4" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Progressive Loading Component
export const ProgressiveLoader: React.FC<{
  stages: string[];
  currentStage: number;
  className?: string;
}> = ({ stages, currentStage, className }) => {
  return (
    <Card className={cn('w-full', className)}>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <PulsingLoader size="lg" className="mb-6" />

        <div className="text-center space-y-4 w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-900">
            Loading Agent Data
          </h3>

          <div className="space-y-2">
            {stages.map((stage, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={cn(
                  'w-4 h-4 rounded-full border-2',
                  index < currentStage
                    ? 'bg-green-500 border-green-500'
                    : index === currentStage
                    ? 'bg-blue-500 border-blue-500 animate-pulse'
                    : 'border-gray-300'
                )}>
                  {index < currentStage && (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full" />
                    </div>
                  )}
                </div>
                <span className={cn(
                  'text-sm',
                  index <= currentStage ? 'text-gray-900' : 'text-gray-500'
                )}>
                  {stage}
                </span>
              </div>
            ))}
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((currentStage + 1) / stages.length) * 100}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Empty State Component
export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}> = ({
  icon = <Users className="h-12 w-12 text-gray-300" />,
  title,
  description,
  action,
  className
}) => {
  return (
    <Card className={cn('w-full', className)}>
      <CardContent className="flex flex-col items-center justify-center py-16">
        {icon}
        <h3 className="text-lg font-medium text-gray-900 mt-6 mb-2">{title}</h3>
        <p className="text-gray-600 text-center max-w-md mb-6">{description}</p>
        {action}
      </CardContent>
    </Card>
  );
};

export default LoadingSpinner;
