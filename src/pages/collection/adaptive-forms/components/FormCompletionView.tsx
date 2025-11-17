/**
 * FormCompletionView Component
 * Success screen shown when form submission is complete
 * Extracted from AdaptiveForms.tsx
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';

interface FormCompletionViewProps {
  onContinueToDiscovery: () => void;
  onViewCollectionOverview: () => void;
  onStartNewCollection: () => void;
}

export const FormCompletionView: React.FC<FormCompletionViewProps> = ({
  onContinueToDiscovery,
  onViewCollectionOverview,
  onStartNewCollection,
}) => {
  return (
    <CollectionPageLayout
      title="Collection Complete"
      description="Your application data has been successfully collected"
    >
      <div className="max-w-3xl mx-auto mt-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>

            <h3 className="text-2xl font-bold text-green-900 mb-2">
              Collection Complete!
            </h3>

            <p className="text-green-700 mb-6">
              Your application data has been successfully collected and processed by our AI agents.
              The information will be used to generate personalized migration recommendations.
            </p>

            <div className="bg-white rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-3">What happens next?</h4>
              <ul className="text-left text-gray-700 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>Our AI agents will analyze your application data</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>Discovery phase will identify migration patterns and dependencies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>Personalized migration recommendations will be generated</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>You'll receive a detailed migration strategy report</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <Button
                onClick={onContinueToDiscovery}
                size="lg"
                className="w-full"
              >
                Continue to Aggregation Phase
              </Button>

              <div className="flex gap-3">
                <Button
                  onClick={onViewCollectionOverview}
                  variant="outline"
                  className="flex-1"
                >
                  View Collection Overview
                </Button>

                <Button
                  onClick={onStartNewCollection}
                  variant="outline"
                  className="flex-1"
                >
                  Start New Collection
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CollectionPageLayout>
  );
};
