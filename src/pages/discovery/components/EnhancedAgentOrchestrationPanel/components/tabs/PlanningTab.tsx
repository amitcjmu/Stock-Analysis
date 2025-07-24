import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Target, TrendingUp, Settings, Timer } from 'lucide-react';
import type { PlanningData } from '../../types';

interface PlanningTabProps {
  planningData: PlanningData | null;
}

export const PlanningTab: React.FC<PlanningTabProps> = ({ planningData }) => {
  if (!planningData) {
    return (
      <div className="text-center py-8 text-gray-500">
        No planning data available yet
      </div>
    );
  }

  const metrics = [
    {
      title: 'Coordination Strategy',
      value: planningData.coordination_strategy,
      icon: Target,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Success Criteria Met',
      value: `${planningData.success_criteria_met}%`,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Adaptive Adjustments',
      value: planningData.adaptive_adjustments,
      icon: Settings,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Predicted Completion',
      value: planningData.predicted_completion,
      icon: Timer,
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
                {idx === 0 ? (
                  <Badge variant="secondary" className="text-sm">
                    {metric.value}
                  </Badge>
                ) : (
                  <span className={`text-2xl font-bold ${metric.color}`}>
                    {metric.value}
                  </span>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-600">{metric.title}</h3>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Optimization Score</CardTitle>
          <CardDescription>
            Overall planning effectiveness
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Optimization Score</span>
                <span className="text-sm font-medium">
                  {planningData.optimization_score}%
                </span>
              </div>
              <Progress value={planningData.optimization_score} className="h-3" />
            </div>
            <div className="text-sm text-gray-600">
              The planning system has made {planningData.adaptive_adjustments} adaptive 
              adjustments to optimize the migration strategy.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};