import { useMemo } from 'react';
import { SixRDecision } from '@/hooks/useAssessmentFlow';
import { SIX_R_STRATEGIES } from '@/utils/assessment/sixrHelpers';

interface UseSixRStatisticsProps {
  sixrDecisions: Record<string, SixRDecision>;
  selectedApplicationIds: string[];
}

interface SixRStatistics {
  totalApps: number;
  assessed: number;
  avgConfidence: number;
  needsReview: number;
  hasIssues: number;
  strategyCount: Record<string, number>;
}

export const useSixRStatistics = ({
  sixrDecisions,
  selectedApplicationIds
}: UseSixRStatisticsProps): SixRStatistics => {
  return useMemo(() => {
    const allDecisions = Object.values(sixrDecisions);
    const strategyCount = SIX_R_STRATEGIES.reduce((acc, strategy) => {
      acc[strategy.value] = allDecisions.filter(d => d.overall_strategy === strategy.value).length;
      return acc;
    }, {} as Record<string, number>);

    const avgConfidence = allDecisions.length > 0 
      ? allDecisions.reduce((sum, d) => sum + d.confidence_score, 0) / allDecisions.length 
      : 0;

    const needsReview = allDecisions.filter(d => d.confidence_score < 0.8).length;
    const hasIssues = allDecisions.filter(d => 
      d.component_treatments?.some(ct => !ct.compatibility_validated)
    ).length;

    return {
      totalApps: selectedApplicationIds.length,
      assessed: allDecisions.length,
      avgConfidence,
      needsReview,
      hasIssues,
      strategyCount
    };
  }, [sixrDecisions, selectedApplicationIds]);
};