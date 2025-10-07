import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, ArrowRight, Download, BarChart3, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

/**
 * Collection Summary Page
 * Displays completion summary and provides navigation to assessment flow
 * Per ADR-012: Collection flows automatically transition to assessment when complete
 */
const CollectionSummary: React.FC = () => {
  const navigate = useNavigate();
  const { flowId } = useParams<{ flowId: string }>();

  // Fetch flow details
  const { data: flow, isLoading, error } = useQuery({
    queryKey: ['collectionFlow', flowId],
    queryFn: () => collectionFlowApi.getFlow(flowId!),
    enabled: !!flowId,
  });

  // Fetch readiness status to check for assessment flow
  const { data: readiness } = useQuery({
    queryKey: ['collectionReadiness', flowId],
    queryFn: () => collectionFlowApi.checkReadiness(flowId!),
    enabled: !!flowId,
  });

  if (isLoading) {
    return (
      <CollectionPageLayout title="Collection Summary">
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading summary...</div>
        </div>
      </CollectionPageLayout>
    );
  }

  if (error || !flow) {
    return (
      <CollectionPageLayout title="Collection Summary">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load collection flow summary. Please try again or contact support.
          </AlertDescription>
        </Alert>
      </CollectionPageLayout>
    );
  }

  const assessmentFlowId = readiness?.assessment_flow_id;

  return (
    <CollectionPageLayout title="Collection Complete">
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="p-4 bg-green-100 rounded-full">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
          </div>

          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Collection Complete!
            </h1>
            <p className="text-lg text-gray-600">
              Your application data has been successfully collected and is ready for assessment.
            </p>
          </div>
        </div>

        {/* Summary Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Collection Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{flow.total_applications || 0}</div>
                <div className="text-sm text-gray-600">Applications Collected</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{flow.completed_questionnaires || 0}</div>
                <div className="text-sm text-gray-600">Questionnaires Completed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">{flow.data_points_collected || 0}</div>
                <div className="text-sm text-gray-600">Data Points Collected</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-600">
                  {readiness?.is_assessment_ready ? '100%' : `${Math.round((readiness?.completion_percentage || 0))}%`}
                </div>
                <div className="text-sm text-gray-600">Completion</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Assessment Transition Info */}
        {assessmentFlowId && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-900">Assessment Flow Created</CardTitle>
              <CardDescription className="text-green-700">
                Your collection data has been automatically transitioned to an assessment flow
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-gray-700">Assessment flow initialized successfully</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-gray-700">Data transferred and validated</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-gray-700">Ready for SIXR analysis</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              Your collection data is now ready for the assessment phase
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">1</span>
                </div>
                <div>
                  <p className="font-medium">Assessment Analysis</p>
                  <p className="text-sm text-gray-600">Review SIXR recommendations and architecture standards</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">2</span>
                </div>
                <div>
                  <p className="font-medium">Migration Planning</p>
                  <p className="text-sm text-gray-600">Create detailed migration plans based on assessment</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">3</span>
                </div>
                <div>
                  <p className="font-medium">Wave Planning</p>
                  <p className="text-sm text-gray-600">Organize applications into migration waves</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <Button
            variant="outline"
            onClick={() => navigate('/collection')}
          >
            Back to Collection
          </Button>

          <Button
            variant="outline"
            onClick={() => {
              // TODO: Implement report download
              console.log('Download report for flow:', flowId);
            }}
          >
            <Download className="h-4 w-4 mr-2" />
            Download Report
          </Button>

          {assessmentFlowId && (
            <Button
              size="lg"
              onClick={() => navigate(`/assessment/${assessmentFlowId}/sixr-review`)}
            >
              Continue to Assessment
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </CollectionPageLayout>
  );
};

export default CollectionSummary;
