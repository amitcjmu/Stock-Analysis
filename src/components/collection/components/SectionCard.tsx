/**
 * Section Card Component
 * 
 * Collapsible card for form sections with progress indicators
 * Agent Team B3 - Section organization component
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, CheckCircle, AlertCircle, Clock, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

import type { SectionCardProps } from '../types';

export const SectionCard: React.FC<SectionCardProps> = ({
  section,
  isExpanded,
  onToggle,
  completionPercentage,
  validationStatus,
  children,
  className
}) => {
  const getStatusIcon = () => {
    switch (validationStatus) {
      case 'valid':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'invalid':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-amber-600" />;
      case 'pending':
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = () => {
    const isComplete = completionPercentage >= 100;
    const hasIssues = validationStatus === 'invalid';
    const hasWarnings = validationStatus === 'warning';

    if (isComplete && validationStatus === 'valid') {
      return (
        <Badge variant="default" className="bg-green-100 text-green-800 border-green-300">
          Complete
        </Badge>
      );
    }

    if (hasIssues) {
      return (
        <Badge variant="destructive">
          Needs Attention
        </Badge>
      );
    }

    if (hasWarnings) {
      return (
        <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-300">
          Review Suggested
        </Badge>
      );
    }

    if (completionPercentage > 0) {
      return (
        <Badge variant="outline">
          In Progress
        </Badge>
      );
    }

    return (
      <Badge variant="outline" className="text-muted-foreground">
        Not Started
      </Badge>
    );
  };

  return (
    <Card className={cn(
      'transition-all duration-200',
      isExpanded && 'ring-2 ring-primary/20',
      className
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-auto p-0 hover:bg-transparent"
                onClick={onToggle}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
              
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                {getStatusIcon()}
                {section.title}
              </CardTitle>
              
              {section.requiredFieldsCount > 0 && (
                <Badge variant="outline" className="text-xs">
                  {section.requiredFieldsCount} required
                </Badge>
              )}
            </div>

            {section.description && (
              <CardDescription className="ml-6">
                {section.description}
              </CardDescription>
            )}
          </div>

          <div className="flex flex-col items-end gap-2 ml-4">
            {getStatusBadge()}
            
            {/* Progress indicator */}
            <div className="flex items-center gap-2 min-w-0">
              <Progress 
                value={completionPercentage} 
                className="w-20"
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {Math.round(completionPercentage)}%
              </span>
            </div>
          </div>
        </div>

        {/* Section metrics when expanded */}
        {isExpanded && (
          <div className="ml-6 pt-2 border-t">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Target className="h-3 w-3" />
                {section.fields.length} fields
              </div>
              
              {section.completionWeight > 0 && (
                <div className="flex items-center gap-1">
                  <span>Weight: {Math.round(section.completionWeight * 100)}%</span>
                </div>
              )}
              
              {validationStatus === 'valid' && completionPercentage >= 100 && (
                <Badge variant="outline" className="text-green-600 border-green-300">
                  ✓ Section Complete
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0">
          {children}
        </CardContent>
      )}
    </Card>
  );
};