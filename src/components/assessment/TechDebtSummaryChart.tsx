import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { TechDebtItem } from '@/hooks/useAssessmentFlow';
import { AlertTriangle, BarChart3 } from 'lucide-react';

interface TechDebtSummaryChartProps {
  techDebt: TechDebtItem[];
  detailed?: boolean;
  printMode?: boolean;
}

export const TechDebtSummaryChart: React.FC<TechDebtSummaryChartProps> = ({
  techDebt,
  detailed = false,
  printMode = false
}) => {
  const severityStats = {
    critical: techDebt.filter(t => t.severity === 'critical').length,
    high: techDebt.filter(t => t.severity === 'high').length,
    medium: techDebt.filter(t => t.severity === 'medium').length,
    low: techDebt.filter(t => t.severity === 'low').length
  };

  const totalEffort = techDebt.reduce((sum, t) => sum + (t.remediation_effort_hours || 0), 0);
  const avgScore = techDebt.length > 0 ?
    techDebt.reduce((sum, t) => sum + (t.tech_debt_score || 0), 0) / techDebt.length : 0;

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      'critical': 'bg-red-100 text-red-700 border-red-200',
      'high': 'bg-orange-100 text-orange-700 border-orange-200',
      'medium': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      'low': 'bg-blue-100 text-blue-700 border-blue-200'
    };
    return colors[severity] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Technical Debt Analysis</span>
        </CardTitle>
        <CardDescription>
          Summary of technical debt issues and remediation efforts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{techDebt.length}</div>
            <div className="text-sm text-gray-600">Total Issues</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{totalEffort}h</div>
            <div className="text-sm text-gray-600">Total Effort</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.round(avgScore)}</div>
            <div className="text-sm text-gray-600">Avg Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{severityStats.critical}</div>
            <div className="text-sm text-gray-600">Critical</div>
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Severity Breakdown</h4>
          <div className="space-y-2">
            {Object.entries(severityStats).map(([severity, count]) => (
              <div key={severity} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Badge className={getSeverityColor(severity)}>
                    {severity.charAt(0).toUpperCase() + severity.slice(1)}
                  </Badge>
                  <span className="text-sm text-gray-600">{count} issues</span>
                </div>
                <div className="flex-1 mx-4">
                  <Progress
                    value={techDebt.length > 0 ? (count / techDebt.length) * 100 : 0}
                    className="h-2"
                  />
                </div>
                <span className="text-sm font-medium">
                  {techDebt.length > 0 ? Math.round((count / techDebt.length) * 100) : 0}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Detailed View */}
        {detailed && techDebt.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Detailed Issues</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {techDebt.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900">{item.category}</h5>
                    <Badge className={getSeverityColor(item.severity)}>
                      {item.severity}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{item.description}</p>

                  <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
                    <div>
                      <span className="font-medium">Effort:</span> {item.remediation_effort_hours || 0}h
                    </div>
                    <div>
                      <span className="font-medium">Score:</span> {item.tech_debt_score || 0}/100
                    </div>
                  </div>

                  {item.impact_on_migration && (
                    <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded">
                      <p className="text-xs text-orange-700">
                        <strong>Migration Impact:</strong> {item.impact_on_migration}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {techDebt.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p>No technical debt issues identified</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
