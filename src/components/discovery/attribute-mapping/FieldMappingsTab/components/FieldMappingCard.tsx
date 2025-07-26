import React from 'react'
import { useState } from 'react'
import { ArrowRight, CheckCircle, X, Tag, RefreshCw } from 'lucide-react';
import type { FieldMapping } from '../types';
import { EnhancedFieldDropdown } from './EnhancedFieldDropdown';

// Available field interface
interface AvailableField {
  id: string;
  name: string;
  type: string;
  description?: string;
  isRequired?: boolean;
  metadata?: Record<string, unknown>;
}

interface FieldMappingCardProps {
  mapping: FieldMapping;
  availableFields: AvailableField[];
  onMappingAction: (mappingId: string, action: 'approve' | 'reject') => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onReject: (mappingId: string, sourceField: string, targetField: string) => void;
}

export const FieldMappingCard: React.FC<FieldMappingCardProps> = ({
  mapping,
  availableFields,
  onMappingAction,
  onMappingChange,
  onReject
}) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApproval = async (): void => {
    if (isProcessing) return; // Prevent duplicate calls

    setIsProcessing(true);
    try {
      await onMappingAction(mapping.id, 'approve');
    } finally {
      // Reset processing state after delay to prevent rapid clicking
      setTimeout(() => setIsProcessing(false), 2000);
    }
  };

  const handleRejection = async (): void => {
    if (isProcessing) return; // Prevent duplicate calls

    setIsProcessing(true);
    try {
      onReject(mapping.id, mapping.sourceField, mapping.targetAttribute);
    } finally {
      // Reset processing state after delay
      setTimeout(() => setIsProcessing(false), 1000);
    }
  };

  const getConfidenceColor = (confidence: number): any => {
    if (confidence >= 90) return 'text-green-600';
    if (confidence >= 70) return 'text-blue-600';
    if (confidence >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (confidence: number): any => {
    if (confidence >= 90) return 'Very High';
    if (confidence >= 70) return 'High';
    if (confidence >= 50) return 'Medium';
    return 'Low';
  };

  const getStatusColor = (status: string): any => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-50';
      case 'rejected': return 'text-red-600 bg-red-50';
      case 'pending': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getMappingTypeIcon = (type: string): any => {
    switch (type) {
      case 'direct': return '🔗';
      case 'calculated': return '🧮';
      case 'manual': return '✋';
      default: return '❓';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="font-medium text-gray-900">{mapping.sourceField}</span>
            <ArrowRight className="h-4 w-4 text-gray-400" />
            {mapping.status === 'pending' && onMappingChange ? (
              <EnhancedFieldDropdown
                selectedField={mapping.targetAttribute}
                availableFields={availableFields}
                onFieldSelect={(field) => onMappingChange(mapping.id, field)}
              />
            ) : (
              <span className="font-medium text-blue-600">{mapping.targetAttribute}</span>
            )}
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span className="flex items-center">
              <span className="mr-1">{getMappingTypeIcon(mapping.mapping_type)}</span>
              {mapping.mapping_type}
            </span>
            <span className={`font-medium ${getConfidenceColor(mapping.confidence)}`}>
              {mapping.confidence}% ({getConfidenceLabel(mapping.confidence)})
            </span>
            <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(mapping.status)}`}>
              {mapping.status}
            </span>
          </div>
        </div>
      </div>

      {mapping.sample_values && mapping.sample_values.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-500 mb-1">Sample values:</div>
          <div className="flex flex-wrap gap-1">
            {mapping.sample_values.slice(0, 3).map((value, index) => (
              <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
                <Tag className="h-3 w-3 mr-1" />
                {value}
              </span>
            ))}
            {mapping.sample_values.length > 3 && (
              <span className="text-xs text-gray-500">
                +{mapping.sample_values.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {mapping.ai_reasoning && (
        <div className="mb-3 p-2 bg-blue-50 rounded text-sm text-blue-800">
          <div className="font-medium text-blue-900 mb-1">AI Reasoning:</div>
          {mapping.ai_reasoning}
        </div>
      )}

      {mapping.status === 'pending' && (
        <div className="flex justify-end space-x-2">
          <button
            onClick={handleRejection}
            disabled={isProcessing}
            className="flex items-center px-3 py-1 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <X className="h-4 w-4 mr-1" />
            )}
            Reject
          </button>
          <button
            onClick={handleApproval}
            disabled={isProcessing}
            className="flex items-center px-3 py-1 text-sm text-green-600 border border-green-200 rounded hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-1" />
            )}
            Approve
          </button>
        </div>
      )}
    </div>
  );
};
