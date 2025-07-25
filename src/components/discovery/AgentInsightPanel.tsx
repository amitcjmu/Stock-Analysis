import React from 'react';
import { Card } from '../ui/card';
import { Lightbulb } from 'lucide-react';

interface AgentInsightPanelProps {
  pageContext: string;
  refreshTrigger?: number;
  onInsightAction?: (insightId: string, action: string) => void;
}

const AgentInsightPanel: React.FC<AgentInsightPanelProps> = ({
  pageContext,
  refreshTrigger = 0,
  onInsightAction
}) => {
  return (
    <Card className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Lightbulb className="h-5 w-5 text-yellow-500" />
        <h3 className="text-lg font-semibold">Agent Insights</h3>
      </div>
      <div className="space-y-4">
        <p className="text-sm text-gray-500">
          AI agents are analyzing your dependencies and will provide insights here.
        </p>
      </div>
    </Card>
  );
};

export default AgentInsightPanel;
