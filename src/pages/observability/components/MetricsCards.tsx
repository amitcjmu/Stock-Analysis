/**
 * MetricsCards Component
 * Extracted from AgentDetailPage.tsx for modularization
 */

import React from 'react';
import { TrendingUp, Activity, Clock, Brain } from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { Progress } from '../../../components/ui/progress';
import type { AgentDetailData, PerformanceMetrics } from '../types/AgentDetailTypes';

interface MetricsCardsProps {
  agentData: AgentDetailData;
  performanceMetrics: PerformanceMetrics;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ agentData, performanceMetrics }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">{performanceMetrics.efficiency}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
          <Progress value={parseFloat(performanceMetrics.efficiency)} className="mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Tasks</p>
              <p className="text-2xl font-bold text-blue-600">{agentData.performance.totalTasks}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {agentData.performance.completedTasks} completed, {agentData.performance.failedTasks} failed
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Duration</p>
              <p className="text-2xl font-bold text-purple-600">{performanceMetrics.speed}s</p>
            </div>
            <Clock className="w-8 h-8 text-purple-500" />
          </div>
          <p className="text-xs text-gray-500 mt-2">Average task completion time</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Confidence</p>
              <p className="text-2xl font-bold text-orange-600">{performanceMetrics.confidence}%</p>
            </div>
            <Brain className="w-8 h-8 text-orange-500" />
          </div>
          <p className="text-xs text-gray-500 mt-2">Average confidence score</p>
        </CardContent>
      </Card>
    </div>
  );
};