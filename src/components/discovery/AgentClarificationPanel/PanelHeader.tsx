/**
 * Panel Header Component
 * 
 * Header section with title, pending count, and refresh button.
 */

import React from 'react';
import { Bot, RefreshCw } from 'lucide-react';

interface PanelHeaderProps {
  pendingCount: number;
  onRefresh: () => void;
}

const PanelHeader: React.FC<PanelHeaderProps> = ({ pendingCount, onRefresh }) => {
  return (
    <div className="p-4 border-b">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-blue-500" />
          <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
          {pendingCount > 0 && (
            <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
              {pendingCount} pending
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh questions"
        >
          <RefreshCw className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </div>
  );
};

export default PanelHeader;