/**
 * Anomalies Tab Component
 * Displays detected anomalies and outliers
 */

import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { AnomalyCard } from '../components';
import type { AnalyticsData } from '../types';

interface AnomaliesTabProps {
  anomalies: AnalyticsData['predictiveInsights']['anomalies'];
}

const AnomaliesTab: React.FC<AnomaliesTabProps> = ({ anomalies }) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Detected Anomalies</CardTitle>
          <p className="text-sm text-gray-600">
            Unusual patterns and outliers in agent performance
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {anomalies.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-gray-500">No anomalies detected</p>
                <p className="text-gray-400 text-sm">No agent performance anomalies found in historical data</p>
              </div>
            ) : (
              anomalies.map((anomaly, index) => (
                <AnomalyCard key={index} anomaly={anomaly} />
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnomaliesTab;
