/**
 * LoadingStateDisplay component
 * Handles all loading state variations (pending, failed, fallback, default)
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import React from "react";
import { Button } from "@/components/ui/button";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";

interface LoadingStateDisplayProps {
  completionStatus: string | null;
  statusLine: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Error type varies
  error: any;
  isLoading: boolean;
  isPolling: boolean;
  flowId: string | null;
  onRetry: () => void;
  onRefresh: () => void;
  onInitialize: () => void;
}

export const LoadingStateDisplay: React.FC<LoadingStateDisplayProps> = ({
  completionStatus,
  statusLine,
  error,
  isLoading,
  isPolling,
  flowId,
  onRetry,
  onRefresh,
  onInitialize,
}) => {
  // Check if there's an error
  if (error && !isLoading) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Error initializing collection form"
      >
        <div className="flex flex-col items-center space-y-6 mt-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-2.186-.833-2.956 0L3.857 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Workflow Error
            </h3>
            <p className="text-gray-600 mb-4">
              {error?.message || "An error occurred while initializing the collection workflow"}
            </p>
          </div>
          <div className="flex space-x-4">
            <Button onClick={onRetry} size="lg">
              Retry
            </Button>
            <Button variant="outline" onClick={onRefresh}>
              Refresh Page
            </Button>
          </div>
        </div>
      </CollectionPageLayout>
    );
  }

  // Handle questionnaire generation states based on completion_status
  if (completionStatus) {
    switch (completionStatus) {
      case 'pending':
        return (
          <CollectionPageLayout
            title="Adaptive Data Collection"
            description="Generating intelligent questionnaire..."
            isLoading={true}
            loadingMessage={statusLine || "Our AI agents are analyzing your environment to generate a tailored questionnaire..."}
            loadingSubMessage="This typically takes 30-60 seconds. Please wait while we create questions specific to your needs."
          >
            <div className="flex flex-col items-center space-y-4 mt-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <div className="text-center max-w-md">
                <p className="text-sm text-gray-600">
                  AI agents are reviewing your selected assets and generating contextual questions...
                </p>
                {isPolling && (
                  <p className="text-xs text-blue-600 mt-2">
                    Status updates every 5 seconds
                  </p>
                )}
              </div>
            </div>
          </CollectionPageLayout>
        );

      case 'failed':
        return (
          <CollectionPageLayout
            title="Adaptive Data Collection"
            description="Questionnaire generation failed"
          >
            <div className="flex flex-col items-center space-y-6 mt-8">
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                  <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-2.186-.833-2.956 0L3.857 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Questionnaire Generation Failed
                </h3>
                <p className="text-gray-600 mb-4">
                  {statusLine || "Unable to generate the adaptive questionnaire. This may be due to a temporary issue with our AI agents."}
                </p>
              </div>
              <div className="flex space-x-4">
                <Button onClick={onRetry} size="lg">
                  Retry Generation
                </Button>
                <Button variant="outline" onClick={onRefresh}>
                  Refresh Page
                </Button>
              </div>
            </div>
          </CollectionPageLayout>
        );

      case 'fallback':
      case 'ready':
        // Continue to regular loading state with optional fallback message
        break;
    }
  }

  // Default loading state
  return (
    <CollectionPageLayout
      title="Adaptive Data Collection"
      description="Loading collection form and saved data..."
      isLoading={isLoading}
      loadingMessage={
        isLoading
          ? "Loading form structure and saved responses..."
          : "Preparing collection form..."
      }
      loadingSubMessage={
        isLoading
          ? `Please wait while we load your saved data${isPolling ? " (Real-time updates active)" : ""}`
          : "Initializing workflow"
      }
    >
      {completionStatus === 'fallback' && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-amber-800">
                Using Standard Questionnaire
              </h3>
              <div className="mt-2 text-sm text-amber-700">
                <p>
                  {statusLine || "Our AI-generated questionnaire is not available. We're using a comprehensive standard questionnaire to ensure all important data is collected."}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
      {!isLoading && (
        <div className="flex flex-col items-center space-y-4 mt-8">
          <div className="text-center">
            <p className="text-gray-600 mb-4">
              The collection form is not loading automatically.
              Click the button below to start the flow manually.
            </p>
          </div>
          <Button onClick={onInitialize} size="lg">
            Start Collection Flow
          </Button>
          <p className="text-sm text-gray-500">
            Flow ID: {flowId || 'Not provided'}
          </p>
        </div>
      )}
    </CollectionPageLayout>
  );
};
