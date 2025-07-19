/**
 * Loading State Component
 * 
 * Displays loading state while fetching questions.
 */

import React from 'react';
import { Bot, Loader2 } from 'lucide-react';

interface LoadingStateProps {
  className?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({ className = "" }) => {
  return (
    <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Bot className="w-5 h-5 text-blue-500" />
        <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
      </div>
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading agent questions...</span>
      </div>
    </div>
  );
};

export default LoadingState;