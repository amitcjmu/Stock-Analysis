/**
 * Empty State Component
 *
 * Displays empty state when no questions are available.
 */

import React from 'react';
import { Brain } from 'lucide-react';

const EmptyState: React.FC = () => {
  return (
    <div className="p-6 text-center text-gray-500">
      <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
      <p>No agent questions yet</p>
      <p className="text-sm mt-1">Agents will ask clarifications as they analyze your data</p>
    </div>
  );
};

export default EmptyState;
