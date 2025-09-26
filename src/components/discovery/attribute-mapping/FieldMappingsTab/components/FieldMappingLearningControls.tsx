/**
 * Field Mapping Learning Controls Component
 *
 * Provides interactive UI controls for users to approve/reject field mappings
 * with learning feedback, including confidence score adjustment and rejection reasons.
 */

import React, { useState, useCallback } from 'react';
import { CheckCircle, XCircle, Brain, AlertCircle, Loader2, TrendingUp, MessageSquare, Star } from 'lucide-react';
import type { FieldMapping } from '../../../../../types/api/discovery/field-mapping-types';
import type {
  FieldMappingLearningApprovalRequest,
  FieldMappingLearningRejectionRequest
} from '../../../../../services/api/discoveryFlowService';

interface FieldMappingLearningControlsProps {
  mapping: FieldMapping;
  onApprove: (mappingId: string, request: FieldMappingLearningApprovalRequest) => Promise<void>;
  onReject: (mappingId: string, request: FieldMappingLearningRejectionRequest) => Promise<void>;
  isProcessing?: boolean;
  isLearned?: boolean;
  compact?: boolean;
  showConfidenceAdjustment?: boolean;
}

interface LearningState {
  showApprovalDialog: boolean;
  showRejectionDialog: boolean;
  confidence_score?: number;
  approval_metadata?: Record<string, unknown>;
  rejection_reason: string;
  alternative_suggestion: string;
  rejection_metadata?: Record<string, unknown>;
}

// Utility function to clamp confidence score to valid range [0, 1]
const clampConfidenceScore = (score: number | undefined | null): number => {
  if (typeof score !== 'number' || isNaN(score)) {
    return 0.5; // Default to 50% for undefined/null/NaN values
  }
  return Math.max(0, Math.min(1, score));
};

// Utility function to get safe confidence score with fallback to mapping default
const getSafeConfidenceScore = (score: number | undefined | null, fallback: number | undefined | null): number => {
  if (typeof score === 'number' && !isNaN(score)) {
    return clampConfidenceScore(score);
  }
  if (typeof fallback === 'number' && !isNaN(fallback)) {
    return clampConfidenceScore(fallback);
  }
  return 0.5; // Default to 50% if both are invalid
};

const FieldMappingLearningControls: React.FC<FieldMappingLearningControlsProps> = ({
  mapping,
  onApprove,
  onReject,
  isProcessing = false,
  isLearned = false,
  compact = false,
  showConfidenceAdjustment = true
}) => {
  const [learningState, setLearningState] = useState<LearningState>({
    showApprovalDialog: false,
    showRejectionDialog: false,
    confidence_score: getSafeConfidenceScore(mapping.confidence_score, mapping.confidence_score),
    rejection_reason: '',
    alternative_suggestion: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirmApproval = useCallback(async () => {
    setIsSubmitting(true);
    try {
      // Ensure confidence score is properly clamped before sending
      const safeConfidenceScore = getSafeConfidenceScore(learningState.confidence_score, mapping.confidence_score);

      const request: FieldMappingLearningApprovalRequest = {
        confidence_score: safeConfidenceScore,
        approval_metadata: {
          original_confidence: getSafeConfidenceScore(mapping.confidence_score, mapping.confidence_score),
          user_adjusted: safeConfidenceScore !== getSafeConfidenceScore(mapping.confidence_score, mapping.confidence_score),
          mapping_type: mapping.mapping_type,
          source_field: mapping.source_field,
          target_field: mapping.target_field,
          ...learningState.approval_metadata
        },
        learning_enabled: true
      };

      await onApprove(mapping.id, request);

      // Reset state
      setLearningState(prev => ({
        ...prev,
        showApprovalDialog: false,
        approval_metadata: undefined
      }));
    } catch (error) {
      console.error('Error approving mapping with learning:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [mapping, learningState, onApprove]);

  const handleConfirmRejection = useCallback(async () => {
    if (!learningState.rejection_reason.trim()) {
      return; // Rejection reason is required
    }

    setIsSubmitting(true);
    try {
      const request: FieldMappingLearningRejectionRequest = {
        rejection_reason: learningState.rejection_reason,
        alternative_suggestion: learningState.alternative_suggestion || undefined,
        rejection_metadata: {
          original_confidence: mapping.confidence_score,
          mapping_type: mapping.mapping_type,
          source_field: mapping.source_field,
          target_field: mapping.target_field,
          ...learningState.rejection_metadata
        },
        learning_enabled: true
      };

      await onReject(mapping.id, request);

      // Reset state
      setLearningState(prev => ({
        ...prev,
        showRejectionDialog: false,
        rejection_reason: '',
        alternative_suggestion: '',
        rejection_metadata: undefined
      }));
    } catch (error) {
      console.error('Error rejecting mapping with learning:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [mapping, learningState, onReject]);

  const handleApprovalClick = useCallback(() => {
    if (!learningState.showApprovalDialog) {
      setLearningState(prev => ({ ...prev, showApprovalDialog: true }));
    } else {
      handleConfirmApproval();
    }
  }, [learningState.showApprovalDialog, handleConfirmApproval]);

  const handleRejectionClick = useCallback(() => {
    if (!learningState.showRejectionDialog) {
      setLearningState(prev => ({ ...prev, showRejectionDialog: true }));
    } else {
      handleConfirmRejection();
    }
  }, [learningState.showRejectionDialog, handleConfirmRejection]);

  const handleCancel = useCallback(() => {
    setLearningState(prev => ({
      ...prev,
      showApprovalDialog: false,
      showRejectionDialog: false,
      rejection_reason: '',
      alternative_suggestion: ''
    }));
  }, []);

  const updateConfidenceScore = useCallback((score: number) => {
    // Clamp the score to [0, 1] range and handle NaN cases
    const clampedScore = clampConfidenceScore(score);
    setLearningState(prev => ({ ...prev, confidence_score: clampedScore }));
  }, []);

  const updateRejectionReason = useCallback((reason: string) => {
    setLearningState(prev => ({ ...prev, rejection_reason: reason }));
  }, []);

  const updateAlternativeSuggestion = useCallback((suggestion: string) => {
    setLearningState(prev => ({ ...prev, alternative_suggestion: suggestion }));
  }, []);

  // Compact version for small cards
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {isLearned && (
          <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
            <Brain className="h-3 w-3" />
            <span>Learned</span>
          </div>
        )}

        <button
          onClick={handleApprovalClick}
          disabled={isProcessing || isSubmitting}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Approve"
        >
          {(isProcessing || isSubmitting) ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <CheckCircle className="h-4 w-4" />
          )}
        </button>

        <button
          onClick={handleRejectionClick}
          disabled={isProcessing || isSubmitting}
          className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Reject"
        >
          <XCircle className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Learning Status Indicator */}
      {isLearned && (
        <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm">
          <Brain className="h-4 w-4" />
          <span>This mapping has been learned from previous feedback</span>
        </div>
      )}

      {/* Main Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleApprovalClick}
          disabled={isProcessing || isSubmitting}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
        >
          {(isProcessing || isSubmitting) ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <CheckCircle className="h-4 w-4" />
          )}
          <span>Approve</span>
        </button>

        <button
          onClick={handleRejectionClick}
          disabled={isProcessing || isSubmitting}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
        >
          <XCircle className="h-4 w-4" />
          <span>Reject</span>
        </button>
      </div>

      {/* Approval Dialog */}
      {learningState.showApprovalDialog && (
        <div className="border rounded-lg p-4 bg-green-50 border-green-200">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <h4 className="font-medium text-green-800">Approve Mapping</h4>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-green-700">
              This will approve the mapping and teach the system that this is a good match.
            </p>

            {showConfidenceAdjustment && (
              <div>
                <label className="block text-sm font-medium text-green-700 mb-2">
                  Adjust Confidence Score (optional)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={learningState.confidence_score || mapping.confidence_score}
                    onChange={(e) => updateConfidenceScore(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <div className="flex items-center gap-1 text-sm font-medium text-green-700">
                    <Star className="h-4 w-4" />
                    <span>{((learningState.confidence_score || mapping.confidence_score) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={handleConfirmApproval}
                disabled={isSubmitting}
                className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <TrendingUp className="h-4 w-4" />
                )}
                <span>Confirm Approval</span>
              </button>
              <button
                onClick={handleCancel}
                className="px-3 py-2 text-green-600 border border-green-300 rounded hover:bg-green-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rejection Dialog */}
      {learningState.showRejectionDialog && (
        <div className="border rounded-lg p-4 bg-red-50 border-red-200">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="h-5 w-5 text-red-600" />
            <h4 className="font-medium text-red-800">Reject Mapping</h4>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-red-700">
              This will reject the mapping and teach the system to avoid similar matches.
            </p>

            <div>
              <label className="block text-sm font-medium text-red-700 mb-1">
                Why is this mapping incorrect? *
              </label>
              <textarea
                value={learningState.rejection_reason}
                onChange={(e) => updateRejectionReason(e.target.value)}
                placeholder="e.g., Wrong data type, Different semantic meaning, etc."
                className="w-full px-3 py-2 border border-red-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                rows={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-red-700 mb-1">
                Suggest better mapping (optional)
              </label>
              <input
                type="text"
                value={learningState.alternative_suggestion}
                onChange={(e) => updateAlternativeSuggestion(e.target.value)}
                placeholder="e.g., asset_name, description, category"
                className="w-full px-3 py-2 border border-red-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleConfirmRejection}
                disabled={isSubmitting || !learningState.rejection_reason.trim()}
                className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <MessageSquare className="h-4 w-4" />
                )}
                <span>Confirm Rejection</span>
              </button>
              <button
                onClick={handleCancel}
                className="px-3 py-2 text-red-600 border border-red-300 rounded hover:bg-red-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldMappingLearningControls;
