import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Brain, Zap } from 'lucide-react';

interface OverallProgressHeaderProps {
  overallProgress: number;
  currentPhase: string;
  flowId: string;
}

export const OverallProgressHeader: React.FC<OverallProgressHeaderProps> = ({
  overallProgress,
  currentPhase,
  flowId
}) => (
  <Card>
    <CardHeader>
      <div className="flex items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            CrewAI Discovery Orchestration
          </CardTitle>
          <CardDescription>
            Multiple specialized crews working collaboratively on your data
          </CardDescription>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-blue-600">{overallProgress.toFixed(0)}%</p>
          <p className="text-sm text-gray-600">Overall Progress</p>
        </div>
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        <Progress value={overallProgress} className="h-3" />
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-orange-500" />
            Current Phase: {currentPhase}
          </span>
          <span className="text-gray-600">
            Flow: {flowId?.substring(0, 8)}...
          </span>
        </div>
      </div>
    </CardContent>
  </Card>
);