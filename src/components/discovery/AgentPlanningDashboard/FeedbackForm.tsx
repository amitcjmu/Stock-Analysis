/**
 * Feedback Form Component
 *
 * Form for submitting plan feedback and suggestions.
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Edit3, Send } from 'lucide-react';
import type { FeedbackType } from './types';

interface FeedbackFormProps {
  feedbackType: FeedbackType;
  setFeedbackType: (type: FeedbackType) => void;
  planSuggestion: string;
  setPlanSuggestion: (suggestion: string) => void;
  onSubmit: () => void;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({
  feedbackType,
  setFeedbackType,
  planSuggestion,
  setPlanSuggestion,
  onSubmit
}) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
        <Edit3 className="h-5 w-5" />
        Provide Plan Feedback
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Feedback Type
          </label>
          <select
            value={feedbackType}
            onChange={(e) => setFeedbackType(e.target.value as FeedbackType)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="suggestion">Suggestion for improvement</option>
            <option value="concern">Concern about current plan</option>
            <option value="approval">Approval with comments</option>
            <option value="correction">Correction needed</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Input
          </label>
          <textarea
            value={planSuggestion}
            onChange={(e) => setPlanSuggestion(e.target.value)}
            placeholder="Share your suggestions, concerns, or corrections for the agent plan..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <Button
          onClick={onSubmit}
          disabled={!planSuggestion.trim()}
          className="w-full"
        >
          <Send className="h-4 w-4 mr-2" />
          Submit Feedback to Agents
        </Button>
      </div>
    </div>
  );
};

export default FeedbackForm;
