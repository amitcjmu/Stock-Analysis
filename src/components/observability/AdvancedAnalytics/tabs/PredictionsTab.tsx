/**
 * Predictions Tab Component
 * Displays forecasts and predictive analytics
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { METRIC_CONFIGS } from '../constants';
import type { AnalyticsData } from '../types';

interface PredictionsTabProps {
  forecasts: AnalyticsData['predictiveInsights']['forecasts'];
  showPredictions: boolean;
}

const PredictionsTab: React.FC<PredictionsTabProps> = ({ forecasts, showPredictions }) => {
  if (!showPredictions) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Predictions are disabled</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {forecasts.slice(0, 4).map((forecast) => (
          <Card key={forecast.metric}>
            <CardHeader>
              <CardTitle className="text-sm">
                {METRIC_CONFIGS.find(m => m.key === forecast.metric)?.label || forecast.metric} Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={forecast.predictions}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#8b5cf6" 
                    strokeDasharray="5 5"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="confidence" 
                    stroke="#f59e0b" 
                    strokeWidth={1}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default PredictionsTab;