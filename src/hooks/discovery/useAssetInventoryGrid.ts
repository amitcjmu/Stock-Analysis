/**
 * Hook for AI Grid Asset Inventory Editing (Issue #911)
 * Provides editable column configuration, validation, and mutations for inline editing
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AssetAPI } from '@/lib/api/assets';
import type { Asset } from '@/types/asset';
import { toast } from 'sonner';

/**
 * Column type for validation and rendering
 */
export type ColumnType = 'text' | 'number' | 'dropdown' | 'boolean';

/**
 * Editable column configuration
 */
export interface EditableColumn {
  field_name: string;
  display_name: string;
  column_type: ColumnType;
  editable: boolean;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: RegExp;
    custom?: (value: any) => boolean | string;
  };
  dropdown_options?: Array<{ value: string; label: string }>;
}

/**
 * Asset type options for dropdown
 */
const ASSET_TYPE_OPTIONS = [
  { value: 'SERVER', label: 'Server' },
  { value: 'APPLICATION', label: 'Application' },
  { value: 'DATABASE', label: 'Database' },
  { value: 'NETWORK_DEVICE', label: 'Network Device' },
  { value: 'STORAGE_DEVICE', label: 'Storage Device' },
  { value: 'SECURITY_DEVICE', label: 'Security Device' },
  { value: 'VIRTUALIZATION', label: 'Virtualization' },
  { value: 'UNKNOWN', label: 'Unknown' }
];

/**
 * Business criticality options for dropdown
 */
const CRITICALITY_OPTIONS = [
  { value: 'Critical', label: 'Critical' },
  { value: 'High', label: 'High' },
  { value: 'Medium', label: 'Medium' },
  { value: 'Low', label: 'Low' },
  { value: 'Unknown', label: 'Unknown' }
];

/**
 * Environment options for dropdown
 */
const ENVIRONMENT_OPTIONS = [
  { value: 'Production', label: 'Production' },
  { value: 'Staging', label: 'Staging' },
  { value: 'Development', label: 'Development' },
  { value: 'QA', label: 'QA' },
  { value: 'UAT', label: 'UAT' },
  { value: 'DR', label: 'Disaster Recovery' },
  { value: 'Unknown', label: 'Unknown' }
];

/**
 * Six R Strategy options for dropdown
 */
const SIXR_STRATEGY_OPTIONS = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)' },
  { value: 'replatform', label: 'Replatform (Reconfigure)' },
  { value: 'refactor', label: 'Refactor (Modify Code)' },
  { value: 'rearchitect', label: 'Rearchitect (Cloud-Native)' },
  { value: 'replace', label: 'Replace (COTS/SaaS or Rewrite)' },
  { value: 'retire', label: 'Retire (Decommission)' }
];

/**
 * Editable columns configuration with validation rules
 */
export const EDITABLE_COLUMNS: EditableColumn[] = [
  {
    field_name: 'asset_name',  // CC FIX: Use 'asset_name' to match Asset type field
    display_name: 'Asset Name',
    column_type: 'text',
    editable: true,
    validation: {
      required: true,
      pattern: /^[a-zA-Z0-9\s\-_\.]+$/,
      custom: (value: string) => {
        if (value.length < 2) return 'Name must be at least 2 characters';
        if (value.length > 255) return 'Name cannot exceed 255 characters';
        return true;
      }
    }
  },
  {
    field_name: 'asset_type',
    display_name: 'Asset Type',
    column_type: 'dropdown',
    editable: true,
    dropdown_options: ASSET_TYPE_OPTIONS,
    validation: {
      required: true
    }
  },
  {
    field_name: 'environment',
    display_name: 'Environment',
    column_type: 'dropdown',
    editable: true,
    dropdown_options: ENVIRONMENT_OPTIONS
  },
  {
    field_name: 'business_criticality',
    display_name: 'Business Criticality',
    column_type: 'dropdown',
    editable: true,
    dropdown_options: CRITICALITY_OPTIONS
  },
  {
    field_name: 'six_r_strategy',
    display_name: '6R Strategy',
    column_type: 'dropdown',
    editable: true,
    dropdown_options: SIXR_STRATEGY_OPTIONS
  },
  {
    field_name: 'hostname',
    display_name: 'Hostname',
    column_type: 'text',
    editable: true,
    validation: {
      pattern: /^[a-zA-Z0-9\-\.]+$/
    }
  },
  {
    field_name: 'ip_address',
    display_name: 'IP Address',
    column_type: 'text',
    editable: true,
    validation: {
      pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
      custom: (value: string) => {
        if (!value) return true; // Optional field
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(value) || 'Invalid IP address format';
      }
    }
  },
  {
    field_name: 'operating_system',
    display_name: 'Operating System',
    column_type: 'text',
    editable: true
  },
  {
    field_name: 'cpu_cores',
    display_name: 'CPU Cores',
    column_type: 'number',
    editable: true,
    validation: {
      min: 1,
      max: 1024
    }
  },
  {
    field_name: 'memory_gb',
    display_name: 'Memory (GB)',
    column_type: 'number',
    editable: true,
    validation: {
      min: 0,
      max: 10240
    }
  },
  {
    field_name: 'storage_gb',
    display_name: 'Storage (GB)',
    column_type: 'number',
    editable: true,
    validation: {
      min: 0,
      max: 1000000
    }
  },
  {
    field_name: 'business_owner',
    display_name: 'Business Owner',
    column_type: 'text',
    editable: true
  },
  {
    field_name: 'technical_owner',
    display_name: 'Technical Owner',
    column_type: 'text',
    editable: true
  },
  {
    field_name: 'department',
    display_name: 'Department',
    column_type: 'text',
    editable: true
  },
  {
    field_name: 'location',
    display_name: 'Location',
    column_type: 'text',
    editable: true
  }
];

/**
 * Validate a field value according to its column configuration
 */
export const validateFieldValue = (
  column: EditableColumn,
  value: any
): { valid: boolean; error?: string } => {
  if (!column.validation) {
    return { valid: true };
  }

  const validation = column.validation;

  // Required validation
  if (validation.required && (value === null || value === undefined || value === '')) {
    return { valid: false, error: `${column.display_name} is required` };
  }

  // Skip other validations if value is empty and not required
  if (!value && !validation.required) {
    return { valid: true };
  }

  // Number validations
  if (column.column_type === 'number') {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) {
      return { valid: false, error: `${column.display_name} must be a valid number` };
    }
    if (validation.min !== undefined && numValue < validation.min) {
      return { valid: false, error: `${column.display_name} must be at least ${validation.min}` };
    }
    if (validation.max !== undefined && numValue > validation.max) {
      return { valid: false, error: `${column.display_name} cannot exceed ${validation.max}` };
    }
  }

  // Pattern validation
  if (validation.pattern && typeof value === 'string') {
    if (!validation.pattern.test(value)) {
      return { valid: false, error: `${column.display_name} has invalid format` };
    }
  }

  // Custom validation
  if (validation.custom) {
    const result = validation.custom(value);
    if (result !== true) {
      return { valid: false, error: typeof result === 'string' ? result : `${column.display_name} is invalid` };
    }
  }

  return { valid: true };
};

/**
 * Hook for managing asset inventory grid with inline editing
 */
export const useAssetInventoryGrid = () => {
  const queryClient = useQueryClient();

  /**
   * Update a single asset field
   */
  const updateFieldMutation = useMutation({
    mutationFn: async ({
      asset_id,
      field_name,
      field_value
    }: {
      asset_id: number;
      field_name: string;
      field_value: any;
    }) => {
      // Find column configuration
      const column = EDITABLE_COLUMNS.find(col => col.field_name === field_name);
      if (!column) {
        throw new Error(`Unknown field: ${field_name}`);
      }

      // Validate field value
      const validation = validateFieldValue(column, field_value);
      if (!validation.valid) {
        throw new Error(validation.error || 'Validation failed');
      }

      return AssetAPI.updateAssetField(asset_id, field_name, field_value);
    },
    onMutate: async ({ asset_id, field_name, field_value }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['assets'] });

      // Optimistically update cached data
      queryClient.setQueriesData<Asset[]>({ queryKey: ['assets'] }, (old) => {
        if (!old) return old;
        return old.map(asset =>
          asset.id === asset_id
            ? { ...asset, [field_name]: field_value }
            : asset
        );
      });
    },
    onSuccess: (_data, variables) => {
      toast.success(`Updated ${variables.field_name} successfully`);
    },
    onError: (error: Error, variables) => {
      toast.error(`Failed to update ${variables.field_name}: ${error.message}`);
      // Refetch to revert optimistic update
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    }
  });

  /**
   * Bulk update a field on multiple assets
   */
  const bulkUpdateFieldMutation = useMutation({
    mutationFn: async ({
      asset_ids,
      field_name,
      field_value
    }: {
      asset_ids: number[];
      field_name: string;
      field_value: any;
    }) => {
      // Find column configuration
      const column = EDITABLE_COLUMNS.find(col => col.field_name === field_name);
      if (!column) {
        throw new Error(`Unknown field: ${field_name}`);
      }

      // Validate field value
      const validation = validateFieldValue(column, field_value);
      if (!validation.valid) {
        throw new Error(validation.error || 'Validation failed');
      }

      return AssetAPI.bulkUpdateAssetField(asset_ids, field_name, field_value);
    },
    onSuccess: (data, variables) => {
      toast.success(`Updated ${variables.field_name} for ${data.updated_count} assets`);
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
    onError: (error: Error, variables) => {
      toast.error(`Failed to bulk update ${variables.field_name}: ${error.message}`);
    }
  });

  return {
    editableColumns: EDITABLE_COLUMNS,
    updateField: updateFieldMutation.mutate,
    bulkUpdateField: bulkUpdateFieldMutation.mutate,
    isUpdating: updateFieldMutation.isPending || bulkUpdateFieldMutation.isPending,
    validateFieldValue
  };
};
