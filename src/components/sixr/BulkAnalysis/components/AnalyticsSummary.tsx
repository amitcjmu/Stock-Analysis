import React from 'react';
import { 
  TrendingUp, 
  Users, 
  Target, 
  Clock,
  BarChart3,
  PieChart
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../ui/card';
import { Progress } from '../../../ui/progress';
import { Badge } from '../../../ui/badge';
import { BulkAnalysisSummary } from '../types';
import { formatDuration, strategyColors } from '../utils/analysisUtils';

interface AnalyticsSummaryProps {
  summary: BulkAnalysisSummary;
}

export const AnalyticsSummary: React.FC<AnalyticsSummaryProps> = ({
  summary
}) => {
  const successRate = summary.total_jobs > 0 
    ? ((summary.completed_jobs / summary.total_jobs) * 100) 
    : 0;

  const strategyEntries = Object.entries(summary.strategy_distribution)
    .sort(([,a], [,b]) => b - a);

  const totalStrategies = Object.values(summary.strategy_distribution)
    .reduce((sum, count) => sum + count, 0);

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Total Jobs</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_jobs}</div>
            <div className="text-sm text-gray-600">
              {summary.active_jobs} active, {summary.completed_jobs} completed
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Target className="h-4 w-4" />
              <span>Success Rate</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{successRate.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">
              {summary.failed_jobs} failed jobs
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span>Avg Confidence</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {(summary.average_confidence * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">
              Across {summary.total_applications_processed} apps
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>Avg Processing Time</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {summary.processing_time_stats.average.toFixed(1)}s
            </div>
            <div className="text-sm text-gray-600">
              Range: {summary.processing_time_stats.min.toFixed(1)}s - {summary.processing_time_stats.max.toFixed(1)}s
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Processing Time Analytics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Processing Time Statistics</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Processing Time</span>
                <span className="text-sm text-gray-600">
                  {formatDuration(summary.processing_time_stats.total / 60)}
                </span>
              </div>
              <Progress value={100} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Average Time</span>
                <span className="text-sm text-gray-600">
                  {summary.processing_time_stats.average.toFixed(1)}s
                </span>
              </div>
              <Progress 
                value={(summary.processing_time_stats.average / summary.processing_time_stats.max) * 100} 
                className="h-2" 
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Performance Index</span>
                <span className="text-sm text-gray-600">
                  {summary.processing_time_stats.min > 0 
                    ? (summary.processing_time_stats.min / summary.processing_time_stats.average * 100).toFixed(0)
                    : 0
                  }%
                </span>
              </div>
              <Progress 
                value={summary.processing_time_stats.min > 0 
                  ? (summary.processing_time_stats.min / summary.processing_time_stats.average) * 100
                  : 0
                } 
                className="h-2" 
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PieChart className="h-5 w-5" />
            <span>Strategy Distribution</span>
          </CardTitle>
          <CardDescription>
            Distribution of recommended migration strategies across all analyzed applications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {strategyEntries.length === 0 ? (
            <div className="text-center py-8">
              <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Strategy Data</h3>
              <p className="text-gray-600">No migration strategies have been recommended yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {strategyEntries.map(([strategy, count]) => {
                const percentage = totalStrategies > 0 ? (count / totalStrategies) * 100 : 0;
                
                return (
                  <div key={strategy} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Badge className={strategyColors[strategy] || 'bg-gray-100 text-gray-800'}>
                          {strategy}
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {count} applications
                        </span>
                      </div>
                      <span className="text-sm font-medium">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Job Status Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{summary.active_jobs}</div>
              <div className="text-sm text-gray-600">Active Jobs</div>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">{summary.completed_jobs}</div>
              <div className="text-sm text-gray-600">Completed Jobs</div>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-red-600">{summary.failed_jobs}</div>
              <div className="text-sm text-gray-600">Failed Jobs</div>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{summary.total_applications_processed}</div>
              <div className="text-sm text-gray-600">Apps Processed</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};