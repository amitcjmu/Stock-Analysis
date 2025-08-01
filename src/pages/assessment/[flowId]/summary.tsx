import React from 'react';
import type { GetServerSideProps } from 'next/router';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, ArrowRight, Download, BarChart3 } from 'lucide-react';

interface SummaryPageProps {
  flowId: string;
}

const SummaryPage: React.FC<SummaryPageProps> = ({ flowId }) => {
  const { state } = useAssessmentFlow(flowId);

  const completedApps = Object.keys(state.sixrDecisions).length;
  const totalApps = state.selectedApplicationIds.length;
  const isComplete = completedApps === totalApps;

  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="p-4 bg-green-100 rounded-full">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
          </div>

          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Assessment Complete!
            </h1>
            <p className="text-lg text-gray-600">
              Your application assessment has been successfully completed and is ready for migration planning.
            </p>
          </div>
        </div>

        {/* Summary Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Assessment Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{totalApps}</div>
                <div className="text-sm text-gray-600">Applications Assessed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{completedApps}</div>
                <div className="text-sm text-gray-600">Strategies Defined</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">{state.appsReadyForPlanning.length}</div>
                <div className="text-sm text-gray-600">Ready for Planning</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-600">{state.engagementStandards.length}</div>
                <div className="text-sm text-gray-600">Architecture Standards</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              Your assessment data is now ready for the migration planning phase
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">1</span>
                </div>
                <div>
                  <p className="font-medium">Migration Planning</p>
                  <p className="text-sm text-gray-600">Use assessment data to create detailed migration plans</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">2</span>
                </div>
                <div>
                  <p className="font-medium">Wave Planning</p>
                  <p className="text-sm text-gray-600">Organize applications into migration waves based on dependencies</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">3</span>
                </div>
                <div>
                  <p className="font-medium">Execution Planning</p>
                  <p className="text-sm text-gray-600">Create detailed execution plans for each migration wave</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download Report
          </Button>

          <Button size="lg">
            Continue to Planning
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </AssessmentFlowLayout>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export { getServerSideProps } from './utils';

export default SummaryPage;
