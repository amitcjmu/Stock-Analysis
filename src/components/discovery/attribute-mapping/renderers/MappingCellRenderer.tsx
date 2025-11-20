/**
 * Mapping Cell Renderer - Editable dropdown for attribute mapping
 *
 * Provides searchable dropdown for mapping source fields to target fields with:
 * - Status badge (Auto-Mapped/Needs Review/Approved)
 * - Confidence score indicator
 * - Approve/Reject action buttons
 * - Outside click handling
 * - Keyboard navigation (Escape, Enter)
 *
 * @component MappingCellRenderer
 */

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import type { ICellRendererParams } from 'ag-grid-community';
import { ChevronDown, Check, AlertCircle, X, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { FieldMappingStatus } from '@/types/api/discovery/field-mapping-types';

export interface MappingCellValue {
  target_field: string | null;
  status: FieldMappingStatus;
  confidence_score: number;
  mapping_id: string;
}

export interface MappingCellRendererProps extends ICellRendererParams {
  value: MappingCellValue;
  sourceField: string;
  availableTargetFields: string[];
  onSelect?: (sourceField: string, targetField: string) => void;
  onApprove?: (mappingId: string) => void;
  onReject?: (mappingId: string) => void;
}

/**
 * Get status badge styling based on mapping status
 */
function getStatusBadge(status: FieldMappingStatus, confidenceScore: number): {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  icon: React.ReactNode;
} {
  switch (status) {
    case 'approved':
      return {
        label: 'Approved',
        variant: 'default',
        icon: <CheckCircle className="w-3 h-3" />
      };
    case 'suggested':
      return {
        label: `Suggested (${Math.round(confidenceScore * 100)}%)`,
        variant: 'secondary',
        icon: null
      };
    case 'pending':
      return {
        label: 'Needs Review',
        variant: 'outline',
        icon: <AlertCircle className="w-3 h-3 text-yellow-600" />
      };
    case 'rejected':
      return {
        label: 'Rejected',
        variant: 'destructive',
        icon: <X className="w-3 h-3" />
      };
    case 'unmapped':
    default:
      return {
        label: 'Unmapped',
        variant: 'outline',
        icon: <AlertCircle className="w-3 h-3 text-gray-400" />
      };
  }
}

/**
 * Get confidence level label based on score
 */
function getConfidenceLabel(score: number): string {
  if (score >= 0.8) return `High (${Math.round(score * 100)}%)`;
  if (score >= 0.5) return `Medium (${Math.round(score * 100)}%)`;
  return `Low (${Math.round(score * 100)}%)`;
}

export const MappingCellRenderer: React.FC<MappingCellRendererProps> = ({
  value,
  sourceField,
  availableTargetFields,
  onSelect,
  onApprove,
  onReject
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
        setSearchTerm(''); // Reset search when closing
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsDropdownOpen(false);
        setSearchTerm('');
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isDropdownOpen]);

  // Filter available fields based on search term
  const filteredFields = searchTerm
    ? availableTargetFields.filter(field =>
        field.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : availableTargetFields;

  // Handle field selection
  const handleSelectField = (fieldName: string) => {
    if (onSelect) {
      onSelect(sourceField, fieldName);
    }
    setIsDropdownOpen(false);
    setSearchTerm('');
  };

  // Get status badge configuration
  const statusBadge = getStatusBadge(value.status, value.confidence_score);

  // Calculate dropdown position when opened
  useEffect(() => {
    if (isDropdownOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: Math.max(rect.width, 350), // Minimum 350px width for comfortable viewing
      });
    }
  }, [isDropdownOpen]);

  // Determine if dropdown should be disabled
  const isDisabled = value.status === 'approved';

  return (
    <div className="flex flex-col gap-2 p-2 w-full h-full">
      {/* Dropdown Section */}
      <div className="relative">
        <button
          ref={buttonRef}
          onClick={() => !isDisabled && setIsDropdownOpen(!isDropdownOpen)}
          disabled={isDisabled}
          className={`
            flex items-center justify-between w-full px-3 py-2 text-sm border-2 rounded-md
            transition-all shadow-sm
            ${isDisabled
              ? 'bg-gray-50 border-gray-200 cursor-not-allowed text-gray-500'
              : 'bg-white border-gray-400 hover:border-blue-500 hover:shadow-md cursor-pointer'
            }
            ${isDropdownOpen ? 'border-blue-500 shadow-md ring-2 ring-blue-100' : ''}
          `}
          aria-label={`Select target field for ${sourceField}`}
          aria-expanded={isDropdownOpen}
          aria-haspopup="listbox"
        >
          <span className={`truncate font-medium ${value.target_field ? 'text-gray-900' : 'text-gray-400'}`}>
            {value.target_field || 'Click to select target field...'}
          </span>
          {!isDisabled && (
            <ChevronDown
              className={`w-4 h-4 flex-shrink-0 ml-2 transition-transform ${
                isDropdownOpen ? 'transform rotate-180 text-blue-600' : 'text-gray-400'
              }`}
            />
          )}
        </button>

        {/* Dropdown Menu - Rendered via Portal to document.body */}
        {isDropdownOpen && !isDisabled && createPortal(
          <div
            ref={dropdownRef}
            className="fixed bg-white border-2 border-blue-400 rounded-lg shadow-2xl max-h-96 overflow-hidden"
            style={{
              top: `${dropdownPosition.top}px`,
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              zIndex: 10000,
            }}
          >
            {/* Search Input */}
            <div className="p-3 border-b-2 border-gray-200 bg-gray-50">
              <input
                type="text"
                placeholder="Search fields..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
                aria-label="Search target fields"
              />
            </div>

            {/* Fields List */}
            <div className="max-h-80 overflow-y-auto bg-white" role="listbox">
              {filteredFields.length === 0 ? (
                <div className="px-4 py-6 text-center text-sm text-gray-500">
                  No fields match your search
                </div>
              ) : (
                filteredFields.map(field => (
                  <button
                    key={field}
                    onClick={() => handleSelectField(field)}
                    className={`
                      w-full text-left px-4 py-3 text-sm hover:bg-blue-50 transition-colors border-b border-gray-100
                      ${field === value.target_field ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-700 hover:text-blue-600'}
                    `}
                    role="option"
                    aria-selected={field === value.target_field}
                  >
                    {field}
                  </button>
                ))
              )}
            </div>
          </div>,
          document.body
        )}
      </div>

      {/* Status and Actions Section */}
      <div className="flex items-center justify-between gap-2">
        {/* Status Badge with Confidence */}
        <div className="flex items-center gap-2">
          <Badge variant={statusBadge.variant} className="flex items-center gap-1">
            {statusBadge.icon}
            <span className="text-xs">{statusBadge.label}</span>
          </Badge>

          {/* Confidence Score (only for suggested/pending) */}
          {(value.status === 'suggested' || value.status === 'pending') && value.target_field && (
            <span className="text-xs text-gray-500">
              {getConfidenceLabel(value.confidence_score)}
            </span>
          )}
        </div>

        {/* Action Buttons (only for pending/suggested) */}
        {(value.status === 'suggested' || value.status === 'pending') && value.target_field && (
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (onApprove) {
                  onApprove(value.mapping_id);
                }
              }}
              className="p-1 rounded hover:bg-green-100 transition-colors group"
              title="Approve mapping"
              aria-label="Approve mapping"
            >
              <Check className="w-4 h-4 text-gray-400 group-hover:text-green-600" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (onReject) {
                  onReject(value.mapping_id);
                }
              }}
              className="p-1 rounded hover:bg-red-100 transition-colors group"
              title="Reject mapping"
              aria-label="Reject mapping"
            >
              <X className="w-4 h-4 text-gray-400 group-hover:text-red-600" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
