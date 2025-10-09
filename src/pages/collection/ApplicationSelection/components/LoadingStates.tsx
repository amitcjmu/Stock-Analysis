/**
 * LoadingStates Component
 * Centralized loading and error state displays
 */

import React from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowLeft } from "lucide-react";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";

interface LoadingStateProps {
  isLoading?: boolean;
  loadingMessage?: string;
  loadingSubMessage?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  isLoading = true,
  loadingMessage = "Loading available assets...",
  loadingSubMessage = "Fetching inventory data",
}) => {
  return (
    <CollectionPageLayout
      title="Select Assets"
      description="Choose assets for data collection"
      isLoading={isLoading}
      loadingMessage={loadingMessage}
      loadingSubMessage={loadingSubMessage}
    >
      {/* Loading handled by layout */}
    </CollectionPageLayout>
  );
};

interface ErrorStateProps {
  onCancel: () => void;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  onCancel,
  onRetry,
}) => {
  return (
    <CollectionPageLayout
      title="Select Assets"
      description="Choose assets for data collection"
    >
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load assets. Please try again or contact support if the
          issue persists.
        </AlertDescription>
      </Alert>
      <div className="mt-4 flex gap-2">
        <Button onClick={onCancel} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Collection
        </Button>
        <Button onClick={onRetry}>Retry</Button>
      </div>
    </CollectionPageLayout>
  );
};
