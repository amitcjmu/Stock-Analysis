import React from 'react';
import { CheckCircle, X } from 'lucide-react'
import { ArrowRight } from 'lucide-react'
import type { FieldMappingItemProps } from './types'
import { CATEGORY_COLORS } from './types'
import TargetFieldSelector from './TargetFieldSelector';
import ApprovalWorkflow from './ApprovalWorkflow';

const FieldMappingItem: React.FC<FieldMappingItemProps> = ({
  mapping,
  availableFields,
  isDropdownOpen,
  isApproving,
  isRejecting,
  onToggleDropdown,
  onTargetFieldChange,
  onApproveMapping,
  onRejectMapping,
  selectedCategory,
  searchTerm,
  loadingFields,
  onCategoryChange,
  onSearchTermChange
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getMappingStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-50 border-green-200';
      case 'rejected': return 'bg-red-50 border-red-200';
      default: return 'bg-white border-gray-200';
    }
  };

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className={`border rounded-lg p-4 ${getMappingStatusColor(mapping.status)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-4 mb-2">
            <h4 className="font-medium text-gray-900">{mapping.sourceField}</h4>
            <ArrowRight className="h-4 w-4 text-gray-400" />
            
            <TargetFieldSelector
              mapping={mapping}
              availableFields={availableFields}
              isOpen={isDropdownOpen}
              onToggle={onToggleDropdown}
              onSelect={onTargetFieldChange}
              selectedCategory={selectedCategory}
              searchTerm={searchTerm}
              loadingFields={loadingFields}
              onCategoryChange={onCategoryChange}
              onSearchTermChange={onSearchTermChange}
            />
            
            {/* Show current field category if mapped */}
            {mapping.targetAttribute !== 'unmapped' && Array.isArray(availableFields) && (
              <span className={`text-xs px-2 py-1 rounded ${getCategoryColor(availableFields.find(f => f.name === mapping.targetAttribute)?.category || 'unknown')}`}>
                {availableFields.find(f => f.name === mapping.targetAttribute)?.category?.replace('_', ' ') || 'Unknown'}
              </span>
            )}
          </div>
          
          {/* Confidence and sample values */}
          <div className="flex items-center space-x-4 mb-2">
            <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(mapping.confidence)}`}>
              {Math.round(mapping.confidence * 100)}% confidence
            </span>
            {Array.isArray(mapping.sample_values) && mapping.sample_values.length > 0 && (
              <div className="text-xs text-gray-500">
                Sample: {mapping.sample_values.slice(0, 3).join(', ')}
                {mapping.sample_values.length > 3 && '...'}
              </div>
            )}
          </div>
          
          {/* AI reasoning */}
          {mapping.ai_reasoning && (
            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
              <strong>AI Analysis:</strong> {mapping.ai_reasoning}
            </div>
          )}
        </div>
        
        <ApprovalWorkflow
          mapping={mapping}
          isApproving={isApproving}
          isRejecting={isRejecting}
          onApprove={onApproveMapping}
          onReject={onRejectMapping}
        />
      </div>
    </div>
  );
};

export default FieldMappingItem;