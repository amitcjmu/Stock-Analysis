import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface PollingErrorNotificationProps {
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const PollingErrorNotification: React.FC<PollingErrorNotificationProps> = ({
  onRetry,
  onDismiss
}) => {
  return (
    <Alert variant="destructive" className="fixed bottom-4 right-4 w-96 z-50">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Auto-refresh stopped</AlertTitle>
      <AlertDescription className="space-y-2">
        <p>
          Auto-refresh has been stopped due to repeated errors. 
          This prevents unnecessary server load.
        </p>
        <div className="flex gap-2">
          {onRetry && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              className="gap-2"
            >
              <RefreshCw className="h-3 w-3" />
              Retry
            </Button>
          )}
          {onDismiss && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onDismiss}
            >
              Dismiss
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};