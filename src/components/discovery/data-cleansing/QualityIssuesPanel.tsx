import React, { useState } from 'react';
import { Button } from '../../ui/button';
import { CheckCircle, ChevronDown, ChevronUp, AlertCircle, FileText, Lightbulb } from 'lucide-react';

interface ValidationDecision {
  field_name: string;
  action: 'split' | 'truncate' | 'skip' | 'keep' | 'first_value';
  custom_delimiter?: string;
}

interface QualityIssue {
  id: string;
  field_name: string;
  issue_type: string;
  severity: 'high' | 'medium' | 'low' | 'critical';
  description: string;
  affected_records: number;
  recommendation: string;
  auto_fixable: boolean;
  status?: 'pending' | 'resolved' | 'ignored';
  // ADR-038: Enhanced fields for detailed issue reporting
  sample_values?: string[];
  expected_format?: string;
  fix_examples?: string[];
  validation_decision?: ValidationDecision;
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
  // Track which issues have their details expanded
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());

  const toggleExpanded = (issueId: string) => {
    setExpandedIssues(prev => {
      const newSet = new Set(prev);
      if (newSet.has(issueId)) {
        newSet.delete(issueId);
      } else {
        newSet.add(issueId);
      }
      return newSet;
    });
  };

  const hasDetails = (issue: QualityIssue): boolean => {
    return !!(issue.sample_values?.length || issue.expected_format || issue.fix_examples?.length || issue.validation_decision);
  };

  const getSeverityBadgeClass = (severity: 'high' | 'medium' | 'low' | 'critical'): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-200 text-red-900';
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
            {qualityIssues.map((issue) => {
              const isExpanded = expandedIssues.has(issue.id);
              const showDetailsButton = hasDetails(issue);

              return (
                <div key={issue.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeClass(issue.severity)}`}>
                          {issue.severity.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{issue.field_name}</span>
                        <span className="text-xs text-gray-500">({issue.affected_records} records)</span>
                        {issue.validation_decision && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            Decision: {issue.validation_decision.action}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                      <p className="text-xs text-gray-500 italic mb-2">{issue.recommendation}</p>

                      {/* Expandable Details Section */}
                      {showDetailsButton && (
                        <button
                          type="button"
                          onClick={() => toggleExpanded(issue.id)}
                          className="flex items-center text-xs text-blue-600 hover:text-blue-800 mb-2"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3 w-3 mr-1" />
                              Hide Details
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3 mr-1" />
                              Show Details & Examples
                            </>
                          )}
                        </button>
                      )}

                      {isExpanded && (
                        <div className="mt-3 space-y-3 bg-gray-50 rounded-lg p-3 text-sm">
                          {/* Expected Format */}
                          {issue.expected_format && (
                            <div className="flex items-start space-x-2">
                              <FileText className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-gray-700">Expected Format:</span>
                                <p className="text-gray-600 mt-0.5">{issue.expected_format}</p>
                              </div>
                            </div>
                          )}

                          {/* Sample Values */}
                          {issue.sample_values && issue.sample_values.length > 0 && (
                            <div className="flex items-start space-x-2">
                              <AlertCircle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-gray-700">Sample Values:</span>
                                <div className="mt-1 space-y-1">
                                  {issue.sample_values.map((value, idx) => (
                                    <code key={idx} className="block bg-white px-2 py-1 rounded text-xs text-gray-800 border">
                                      {value}
                                    </code>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Fix Examples */}
                          {issue.fix_examples && issue.fix_examples.length > 0 && (
                            <div className="flex items-start space-x-2">
                              <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-gray-700">How to Fix:</span>
                                <ul className="mt-1 list-disc list-inside text-gray-600 space-y-0.5">
                                  {issue.fix_examples.map((example, idx) => (
                                    <li key={idx} className="text-xs">{example}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          )}

                          {/* Validation Decision Info */}
                          {issue.validation_decision && (
                            <div className="flex items-start space-x-2 pt-2 border-t border-gray-200">
                              <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-medium text-gray-700">User Decision Applied:</span>
                                <p className="text-gray-600 mt-0.5">
                                  Action: <span className="font-medium">{issue.validation_decision.action}</span>
                                  {issue.validation_decision.custom_delimiter && (
                                    <> with delimiter: <code className="bg-white px-1 rounded">{issue.validation_decision.custom_delimiter}</code></>
                                  )}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <Button
                        size="sm"
                        onClick={() => onResolveIssue(issue.id, 'resolve')}
                        disabled={issue.status === 'resolved'}
                        className={issue.status === 'resolved' ? 'bg-green-600' : ''}
                      >
                        {issue.status === 'resolved' ? 'Resolved' : 'Resolve'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onResolveIssue(issue.id, 'ignore')}
                        disabled={issue.status === 'ignored'}
                      >
                        {issue.status === 'ignored' ? 'Ignored' : 'Ignore'}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default QualityIssuesPanel;
