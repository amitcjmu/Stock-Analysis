/**
 * Patterns Tab Component
 * Displays activity patterns and seasonal trends
 */

import React from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { TrendIndicator } from '../components';
import type { AnalyticsData } from '../types';

interface PatternsTabProps {
  patternAnalysis: AnalyticsData['patternAnalysis'];
}

const PatternsTab: React.FC<PatternsTabProps> = ({ patternAnalysis }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Peak Hours */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Activity Patterns</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={patternAnalysis.peakHours}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="activity" 
                  stroke="#3b82f6" 
                  fill="#3b82f6" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Weekly Patterns */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Performance Patterns</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={patternAnalysis.weeklyPatterns}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="averagePerformance" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Seasonal Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Seasonal Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {patternAnalysis.seasonalTrends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">{trend.period}</span>
                <div className="flex items-center gap-2">
                  <TrendIndicator trend={trend.trend} rate={trend.magnitude} />
                  <span className="text-sm text-gray-600">
                    {trend.magnitude.toFixed(1)}% change
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PatternsTab;