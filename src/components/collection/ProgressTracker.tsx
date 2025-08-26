/**
 * Progress Tracker Component
 *
 * Displays form completion progress, milestones, and time tracking
 * Agent Team B3 - Task B3.5 Frontend Implementation
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Target,
  Clock,
  TrendingUp,
  CheckCircle,
  Circle,
  Timer,
  Trophy,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

import type { ProgressTrackerProps} from './types';
import { ProgressMilestone } from './types';

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  formId,
  totalSections,
  completedSections,
  overallCompletion,
  confidenceScore,
  milestones,
  timeSpent,
  estimatedTimeRemaining,
  className
}) => {
  // Type safety checks for props with user-friendly error UI
  if (!formId || typeof formId !== 'string') {
    console.warn('ProgressTracker: Invalid formId provided');
    return (
      <Card className={cn('w-full max-w-sm', className)}>
        <CardContent className="p-4">
          <div className="text-center text-muted-foreground">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p className="text-sm">Unable to load progress tracker</p>
            <p className="text-xs mt-1">Invalid form configuration</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Ensure numeric values are valid
  const safeTotalSections = typeof totalSections === 'number' && isFinite(totalSections) ? totalSections : 0;
  const safeCompletedSections = typeof completedSections === 'number' && isFinite(completedSections) ? completedSections : 0;
  const safeOverallCompletion = typeof overallCompletion === 'number' && isFinite(overallCompletion) ? overallCompletion : 0;
  const safeConfidenceScore = typeof confidenceScore === 'number' && isFinite(confidenceScore) ? confidenceScore : 0;
  const safeTimeSpent = typeof timeSpent === 'number' && isFinite(timeSpent) ? timeSpent : 0;
  const safeEstimatedTimeRemaining = typeof estimatedTimeRemaining === 'number' && isFinite(estimatedTimeRemaining) ? estimatedTimeRemaining : 0;
  const safeMilestones = Array.isArray(milestones) ? milestones : [];
  const formatTime = (milliseconds: number): string => {
    // Handle invalid inputs
    if (!milliseconds || milliseconds < 0 || !isFinite(milliseconds)) {
      return '0s';
    }

    const seconds = Math.floor(milliseconds / 1000);
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    // Handle extremely large values
    if (hours > 9999) {
      return 'N/A';
    }

    return `${hours}h ${minutes}m`;
  };

  const getProgressColor = (percentage: number): string => {
    // Handle invalid percentages
    if (!isFinite(percentage) || isNaN(percentage)) {
      return 'text-gray-500';
    }
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-amber-600';
    return 'text-red-600';
  };

  // Utility function to safely calculate percentages
  const safePercentage = (value: number): number => {
    if (!isFinite(value) || isNaN(value)) return 0;
    return Math.max(0, Math.min(100, Math.round(value)));
  };

  // Utility function to safely calculate confidence score percentage
  const safeConfidencePercentage = (score: number): number => {
    if (!isFinite(score) || isNaN(score)) return 0;
    return Math.max(0, Math.min(100, Math.round(score * 100)));
  };

  const completedMilestones = safeMilestones.filter(m => m?.achieved === true);
  const nextMilestone = safeMilestones.find(m => m?.achieved !== true);

  return (
    <Card className={cn('w-full max-w-sm', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Target className="h-5 w-5" />
          Progress Tracker
        </CardTitle>
        <CardDescription>
          Track your form completion progress
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className={cn('font-semibold', getProgressColor(safeOverallCompletion))}>
              {safePercentage(safeOverallCompletion)}%
            </span>
          </div>
          <Progress value={safePercentage(safeOverallCompletion)} className="h-2" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{safeCompletedSections}/{safeTotalSections} sections</span>
            <span>
              {safePercentage(safeOverallCompletion) >= 100 ? 'Complete!' : `${safePercentage(100 - safeOverallCompletion)}% remaining`}
            </span>
          </div>
        </div>

        {/* Confidence Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Data Confidence</span>
            <Badge
              variant="outline"
              className={cn(
                safeConfidenceScore >= 0.8 && 'border-green-500 text-green-700',
                safeConfidenceScore >= 0.6 && safeConfidenceScore < 0.8 && 'border-amber-500 text-amber-700',
                safeConfidenceScore < 0.6 && 'border-red-500 text-red-700'
              )}
            >
              {safeConfidencePercentage(safeConfidenceScore)}%
            </Badge>
          </div>
          <Progress value={safeConfidencePercentage(safeConfidenceScore)} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {!isFinite(safeConfidenceScore) || isNaN(safeConfidenceScore)
              ? 'Calculating data quality...'
              : safeConfidenceScore >= 0.8
              ? 'Excellent data quality for 6R analysis'
              : safeConfidenceScore >= 0.6
              ? 'Good quality, some improvements possible'
              : 'More data needed for reliable analysis'
            }
          </p>
        </div>

        {/* Time Tracking */}
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-2 bg-muted rounded-lg">
            <div className="flex items-center justify-center gap-1 text-sm font-medium">
              <Clock className="h-4 w-4" />
              Time Spent
            </div>
            <div className="text-lg font-semibold text-primary">
              {formatTime(safeTimeSpent)}
            </div>
          </div>

          <div className="text-center p-2 bg-muted rounded-lg">
            <div className="flex items-center justify-center gap-1 text-sm font-medium">
              <Timer className="h-4 w-4" />
              Remaining
            </div>
            <div className="text-lg font-semibold text-muted-foreground">
              {formatTime(safeEstimatedTimeRemaining)}
            </div>
          </div>
        </div>

        {/* Next Milestone */}
        {nextMilestone && nextMilestone.title && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <div className="mt-0.5">
                {nextMilestone.required === true ? (
                  <AlertCircle className="h-4 w-4 text-blue-600" />
                ) : (
                  <Trophy className="h-4 w-4 text-blue-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-blue-900">
                  Next: {nextMilestone.title}
                </p>
                {nextMilestone.description && (
                  <p className="text-xs text-blue-700">
                    {nextMilestone.description}
                  </p>
                )}
                {nextMilestone.targetDate && (
                  <p className="text-xs text-blue-600 mt-1">
                    Target: {new Date(nextMilestone.targetDate).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Milestones List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-1">
            <Trophy className="h-4 w-4" />
            Milestones ({completedMilestones.length}/{milestones.length})
          </h4>

          <div className="space-y-1 max-h-32 overflow-y-auto">
            {safeMilestones.map((milestone) => {
              if (!milestone?.id || !milestone?.title) {
                return null;
              }
              return (
                <div
                  key={milestone.id}
                  className={cn(
                    'flex items-center gap-2 p-2 rounded text-sm',
                    milestone.achieved === true
                      ? 'bg-green-50 text-green-800'
                      : 'bg-gray-50 text-gray-600'
                  )}
                >
                  {milestone.achieved === true ? (
                    <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  ) : (
                    <Circle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  )}

                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">
                      {milestone.title}
                    </p>
                    {milestone.achieved === true && milestone.achievedAt && (
                      <p className="text-xs opacity-75">
                        Completed {new Date(milestone.achievedAt).toLocaleDateString()}
                      </p>
                    )}
                  </div>

                  {milestone.required === true && (
                    <Badge variant="outline" className="text-xs">
                      Required
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-2 border-t space-y-2">
          <Button
            variant="outline"
            size="sm"
            className="w-full transition-colors hover:bg-primary/5"
            disabled={!formId}
            aria-label="View detailed progress analytics"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            View Detailed Progress
          </Button>

          {safePercentage(safeOverallCompletion) < 100 && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-muted-foreground transition-colors hover:bg-muted/50"
              disabled={!formId}
              aria-label="Save current progress and continue later"
            >
              Save Progress & Continue Later
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
