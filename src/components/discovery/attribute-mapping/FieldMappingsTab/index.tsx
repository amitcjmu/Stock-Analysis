import React from 'react';
import { RefreshCw } from 'lucide-react';
import { useFieldOptions } from '../../../../contexts/FieldOptionsContext';

// Components
import ThreeColumnFieldMapper from './components/ThreeColumnFieldMapper/ThreeColumnFieldMapper';

// Types
import type { FieldMappingsTabProps } from './types';

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onRemoveMapping,
  onMappingChange,
  onRefresh,
  onApproveMappingWithLearning,
  onRejectMappingWithLearning,
  onBulkLearnMappings,
  learnedMappings,
  clientAccountId,
  engagementId
}) => {
  // Use cached field options instead of fetching every time
  const { availableFields, isLoading: fieldsLoading } = useFieldOptions();

  // Filter mappings based on visible statuses - with safety check
  const safeFieldMappings = Array.isArray(fieldMappings) ? fieldMappings : [];

  if (isAnalyzing || fieldsLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Analyzing field mappings...</p>
          <p className="text-sm text-gray-500 mt-2">
            AI agents are determining the best field mappings for your data
          </p>
        </div>
      </div>
    );
  }

  if (!safeFieldMappings || safeFieldMappings.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-2">No field mappings available</p>
        <p className="text-sm text-gray-500">
          Complete the data import to see AI-generated field mappings
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ThreeColumnFieldMapper
        fieldMappings={safeFieldMappings}
        availableFields={availableFields}
        onMappingAction={onMappingAction}
        onRemoveMapping={onRemoveMapping}
        onMappingChange={onMappingChange}
        onRefresh={onRefresh}
        // Pass learning props to the mapper
        onApproveMappingWithLearning={onApproveMappingWithLearning}
        onRejectMappingWithLearning={onRejectMappingWithLearning}
        onBulkLearnMappings={onBulkLearnMappings}
        learnedMappings={learnedMappings}
        clientAccountId={clientAccountId}
        engagementId={engagementId}
      />
    </div>
  );
};

export default FieldMappingsTab;
