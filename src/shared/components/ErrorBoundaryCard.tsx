/**
 * Reusable ErrorBoundaryCard Component
 * Common pattern for error states in cards across components
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Button } from '../../components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryCardProps {
  title: string;
  error: string | Error;
  onRetry?: () => void;
  className?: string;
}

export const ErrorBoundaryCard: React.FC<ErrorBoundaryCardProps> = ({
  title,
  error,
  onRetry,
  className = ''
}) => {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {errorMessage}
          </AlertDescription>
        </Alert>
        {onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            size="sm"
            className="mt-4"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
