/**
 * Dependency Warning Banner Component
 *
 * Displays a warning when questions have been reopened due to dependency changes
 * (e.g., changing a critical field value requires re-answering dependent questions)
 *
 * Issue #796 - Frontend UI Integration for Dynamic Questions
 */

import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export interface DependencyWarningBannerProps {
  reopenedQuestionIds: string[];
  reason: string;
  reopenedQuestionTitles?: string[]; // Optional: display question titles
  onDismiss?: () => void;
}

export const DependencyWarningBanner: React.FC<DependencyWarningBannerProps> = ({
  reopenedQuestionIds,
  reason,
  reopenedQuestionTitles,
  onDismiss
}) => {
  if (reopenedQuestionIds.length === 0) return null;

  return (
    <Alert variant="default" className="border-amber-500 bg-amber-50" data-testid="dependency-warning">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-900 font-semibold flex items-center justify-between">
        <span>
          Questions Reopened
          <Badge variant="outline" className="ml-2 bg-white" data-testid="reopened-count">
            {reopenedQuestionIds.length} question{reopenedQuestionIds.length !== 1 ? 's' : ''}
          </Badge>
        </span>
        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="h-6 w-6 p-0 hover:bg-amber-100"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </AlertTitle>
      <AlertDescription className="text-amber-800 space-y-2">
        <p data-testid="dependency-reason">
          <strong>Reason:</strong> {reason}
        </p>
        {reopenedQuestionTitles && reopenedQuestionTitles.length > 0 && (
          <div data-testid="reopened-questions-list">
            <strong>Affected questions:</strong>
            <ul className="list-disc list-inside mt-1 space-y-1">
              {reopenedQuestionTitles.map((title, index) => (
                <li key={reopenedQuestionIds[index]} className="text-sm">
                  {title}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs italic mt-2">
          Please review and answer these questions again to ensure data accuracy.
        </p>
      </AlertDescription>
    </Alert>
  );
};
