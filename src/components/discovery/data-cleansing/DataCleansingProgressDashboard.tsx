import React from 'react';
import { Database, Activity, CheckCircle, XCircle } from 'lucide-react';

interface DataCleansingProgress {
  total_records: number;
  cleaned_records: number;
  quality_score: number;
  completion_percentage: number;
  issues_resolved: number;
  issues_found?: number;
  crew_completion_status: Record<string, boolean>;
}

interface DataCleansingProgressDashboardProps {
  progress: DataCleansingProgress;
  isLoading?: boolean;
}

const DataCleansingProgressDashboard: React.FC<DataCleansingProgressDashboardProps> = ({
  progress,
  isLoading = false
}) => {
  const getQualityScoreColor = (score: number): unknown => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow-md animate-pulse">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="h-8 w-8 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Records */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Total Records</p>
            <p className="text-2xl font-bold text-gray-900">{progress.total_records}</p>
          </div>
          <Database className="h-8 w-8 text-blue-600" />
        </div>
      </div>

      {/* Quality Score */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Quality Score</p>
            <p className="text-2xl font-bold text-gray-900">{progress.quality_score}%</p>
          </div>
          <Activity className={`h-8 w-8 ${getQualityScoreColor(progress.quality_score)}`} />
        </div>
      </div>

      {/* Issues Found */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Issues Found</p>
            <p className="text-2xl font-bold text-gray-900">{progress.issues_found ?? 0}</p>
            <p className="text-xs text-gray-500">{progress.issues_resolved} resolved</p>
          </div>
          <XCircle className="h-8 w-8 text-red-600" />
        </div>
      </div>

      {/* Completion */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Completion</p>
            <p className="text-2xl font-bold text-gray-900">{progress.completion_percentage}%</p>
          </div>
          <CheckCircle className="h-8 w-8 text-green-600" />
        </div>
      </div>
    </div>
  );
};

export default DataCleansingProgressDashboard;
