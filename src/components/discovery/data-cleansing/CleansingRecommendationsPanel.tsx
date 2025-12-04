import React, { useState } from 'react';
import { Button } from '../../ui/button';
import { Brain, CheckCircle, XCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../ui/dialog';

interface CleansingRecommendation {
  id: string;
  category?: string; // 'standardization' | 'validation' | 'enrichment' | 'deduplication'
  type?: string; // Legacy field for backward compatibility
  title: string;
  description: string;
  confidence?: number; // Optional, may not be provided by backend
  priority: 'high' | 'medium' | 'low';
  fields_affected?: string[]; // Backend field name
  fields?: string[]; // Legacy field for backward compatibility
  agent_source?: string; // Optional, may not be provided by backend
  implementation_steps?: string[]; // Optional, may not be provided by backend
  status?: 'pending' | 'applied' | 'rejected'; // Optional, defaults to 'pending'
}

interface CleansingRecommendationsPanelProps {
  recommendations: CleansingRecommendation[];
  onApplyRecommendation: (recommendationId: string, action: 'apply' | 'reject') => void;
  isLoading?: boolean;
}

const CleansingRecommendationsPanel: React.FC<CleansingRecommendationsPanelProps> = ({
  recommendations,
  onApplyRecommendation,
  isLoading = false
}) => {
  // Ensure recommendations is always an array to prevent runtime errors
  const safeRecommendations = Array.isArray(recommendations) ? recommendations : [];

  // CC: Track confirmation modal state - shows user what will happen before applying/rejecting
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean;
    recommendation: CleansingRecommendation | null;
    action: 'apply' | 'reject';
  }>({ isOpen: false, recommendation: null, action: 'apply' });

  const openConfirmationModal = (rec: CleansingRecommendation, action: 'apply' | 'reject') => {
    setConfirmationModal({ isOpen: true, recommendation: rec, action });
  };

  const closeConfirmationModal = () => {
    setConfirmationModal({ isOpen: false, recommendation: null, action: 'apply' });
  };

  const handleConfirmAction = () => {
    if (confirmationModal.recommendation) {
      onApplyRecommendation(confirmationModal.recommendation.id, confirmationModal.action);
    }
    closeConfirmationModal();
  };

  // Generate human-readable description of what the action will do
  const getActionDescription = (rec: CleansingRecommendation, action: 'apply' | 'reject'): string => {
    const fields = (rec.fields_affected || rec.fields || []).join(', ') || 'affected fields';

    if (action === 'apply') {
      switch (rec.category) {
        case 'standardization':
          return `Apply standardization rules to ${fields}. This will transform data values to match consistent formats.`;
        case 'validation':
          return `Apply validation fixes to ${fields}. Invalid or inconsistent values will be corrected based on the recommendation.`;
        case 'enrichment':
          return `Enrich data in ${fields} by adding derived or supplemental information.`;
        case 'deduplication':
          return `Remove duplicate entries affecting ${fields}. Redundant records will be consolidated.`;
        default:
          return `Apply the recommended changes to ${fields}.`;
      }
    } else {
      return `Reject this recommendation. The suggested changes to ${fields} will NOT be applied, and the recommendation will be marked as rejected.`;
    }
  };

  const getPriorityBadgeClass = (priority: 'high' | 'medium' | 'low'): unknown => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Cleansing Recommendations</h3>
          <div className="h-4 bg-gray-200 rounded w-72 mt-1"></div>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="h-5 bg-gray-200 rounded w-16"></div>
                      <div className="h-4 bg-gray-200 rounded w-32"></div>
                      <div className="h-3 bg-gray-200 rounded w-20"></div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="space-y-1">
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                    </div>
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
        <h3 className="text-lg font-medium text-gray-900">Cleansing Recommendations</h3>
        <p className="text-sm text-gray-600">
          {safeRecommendations.length} improvement recommendations from the Data Standardization Specialist
        </p>
      </div>
      <div className="p-6">
        {safeRecommendations.length === 0 ? (
          <div className="text-center py-8">
            <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">No recommendations yet. Trigger analysis to get AI-powered suggestions.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {safeRecommendations.map((rec) => {
              // Default status to 'pending' to ensure consistent button states
              const status = rec.status || 'pending';

              return (
                <div key={rec.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityBadgeClass(rec.priority)}`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{rec.title}</span>
                        <span className="text-xs text-gray-500">
                          ({rec.confidence !== undefined && rec.confidence !== null
                            ? `${Math.round(rec.confidence * 100)}%`
                            : 'N/A'} confidence)
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                      <div className="text-xs text-gray-600">
                        <p><strong>Fields:</strong> {(rec.fields_affected || rec.fields || []).join(', ') || 'N/A'}</p>
                        {rec.implementation_steps && rec.implementation_steps.length > 0 && (
                          <>
                            <p><strong>Steps:</strong></p>
                            <ul className="list-disc list-inside ml-2 space-y-1">
                              {rec.implementation_steps.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </div>
                      {rec.agent_source && (
                        <p className="text-xs text-blue-600 mt-1">Source: {rec.agent_source}</p>
                      )}
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <Button
                        size="sm"
                        onClick={() => openConfirmationModal(rec, 'apply')}
                        disabled={status === 'applied' || status === 'rejected'}
                        className={status === 'applied' ? 'bg-green-600 hover:bg-green-700' : ''}
                      >
                        {status === 'applied' ? 'Applied' : 'Apply'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openConfirmationModal(rec, 'reject')}
                        disabled={status === 'applied' || status === 'rejected'}
                        className={status === 'rejected' ? 'border-red-300 text-red-700 bg-red-50' : ''}
                      >
                        {status === 'rejected' ? 'Rejected' : 'Reject'}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* CC: Confirmation Modal - Shows user what will happen before applying/rejecting */}
      <Dialog open={confirmationModal.isOpen} onOpenChange={(open) => !open && closeConfirmationModal()}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {confirmationModal.action === 'apply' ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Confirm Apply Recommendation</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-600" />
                  <span>Confirm Reject Recommendation</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {confirmationModal.action === 'apply'
                ? 'Review what will happen when you apply this recommendation.'
                : 'This recommendation will be marked as rejected and no changes will be made.'
              }
            </DialogDescription>
          </DialogHeader>

          {confirmationModal.recommendation && (
            <div className="space-y-4 py-4">
              {/* Recommendation Summary */}
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityBadgeClass(confirmationModal.recommendation.priority)}`}>
                    {confirmationModal.recommendation.priority.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{confirmationModal.recommendation.title}</span>
                </div>
                <p className="text-sm text-gray-600">{confirmationModal.recommendation.description}</p>
              </div>

              {/* Fields Affected */}
              <div className="text-sm">
                <p className="font-medium text-gray-700 mb-1">Fields that will be affected:</p>
                <div className="flex flex-wrap gap-1">
                  {(confirmationModal.recommendation.fields_affected || confirmationModal.recommendation.fields || []).map((field, idx) => (
                    <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {field}
                    </span>
                  ))}
                </div>
              </div>

              {/* What Will Happen */}
              <div className={`border-l-4 p-3 rounded-r-lg ${
                confirmationModal.action === 'apply'
                  ? 'border-green-500 bg-green-50'
                  : 'border-red-500 bg-red-50'
              }`}>
                <p className={`text-sm font-medium mb-1 ${
                  confirmationModal.action === 'apply' ? 'text-green-800' : 'text-red-800'
                }`}>
                  What will happen:
                </p>
                <p className={`text-sm ${
                  confirmationModal.action === 'apply' ? 'text-green-700' : 'text-red-700'
                }`}>
                  {getActionDescription(confirmationModal.recommendation, confirmationModal.action)}
                </p>
              </div>

              {/* Implementation Steps (for apply action) */}
              {confirmationModal.action === 'apply' && confirmationModal.recommendation.implementation_steps && confirmationModal.recommendation.implementation_steps.length > 0 && (
                <div className="text-sm">
                  <p className="font-medium text-gray-700 mb-2">Implementation steps:</p>
                  <ol className="list-decimal list-inside space-y-1 text-gray-600">
                    {confirmationModal.recommendation.implementation_steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
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
              className={confirmationModal.action === 'apply' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
            >
              {confirmationModal.action === 'apply' ? 'Confirm Apply' : 'Confirm Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CleansingRecommendationsPanel;
