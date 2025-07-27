/**
 * Validation Display Component
 *
 * Shows form validation results, errors, warnings, and overall status
 * Agent Team B3 - Validation feedback component
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible'
import { Info } from 'lucide-react'
import { AlertCircle, CheckCircle, AlertTriangle, Target, TrendingUp, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils';

import type { ValidationDisplayProps, ValidationError } from './types';

export const ValidationDisplay: React.FC<ValidationDisplayProps> = ({
  validation,
  onErrorClick,
  showWarnings = true,
  className
}) => {
  const [showDetails, setShowDetails] = React.useState(false);

  // Aggregate validation statistics
  const stats = React.useMemo(() => {
    const fieldResults = Object.values(validation.field_results || {});
    const allErrors = [
      ...validation.cross_field_errors || [],
      ...validation.business_rule_violations || [],
      ...fieldResults.flatMap(fr => fr.errors || [])
    ];
    const allWarnings = fieldResults.flatMap(fr => fr.warnings || []);

    return {
      totalFields: fieldResults.length,
      validFields: fieldResults.filter(fr => fr.is_valid).length,
      errorCount: allErrors.filter(e => e.severity === 'error').length,
      warningCount: allWarnings.filter(w => w.severity === 'warning').length,
      infoCount: allErrors.filter(e => e.severity === 'info').length,
      allErrors,
      allWarnings
    };
  }, [validation]);

  const getOverallStatus = (): JSX.Element => {
    if (validation.is_valid && stats.errorCount === 0) {
      return {
        icon: <CheckCircle className="h-5 w-5 text-green-600" />,
        title: 'Form Valid',
        description: 'All validation checks passed',
        variant: 'default' as const,
        bgColor: 'bg-green-50 border-green-200'
      };
    }

    if (stats.errorCount > 0) {
      return {
        icon: <AlertCircle className="h-5 w-5 text-red-600" />,
        title: 'Validation Errors',
        description: `${stats.errorCount} error(s) need to be fixed`,
        variant: 'destructive' as const,
        bgColor: 'bg-red-50 border-red-200'
      };
    }

    if (stats.warningCount > 0) {
      return {
        icon: <AlertTriangle className="h-5 w-5 text-amber-600" />,
        title: 'Validation Warnings',
        description: `${stats.warningCount} warning(s) for review`,
        variant: 'default' as const,
        bgColor: 'bg-amber-50 border-amber-200'
      };
    }

    return {
      icon: <Info className="h-5 w-5 text-blue-600" />,
      title: 'Validation Pending',
      description: 'Complete the form to see validation results',
      variant: 'default' as const,
      bgColor: 'bg-blue-50 border-blue-200'
    };
  };

  const status = getOverallStatus();

  const renderValidationIssue = (issue: ValidationError, index: number): JSX.Element => {
    const getIssueIcon = (): JSX.Element => {
      switch (issue.severity) {
        case 'error':
          return <AlertCircle className="h-4 w-4 text-red-600" />;
        case 'warning':
          return <AlertTriangle className="h-4 w-4 text-amber-600" />;
        case 'info':
        default:
          return <Info className="h-4 w-4 text-blue-600" />;
      }
    };

    return (
      <div
        key={`${issue.field_id}-${index}`}
        className={cn(
          'p-3 rounded-lg border',
          issue.severity === 'error' && 'bg-red-50 border-red-200',
          issue.severity === 'warning' && 'bg-amber-50 border-amber-200',
          issue.severity === 'info' && 'bg-blue-50 border-blue-200'
        )}
      >
        <div className="flex items-start gap-2">
          {getIssueIcon()}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium">
                {issue.field_label || issue.field_id}
              </span>
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  issue.severity === 'error' && 'border-red-300 text-red-700',
                  issue.severity === 'warning' && 'border-amber-300 text-amber-700',
                  issue.severity === 'info' && 'border-blue-300 text-blue-700'
                )}
              >
                {issue.error_code}
              </Badge>
            </div>

            <p className="text-sm text-gray-700 mb-2">
              {issue.error_message}
            </p>

            {issue.suggested_value && (
              <Button
                type="button"
                variant="link"
                size="sm"
                className="h-auto p-0 text-xs"
                onClick={() => onErrorClick?.(issue.field_id)}
              >
                Go to field →
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className={cn(status.bgColor, className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {status.icon}
            <div>
              <CardTitle className="text-lg">
                {status.title}
              </CardTitle>
              <CardDescription>
                {status.description}
              </CardDescription>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2">
            <Badge variant="outline" className="text-xs">
              {Math.round(validation.overall_confidence_score * 100)}% confidence
            </Badge>

            <div className="flex items-center gap-2">
              <Progress
                value={validation.completion_percentage}
                className="w-20"
              />
              <span className="text-xs text-muted-foreground">
                {Math.round(validation.completion_percentage)}%
              </span>
            </div>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center gap-1 text-sm">
            <Target className="h-4 w-4 text-muted-foreground" />
            <span>{stats.validFields}/{stats.totalFields} fields valid</span>
          </div>

          {stats.errorCount > 0 && (
            <Badge variant="destructive" className="text-xs">
              {stats.errorCount} errors
            </Badge>
          )}

          {stats.warningCount > 0 && showWarnings && (
            <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800">
              {stats.warningCount} warnings
            </Badge>
          )}

          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            <span>+{Math.round(validation.estimated_6r_confidence_impact * 100)}% 6R confidence</span>
          </div>

          {(stats.errorCount > 0 || (stats.warningCount > 0 && showWarnings)) && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="ml-auto"
            >
              {showDetails ? 'Hide Details' : 'Show Details'}
              {showDetails ? (
                <ChevronDown className="ml-1 h-4 w-4" />
              ) : (
                <ChevronRight className="ml-1 h-4 w-4" />
              )}
            </Button>
          )}
        </div>
      </CardHeader>

      {/* Detailed Validation Issues */}
      {showDetails && (stats.errorCount > 0 || (stats.warningCount > 0 && showWarnings)) && (
        <CardContent className="pt-0">
          <Collapsible open={showDetails}>
            <CollapsibleContent>
              <div className="space-y-4">
                {/* Errors */}
                {stats.errorCount > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      Errors ({stats.errorCount})
                    </h4>
                    <div className="space-y-2">
                      {stats.allErrors
                        .filter(error => error.severity === 'error')
                        .map((error, index) => renderValidationIssue(error, index))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {stats.warningCount > 0 && showWarnings && (
                  <div>
                    <h4 className="text-sm font-medium text-amber-700 mb-2 flex items-center gap-1">
                      <AlertTriangle className="h-4 w-4" />
                      Warnings ({stats.warningCount})
                    </h4>
                    <div className="space-y-2">
                      {stats.allWarnings
                        .filter(warning => warning.severity === 'warning')
                        .map((warning, index) => renderValidationIssue(warning, index))}
                    </div>
                  </div>
                )}

                {/* Cross-field and Business Rule Violations */}
                {(validation.cross_field_errors?.length > 0 || validation.business_rule_violations?.length > 0) && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                      <Info className="h-4 w-4" />
                      Business Rules & Dependencies
                    </h4>
                    <div className="space-y-2">
                      {[
                        ...(validation.cross_field_errors || []),
                        ...(validation.business_rule_violations || [])
                      ].map((issue, index) => renderValidationIssue(issue, index))}
                    </div>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      )}
    </Card>
  );
};
