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
        <p className="text-sm text-gray-600 mt-1">Click on an issue to see record details in the table below</p>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {qualityIssues.length > 0 ? (
          <div className="space-y-1 p-4">
            {qualityIssues.map((issue) => (
              <div
                key={issue.id}
                onClick={() => {
                  try {
                    onIssueSelect(selectedIssue === issue.id ? null : issue.id);
                  } catch (error) {
                    console.error('Error selecting issue:', error);
                  }
                }}
                className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                  selectedIssue === issue.id
                    ? 'border-red-300 bg-red-50 shadow-md'
                    : 'border-gray-200 hover:border-red-200 hover:bg-red-25 hover:shadow-sm'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <p className="text-sm font-medium text-gray-900">{issue.asset_name}</p>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        issue.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        issue.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                        issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {issue.severity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 font-medium">{issue.issue_type}</p>
                    <p className="text-xs text-gray-500">Field: {issue.field_name}</p>
                    {issue.current_value && (
                      <p className="text-xs text-red-600 mt-1">Current: "{issue.current_value}"</p>
                    )}
                  </div>
                </div>
                
                {selectedIssue === issue.id && (
                  <div className="mt-3 pt-3 border-t border-red-200 bg-white rounded p-3">
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs font-medium text-gray-700">Issue Description:</p>
                        <p className="text-xs text-gray-600">{issue.description}</p>
                      </div>
                      
                      <div>
                        <p className="text-xs font-medium text-gray-700">Suggested Fix:</p>
                        <p className="text-xs text-green-600 bg-green-50 p-2 rounded">"{issue.suggested_fix}"</p>
                      </div>
                      
                      {issue.impact && (
                        <div>
                          <p className="text-xs font-medium text-gray-700">Impact:</p>
                          <p className="text-xs text-gray-600">{issue.impact}</p>
                        </div>
                      )}
                      
                      <div>
                        <p className="text-xs font-medium text-gray-700">Confidence:</p>
                        <p className="text-xs text-gray-600">{Math.round(issue.confidence * 100)}%</p>
                      </div>
                      
                      <div className="flex space-x-2 pt-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            try {
                              onFixIssue(issue.id);
                            } catch (error) {
                              console.error('Error fixing issue:', error);
                            }
                          }}
                          className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition-colors"
                        >
                          Apply Fix
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            try {
                              onIssueSelect(null);
                            } catch (error) {
                              console.error('Error clearing selection:', error);
                            }
                          }}
                          className="text-xs bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600 transition-colors"
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No quality issues found</p>
            <p className="text-xs mt-1">All data appears to be in good condition</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QualityIssuesSummary; 