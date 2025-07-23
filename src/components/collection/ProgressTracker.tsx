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

import { ProgressTrackerProps, ProgressMilestone } from './types';

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
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-amber-600';
    return 'text-red-600';
  };

  const completedMilestones = milestones.filter(m => m.achieved);
  const nextMilestone = milestones.find(m => !m.achieved);

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
            <span className={cn('font-semibold', getProgressColor(overallCompletion))}>
              {Math.round(overallCompletion)}%
            </span>
          </div>
          <Progress value={overallCompletion} className="h-2" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{completedSections}/{totalSections} sections</span>
            <span>
              {overallCompletion >= 100 ? 'Complete!' : `${Math.round(100 - overallCompletion)}% remaining`}
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
                confidenceScore >= 0.8 && 'border-green-500 text-green-700',
                confidenceScore >= 0.6 && confidenceScore < 0.8 && 'border-amber-500 text-amber-700',
                confidenceScore < 0.6 && 'border-red-500 text-red-700'
              )}
            >
              {Math.round(confidenceScore * 100)}%
            </Badge>
          </div>
          <Progress value={confidenceScore * 100} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {confidenceScore >= 0.8 
              ? 'Excellent data quality for 6R analysis'
              : confidenceScore >= 0.6
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
              {formatTime(timeSpent)}
            </div>
          </div>
          
          <div className="text-center p-2 bg-muted rounded-lg">
            <div className="flex items-center justify-center gap-1 text-sm font-medium">
              <Timer className="h-4 w-4" />
              Remaining
            </div>
            <div className="text-lg font-semibold text-muted-foreground">
              {formatTime(estimatedTimeRemaining)}
            </div>
          </div>
        </div>

        {/* Next Milestone */}
        {nextMilestone && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <div className="mt-0.5">
                {nextMilestone.required ? (
                  <AlertCircle className="h-4 w-4 text-blue-600" />
                ) : (
                  <Trophy className="h-4 w-4 text-blue-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-blue-900">
                  Next: {nextMilestone.title}
                </p>
                <p className="text-xs text-blue-700">
                  {nextMilestone.description}
                </p>
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
            {milestones.map((milestone) => (
              <div
                key={milestone.id}
                className={cn(
                  'flex items-center gap-2 p-2 rounded text-sm',
                  milestone.achieved 
                    ? 'bg-green-50 text-green-800' 
                    : 'bg-gray-50 text-gray-600'
                )}
              >
                {milestone.achieved ? (
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                ) : (
                  <Circle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">
                    {milestone.title}
                  </p>
                  {milestone.achieved && milestone.achievedAt && (
                    <p className="text-xs opacity-75">
                      Completed {new Date(milestone.achievedAt).toLocaleDateString()}
                    </p>
                  )}
                </div>
                
                {milestone.required && (
                  <Badge variant="outline" className="text-xs">
                    Required
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-2 border-t space-y-2">
          <Button variant="outline" size="sm" className="w-full">
            <TrendingUp className="h-4 w-4 mr-2" />
            View Detailed Progress
          </Button>
          
          {overallCompletion < 100 && (
            <Button variant="ghost" size="sm" className="w-full text-muted-foreground">
              Save Progress & Continue Later
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};