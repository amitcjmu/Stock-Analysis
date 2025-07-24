import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { MappingPaginationProps } from './types';

const MappingPagination: React.FC<MappingPaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  filteredItems,
  startIndex,
  endIndex,
  onPageChange
}) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between mt-6">
      <p className="text-sm text-gray-700">
        Showing <span className="font-medium">{startIndex + 1}</span> to <span className="font-medium">{Math.min(endIndex, filteredItems)}</span> of <span className="font-medium">{filteredItems}</span> results
        {filteredItems !== totalItems && (
          <span className="ml-2 text-gray-500">(filtered from {totalItems} total)</span>
        )}
      </p>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default MappingPagination;