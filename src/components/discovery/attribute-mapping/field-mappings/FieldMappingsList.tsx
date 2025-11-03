import React from 'react';
import { Tag } from 'lucide-react';
import type { FieldMappingsListProps } from './types';
import FieldMappingItem from './FieldMappingItem';

const FieldMappingsList: React.FC<FieldMappingsListProps> = ({
  fieldMappings,
  currentPage,
  itemsPerPage,
  availableFields,
  openDropdowns,
  approvingMappings,
  rejectingMappings,
  onToggleDropdown,
  onTargetFieldChange,
  onApproveMapping,
  onRejectMapping,
  onRemoveMapping,
  selectedCategory,
  searchTerm,
  loadingFields,
  onCategoryChange,
  onSearchTermChange
}) => {
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentMappings = fieldMappings.slice(startIndex, endIndex);

  if (fieldMappings.length === 0) {
    return (
      <div className="text-center py-10">
        <Tag className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No Field Mappings</h3>
        <p className="mt-1 text-sm text-gray-500">
          No mappings match your current filter criteria. Try adjusting the filters above.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[500px] overflow-y-auto">
      {currentMappings.map((mapping) => (
        <FieldMappingItem
          key={mapping.id}
          mapping={mapping}
          availableFields={availableFields}
          isDropdownOpen={openDropdowns[mapping.id] || false}
          isApproving={approvingMappings.has(mapping.id)}
          isRejecting={rejectingMappings.has(mapping.id)}
          onToggleDropdown={() => onToggleDropdown(mapping.id)}
          onTargetFieldChange={(newTarget) => onTargetFieldChange(mapping.id, newTarget)}
          onApproveMapping={() => onApproveMapping(mapping.id)}
          onRejectMapping={() => onRejectMapping(mapping.id, mapping.sourceField, mapping.targetAttribute)}
          onRemoveMapping={onRemoveMapping}
          selectedCategory={selectedCategory}
          searchTerm={searchTerm}
          loadingFields={loadingFields}
          onCategoryChange={onCategoryChange}
          onSearchTermChange={onSearchTermChange}
        />
      ))}
    </div>
  );
};

export default FieldMappingsList;
