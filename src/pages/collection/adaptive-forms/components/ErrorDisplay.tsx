/**
 * ErrorDisplay Component
 * Error boundary and display for form initialization errors
 * Extracted from AdaptiveForms.tsx
 */

import React from 'react';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import { CollectionWorkflowError } from '@/components/collection/CollectionWorkflowError';

interface ErrorDisplayProps {
  error: Error | null;
  flowId: string | null;
  isPollingActive: boolean;
  onRetry: () => void;
  onRefresh: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  flowId,
  isPollingActive,
  onRetry,
  onRefresh,
}) => {
  if (!error) return null;

  return (
    <CollectionPageLayout
      title="Adaptive Data Collection"
      description="Error initializing collection form"
    >
      <CollectionWorkflowError
        error={error}
        flowId={flowId}
        isPollingActive={isPollingActive}
        onRetry={onRetry}
        onRefresh={onRefresh}
      />
    </CollectionPageLayout>
  );
};
