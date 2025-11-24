import React from 'react'
import { useState, useRef } from 'react'
import { useEffect } from 'react'
import { ChevronDown } from 'lucide-react';

// Enhanced field interface
interface EnhancedField {
  id: string;
  name: string;
  type: string;
  category?: string;
  description?: string;
  isRequired?: boolean;
  metadata?: Record<string, unknown>;
}

interface EnhancedFieldDropdownProps {
  value: string;
  onChange: (field: string) => void;
  availableFields: EnhancedField[];
  placeholder?: string;
}

export const EnhancedFieldDropdown: React.FC<EnhancedFieldDropdownProps> = ({
  value,
  onChange,
  availableFields,
  placeholder = "Select field"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent): void => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Safety check for availableFields
  const safeAvailableFields = Array.isArray(availableFields) ? availableFields : [];

  // DEBUG: Log available fields count
  React.useEffect(() => {
    console.log('🔍 EnhancedFieldDropdown - Available fields:', safeAvailableFields.length);
    if (safeAvailableFields.length < 50) {
      console.warn('⚠️ Only', safeAvailableFields.length, 'fields available - expected 90+');
      console.log('First 5 fields:', safeAvailableFields.slice(0, 5).map(f => f?.name));
    }
  }, [safeAvailableFields.length]);

  const allCategories = Array.from(new Set(safeAvailableFields.map(field => field?.category || 'unknown')));
  // Move 'other' to the end
  const filteredCategories = allCategories.filter(cat => cat !== 'other');
  if (allCategories.includes('other')) {
    filteredCategories.push('other');
  }
  const categories = ['all', ...filteredCategories];

  const filteredFields = safeAvailableFields.filter(field => {
    try {
      if (!field || !field.name) {
        console.warn('🚨 EnhancedFieldDropdown - Invalid field object:', field);
        return false;
      }
      const matchesSearch = field.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (field.description || '').toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || field.category === selectedCategory;
      return matchesSearch && matchesCategory;
    } catch (error) {
      console.error('🚨 EnhancedFieldDropdown - Error filtering field:', field, error);
      return false;
    }
  });

  const handleFieldSelect = (fieldName: string): void => {
    try {
      onChange(fieldName);
      setIsOpen(false);
      setSearchTerm('');
    } catch (error) {
      console.error('🚨 EnhancedFieldDropdown - Error in handleFieldSelect:', error);
    }
  };

  // Look up display_name from availableFields when displaying the selected value
  const getDisplayName = (fieldName: string): string => {
    if (!fieldName) return placeholder;
    const field = safeAvailableFields.find(f => f?.name === fieldName);
    return field?.display_name || fieldName;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between min-w-[200px] px-3 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <span className="truncate font-medium text-blue-600">{getDisplayName(value)}</span>
        <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-10 w-60 mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-96 overflow-hidden">
          <div className="p-3 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search fields..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="p-2 border-b border-gray-200">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          <div
            className="max-h-64 overflow-y-scroll pr-2"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: '#9CA3AF #E5E7EB'
            }}
          >
            {filteredFields.length === 0 ? (
              <div className="p-3 text-sm text-gray-500 text-center">
                No fields found matching your criteria
              </div>
            ) : (
              filteredFields.map((field) => (
                <button
                  key={field.name}
                  onClick={(e) => {
                    e.stopPropagation();
                    try {
                      handleFieldSelect(field.name);
                    } catch (error) {
                      console.error('🚨 EnhancedFieldDropdown - Error in field selection:', error);
                    }
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          {field.display_name || field.name}
                        </span>
                        {field.required && (
                          <span className="text-xs text-red-500">*</span>
                        )}
                        {field.is_custom && (
                          <span className="text-xs text-purple-600">Custom</span>
                        )}
                      </div>
                      {field.short_hint && (
                        <div className="text-xs text-gray-500 mt-1">{field.short_hint}</div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 ml-2">
                      {field.type}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
