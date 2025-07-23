import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Progress } from '@/components/ui/progress';
import type { SixRDecision } from '@/hooks/useAssessmentFlow'
import { ApplicationComponent, TechDebtItem } from '@/hooks/useAssessmentFlow'
import { ConfidenceScoreIndicator } from './ConfidenceScoreIndicator';
import type { Cpu } from 'lucide-react'
import { Target, AlertTriangle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils';

interface ApplicationSummaryCardProps {
  applicationId: string;
  decision: SixRDecision;
  components: ApplicationComponent[];
  techDebt: TechDebtItem[];
  printMode?: boolean;
  compact?: boolean;
}

const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', color: 'bg-green-100 text-green-700 border-green-200' },
  { value: 'replatform', label: 'Replatform (Lift & Reshape)', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'refactor', label: 'Refactor/Re-architect', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { value: 'repurchase', label: 'Repurchase (SaaS)', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { value: 'retire', label: 'Retire', color: 'bg-gray-100 text-gray-700 border-gray-200' },
  { value: 'retain', label: 'Retain (Revisit)', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' }
];

export const ApplicationSummaryCard: React.FC<ApplicationSummaryCardProps> = ({
  applicationId,
  decision,
  components,
  techDebt,
  printMode = false,
  compact = false
}) => {
  const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === decision.overall_strategy);
  
  const techDebtStats = {
    total: techDebt.length,
    critical: techDebt.filter(t => t.severity === 'critical').length,
    high: techDebt.filter(t => t.severity === 'high').length,
    avgScore: techDebt.length > 0 ? 
      techDebt.reduce((sum, t) => sum + (t.tech_debt_score || 0), 0) / techDebt.length : 0
  };

  const compatibilityIssues = decision.component_treatments.filter(ct => 
    ct.compatibility_issues && ct.compatibility_issues.length > 0
  ).length;

  return (
    <Card className={cn("print:shadow-none print:border-2", printMode && "print:mb-4")}>
      <CardHeader className={cn("pb-4", compact && "pb-3")}>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className={cn("text-xl", compact && "text-lg")}>
              {decision.application_name || applicationId}
            </CardTitle>
            <CardDescription className="mt-1">
              Application ID: {applicationId}
            </CardDescription>
          </div>
          
          <div className="flex items-center space-x-3">
            <Badge className={cn(strategyInfo?.color, compact ? "text-xs" : "text-sm")}>
              {strategyInfo?.label || decision.overall_strategy}
            </Badge>
            {!compact && (
              <ConfidenceScoreIndicator 
                score={decision.confidence_score}
                size="small"
                showLabel={false}
              />
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className={cn("grid gap-4", compact ? "grid-cols-4" : "grid-cols-2 md:grid-cols-4")}>
          <div className="text-center">
            <div className={cn("font-bold text-blue-600", compact ? "text-lg" : "text-xl")}>
              {components.length}
            </div>
            <div className={cn("text-gray-600", compact ? "text-xs" : "text-sm")}>
              Components
            </div>
          </div>
          
          <div className="text-center">
            <div className={cn("font-bold", compact ? "text-lg" : "text-xl", 
              techDebtStats.total > 0 ? "text-orange-600" : "text-green-600")}>
              {techDebtStats.total}
            </div>
            <div className={cn("text-gray-600", compact ? "text-xs" : "text-sm")}>
              Tech Debt Items
            </div>
          </div>
          
          <div className="text-center">
            <div className={cn("font-bold", compact ? "text-lg" : "text-xl",
              compatibilityIssues > 0 ? "text-red-600" : "text-green-600")}>
              {compatibilityIssues}
            </div>
            <div className={cn("text-gray-600", compact ? "text-xs" : "text-sm")}>
              Compatibility Issues
            </div>
          </div>
          
          <div className="text-center">
            <div className={cn("font-bold", compact ? "text-lg" : "text-xl",
              decision.confidence_score >= 0.8 ? "text-green-600" : "text-orange-600")}>
              {Math.round(decision.confidence_score * 100)}%
            </div>
            <div className={cn("text-gray-600", compact ? "text-xs" : "text-sm")}>
              Confidence
            </div>
          </div>
        </div>

        {!compact && (
          <>
            {/* Strategy Rationale */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-1">
                <Target className="h-4 w-4" />
                <span>Strategy Rationale</span>
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                {decision.rationale}
              </p>
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
                    <div key={index} className="text-xs bg-orange-50 text-orange-700 p-2 rounded border border-orange-200">
                      {risk}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tech Debt Breakdown */}
            {techDebt.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">
                  Technical Debt Breakdown
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span>Critical:</span>
                    <span className="font-medium text-red-600">{techDebtStats.critical}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>High:</span>
                    <span className="font-medium text-orange-600">{techDebtStats.high}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Score:</span>
                    <span className="font-medium">{Math.round(techDebtStats.avgScore)}/100</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Issues:</span>
                    <span className="font-medium">{techDebtStats.total}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Architecture Exceptions */}
            {decision.architecture_exceptions.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">
                  Architecture Exceptions
                </h4>
                <div className="space-y-1">
                  {decision.architecture_exceptions.slice(0, 3).map((exception, index) => (
                    <div key={index} className="text-xs bg-yellow-50 text-yellow-700 p-2 rounded border border-yellow-200">
                      {exception}
                    </div>
                  ))}
                  {decision.architecture_exceptions.length > 3 && (
                    <div className="text-xs text-gray-500">
                      +{decision.architecture_exceptions.length - 3} more exceptions
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* Status Indicators */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {decision.confidence_score >= 0.8 ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-600" />
            )}
            <span className={cn("text-sm", compact ? "text-xs" : "text-sm",
              decision.confidence_score >= 0.8 ? "text-green-600" : "text-orange-600")}>
              {decision.confidence_score >= 0.8 ? 'Ready for Planning' : 'Needs Review'}
            </span>
          </div>
          
          {decision.move_group_hints.length > 0 && (
            <Badge variant="outline" className={compact ? "text-xs" : ""}>
              Move Group: {decision.move_group_hints[0]}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};