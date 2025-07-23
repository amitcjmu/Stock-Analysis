import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Crown, Activity } from 'lucide-react';
import type { AgentInfo } from '../types';
import { getStatusIcon } from '../utils/statusHelpers';

interface AgentCardProps {
  agent: AgentInfo;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent }) => {
  return (
    <Card className="mb-2">
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm flex items-center gap-1">
              {agent.isManager && <Crown className="h-3 w-3 text-yellow-500" />}
              {agent.name}
            </span>
            {getStatusIcon(agent.status)}
          </div>
          {agent.performance && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Activity className="h-3 w-3" />
              {agent.performance.success_rate}% success
            </div>
          )}
        </div>
        <p className="text-xs text-gray-600">{agent.role}</p>
        {agent.currentTask && (
          <p className="text-xs text-blue-600 mt-1">Current: {agent.currentTask}</p>
        )}
        {agent.collaborations && agent.collaborations.length > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            Collaborating with: {agent.collaborations.join(', ')}
          </p>
        )}
      </CardContent>
    </Card>
  );
};