/**
 * Correlations Tab Component
 * Displays metric correlation analysis
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { CorrelationHeatmap } from '../components';
import { AnalyticsData } from '../types';

interface CorrelationsTabProps {
  correlationMatrix: AnalyticsData['correlationMatrix'];
}

const CorrelationsTab: React.FC<CorrelationsTabProps> = ({ correlationMatrix }) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Metric Correlation Matrix</CardTitle>
          <p className="text-sm text-gray-600">
            Shows how different performance metrics correlate with each other
          </p>
        </CardHeader>
        <CardContent>
          <CorrelationHeatmap correlationMatrix={correlationMatrix} />
          <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded" />
              Positive correlation
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-500 rounded" />
              Negative correlation
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-gray-300 rounded" />
              No correlation
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CorrelationsTab;