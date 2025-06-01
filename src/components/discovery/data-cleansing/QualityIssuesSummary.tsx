import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface QualityIssue {
  id: string;
  asset_id: string;
  asset_name: string;
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  suggested_fix: string;
  confidence: number;
  impact: string;
  current_value?: string;
  field_name?: string;
}

interface QualityIssuesSummaryProps {
  qualityIssues: QualityIssue[];
  selectedIssue: string | null;
  onIssueSelect: (issueId: string | null) => void;
  onFixIssue: (issueId: string) => void;
}

const QualityIssuesSummary: React.FC<QualityIssuesSummaryProps> = ({
  qualityIssues,
  selectedIssue,
  onIssueSelect,
  onFixIssue
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          Quality Issues ({qualityIssues.length})
        </h3>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {qualityIssues.length > 0 ? (
          <div className="space-y-2 p-4">
            {qualityIssues.map((issue) => (
              <div
                key={issue.id}
                onClick={() => onIssueSelect(selectedIssue === issue.id ? null : issue.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedIssue === issue.id
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-200 hover:border-red-200 hover:bg-red-25'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{issue.asset_name}</p>
                    <p className="text-xs text-gray-600">{issue.issue_type}</p>
                    <p className="text-xs text-gray-500">{issue.field_name}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    issue.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    issue.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {issue.severity}
                  </span>
                </div>
                {selectedIssue === issue.id && (
                  <div className="mt-2 pt-2 border-t border-red-200">
                    <p className="text-xs text-gray-600 mb-2">{issue.description}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onFixIssue(issue.id);
                      }}
                      className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                    >
                      Apply Fix
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No quality issues found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QualityIssuesSummary; 