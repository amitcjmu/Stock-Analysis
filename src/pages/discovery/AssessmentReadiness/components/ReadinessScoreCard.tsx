import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { ReadinessAssessment } from '../types';
import { getReadinessColor, getReadinessBadgeVariant } from '../utils';

interface ReadinessScoreCardProps {
  assessment: ReadinessAssessment;
  onRefresh: () => void;
  isLoading?: boolean;
}

export const ReadinessScoreCard = ({
  assessment,
  onRefresh,
  isLoading = false,
}: ReadinessScoreCardProps) => {
  const { overall_readiness, handoff_metadata, outstanding_questions } = assessment;
  const readinessPercentage = Math.round(overall_readiness.readiness_score * 100);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Assessment Readiness</CardTitle>
        <Button
          variant="ghost"
          size="icon"
          onClick={onRefresh}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="text-center">
            <div className={`text-3xl font-bold ${getReadinessColor(overall_readiness.readiness_score)}`}>
              {readinessPercentage}%
            </div>
            <div className="text-sm text-gray-600">Overall Readiness</div>
            <Badge
              variant={getReadinessBadgeVariant(overall_readiness.readiness_state)}
              className="mt-1"
            >
              {overall_readiness.readiness_state.replace('_', ' ')}
            </Badge>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {handoff_metadata.applications_ready_for_assessment}
            </div>
            <div className="text-sm text-gray-600">Apps Ready</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {outstanding_questions.length}
            </div>
            <div className="text-sm text-gray-600">Outstanding Questions</div>
          </div>

          <div className="text-center">
            <div className={`text-2xl font-bold ${getReadinessColor(overall_readiness.confidence_level)}`}>
              {Math.round(overall_readiness.confidence_level * 100)}%
            </div>
            <div className="text-sm text-gray-600">Confidence Level</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Readiness Progress</span>
            <span>{readinessPercentage}%</span>
          </div>
          <Progress value={readinessPercentage} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
};
