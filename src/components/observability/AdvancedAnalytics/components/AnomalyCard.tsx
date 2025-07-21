/**
 * Anomaly Card Component
 * Displays detected anomalies with severity and details
 */

import React from 'react';
import { format } from 'date-fns';
import { Badge } from '../../../ui/badge';
import { AnalyticsData } from '../types';

interface AnomalyCardProps {
  anomaly: AnalyticsData['predictiveInsights']['anomalies'][0];
}

const AnomalyCard: React.FC<AnomalyCardProps> = ({ anomaly }) => {
  const severityColors = {
    low: 'border-l-yellow-400 bg-yellow-50',
    medium: 'border-l-orange-400 bg-orange-50',
    high: 'border-l-red-400 bg-red-50'
  };

  const deviation = ((anomaly.value - anomaly.expectedValue) / anomaly.expectedValue) * 100;

  return (
    <div className={`border-l-4 p-3 rounded-r-md ${severityColors[anomaly.severity]}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm">{anomaly.agentName}</span>
        <Badge variant={anomaly.severity === 'high' ? 'destructive' : 'secondary'} className="text-xs">
          {anomaly.severity}
        </Badge>
      </div>
      <div className="text-sm text-gray-700">
        {anomaly.metric}: {anomaly.value.toFixed(2)} (expected: {anomaly.expectedValue.toFixed(2)})
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {deviation > 0 ? '+' : ''}{deviation.toFixed(1)}% deviation at {format(new Date(anomaly.timestamp), 'MMM dd, HH:mm')}
      </div>
    </div>
  );
};

export default AnomalyCard;