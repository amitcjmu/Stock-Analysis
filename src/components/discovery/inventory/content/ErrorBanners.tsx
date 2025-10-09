import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface CleansingRequiredBannerProps {
  showCleansingRequiredBanner: boolean;
  setShowCleansingRequiredBanner: (value: boolean) => void;
  setExecutionError: (value: string | null) => void;
}

export const CleansingRequiredBanner: React.FC<CleansingRequiredBannerProps> = ({
  showCleansingRequiredBanner,
  setShowCleansingRequiredBanner,
  setExecutionError
}) => {
  if (!showCleansingRequiredBanner) return null;

  return (
    <Card className="mb-6 border-amber-200 bg-amber-50">
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-5 h-5 text-amber-500">
              ⚠️
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-medium text-amber-800">Data Cleansing Required</h3>
            <p className="mt-1 text-sm text-amber-700">
              Asset inventory cannot be generated until data cleansing is completed.
              Please complete the data cleansing phase before proceeding.
            </p>
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowCleansingRequiredBanner(false);
                  setExecutionError(null);
                }}
                className="border-amber-300 text-amber-800 hover:bg-amber-100"
              >
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface ExecutionErrorBannerProps {
  executionError: string | null;
  showCleansingRequiredBanner: boolean;
  setExecutionError: (value: string | null) => void;
  attemptCountRef: React.MutableRefObject<number>;
}

export const ExecutionErrorBanner: React.FC<ExecutionErrorBannerProps> = ({
  executionError,
  showCleansingRequiredBanner,
  setExecutionError,
  attemptCountRef
}) => {
  if (!executionError || showCleansingRequiredBanner) return null;

  return (
    <Card className="mb-6 border-red-200 bg-red-50">
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-5 h-5 text-red-500">
              ❌
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">Execution Error</h3>
            <p className="mt-1 text-sm text-red-700">{executionError}</p>
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setExecutionError(null);
                  attemptCountRef.current = 0;
                }}
                className="border-red-300 text-red-800 hover:bg-red-100"
              >
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
