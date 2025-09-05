import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Clock, RefreshCw, ArrowRight } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';

import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/hooks/use-toast';
import { FLOW_PHASE_ROUTES } from '@/config/flowRoutes';

interface GapAnalysisData {
  identified_gaps: Array<{
    id: string;
    category: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    impact: string;
    recommended_action: string;
  }>;
  analysis_complete: boolean;
  completion_percentage: number;
  business_impact?: {
    risk_score: number;
    priority_areas: string[];
  };
}

interface CollectionFlowDetails {
  id: string;
  flow_id?: string;
  flow_name?: string;
  status: string;
  current_phase: string;
  progress: number;
  gap_analysis_results?: GapAnalysisData;
}

const GapAnalysis: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [flowDetails, setFlowDetails] = useState<CollectionFlowDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isContinuing, setIsContinuing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load flow details on mount
  useEffect(() => {
    if (!flowId) {
      setError('No flow ID provided');
      setIsLoading(false);
      return;
    }

    const loadFlowDetails = async () => {
      try {
        setIsLoading(true);
        // Get flow details from incomplete flows API
        const incompleteFlows = await collectionFlowApi.getIncompleteFlows();
        const flow = incompleteFlows.find(f => f.id === flowId);

        if (!flow) {
          throw new Error('Flow not found');
        }

        setFlowDetails(flow);
      } catch (err: any) {
        console.error('Failed to load flow details:', err);
        setError(err.message || 'Failed to load flow details');
      } finally {
        setIsLoading(false);
      }
    };

    loadFlowDetails();
  }, [flowId]);

  const handleContinueFlow = async () => {
    if (!flowId) return;

    try {
      setIsContinuing(true);
      await collectionFlowApi.continueFlow(flowId);

      // Get updated flow details
      const updatedFlows = await collectionFlowApi.getIncompleteFlows();
      const updatedFlow = updatedFlows.find(f => f.id === flowId);

      if (updatedFlow && updatedFlow.current_phase) {
        // Navigate to next phase
        const phaseRoute = FLOW_PHASE_ROUTES.collection[updatedFlow.current_phase];
        if (phaseRoute) {
          const route = phaseRoute(flowId);
          navigate(route);
          toast({
            title: "Proceeding to Next Phase",
            description: `Moving to ${updatedFlow.current_phase.replace('_', ' ')} phase...`,
            variant: "default"
          });
          return;
        }
      }

      // Fallback navigation
      navigate(`/collection/progress/${flowId}`);
    } catch (err: any) {
      console.error('Failed to continue flow:', err);
      toast({
        title: "Failed to Continue",
        description: err.message || "Failed to continue to next phase",
        variant: "destructive"
      });
    } finally {
      setIsContinuing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <CollectionPageLayout
        title="Gap Analysis"
        description="Analyzing data collection gaps..."
      >
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mr-2" />
          <span>Loading gap analysis...</span>
        </div>
      </CollectionPageLayout>
    );
  }

  if (error) {
    return (
      <CollectionPageLayout
        title="Gap Analysis"
        description="Data collection gap analysis"
      >
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Gap Analysis</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={() => navigate('/collection')}>
                Return to Collection
              </Button>
            </div>
          </CardContent>
        </Card>
      </CollectionPageLayout>
    );
  }

  const gapAnalysis = flowDetails?.gap_analysis_results;
  const isAnalysisComplete = gapAnalysis?.analysis_complete ?? false;
  const gaps = gapAnalysis?.identified_gaps ?? [];
  const completionPercentage = gapAnalysis?.completion_percentage ?? 0;

  return (
    <CollectionPageLayout
      title="Gap Analysis"
      description={`Analyzing data collection gaps for ${flowDetails?.flow_name || 'collection flow'}`}
    >
      <div className="space-y-6">
        {/* Status Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              {isAnalysisComplete ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              ) : (
                <Clock className="w-5 h-5 text-orange-600 mr-2" />
              )}
              Gap Analysis Status
            </CardTitle>
            <CardDescription>
              Flow: {flowDetails?.flow_name || flowDetails?.flow_id} | Status: {flowDetails?.status}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Analysis Progress</span>
                  <span className="text-sm text-gray-600">{completionPercentage}%</span>
                </div>
                <Progress value={completionPercentage} className="w-full" />
              </div>

              {gapAnalysis?.business_impact && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-2">Business Impact Assessment</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-blue-600">Risk Score:</span>
                      <span className="ml-2 font-medium">{gapAnalysis.business_impact.risk_score}/10</span>
                    </div>
                    <div>
                      <span className="text-blue-600">Priority Areas:</span>
                      <span className="ml-2 font-medium">
                        {gapAnalysis.business_impact.priority_areas.join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Identified Gaps */}
        {gaps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Identified Data Gaps ({gaps.length})</CardTitle>
              <CardDescription>
                Areas where additional data collection is needed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {gaps.map((gap, index) => (
                  <div key={gap.id || index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <Badge className={getSeverityColor(gap.severity)}>
                            {gap.severity.toUpperCase()}
                          </Badge>
                          <span className="ml-2 font-medium text-gray-900">
                            {gap.category}
                          </span>
                        </div>
                        <p className="text-gray-700 mb-2">{gap.description}</p>
                        {gap.impact && (
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Impact:</strong> {gap.impact}
                          </p>
                        )}
                        {gap.recommended_action && (
                          <p className="text-sm text-blue-600">
                            <strong>Recommended Action:</strong> {gap.recommended_action}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* No Gaps Found */}
        {gaps.length === 0 && isAnalysisComplete && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Critical Gaps Identified
                </h3>
                <p className="text-gray-600">
                  The gap analysis found no significant data collection gaps.
                  You can proceed to the next phase of collection.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis In Progress */}
        {!isAnalysisComplete && completionPercentage < 100 && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <RefreshCw className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Gap Analysis In Progress
                </h3>
                <p className="text-gray-600">
                  Analyzing collected data to identify gaps and areas needing additional information...
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => navigate(`/collection/progress/${flowId}`)}
          >
            View Progress
          </Button>

          {isAnalysisComplete && (
            <Button
              onClick={handleContinueFlow}
              disabled={isContinuing}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isContinuing ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4 mr-2" />
              )}
              Continue to Next Phase
            </Button>
          )}
        </div>
      </div>
    </CollectionPageLayout>
  );
};

export default GapAnalysis;
