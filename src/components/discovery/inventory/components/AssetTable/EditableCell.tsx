/**
 * Editable Cell Component (Issue #911)
 * Provides inline editing functionality for asset fields with validation
 */

import React, { useState, useEffect, useRef } from 'react';
import { Check, X, Pencil } from 'lucide-react';
import type { EditableColumn } from '@/hooks/discovery/useAssetInventoryGrid';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface EditableCellProps {
  value: any;
  column: EditableColumn;
  onSave: (value: any) => Promise<void>;
  isUpdating: boolean;
}

export const EditableCell: React.FC<EditableCellProps> = ({
  value,
  column,
  onSave,
  isUpdating
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async () => {
    // Validate before saving
    if (column.validation) {
      if (column.validation.required && !editValue) {
        setValidationError(`${column.display_name} is required`);
        return;
      }

      if (column.column_type === 'number') {
        if (editValue === '' || editValue === null) {
          if (column.validation.required) {
            setValidationError(`${column.display_name} is required`);
            return;
          }
        } else {
          const numValue = parseFloat(editValue);
          if (isNaN(numValue)) {
            setValidationError('Must be a valid number');
            return;
          }
          if (column.validation.min !== undefined && numValue < column.validation.min) {
            setValidationError(`Must be at least ${column.validation.min}`);
            return;
          }
          if (column.validation.max !== undefined && numValue > column.validation.max) {
            setValidationError(`Cannot exceed ${column.validation.max}`);
            return;
          }
        }
      }

      if (column.validation.pattern && !column.validation.pattern.test(editValue)) {
        setValidationError('Invalid format');
        return;
      }

      if (column.validation.custom) {
        const result = column.validation.custom(editValue);
        if (result !== true) {
          setValidationError(typeof result === 'string' ? result : 'Invalid value');
          return;
        }
      }
    }

    try {
      await onSave(editValue);
      setIsEditing(false);
      setValidationError(null);
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : 'Save failed');
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
    setValidationError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  if (!column.editable) {
    return <span>{value || '-'}</span>;
  }

  if (!isEditing) {
    return (
      <div className="group flex items-center gap-2">
        <span>{value || '-'}</span>
        <button
          onClick={() => setIsEditing(true)}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          title={`Edit ${column.display_name}`}
          disabled={isUpdating}
        >
          <Pencil className="h-3 w-3 text-gray-400 hover:text-blue-600" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1">
        {column.column_type === 'dropdown' ? (
          <Select value={editValue} onValueChange={setEditValue}>
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {column.dropdown_options?.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            ref={inputRef}
            type={column.column_type === 'number' ? 'number' : 'text'}
            value={editValue || ''}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="h-8 text-sm"
            disabled={isUpdating}
          />
        )}
        <button
          onClick={handleSave}
          disabled={isUpdating}
          className="p-1 hover:bg-green-100 rounded"
          title="Save"
        >
          <Check className="h-4 w-4 text-green-600" />
        </button>
        <button
          onClick={handleCancel}
          disabled={isUpdating}
          className="p-1 hover:bg-red-100 rounded"
          title="Cancel"
        >
          <X className="h-4 w-4 text-red-600" />
        </button>
      </div>
      {validationError && (
        <span className="text-xs text-red-600">{validationError}</span>
      )}
    </div>
  );
};
