import React from 'react';
import { ChevronDown } from 'lucide-react';
import type { TargetFieldSelectorProps } from './types'
import { CATEGORY_COLORS } from './types'

const TargetFieldSelector: React.FC<TargetFieldSelectorProps> = ({
  mapping,
  availableFields,
  isOpen,
  onToggle,
  onSelect,
  selectedCategory,
  searchTerm,
  loadingFields,
  onCategoryChange,
  onSearchTermChange
}) => {
  const getCategories = (): any => {
    if (!Array.isArray(availableFields) || availableFields.length === 0) {
      return ['all'];
    }
    const categories = Array.from(new Set(availableFields.map(field => field.category))).sort();
    return ['all', ...categories];
  };

  const getFilteredFields = (): any[] => {
    if (!Array.isArray(availableFields) || availableFields.length === 0) {
      return [];
    }

    let filtered = availableFields;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(field => field.category === selectedCategory);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(field =>
        field.name.toLowerCase().includes(term) ||
        field.description.toLowerCase().includes(term) ||
        field.category.toLowerCase().includes(term)
      );
    }

    return filtered.sort((a, b) => {
      // Sort by required first, then by name
      if (a.required && !b.required) return -1;
      if (!a.required && b.required) return 1;
      return a.name.localeCompare(b.name);
    });
  };

  const getCategoryColor = (category: string): any => {
    return CATEGORY_COLORS[category] || 'bg-gray-100 text-gray-700';
  };

  const getButtonStyle = (): any => {
    if (mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) {
      return 'bg-white border-gray-300 hover:border-blue-500 cursor-pointer';
    } else if (mapping.status === 'approved') {
      return 'bg-green-50 border-green-200 cursor-not-allowed';
    } else {
      return 'bg-red-50 border-red-200 cursor-not-allowed';
    }
  };

  const getTextColor = (): any => {
    if (mapping.status === 'pending') return 'text-blue-600';
    if (mapping.status === 'approved') return 'text-green-700';
    return 'text-red-700';
  };

  return (
    <div className="relative dropdown-container">
      <button
        onClick={onToggle}
        disabled={mapping.status === 'approved' || mapping.status === 'rejected'}
        className={`flex items-center space-x-2 px-3 py-1 rounded-lg border ${getButtonStyle()}`}
      >
        <span className="text-xs bg-gray-100 px-1 rounded">{mapping.status || 'unknown'}</span>
        <span className={`font-medium ${getTextColor()}`}>
          {mapping.targetAttribute}
        </span>
        {mapping.status === 'pending' && (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>

      {isOpen && (mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) && (
        <div className="absolute z-10 mt-1 w-80 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-hidden">
          {loadingFields ? (
            <div className="p-3 text-center text-gray-500">Loading fields...</div>
          ) : (
            <>
              {/* Search and category filter */}
              <div className="p-3 border-b border-gray-200 space-y-2">
                <input
                  type="text"
                  placeholder="Search fields..."
                  value={searchTerm}
                  onChange={(e) => onSearchTermChange(e.target.value)}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                />
                <select
                  value={selectedCategory}
                  onChange={(e) => onCategoryChange(e.target.value)}
                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                >
                  {getCategories().map(category => (
                    <option key={category} value={category}>
                      {category === 'all' ? 'All Categories' : category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              {/* Fields list */}
              <div className="max-h-64 overflow-y-auto">
                {getFilteredFields().length === 0 ? (
                  <div className="p-3 text-center text-gray-500 text-sm">
                    No fields match your search criteria
                  </div>
                ) : (
                  <div className="py-1">
                    {getFilteredFields().map((field) => (
                      <button
                        key={field.name}
                        onClick={() => onSelect(field.name)}
                        className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                          field.name === mapping.targetAttribute ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-medium">{field.name}</div>
                            <div className="text-xs text-gray-500 mt-1">{field.description}</div>
                          </div>
                          <div className="flex flex-col items-end space-y-1 ml-2">
                            <span className={`text-xs px-1 py-0.5 rounded ${getCategoryColor(field.category)}`}>
                              {field.category.replace('_', ' ')}
                            </span>
                            <span className={`px-1 py-0.5 text-xs rounded ${field.required ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                              {field.required ? 'Required' : 'Optional'}
                            </span>
                            {field.is_custom && (
                              <span className="px-1 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Custom</span>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default TargetFieldSelector;
