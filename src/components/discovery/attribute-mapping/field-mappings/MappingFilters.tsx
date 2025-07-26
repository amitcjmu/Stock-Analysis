import React from 'react';
import type { MappingFiltersProps } from './types';

const MappingFilters: React.FC<MappingFiltersProps> = ({
  filterOptions,
  onFilterChange,
  mappingCounts
}) => {
  const handleFilterChange = (filterType: keyof typeof filterOptions, value: boolean): void => {
    onFilterChange({
      ...filterOptions,
      [filterType]: value
    });
  };

  return (
    <div className="mb-4 flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
      <span className="text-sm font-medium text-gray-700">Show:</span>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={filterOptions.showPending}
          onChange={(e) => handleFilterChange('showPending', e.target.checked)}
          className="mr-2"
        />
        <span className="text-sm text-gray-600">Pending ({mappingCounts.pending})</span>
      </label>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={filterOptions.showApproved}
          onChange={(e) => handleFilterChange('showApproved', e.target.checked)}
          className="mr-2"
        />
        <span className="text-sm text-gray-600">Approved ({mappingCounts.approved})</span>
      </label>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={filterOptions.showRejected}
          onChange={(e) => handleFilterChange('showRejected', e.target.checked)}
          className="mr-2"
        />
        <span className="text-sm text-gray-600">Rejected ({mappingCounts.rejected})</span>
      </label>
    </div>
  );
};

export default MappingFilters;
