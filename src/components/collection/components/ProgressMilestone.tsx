/**
 * Progress Milestone Component
 * 
 * Individual milestone display with achievement status
 * Agent Team B3 - Progress milestone component
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Circle, Clock, Trophy } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ProgressMilestoneProps {
  milestone: {
    id: string;
    title: string;
    description: string;
    achieved: boolean;
    achievedAt?: string;
    targetDate?: string;
    weight: number;
    required: boolean;
  };
  className?: string;
}

export const ProgressMilestone: React.FC<ProgressMilestoneProps> = ({
  milestone,
  className
}) => {
  return (
    <div className={cn(
      'flex items-start gap-3 p-3 rounded-lg',
      milestone.achieved ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200',
      className
    )}>
      <div className="mt-0.5">
        {milestone.achieved ? (
          <CheckCircle className="h-5 w-5 text-green-600" />
        ) : (
          <Circle className="h-5 w-5 text-gray-400" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className={cn(
            'text-sm font-medium',
            milestone.achieved ? 'text-green-900' : 'text-gray-900'
          )}>
            {milestone.title}
          </h4>
          
          {milestone.required && (
            <Badge variant="outline" className="text-xs">
              Required
            </Badge>
          )}
          
          {milestone.weight > 0.1 && (
            <Badge variant="secondary" className="text-xs">
              <Trophy className="h-3 w-3 mr-1" />
              High Value
            </Badge>
          )}
        </div>
        
        <p className={cn(
          'text-xs',
          milestone.achieved ? 'text-green-700' : 'text-gray-600'
        )}>
          {milestone.description}
        </p>
        
        {milestone.achieved && milestone.achievedAt && (
          <div className="flex items-center gap-1 mt-1 text-xs text-green-600">
            <CheckCircle className="h-3 w-3" />
            Completed {new Date(milestone.achievedAt).toLocaleDateString()}
          </div>
        )}
        
        {!milestone.achieved && milestone.targetDate && (
          <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Target: {new Date(milestone.targetDate).toLocaleDateString()}
          </div>
        )}
      </div>
    </div>
  );
};