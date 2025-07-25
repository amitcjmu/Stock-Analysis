import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Brain, Lightbulb, Network, BarChart3 } from 'lucide-react';
import type { CrewProgress } from '../types';

interface OverallProgressProps {
  crews: CrewProgress[];
}

export const OverallProgress: React.FC<OverallProgressProps> = ({ crews }) => {
  const overallProgress = Math.round(
    crews.reduce((sum, crew) => sum + crew.progress, 0) / crews.length
  );

  const activeCrews = crews.filter(c => c.status === 'running').length;
  const completedCrews = crews.filter(c => c.status === 'completed').length;
  const totalAgents = crews.reduce((sum, crew) => sum + crew.agents.length, 0);
  const activeAgents = crews.reduce(
    (sum, crew) => sum + crew.agents.filter(a => a.status === 'active').length,
    0
  );

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Enhanced Agent Orchestration
          </span>
          <Badge variant="outline" className="text-sm">
            {totalAgents} Total Agents
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-gray-600">{overallProgress}%</span>
            </div>
            <Progress value={overallProgress} className="h-3" />
          </div>

          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="flex justify-center mb-2">
                <Network className="h-8 w-8 text-blue-500" />
              </div>
              <div className="text-2xl font-bold">{crews.length}</div>
              <div className="text-xs text-gray-600">Total Crews</div>
            </div>
            <div>
              <div className="flex justify-center mb-2">
                <Lightbulb className="h-8 w-8 text-green-500" />
              </div>
              <div className="text-2xl font-bold">{activeCrews}</div>
              <div className="text-xs text-gray-600">Active Crews</div>
            </div>
            <div>
              <div className="flex justify-center mb-2">
                <BarChart3 className="h-8 w-8 text-purple-500" />
              </div>
              <div className="text-2xl font-bold">{completedCrews}</div>
              <div className="text-xs text-gray-600">Completed</div>
            </div>
            <div>
              <div className="flex justify-center mb-2">
                <Brain className="h-8 w-8 text-orange-500" />
              </div>
              <div className="text-2xl font-bold">{activeAgents}</div>
              <div className="text-xs text-gray-600">Active Agents</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
