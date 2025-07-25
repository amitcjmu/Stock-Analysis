import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock } from 'lucide-react';

interface ResultsTabProps {
  flowState: unknown;
}

export const ResultsTab: React.FC<ResultsTabProps> = ({ flowState }) => (
  <>
    {flowState?.processing_summary ? (
      <Card>
        <CardHeader>
          <CardTitle>Processing Summary</CardTitle>
          <CardDescription>Complete results from all crews</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {flowState.processing_summary.total_records_processed || 0}
              </p>
              <p className="text-sm text-gray-600">Records Processed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {flowState.processing_summary.assets_created || 0}
              </p>
              <p className="text-sm text-gray-600">Assets Created</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {((flowState.processing_summary.data_quality_score || 0) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Quality Score</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {flowState.processing_summary.crews_executed || 0}
              </p>
              <p className="text-sm text-gray-600">Crews Executed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    ) : (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <Clock className="h-8 w-8 mx-auto mb-2" />
            <p>Results will appear here once crews complete their work</p>
          </div>
        </CardContent>
      </Card>
    )}
  </>
);
