import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import type { SixRDecision } from '@/hooks/useAssessmentFlow';
import { ConfidenceScoreIndicator } from './ConfidenceScoreIndicator';
import { AlertTriangle, CheckCircle, Eye, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ApplicationRollupViewProps {
  decisions: Record<string, SixRDecision>;
  selectedApplicationIds: string[];
  selectedApplications?: Array<{ application_id: string; application_name: string }>;
  onApplicationSelect: (appId: string) => void;
}

const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost', color: 'bg-green-100 text-green-700 border-green-200' },
  { value: 'replatform', label: 'Replatform', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'refactor', label: 'Refactor', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { value: 'repurchase', label: 'Repurchase', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { value: 'retire', label: 'Retire', color: 'bg-gray-100 text-gray-700 border-gray-200' },
  { value: 'retain', label: 'Retain', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' }
];

export const ApplicationRollupView: React.FC<ApplicationRollupViewProps> = ({
  decisions,
  selectedApplicationIds,
  selectedApplications,
  onApplicationSelect
}) => {
  const getStrategyInfo = (strategy: string): unknown => {
    return SIX_R_STRATEGIES.find(s => s.value === strategy) || {
      value: strategy,
      label: strategy,
      color: 'bg-gray-100 text-gray-700 border-gray-200'
    };
  };

  const getModernizationLevel = (strategy: string): JSX.Element => {
    const levels: Record<string, { level: number; label: string }> = {
      'retain': { level: 1, label: 'No Change' },
      'retire': { level: 1, label: 'No Change' },
      'rehost': { level: 2, label: 'Low Modernization' },
      'replatform': { level: 3, label: 'Medium Modernization' },
      'repurchase': { level: 4, label: 'High Modernization' },
      'refactor': { level: 5, label: 'Full Modernization' }
    };
    return levels[strategy] || { level: 1, label: 'Unknown' };
  };

  const sortedApplications = selectedApplicationIds.map(appId => {
    const app = selectedApplications?.find(a => a.application_id === appId);
    return {
      appId,
      appName: app?.application_name || appId,
      decision: decisions[appId],
      hasDecision: !!decisions[appId]
    };
  }).sort((a, b) => {
    // Sort by: 1) Has decision, 2) Confidence score (low first), 3) Modernization level (high first)
    if (!a.hasDecision && b.hasDecision) return 1;
    if (a.hasDecision && !b.hasDecision) return -1;

    if (a.decision && b.decision) {
      // Low confidence first (needs review)
      const confidenceDiff = a.decision.confidence_score - b.decision.confidence_score;
      if (Math.abs(confidenceDiff) > 0.1) return confidenceDiff;

      // High modernization first
      const aLevel = getModernizationLevel(a.decision.overall_strategy).level;
      const bLevel = getModernizationLevel(b.decision.overall_strategy).level;
      return bLevel - aLevel;
    }

    return a.appId.localeCompare(b.appId);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Application Rollup Summary</CardTitle>
        <CardDescription>
          Overview of 6R strategy decisions across all applications (highest modernization first)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedApplications.map(({ appId, appName, decision, hasDecision }) => (
            <ApplicationRollupCard
              key={appId}
              appId={appId}
              appName={appName}
              decision={decision}
              hasDecision={hasDecision}
              onSelect={() => onApplicationSelect(appId)}
            />
          ))}

          {selectedApplicationIds.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-8 w-8 mx-auto mb-2" />
              <p>No applications selected for assessment</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface ApplicationRollupCardProps {
  appId: string;
  appName: string;
  decision?: SixRDecision;
  hasDecision: boolean;
  onSelect: () => void;
}

const ApplicationRollupCard: React.FC<ApplicationRollupCardProps> = ({
  appId,
  appName,
  decision,
  hasDecision,
  onSelect
}) => {
  const getStrategyInfo = (strategy: string): unknown => {
    return SIX_R_STRATEGIES.find(s => s.value === strategy) || {
      value: strategy,
      label: strategy,
      color: 'bg-gray-100 text-gray-700 border-gray-200'
    };
  };

  const getModernizationLevel = (strategy: string): JSX.Element => {
    const levels: Record<string, { level: number; label: string; color: string }> = {
      'retain': { level: 1, label: 'No Change', color: 'text-gray-600' },
      'retire': { level: 1, label: 'No Change', color: 'text-gray-600' },
      'rehost': { level: 2, label: 'Low Modernization', color: 'text-blue-600' },
      'replatform': { level: 3, label: 'Medium Modernization', color: 'text-purple-600' },
      'repurchase': { level: 4, label: 'High Modernization', color: 'text-orange-600' },
      'refactor': { level: 5, label: 'Full Modernization', color: 'text-red-600' }
    };
    return levels[strategy] || { level: 1, label: 'Unknown', color: 'text-gray-600' };
  };

  if (!hasDecision) {
    return (
      <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-gray-50">
        <div className="flex items-center space-x-3">
          <Clock className="h-5 w-5 text-gray-400" />
          <div>
            <h3 className="font-medium text-gray-900">{appName}</h3>
            <p className="text-sm text-gray-500">Pending analysis</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={onSelect}>
          <Eye className="h-4 w-4 mr-1" />
          View
        </Button>
      </div>
    );
  }

  const strategyInfo = getStrategyInfo(decision.overall_strategy);
  const modernizationInfo = getModernizationLevel(decision.overall_strategy);
  const needsReview = decision.confidence_score < 0.8;
  const hasIssues = decision.component_treatments?.some(ct => !ct.compatibility_validated);

  return (
    <div className={cn(
      "flex items-center justify-between p-4 border rounded-lg transition-colors hover:bg-gray-50",
      needsReview ? "border-orange-200 bg-orange-50/30" : "border-gray-200"
    )}>
      <div className="flex items-center space-x-4 flex-1">
        {/* Status Icon */}
        <div className="flex-shrink-0">
          {hasIssues ? (
            <AlertTriangle className="h-5 w-5 text-red-600" />
          ) : needsReview ? (
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          ) : (
            <CheckCircle className="h-5 w-5 text-green-600" />
          )}
        </div>

        {/* Application Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="font-medium text-gray-900 truncate">{decision.application_name || appId}</h3>
            <Badge className={strategyInfo.color}>
              {strategyInfo.label}
            </Badge>
          </div>

          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <span className="text-gray-600">Modernization:</span>
              <span className={cn("font-medium", modernizationInfo.color)}>
                {modernizationInfo.label}
              </span>
            </div>

            <div className="flex items-center space-x-1">
              <span className="text-gray-600">Components:</span>
              <span className="font-medium">
                {decision.component_treatments?.length || 0}
              </span>
            </div>

            {decision.tech_debt_score !== undefined && (
              <div className="flex items-center space-x-1">
                <span className="text-gray-600">Tech Debt:</span>
                <span className={cn(
                  "font-medium",
                  decision.tech_debt_score >= 80 ? "text-red-600" :
                  decision.tech_debt_score >= 60 ? "text-orange-600" :
                  decision.tech_debt_score >= 40 ? "text-yellow-600" : "text-green-600"
                )}>
                  {decision.tech_debt_score}/100
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Confidence Score */}
        <div className="flex-shrink-0">
          <ConfidenceScoreIndicator
            score={decision.confidence_score}
            size="small"
            showLabel={false}
          />
        </div>
      </div>

      {/* Action Button */}
      <Button variant="outline" size="sm" onClick={onSelect} className="ml-4">
        <Eye className="h-4 w-4 mr-1" />
        Review
      </Button>
    </div>
  );
};
