import React, { useState } from 'react';
import { Button } from '../../ui/button';
import { CheckCircle, ChevronDown, ChevronUp, AlertCircle, FileText, Lightbulb, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../ui/dialog';

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

  // CC: Track confirmation modal state - shows user what changes will be applied before resolving
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean;
    issue: QualityIssue | null;
    action: 'resolve' | 'ignore';
  }>({ isOpen: false, issue: null, action: 'resolve' });

  const openConfirmationModal = (issue: QualityIssue, action: 'resolve' | 'ignore') => {
    setConfirmationModal({ isOpen: true, issue, action });
  };

  const closeConfirmationModal = () => {
    setConfirmationModal({ isOpen: false, issue: null, action: 'resolve' });
  };

  const handleConfirmAction = () => {
    if (confirmationModal.issue) {
      onResolveIssue(confirmationModal.issue.id, confirmationModal.action);
    }
    closeConfirmationModal();
  };

  // Generate human-readable description of what the resolution will do
  const getResolutionDescription = (issue: QualityIssue): string => {
    const decision = issue.validation_decision;
    if (!decision) {
      return `Mark ${issue.affected_records} records as resolved for field "${issue.field_name}".`;
    }

    switch (decision.action) {
      case 'split':
        return `Split multi-value entries in "${issue.field_name}" using delimiter "${decision.custom_delimiter || ','}" for ${issue.affected_records} records. Each value will become a separate entry.`;
      case 'truncate':
        return `Truncate overly long values in "${issue.field_name}" to fit the expected format for ${issue.affected_records} records.`;
      case 'skip':
        return `Skip processing ${issue.affected_records} records with invalid data in "${issue.field_name}". These records will not be imported.`;
      case 'keep':
        return `Keep the existing values in "${issue.field_name}" as-is for ${issue.affected_records} records without modification.`;
      case 'first_value':
        return `Extract only the first value from multi-value entries in "${issue.field_name}" for ${issue.affected_records} records. Other values will be discarded.`;
      default:
        return `Apply "${decision.action}" action to ${issue.affected_records} records in "${issue.field_name}".`;
    }
  };

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

  // CC FIX: Use explicit boolean checks for robustness (Qodo suggestion)
  const hasDetails = (issue: QualityIssue): boolean => {
    const hasSamples =
      Array.isArray(issue.sample_values) && issue.sample_values.length > 0;
    const hasFixExamples =
      Array.isArray(issue.fix_examples) && issue.fix_examples.length > 0;
    const hasExpected =
      typeof issue.expected_format === 'string' &&
      issue.expected_format.length > 0;
    const hasDecision = !!issue.validation_decision;
    return hasSamples || hasExpected || hasFixExamples || hasDecision;
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
                        onClick={() => openConfirmationModal(issue, 'resolve')}
                        disabled={issue.status === 'resolved'}
                        className={issue.status === 'resolved' ? 'bg-green-600' : ''}
                      >
                        {issue.status === 'resolved' ? 'Resolved' : 'Resolve'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openConfirmationModal(issue, 'ignore')}
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

      {/* CC: Confirmation Modal - Shows user what changes will be applied before action */}
      <Dialog open={confirmationModal.isOpen} onOpenChange={(open) => !open && closeConfirmationModal()}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {confirmationModal.action === 'resolve' ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Confirm Resolution</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  <span>Confirm Ignore</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {confirmationModal.action === 'resolve'
                ? 'Review the changes that will be applied to your data.'
                : 'This issue will be marked as ignored and no action will be taken.'
              }
            </DialogDescription>
          </DialogHeader>

          {confirmationModal.issue && (
            <div className="space-y-4 py-4">
              {/* Issue Summary */}
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityBadgeClass(confirmationModal.issue.severity)}`}>
                    {confirmationModal.issue.severity.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{confirmationModal.issue.field_name}</span>
                </div>
                <p className="text-sm text-gray-600">{confirmationModal.issue.description}</p>
              </div>

              {/* What Will Happen */}
              <div className="border-l-4 border-blue-500 bg-blue-50 p-3 rounded-r-lg">
                <p className="text-sm font-medium text-blue-800 mb-1">
                  {confirmationModal.action === 'resolve' ? 'What will happen:' : 'Result:'}
                </p>
                <p className="text-sm text-blue-700">
                  {confirmationModal.action === 'resolve'
                    ? getResolutionDescription(confirmationModal.issue)
                    : `No changes will be made. The issue for "${confirmationModal.issue.field_name}" affecting ${confirmationModal.issue.affected_records} records will be marked as ignored.`
                  }
                </p>
              </div>

              {/* Sample Values Preview (for resolve action) */}
              {confirmationModal.action === 'resolve' && confirmationModal.issue.sample_values && confirmationModal.issue.sample_values.length > 0 && (
                <div className="text-sm">
                  <p className="font-medium text-gray-700 mb-2">Sample values that will be affected:</p>
                  <div className="space-y-1">
                    {confirmationModal.issue.sample_values.slice(0, 3).map((value, idx) => (
                      <code key={idx} className="block bg-gray-100 px-2 py-1 rounded text-xs text-gray-800 border">
                        {value}
                      </code>
                    ))}
                    {confirmationModal.issue.sample_values.length > 3 && (
                      <p className="text-xs text-gray-500 italic">
                        ...and {confirmationModal.issue.sample_values.length - 3} more values
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter className="flex space-x-2">
            <Button variant="outline" onClick={closeConfirmationModal}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmAction}
              className={confirmationModal.action === 'resolve' ? 'bg-green-600 hover:bg-green-700' : 'bg-yellow-600 hover:bg-yellow-700'}
            >
              {confirmationModal.action === 'resolve' ? 'Confirm Resolution' : 'Confirm Ignore'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default QualityIssuesPanel;
