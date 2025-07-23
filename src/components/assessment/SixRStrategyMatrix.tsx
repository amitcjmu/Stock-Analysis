import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { SixRDecision } from '@/hooks/useAssessmentFlow';
import { TrendingUp } from 'lucide-react'
import { Target, AlertTriangle } from 'lucide-react'

interface SixRStrategyMatrixProps {
  decision: SixRDecision;
  onDecisionChange: (updates: Partial<SixRDecision>) => void;
}

const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', description: 'Move to cloud without changes' },
  { value: 'replatform', label: 'Replatform (Lift & Reshape)', description: 'Minor optimizations for cloud' },
  { value: 'refactor', label: 'Refactor/Re-architect', description: 'Significant code changes for cloud-native' },
  { value: 'repurchase', label: 'Repurchase (SaaS)', description: 'Replace with SaaS solution' },
  { value: 'retire', label: 'Retire', description: 'Decommission the application' },
  { value: 'retain', label: 'Retain (Revisit)', description: 'Keep on-premises for now' }
];

export const SixRStrategyMatrix: React.FC<SixRStrategyMatrixProps> = ({
  decision,
  onDecisionChange
}) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Strategy Selection</span>
          </CardTitle>
          <CardDescription>
            Choose the appropriate modernization strategy for this application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="overall-strategy">Overall Strategy</Label>
            <Select
              value={decision.overall_strategy}
              onValueChange={(value) => onDecisionChange({ overall_strategy: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select strategy" />
              </SelectTrigger>
              <SelectContent>
                {SIX_R_STRATEGIES.map((strategy) => (
                  <SelectItem key={strategy.value} value={strategy.value}>
                    <div className="space-y-1">
                      <div className="font-medium">{strategy.label}</div>
                      <div className="text-xs text-gray-500">{strategy.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="rationale">Rationale</Label>
            <Textarea
              id="rationale"
              value={decision.rationale}
              onChange={(e) => onDecisionChange({ rationale: e.target.value })}
              placeholder="Explain why this strategy was chosen..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium">Confidence Score</Label>
              <div className="mt-1">
                <Badge variant={decision.confidence_score >= 0.8 ? "default" : "secondary"}>
                  {Math.round(decision.confidence_score * 100)}%
                </Badge>
              </div>
            </div>
            
            {decision.tech_debt_score !== undefined && (
              <div>
                <Label className="text-sm font-medium">Tech Debt Score</Label>
                <div className="mt-1">
                  <Badge variant={decision.tech_debt_score <= 40 ? "default" : "destructive"}>
                    {decision.tech_debt_score}/100
                  </Badge>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {decision.risk_factors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span>Risk Factors</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {decision.risk_factors.map((risk, index) => (
                <div key={index} className="p-2 bg-orange-50 border border-orange-200 rounded">
                  <p className="text-sm text-orange-700">{risk}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};