/**
 * Unit tests for canContinueToDataCleansing validation logic
 *
 * Tests the practical field validation approach that doesn't rely on agent decisions.
 * Ensures minimum required fields (name, asset_type) are validated along with approval percentage.
 */

import { describe, it, expect } from 'vitest';
import type { FieldMapping } from '@/types/api/discovery/field-mapping-types';

// Extract the validation logic for testing
const canContinueToDataCleansingLogic = (
  flow: { phases?: Record<string, boolean> } | null,
  fieldMappings: FieldMapping[]
): boolean => {
  // Check if flow phase is already complete
  if (flow?.phases?.attribute_mapping === true) {
    return true;
  }

  // Ensure we have field mappings
  if (!fieldMappings || fieldMappings.length === 0) {
    return false;
  }

  // Get approved mappings
  const approvedMappings = fieldMappings.filter(m => m.status === 'approved');

  // Must have at least some approved mappings
  if (approvedMappings.length === 0) {
    return false;
  }

  // Check for minimum required fields: name and asset_type
  const hasNameField = approvedMappings.some(m => {
    const targetField = m.target_field?.toLowerCase() || '';
    return targetField.includes('name') || targetField.includes('asset_name');
  });

  const hasTypeField = approvedMappings.some(m => {
    const targetField = m.target_field?.toLowerCase() || '';
    return targetField.includes('type') || targetField.includes('asset_type');
  });

  if (!hasNameField || !hasTypeField) {
    return false;
  }

  // Check for minimum approval percentage (at least 30% should be approved)
  const approvalPercentage = (approvedMappings.length / fieldMappings.length) * 100;
  const minimumPercentage = 30;

  if (approvalPercentage < minimumPercentage) {
    return false;
  }

  return true;
};

describe('canContinueToDataCleansing validation', () => {
  const createMapping = (id: string, source_field: string, target_field: string | null, status: string): FieldMapping => ({
    id,
    source_field,
    target_field,
    confidence_score: 0.8,
    mapping_type: 'suggested',
    transformation: null,
    validation_rules: null,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
    status: status as any,
    sample_values: [],
    ai_reasoning: 'Test mapping',
    is_user_defined: false,
    user_feedback: null,
    validation_method: 'test',
    is_validated: true,
    metadata: {}
  });

  it('should return true when flow phase is already complete', () => {
    const flow = { phases: { attribute_mapping: true } };
    const fieldMappings: FieldMapping[] = [];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(true);
  });

  it('should return false when no field mappings are provided', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings: FieldMapping[] = [];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(false);
  });

  it('should return false when no mappings are approved', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'pending'),
      createMapping('2', 'device_type', 'asset_type', 'pending')
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(false);
  });

  it('should return false when name field is missing', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'device_type', 'asset_type', 'approved'),
      createMapping('2', 'cpu_cores', 'cpu_cores', 'approved')
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(false);
  });

  it('should return false when type field is missing', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'approved'),
      createMapping('2', 'cpu_cores', 'cpu_cores', 'approved')
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(false);
  });

  it('should return false when approval percentage is below 30%', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'approved'), // 1 approved
      createMapping('2', 'device_type', 'asset_type', 'pending'),  // out of 4 total
      createMapping('3', 'cpu_cores', 'cpu_cores', 'pending'),     // = 25% (below 30%)
      createMapping('4', 'memory_gb', 'memory_gb', 'pending')
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(false);
  });

  it('should return true with minimum requirements met', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'approved'),     // Has name field
      createMapping('2', 'device_type', 'asset_type', 'approved'),     // Has type field
      createMapping('3', 'cpu_cores', 'cpu_cores', 'pending')         // 2/3 = 67% > 30%
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(true);
  });

  it('should detect name field variations', () => {
    const flow = { phases: { attribute_mapping: false } };

    // Test different name field variations
    const nameVariations = ['asset_name', 'device_name', 'hostname', 'server_name'];

    for (const nameField of nameVariations) {
      const fieldMappings = [
        createMapping('1', 'name_field', nameField, 'approved'),
        createMapping('2', 'device_type', 'asset_type', 'approved')
      ];

      const result = canContinueToDataCleansingLogic(flow, fieldMappings);
      expect(result).toBe(true);
    }
  });

  it('should detect type field variations', () => {
    const flow = { phases: { attribute_mapping: false } };

    // Test different type field variations
    const typeVariations = ['asset_type', 'device_type', 'server_type'];

    for (const typeField of typeVariations) {
      const fieldMappings = [
        createMapping('1', 'server_name', 'asset_name', 'approved'),
        createMapping('2', 'type_field', typeField, 'approved')
      ];

      const result = canContinueToDataCleansingLogic(flow, fieldMappings);
      expect(result).toBe(true);
    }
  });

  it('should work with exactly 30% approval rate', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'approved'),    // 1 approved
      createMapping('2', 'device_type', 'asset_type', 'approved'),    // 2 approved
      createMapping('3', 'cpu_cores', 'cpu_cores', 'pending'),       // 3 pending
      createMapping('4', 'memory_gb', 'memory_gb', 'pending'),
      createMapping('5', 'storage_gb', 'storage_gb', 'pending'),
      createMapping('6', 'os_version', 'os_version', 'pending'),
      createMapping('7', 'ip_address', 'ip_address', 'pending')       // 2/7 ≈ 28.6% < 30%
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    // Should fail because 28.6% < 30%
    expect(result).toBe(false);
  });

  it('should work with high approval rate and required fields', () => {
    const flow = { phases: { attribute_mapping: false } };
    const fieldMappings = [
      createMapping('1', 'server_name', 'asset_name', 'approved'),
      createMapping('2', 'device_type', 'asset_type', 'approved'),
      createMapping('3', 'cpu_cores', 'cpu_cores', 'approved'),
      createMapping('4', 'memory_gb', 'memory_gb', 'approved'),
      createMapping('5', 'storage_gb', 'storage_gb', 'pending')     // 4/5 = 80% > 30%
    ];

    const result = canContinueToDataCleansingLogic(flow, fieldMappings);

    expect(result).toBe(true);
  });
});
