/**
 * Auto-Mapped Card Component
 *
 * Card component for displaying auto-mapped field mappings with agent reasoning and confidence.
 */

import React, { useState, useCallback } from 'react';
import { CheckCircle, XCircle, ArrowRight, Zap, Edit2 } from 'lucide-react';
import type { CardProps } from './types';
import { getAgentReasoningForMapping, getAgentTypeForMapping, getConfidenceDisplay } from './agentHelpers';
import { formatFieldValue, formatTargetAttribute } from './mappingUtils';
import { EnhancedFieldDropdown } from '../EnhancedFieldDropdown';
import FieldMappingLearningControls from '../FieldMappingLearningControls';
import MappingSourceIndicator from '../MappingSourceIndicator';
import { useLearningToasts } from '../../../../../../hooks/useLearningToasts';
import type { TargetField } from '../../types';
import type {
  FieldMappingLearningApprovalRequest,
  FieldMappingLearningRejectionRequest
} from '../../../../../../services/api/discoveryFlowService';

interface AutoMappedCardProps extends CardProps {
  onApprove: (mappingId: string) => void;
  onReject: (mappingId: string) => void;
  isProcessing: boolean;
  expandedReasonings: Set<string>;
  onToggleReasoning: (mappingId: string) => void;
  availableFields?: TargetField[];
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  // Learning-related props
  onApproveMappingWithLearning?: (mappingId: string, request: FieldMappingLearningApprovalRequest) => Promise<void>;
  onRejectMappingWithLearning?: (mappingId: string, request: FieldMappingLearningRejectionRequest) => Promise<void>;
  isLearned?: boolean;
  showLearningControls?: boolean;
}

const AutoMappedCard: React.FC<AutoMappedCardProps> = ({
  mapping,
  onApprove,
  onReject,
  isProcessing,
  expandedReasonings,
  onToggleReasoning,
  availableFields,
  onMappingChange,
  onApproveMappingWithLearning,
  onRejectMappingWithLearning,
  isLearned = false,
  showLearningControls = true
}) => {
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(mapping.target_field || '');
  const agentType = getAgentTypeForMapping(mapping);
  const confidenceValue = typeof mapping.confidence_score === 'number' ? mapping.confidence_score : 0;
  const confidence = getConfidenceDisplay(confidenceValue);
  const reasoning = getAgentReasoningForMapping(mapping);
  const isExpanded = expandedReasonings.has(mapping.id);

  // Learning hooks and handlers
  const { showApprovalSuccess, showApprovalError, showRejectionSuccess, showRejectionError } = useLearningToasts();

  const handleApproveWithLearning = useCallback(async (mappingId: string, request: FieldMappingLearningApprovalRequest) => {
    try {
      if (onApproveMappingWithLearning) {
        await onApproveMappingWithLearning(mappingId, request);
        showApprovalSuccess({ success: true, mapping_id: mappingId, patterns_created: 1 }, mapping.source_field);
      }
    } catch (error) {
      showApprovalError(error, mapping.source_field);
    }
  }, [onApproveMappingWithLearning, showApprovalSuccess, showApprovalError, mapping.source_field]);

  const handleRejectWithLearning = useCallback(async (mappingId: string, request: FieldMappingLearningRejectionRequest) => {
    try {
      if (onRejectMappingWithLearning) {
        await onRejectMappingWithLearning(mappingId, request);
        showRejectionSuccess({ success: true, mapping_id: mappingId, patterns_created: 1 }, mapping.source_field);
      }
    } catch (error) {
      showRejectionError(error, mapping.source_field);
    }
  }, [onRejectMappingWithLearning, showRejectionSuccess, showRejectionError, mapping.source_field]);

  const handleEditClick = useCallback(() => {
    setIsEditMode(true);
    setSelectedTarget(mapping.target_field || '');
  }, [mapping.target_field]);

  const handleSaveEdit = useCallback(() => {
    if (onMappingChange && selectedTarget !== mapping.target_field) {
      onMappingChange(mapping.id, selectedTarget);
    }
    setIsEditMode(false);
  }, [mapping.id, mapping.target_field, onMappingChange, selectedTarget]);

  const handleCancelEdit = useCallback(() => {
    setIsEditMode(false);
    setSelectedTarget(mapping.target_field || '');
  }, [mapping.target_field]);

  const handleFieldChange = useCallback((newValue: string) => {
    setSelectedTarget(newValue);
  }, []);

  return (
    <div className="p-4 border rounded-lg transition-all duration-200 hover:shadow-md bg-white border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <span className="font-medium text-gray-900">
          {formatFieldValue(mapping.source_field)}
        </span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
        {isEditMode && availableFields ? (
          <div className="flex items-center gap-2 flex-1">
            <EnhancedFieldDropdown
              value={selectedTarget}
              onChange={handleFieldChange}
              availableFields={availableFields}
              placeholder="Select target field"
            />
            <button
              onClick={handleSaveEdit}
              className="text-green-600 hover:text-green-700"
              title="Save changes"
            >
              <CheckCircle className="h-4 w-4" />
            </button>
            <button
              onClick={handleCancelEdit}
              className="text-red-600 hover:text-red-700"
              title="Cancel edit"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <span className="font-medium text-blue-600">
              {formatTargetAttribute(mapping.target_field, availableFields)}
            </span>
            {availableFields && onMappingChange && (
              <button
                onClick={handleEditClick}
                className="text-gray-500 hover:text-gray-700 ml-1"
                title="Edit mapping"
              >
                <Edit2 className="h-3 w-3" />
              </button>
            )}
          </>
        )}
      </div>

      {/* Mapping Source Indicator with Learning Status */}
      <div className="mb-3">
        <MappingSourceIndicator
          mapping={mapping}
          showConfidence={true}
          showDetails={false}
          compact={false}
        />
      </div>

      {/* AGENTIC UI: Agent reasoning toggle */}
      <div className="mb-3">
        <button
          onClick={() => onToggleReasoning(mapping.id)}
            className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
          >
            <Zap className="w-3 h-3" />
            {isExpanded ? 'Hide' : 'Show'} agent reasoning
          </button>

          {isExpanded && (
            <div className="mt-2 p-3 bg-gray-50 rounded-md border">
              <div className="text-xs text-gray-600">
                <strong>Agent Analysis:</strong> {reasoning}
              </div>
            </div>
        )}
      </div>

      {/* Learning Controls or Legacy Buttons */}
      {showLearningControls && onApproveMappingWithLearning && onRejectMappingWithLearning ? (
        <FieldMappingLearningControls
          mapping={mapping}
          onApprove={handleApproveWithLearning}
          onReject={handleRejectWithLearning}
          isProcessing={isProcessing}
          isLearned={isLearned}
          compact={false}
          showConfidenceAdjustment={true}
        />
      ) : (
        /* Legacy buttons for backward compatibility */
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Status indicator for agent suggestions */}
            <span className="text-xs text-gray-500">
              {confidenceValue > 0.8 ? '✨ High confidence' :
               confidenceValue > 0.6 ? '⚡ Moderate confidence' :
               '🔍 Needs review'}
            </span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onApprove(mapping.id)}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1 rounded transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed bg-green-600 text-white hover:bg-green-700"
              title="Approve agent suggestion"
            >
              {isProcessing ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              Approve
            </button>
            <button
              onClick={() => onReject(mapping.id)}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              title="Reject agent suggestion"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
  </div>
  );
};

export default AutoMappedCard;
