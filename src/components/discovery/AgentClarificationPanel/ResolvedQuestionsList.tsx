/**
 * Resolved Questions List Component
 * 
 * Displays recently resolved questions with their responses.
 */

import React from 'react';
import { CheckCircle } from 'lucide-react';
import { AgentQuestion } from './types';
import { formatTimestamp } from './utils';

interface ResolvedQuestionsListProps {
  resolvedQuestions: AgentQuestion[];
}

const ResolvedQuestionsList: React.FC<ResolvedQuestionsListProps> = ({ 
  resolvedQuestions 
}) => {
  if (resolvedQuestions.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-gray-200">
      <div className="p-3 bg-gray-50">
        <h4 className="text-sm font-medium text-gray-700">Recently Resolved</h4>
      </div>
      {resolvedQuestions.slice(-3).map((question) => (
        <div key={question.id} className="p-4 border-b border-gray-100 bg-green-50">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="font-medium text-gray-700">{question.title}</span>
            <span className="text-xs text-gray-500">
              Resolved at {formatTimestamp(question.answered_at || '')}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-1">{question.question}</p>
          <p className="text-sm font-medium text-green-700">
            Response: {question.user_response}
          </p>
        </div>
      ))}
    </div>
  );
};

export default ResolvedQuestionsList;