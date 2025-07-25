import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Link, Brain, Zap } from 'lucide-react';
import type { CrewProgress } from '../types';
import { getStatusBadge } from '../utils/statusHelpers';
import { AgentCard } from './AgentCard';

interface CrewCardProps {
  crew: CrewProgress;
  isActive: boolean;
}

export const CrewCard: React.FC<CrewCardProps> = ({ crew, isActive }) => {
  return (
    <Card className={`mb-4 ${isActive ? 'border-blue-500' : ''}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {crew.icon}
            {crew.name}
          </CardTitle>
          {getStatusBadge(crew.status)}
        </div>
        <CardDescription>{crew.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progress</span>
            <span>{crew.progress}%</span>
          </div>
          <Progress value={crew.progress} className="h-2" />
        </div>

        {crew.currentTask && (
          <div className="mb-4 p-2 bg-blue-50 rounded text-sm">
            <span className="font-medium">Current Task: </span>
            {crew.currentTask}
          </div>
        )}

        {/* Collaboration Status */}
        {crew.collaboration_status && (
          <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3 text-blue-500" />
              <span>Intra-crew: {crew.collaboration_status.intra_crew}</span>
            </div>
            <div className="flex items-center gap-1">
              <Link className="h-3 w-3 text-purple-500" />
              <span>Cross-crew: {crew.collaboration_status.cross_crew}</span>
            </div>
            <div className="flex items-center gap-1">
              <Brain className="h-3 w-3 text-green-500" />
              <span>Memory: {crew.collaboration_status.memory_sharing ? 'Active' : 'Inactive'}</span>
            </div>
            <div className="flex items-center gap-1">
              <Zap className="h-3 w-3 text-orange-500" />
              <span>Knowledge: {crew.collaboration_status.knowledge_utilization}%</span>
            </div>
          </div>
        )}

        {/* Planning Status */}
        {crew.planning_status && (
          <div className="mb-4 p-2 bg-gray-50 rounded">
            <div className="text-xs font-medium mb-1">Planning Strategy: {crew.planning_status.strategy}</div>
            <div className="flex items-center justify-between text-xs">
              <span>Coordination Score</span>
              <Badge variant="secondary">{crew.planning_status.coordination_score}%</Badge>
            </div>
            {crew.planning_status.adaptive_triggers.length > 0 && (
              <div className="mt-1 text-xs text-gray-600">
                Triggers: {crew.planning_status.adaptive_triggers.join(', ')}
              </div>
            )}
          </div>
        )}

        <div className="space-y-2">
          <h4 className="text-sm font-medium">Agents ({crew.agents.length})</h4>
          {crew.agents.map((agent, idx) => (
            <AgentCard key={idx} agent={agent} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
