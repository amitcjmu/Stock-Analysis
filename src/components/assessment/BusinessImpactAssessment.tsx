import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Progress } from '@/components/ui/progress';
import type { SixRDecision } from '@/hooks/useAssessmentFlow'
import { TechDebtItem } from '@/hooks/useAssessmentFlow'
import { TrendingUp, DollarSign, Clock, Users } from 'lucide-react';

interface BusinessImpactAssessmentProps {
  decision: SixRDecision;
  techDebt: TechDebtItem[];
  printMode?: boolean;
}

export const BusinessImpactAssessment: React.FC<BusinessImpactAssessmentProps> = ({
  decision,
  techDebt,
  printMode = false
}) => {
  // Calculate business impact metrics
  const totalEffort = techDebt.reduce((sum, t) => sum + (t.remediation_effort_hours || 0), 0);
  const avgTechDebtScore = techDebt.length > 0 ? 
    techDebt.reduce((sum, t) => sum + (t.tech_debt_score || 0), 0) / techDebt.length : 0;

  // Estimate business impact based on strategy and tech debt
  const getBusinessImpact = () => {
    const strategyImpact: Record<string, { effort: string; risk: string; value: string }> = {
      'rehost': { effort: 'Low', risk: 'Low', value: 'Medium' },
      'replatform': { effort: 'Medium', risk: 'Medium', value: 'High' },
      'refactor': { effort: 'High', risk: 'High', value: 'Very High' },
      'repurchase': { effort: 'Medium', risk: 'Medium', value: 'High' },
      'retire': { effort: 'Low', risk: 'Low', value: 'High' },
      'retain': { effort: 'Very Low', risk: 'Very Low', value: 'Low' }
    };
    
    return strategyImpact[decision.overall_strategy] || { effort: 'Unknown', risk: 'Unknown', value: 'Unknown' };
  };

  const businessImpact = getBusinessImpact();

  const getImpactColor = (impact: string) => {
    const colors: Record<string, string> = {
      'Very Low': 'text-green-600',
      'Low': 'text-green-600',
      'Medium': 'text-yellow-600',
      'High': 'text-orange-600',
      'Very High': 'text-red-600'
    };
    return colors[impact] || 'text-gray-600';
  };

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5" />
          <span>Business Impact Assessment</span>
        </CardTitle>
        <CardDescription>
          Analysis of business value, effort, and risk factors for the chosen strategy
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Impact Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <Clock className="h-6 w-6 mx-auto text-blue-600 mb-2" />
            <div className={`text-lg font-bold ${getImpactColor(businessImpact.effort)}`}>
              {businessImpact.effort}
            </div>
            <div className="text-sm text-gray-600">Migration Effort</div>
          </div>

          <div className="text-center p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <Users className="h-6 w-6 mx-auto text-orange-600 mb-2" />
            <div className={`text-lg font-bold ${getImpactColor(businessImpact.risk)}`}>
              {businessImpact.risk}
            </div>
            <div className="text-sm text-gray-600">Business Risk</div>
          </div>

          <div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
            <DollarSign className="h-6 w-6 mx-auto text-green-600 mb-2" />
            <div className={`text-lg font-bold ${getImpactColor(businessImpact.value)}`}>
              {businessImpact.value}
            </div>
            <div className="text-sm text-gray-600">Business Value</div>
          </div>
        </div>

        {/* Effort Breakdown */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Effort Breakdown</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Technical Debt Remediation</span>
              <span className="font-medium">{totalEffort} hours</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Migration Complexity</span>
              <Badge variant="outline">
                {decision.component_treatments.length} components
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Architecture Changes</span>
              <Badge variant="outline">
                {decision.architecture_exceptions.length} exceptions
              </Badge>
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Risk Factors</h4>
          {decision.risk_factors.length === 0 ? (
            <p className="text-sm text-green-600">No significant risks identified</p>
          ) : (
            <div className="space-y-2">
              {decision.risk_factors.map((risk, index) => (
                <div key={index} className="p-2 bg-orange-50 border border-orange-200 rounded text-sm">
                  <span className="text-orange-700">• {risk}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Value Proposition */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Value Proposition</h4>
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700">
              {decision.overall_strategy === 'rehost' && 
                "Quick migration with immediate cloud benefits including cost savings and improved reliability."}
              {decision.overall_strategy === 'replatform' && 
                "Balanced approach with moderate effort for significant cloud-native benefits and improved performance."}
              {decision.overall_strategy === 'refactor' && 
                "High investment with maximum modernization benefits including scalability, maintainability, and innovation enablement."}
              {decision.overall_strategy === 'repurchase' && 
                "Replace with modern SaaS solution to reduce operational overhead and gain advanced features."}
              {decision.overall_strategy === 'retire' && 
                "Eliminate application complexity and reduce operational costs by decommissioning unused functionality."}
              {decision.overall_strategy === 'retain' && 
                "Maintain current state while planning future modernization strategy based on business priorities."}
            </p>
          </div>
        </div>

        {/* Success Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Success Metrics</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Confidence Score:</span>
              <span className="font-medium">{Math.round(decision.confidence_score * 100)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tech Debt Score:</span>
              <span className="font-medium">{Math.round(avgTechDebtScore)}/100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Components Analyzed:</span>
              <span className="font-medium">{decision.component_treatments.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Compatibility Validated:</span>
              <span className="font-medium">
                {decision.component_treatments.filter(ct => ct.compatibility_validated).length}/
                {decision.component_treatments.length}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};