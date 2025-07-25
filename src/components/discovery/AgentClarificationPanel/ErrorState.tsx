/**
 * Error State Component
 *
 * Displays error state when questions fail to load.
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorStateProps {
  error: string;
}

const ErrorState: React.FC<ErrorStateProps> = ({ error }) => {
  return (
    <div className="p-4 bg-red-50 border-l-4 border-red-500">
      <div className="flex items-center">
        <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
        <span className="text-red-700">{error}</span>
      </div>
    </div>
  );
};

export default ErrorState;
