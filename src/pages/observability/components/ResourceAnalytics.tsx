/**
 * ResourceAnalytics Component
 * Extracted from AgentDetailPage.tsx for modularization
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Progress } from '../../../components/ui/progress';
import { AgentMetricsChart } from '../../../components/observability';
import type { AgentDetailData } from '../types/AgentDetailTypes';

interface ResourceAnalyticsProps {
  agentData: AgentDetailData;
}

export const ResourceAnalytics: React.FC<ResourceAnalyticsProps> = ({ agentData }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Memory Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Current Usage</span>
              <span className="font-medium">{agentData.performance.memoryUsage.toFixed(1)} MB</span>
            </div>
            <Progress value={Math.min((agentData.performance.memoryUsage / 500) * 100, 100)} />
            <AgentMetricsChart 
              data={{
                data: agentData.trends.memoryUsageHistory.map((usage, index) => ({
                  timestamp: agentData.trends.timestamps[index],
                  value: usage,
                  label: `${usage.toFixed(1)} MB`
                })),
                color: '#8b5cf6',
                trend: 'stable',
                changePercent: 0
              }}
              title="Memory Usage Over Time"
              height={150}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LLM Usage Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Tokens</p>
                <p className="text-lg font-bold">{agentData.llmAnalytics.totalTokens.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Avg per Task</p>
                <p className="text-lg font-bold">{agentData.llmAnalytics.avgTokensPerTask}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Est. Cost</p>
                <p className="text-lg font-bold">${agentData.llmAnalytics.costEstimate.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">LLM Calls</p>
                <p className="text-lg font-bold">{agentData.performance.llmCalls}</p>
              </div>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Model Usage</h4>
              {agentData.llmAnalytics.topModelsUsed.map((model, index) => (
                <div key={index} className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">{model.model}</span>
                  <span className="text-sm font-medium">{model.usage}%</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};