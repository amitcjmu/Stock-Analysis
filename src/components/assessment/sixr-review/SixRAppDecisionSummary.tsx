import React from 'react';
import { Target, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ConfidenceScoreIndicator } from '@/components/assessment/ConfidenceScoreIndicator';
import type { SixRDecision } from '@/hooks/useAssessmentFlow';
import type { getStrategyColor } from '@/utils/assessment/sixrHelpers'
import { getStrategyLabel } from '@/utils/assessment/sixrHelpers'

interface SixRAppDecisionSummaryProps {
  selectedApp: string;
  decision: SixRDecision;
}

export const SixRAppDecisionSummary: React.FC<SixRAppDecisionSummaryProps> = ({
  selectedApp,
  decision
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>{selectedApp} Strategy</span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className={getStrategyColor(decision.overall_strategy)}>
              {getStrategyLabel(decision.overall_strategy)}
            </Badge>
            <ConfidenceScoreIndicator 
              score={decision.confidence_score}
              size="large"
            />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Rationale</h4>
              <p className="text-sm text-gray-600">{decision.rationale}</p>
            </div>
            
            {decision.risk_factors.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Risk Factors</h4>
                <div className="flex flex-wrap gap-1">
                  {decision.risk_factors.map((risk, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      {risk}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {decision.architecture_exceptions.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Architecture Exceptions</h4>
                <div className="space-y-1">
                  {decision.architecture_exceptions.map((exception, index) => (
                    <p key={index} className="text-xs text-orange-600 bg-orange-50 p-1 rounded">
                      {exception}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {decision.move_group_hints.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Move Group Hints</h4>
                <div className="flex flex-wrap gap-1">
                  {decision.move_group_hints.map((hint, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {hint}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};