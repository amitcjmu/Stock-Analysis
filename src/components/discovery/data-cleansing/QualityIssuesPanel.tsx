import React from 'react';
import { Button } from '../../ui/button';
import { CheckCircle } from 'lucide-react';

interface QualityIssue {
  id: string;
  field: string;
  issue_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_records: number;
  recommendation: string;
  agent_source: string;
  status: 'pending' | 'resolved' | 'ignored';
}

interface QualityIssuesPanelProps {
  qualityIssues: QualityIssue[];
  onResolveIssue: (issueId: string, action: 'resolve' | 'ignore') => void;
  isLoading?: boolean;
}

const QualityIssuesPanel: React.FC<QualityIssuesPanelProps> = ({
  qualityIssues,
  onResolveIssue,
  isLoading = false
}) => {
  const getSeverityBadgeClass = (severity: 'high' | 'medium' | 'low'): unknown => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quality Issues</h3>
          <div className="h-4 bg-gray-200 rounded w-64 mt-1"></div>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="h-5 bg-gray-200 rounded w-16"></div>
                      <div className="h-4 bg-gray-200 rounded w-24"></div>
                      <div className="h-3 bg-gray-200 rounded w-20"></div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <div className="h-8 bg-gray-200 rounded w-16"></div>
                    <div className="h-8 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Quality Issues</h3>
        <p className="text-sm text-gray-600">
          {qualityIssues.length} data quality issues identified by the Data Quality Manager
        </p>
      </div>
      <div className="p-6">
        {qualityIssues.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <p className="text-gray-600">No quality issues found. Data quality looks good!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {qualityIssues.map((issue) => (
              <div key={issue.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeClass(issue.severity)}`}>
                        {issue.severity.toUpperCase()}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{issue.field}</span>
                      <span className="text-xs text-gray-500">({issue.affected_records} records)</span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                    <p className="text-xs text-gray-500 italic">{issue.recommendation}</p>
                    <p className="text-xs text-blue-600 mt-1">Source: {issue.agent_source}</p>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => onResolveIssue(issue.id, 'resolve')}
                      disabled={issue.status !== 'pending'}
                      className={issue.status === 'resolved' ? 'bg-green-600' : ''}
                    >
                      {issue.status === 'resolved' ? 'Resolved' : 'Resolve'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onResolveIssue(issue.id, 'ignore')}
                      disabled={issue.status !== 'pending'}
                    >
                      {issue.status === 'ignored' ? 'Ignored' : 'Ignore'}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default QualityIssuesPanel;
