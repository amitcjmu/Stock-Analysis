/**
 * MetricCard component extracted from AgentComparison
 * Displays a single metric comparison across agents
 */

import React from 'react';
import { TrendingUp, TrendingDown, Trophy } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { AgentComparisonData } from '../hooks/useAgentComparison';
import type { COMPARISON_METRICS } from '../utils/constants';

export interface MetricCardProps {
  metric: typeof COMPARISON_METRICS[number];
  agents: AgentComparisonData[];
  selectedAgents: string[];
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, agents, selectedAgents }) => {
  const values = agents
    .filter(agent => selectedAgents.includes(agent.agentName))
    .map(agent => ({
      name: agent.agentName,
      value: agent.metrics[metric.key],
      ranking: agent.ranking.overall
    }))
    .sort((a, b) => metric.higherIsBetter ? b.value - a.value : a.value - b.value);

  const best = values[0];
  const worst = values[values.length - 1];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-gray-600">
          {metric.label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {values.map((item, index) => {
            const isBest = item === best;
            const isWorst = item === worst && values.length > 1;

            return (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    isBest ? 'bg-green-500' :
                    isWorst ? 'bg-red-500' :
                    'bg-gray-400'
                  }`} />
                  <span className="text-sm font-medium text-gray-900 truncate max-w-32">
                    {item.name.replace('Agent', '')}
                  </span>
                  {isBest && <Trophy className="w-4 h-4 text-yellow-500" />}
                </div>
                <div className="flex items-center gap-1">
                  <span className={`text-sm font-bold ${
                    isBest ? 'text-green-600' :
                    isWorst ? 'text-red-600' :
                    'text-gray-900'
                  }`}>
                    {metric.format(item.value)}
                  </span>
                  {index === 0 && values.length > 1 && (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  )}
                  {index === values.length - 1 && values.length > 1 && (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
