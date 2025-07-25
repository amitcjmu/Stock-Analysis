import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MessageSquare, Users, Brain, Zap } from 'lucide-react';
import type { CollaborationData } from '../../types';

interface CollaborationTabProps {
  collaborationData: CollaborationData | null;
}

export const CollaborationTab: React.FC<CollaborationTabProps> = ({ collaborationData }) => {
  if (!collaborationData) {
    return (
      <div className="text-center py-8 text-gray-500">
        No collaboration data available yet
      </div>
    );
  }

  const metrics = [
    {
      title: 'Total Collaborations',
      value: collaborationData.total_collaborations,
      icon: MessageSquare,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Active Collaborations',
      value: collaborationData.active_collaborations,
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Cross-Crew Insights',
      value: collaborationData.cross_crew_insights,
      icon: Brain,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Knowledge Sharing',
      value: `${collaborationData.knowledge_sharing_score}%`,
      icon: Zap,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric, idx) => (
          <Card key={idx}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                  <metric.icon className={`h-6 w-6 ${metric.color}`} />
                </div>
                <span className={`text-2xl font-bold ${metric.color}`}>
                  {metric.value}
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-600">{metric.title}</h3>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Memory Utilization</CardTitle>
          <CardDescription>
            Shared memory usage across all crews
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Memory Utilization</span>
                <span className="text-sm font-medium">
                  {collaborationData.memory_utilization}%
                </span>
              </div>
              <Progress value={collaborationData.memory_utilization} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
