import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SixRDecision } from '@/hooks/useAssessmentFlow';
import { ConfidenceScoreIndicator } from './ConfidenceScoreIndicator';
import { Target, AlertTriangle, TrendingUp } from 'lucide-react';

interface SixRDecisionRationaleProps {
  decision: SixRDecision;
  printMode?: boolean;
}

const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', description: 'Move to cloud without changes' },
  { value: 'replatform', label: 'Replatform (Lift & Reshape)', description: 'Minor optimizations for cloud' },
  { value: 'refactor', label: 'Refactor/Re-architect', description: 'Significant code changes for cloud-native' },
  { value: 'repurchase', label: 'Repurchase (SaaS)', description: 'Replace with SaaS solution' },
  { value: 'retire', label: 'Retire', description: 'Decommission the application' },
  { value: 'retain', label: 'Retain (Revisit)', description: 'Keep on-premises for now' }
];

export const SixRDecisionRationale: React.FC<SixRDecisionRationaleProps> = ({
  decision,
  printMode = false
}) => {
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === decision.overall_strategy);

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="h-5 w-5" />
          <span>6R Strategy Decision</span>
        </CardTitle>
        <CardDescription>
          Detailed rationale and confidence assessment for the chosen modernization strategy
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Strategy Selection */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700">Selected Strategy</h4>
            <Badge variant="outline" className="text-lg px-3 py-1">
              {strategyInfo?.label || decision.overall_strategy}
            </Badge>
          </div>
          {strategyInfo && (
            <p className="text-sm text-gray-600">{strategyInfo.description}</p>
          )}
        </div>

        {/* Confidence Score */}
        <div className="space-y-2">
          <ConfidenceScoreIndicator 
            score={decision.confidence_score}
            size="large"
            showIcon={true}
            showLabel={true}
          />
        </div>

        {/* Rationale */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Decision Rationale</h4>
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-700 leading-relaxed">
              {decision.rationale}
            </p>
          </div>
        </div>

        {/* Risk Factors */}
        {decision.risk_factors.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-1">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <span>Risk Factors</span>
            </h4>
            <div className="space-y-1">
              {decision.risk_factors.map((risk, index) => (
                <div key={index} className="p-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-700">
                  • {risk}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tech Debt Impact */}
        {decision.tech_debt_score !== undefined && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-1">
              <TrendingUp className="h-4 w-4" />
              <span>Technical Debt Impact</span>
            </h4>
            <div className="flex items-center justify-between p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <span className="text-sm text-purple-700">
                Overall Tech Debt Score
              </span>
              <Badge variant="outline" className={
                decision.tech_debt_score >= 80 ? "border-red-300 text-red-700" :
                decision.tech_debt_score >= 60 ? "border-orange-300 text-orange-700" :
                decision.tech_debt_score >= 40 ? "border-yellow-300 text-yellow-700" : 
                "border-green-300 text-green-700"
              }>
                {decision.tech_debt_score}/100
              </Badge>
            </div>
          </div>
        )}

        {/* Component Summary */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Component Strategy Summary</h4>
          <div className="space-y-1">
            {decision.component_treatments.slice(0, 5).map((treatment, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-gray-600 truncate flex-1">
                  {treatment.component_name}
                </span>
                <Badge variant="outline" className="ml-2 text-xs">
                  {treatment.recommended_strategy}
                </Badge>
              </div>
            ))}
            {decision.component_treatments.length > 5 && (
              <p className="text-xs text-gray-500">
                +{decision.component_treatments.length - 5} more components
              </p>
            )}
          </div>
        </div>

        {/* Move Group Hints */}
        {decision.move_group_hints.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Migration Planning Hints</h4>
            <div className="space-y-1">
              {decision.move_group_hints.map((hint, index) => (
                <div key={index} className="p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                  • {hint}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};