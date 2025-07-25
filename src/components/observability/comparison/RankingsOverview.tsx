/**
 * Rankings overview component extracted from AgentComparison
 * Displays overall agent rankings
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { AgentStatusIndicator } from '../AgentStatusIndicator';
import type { AgentComparisonData } from '../hooks/useAgentComparison';

interface RankingsOverviewProps {
  comparisonData: AgentComparisonData[];
}

export const RankingsOverview: React.FC<RankingsOverviewProps> = ({ comparisonData }) => {
  const sortedAgents = [...comparisonData].sort((a, b) => a.ranking.overall - b.ranking.overall);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Overall Rankings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedAgents.map((agent, index) => (
            <div key={agent.agentName} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <div className="flex items-center gap-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                  index === 0 ? 'bg-yellow-500' :
                  index === 1 ? 'bg-gray-400' :
                  index === 2 ? 'bg-orange-500' :
                  'bg-gray-300'
                }`}>
                  {index + 1}
                </div>
                <span className="font-medium">{agent.agentName}</span>
                <AgentStatusIndicator status="active" variant="dot" size="sm" />
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>Success: #{agent.ranking.successRate}</span>
                <span>Speed: #{agent.ranking.performance}</span>
                <span>Reliability: #{agent.ranking.reliability}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
