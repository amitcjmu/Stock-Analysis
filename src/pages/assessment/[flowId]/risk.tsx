import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Shield,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'minimal';

interface RiskFactor {
  id: string;
  category: string;
  description: string;
  severity: RiskLevel;
  impact: string;
  mitigation?: string;
}

const RiskAssessmentPage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const navigate = useNavigate();
  const { state, resumeFlow } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate('/assess/overview', { replace: true });
    }
  }, [flowId, navigate]);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplicationIds[0]);
    }
  }, [state.selectedApplicationIds, selectedApp]);

  // Extract risk factors from 6R decisions
  const currentAppRisks: RiskFactor[] = useMemo(() => {
    if (!selectedApp || !state.sixrDecisions[selectedApp]) {
      return [];
    }

    const decision = state.sixrDecisions[selectedApp];
    const risks: RiskFactor[] = decision.risk_factors?.map((risk, index) => ({
      id: `risk-${index}`,
      category: 'Migration Risk',
      description: risk,
      severity: inferRiskSeverity(risk),
      impact: 'Migration timeline and success',
      mitigation: 'Review and address before migration',
    })) || [];

    return risks;
  }, [selectedApp, state.sixrDecisions]);

  // Calculate risk statistics
  const riskStats = useMemo(() => {
    const stats = {
      total: currentAppRisks.length,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      minimal: 0,
    };

    currentAppRisks.forEach(risk => {
      stats[risk.severity]++;
    });

    return stats;
  }, [currentAppRisks]);

  // Overall risk level
  const overallRisk: RiskLevel = useMemo(() => {
    if (riskStats.critical > 0) return 'critical';
    if (riskStats.high >= 3) return 'high';
    if (riskStats.high > 0 || riskStats.medium >= 5) return 'medium';
    if (riskStats.medium > 0 || riskStats.low > 0) return 'low';
    return 'minimal';
  }, [riskStats]);

  // Infer severity from risk description keywords
  function inferRiskSeverity(risk: string): RiskLevel {
    const lowerRisk = risk.toLowerCase();
    if (lowerRisk.includes('critical') || lowerRisk.includes('blocker')) return 'critical';
    if (lowerRisk.includes('high') || lowerRisk.includes('major')) return 'high';
    if (lowerRisk.includes('medium') || lowerRisk.includes('moderate')) return 'medium';
    if (lowerRisk.includes('low') || lowerRisk.includes('minor')) return 'low';
    return 'medium'; // Default to medium if no keywords found
  }

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // Handle submit
  const handleSubmit = async (): void => {
    setIsSubmitting(true);
    try {
      await resumeFlow({
        phase: 'risk_assessment',
        action: 'continue',
      });

      // Navigate to 6R recommendations
      navigate(`/assessment/${flowId}/sixr-review`);
    } catch (error) {
      console.error('Failed to proceed to 6R recommendations:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRiskLevelColor = (level: RiskLevel): string => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'minimal':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getRiskIcon = (level: RiskLevel) => {
    switch (level) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'medium':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      case 'low':
        return <AlertCircle className="h-5 w-5 text-blue-600" />;
      case 'minimal':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    }
  };

  // CC: Fixed bug - check selectedApplications (populated) not selectedApplicationIds (may be empty)
  // Bug #640 fix: Improved guard to check loading state before showing error
  if (state.selectedApplications.length === 0) {
    if (state.isLoading) {
      return <div className="p-6 text-sm text-muted-foreground">Loading application data...</div>;
    }

    return (
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 text-center">
          <AlertCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Applications Selected</h2>
          <p className="text-gray-600">
            Please return to the previous step to select applications for analysis.
          </p>
        </div>
      </AssessmentFlowLayout>
    );
  }

  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">Risk Assessment</h1>
          <p className="text-gray-600">
            Review migration risks and mitigation strategies for selected applications
          </p>
        </div>

        {/* Status Alert */}
        {state.status === 'error' && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        )}

        {state.status === 'processing' && (
          <Alert>
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertTitle>Processing</AlertTitle>
            <AlertDescription>
              AI agents are analyzing migration risks...
            </AlertDescription>
          </Alert>
        )}

        {/* Real-time Progress */}
        {state.status === 'processing' && (
          <RealTimeProgressIndicator
            agentUpdates={state.agentUpdates}
            currentPhase="risk_assessment"
          />
        )}

        {/* Application Selection */}
        <ApplicationTabs
          applications={state.selectedApplicationIds}
          selectedApp={selectedApp}
          onAppSelect={setSelectedApp}
          getApplicationName={(appId) => {
            const app = state.selectedApplications.find(a => a.application_id === appId);
            return app?.application_name || appId;
          }}
        />

        {selectedApp && (
          <>
            {/* Overall Risk Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-5 w-5" />
                  <span>Overall Risk Assessment</span>
                </CardTitle>
                <CardDescription>Summary for {state.selectedApplications.find(a => a.application_id === selectedApp)?.application_name || selectedApp}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Overall Risk Badge */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getRiskIcon(overallRisk)}
                      <div>
                        <div className="font-semibold text-gray-900">Overall Risk Level</div>
                        <div className="text-sm text-gray-600">
                          Based on {riskStats.total} identified risk factors
                        </div>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={cn('px-4 py-2 text-base', getRiskLevelColor(overallRisk))}
                    >
                      {overallRisk.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Risk Statistics */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{riskStats.total}</div>
                      <div className="text-sm text-gray-600">Total Risks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{riskStats.critical}</div>
                      <div className="text-sm text-gray-600">Critical</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{riskStats.high}</div>
                      <div className="text-sm text-gray-600">High</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{riskStats.medium}</div>
                      <div className="text-sm text-gray-600">Medium</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{riskStats.low}</div>
                      <div className="text-sm text-gray-600">Low</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk Factors List */}
            <Card>
              <CardHeader>
                <CardTitle>Identified Risk Factors</CardTitle>
                <CardDescription>
                  Detailed breakdown of migration risks and recommended mitigations
                </CardDescription>
              </CardHeader>
              <CardContent>
                {currentAppRisks.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-2" />
                    <p>No significant risks identified for this application</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {currentAppRisks.map(risk => (
                      <div
                        key={risk.id}
                        className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex-shrink-0 mt-1">{getRiskIcon(risk.severity)}</div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-gray-900">{risk.category}</span>
                            <Badge
                              variant="outline"
                              className={cn('text-xs', getRiskLevelColor(risk.severity))}
                            >
                              {risk.severity.toUpperCase()}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-700">{risk.description}</p>
                          <div className="text-xs text-gray-500">
                            <strong>Impact:</strong> {risk.impact}
                          </div>
                          {risk.mitigation && (
                            <div className="text-xs text-blue-600 mt-2">
                              <strong>Mitigation:</strong> {risk.mitigation}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end items-center pt-6 border-t border-gray-200">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading}
            size="lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Continue to 6R Recommendations
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </AssessmentFlowLayout>
  );
};

export default RiskAssessmentPage;
