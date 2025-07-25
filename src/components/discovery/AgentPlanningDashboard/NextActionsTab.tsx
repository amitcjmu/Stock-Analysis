/**
 * Next Actions Tab Component
 *
 * Displays next actions for the user.
 */

import React from 'react';
import { Target, ArrowRight } from 'lucide-react';

interface NextActionsTabProps {
  nextActions: string[];
}

const NextActionsTab: React.FC<NextActionsTabProps> = ({ nextActions }) => {
  if (nextActions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No next actions at this time</p>
      </div>
    );
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
        <Target className="h-4 w-4" />
        Next Actions for You
      </h4>
      <ul className="space-y-1">
        {nextActions.map((action, index) => (
          <li key={index} className="text-sm text-green-800 flex items-center gap-2">
            <ArrowRight className="h-3 w-3" />
            {action}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default NextActionsTab;
