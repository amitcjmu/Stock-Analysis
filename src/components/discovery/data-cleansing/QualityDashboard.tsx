import React from 'react';
import { Target } from 'lucide-react'
import { CheckCircle, AlertTriangle, XCircle, TrendingUp, Database } from 'lucide-react'

interface QualityMetrics {
  total_assets: number;
  clean_data: number;
  needs_attention: number;
  critical_issues: number;
  completion_percentage: number;
  average_quality: number;
}

interface QualityDashboardProps {
  metrics: QualityMetrics;
  isLoading?: boolean;
}

const QualityDashboard: React.FC<QualityDashboardProps> = ({ metrics, isLoading = false }) => {
  const getQualityColor = (percentage: number) => {
    if (percentage >= 85) return 'text-green-600 bg-green-100';
    if (percentage >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 85) return 'bg-green-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-2"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="mb-8">
      {/* Quality Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{metrics.total_assets}</h3>
              <p className="text-xs text-gray-600">Total Assets</p>
            </div>
            <Database className="h-6 w-6 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-green-600">{metrics.clean_data}</h3>
              <p className="text-xs text-gray-600">Clean Data</p>
            </div>
            <CheckCircle className="h-6 w-6 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-yellow-600">{metrics.needs_attention}</h3>
              <p className="text-xs text-gray-600">Needs Attention</p>
            </div>
            <AlertTriangle className="h-6 w-6 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-red-600">{metrics.critical_issues}</h3>
              <p className="text-xs text-gray-600">Critical Issues</p>
            </div>
            <XCircle className="h-6 w-6 text-red-500" />
          </div>
        </div>
      </div>

      {/* Quality Progress */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900">Data Quality Progress</h2>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 text-sm rounded-full ${getQualityColor(metrics.average_quality)}`}>
              {Math.round(metrics.average_quality)}% Quality Score
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">Overall Data Quality</span>
            <span className="font-medium text-gray-900">{Math.round(metrics.completion_percentage)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(metrics.completion_percentage)}`}
              style={{ width: `${metrics.completion_percentage}%` }}
            />
          </div>
        </div>

        {/* Quality Distribution */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {Math.round((metrics.clean_data / metrics.total_assets) * 100)}%
            </div>
            <div className="text-sm text-green-700">Ready for Migration</div>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {Math.round((metrics.needs_attention / metrics.total_assets) * 100)}%
            </div>
            <div className="text-sm text-yellow-700">Needs Review</div>
          </div>
          <div className="p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {Math.round((metrics.critical_issues / metrics.total_assets) * 100)}%
            </div>
            <div className="text-sm text-red-700">Critical Issues</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QualityDashboard; 