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
import type { TargetField } from '../../types';

interface AutoMappedCardProps extends CardProps {
  onApprove: (mappingId: string) => void;
  onReject: (mappingId: string) => void;
  isProcessing: boolean;
  expandedReasonings: Set<string>;
  onToggleReasoning: (mappingId: string) => void;
  availableFields?: TargetField[];
  onMappingChange?: (mappingId: string, newTarget: string) => void;
}

const AutoMappedCard: React.FC<AutoMappedCardProps> = ({
  mapping,
  onApprove,
  onReject,
  isProcessing,
  expandedReasonings,
  onToggleReasoning,
  availableFields,
  onMappingChange
}) => {
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(mapping.target_field || '');
  const isPlaceholder = mapping.is_placeholder || mapping.is_fallback;
  const agentType = getAgentTypeForMapping(mapping);
  const confidence = getConfidenceDisplay(mapping.confidence_score || 0);
  const reasoning = getAgentReasoningForMapping(mapping);
  const isExpanded = expandedReasonings.has(mapping.id);

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
    <div className={`p-4 border rounded-lg transition-all duration-200 hover:shadow-md ${isPlaceholder ? 'bg-yellow-50 border-yellow-200' : 'bg-white border-gray-200'}`}>
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
            <span className={`font-medium ${isPlaceholder ? 'text-yellow-600' : 'text-blue-600'}`}>
              {formatTargetAttribute(mapping.target_field)}
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
        {isPlaceholder && !isEditMode && (
          <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full">
            Needs Configuration
          </span>
        )}
      </div>

      {/* AGENTIC UI: Agent type and confidence display */}
      <div className="flex items-center gap-2 mb-3">
        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${agentType.color}`}>
          {agentType.icon}
          {agentType.type} Agent
        </div>
        {mapping.confidence_score && (
          <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${confidence.colorClass}`}>
            {confidence.icon}
            {confidence.percentage}% confidence
          </div>
        )}
      </div>

      {/* AGENTIC UI: Agent reasoning toggle */}
      {!isPlaceholder && (
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
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Status indicator for agent suggestions */}
          {!isPlaceholder && (
            <span className="text-xs text-gray-500">
              {mapping.confidence_score && mapping.confidence_score > 0.8 ? '✨ High confidence' :
               mapping.confidence_score && mapping.confidence_score > 0.6 ? '⚡ Moderate confidence' :
               '🔍 Needs review'}
            </span>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onApprove(mapping.id)}
            disabled={isProcessing || isPlaceholder}
            className={`flex items-center gap-1 px-3 py-1 rounded transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed ${
              isPlaceholder
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
            title={isPlaceholder ? 'Configure target field before approval' : 'Approve agent suggestion'}
          >
            {isProcessing ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            {isPlaceholder ? 'Configure' : 'Approve'}
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
  </div>
  );
};

export default AutoMappedCard;
