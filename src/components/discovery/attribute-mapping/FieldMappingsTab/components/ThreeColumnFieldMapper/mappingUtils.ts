/**
 * Mapping Utilities
 *
 * Functions for categorizing mappings, filtering, and state management.
 */

import type { FieldMapping } from '../../types';
import type { ProgressInfo } from './types'
import type { MappingBuckets } from './types'

// SECURITY FIX: Environment-controlled debug logging to prevent sensitive data leaks
const DEBUG_ENABLED = process.env.NODE_ENV !== 'production' && process.env.NEXT_PUBLIC_DEBUG_MAPPING_UTILS === 'true';
const TRUNCATE_LOGGED_DATA = true; // Always truncate in production-like environments

// Secure debug logging helper
const debugLog = (message: string, data?: any) => {
  if (!DEBUG_ENABLED) return;

  if (data && TRUNCATE_LOGGED_DATA) {
    // SECURITY FIX: Truncate logged data to prevent sensitive information exposure
    const truncatedData = typeof data === 'object' && data !== null
      ? JSON.stringify(data).substring(0, 200) + '...[truncated]'
      : String(data).substring(0, 200) + '...[truncated]';
    console.log(message, truncatedData);
  } else if (data) {
    console.log(message, data);
  } else {
    console.log(message);
  }
};

export const categorizeMappings = (fieldMappings: FieldMapping[]): MappingBuckets => {
  // SECURITY FIX: Use secure debug logging instead of verbose console.log
  debugLog('🔍 ThreeColumnFieldMapper - Field mappings data:', {
    total_mappings: fieldMappings.length,
    sample_mappings: fieldMappings.slice(0, 3).map(m => ({
      id: m.id,
      sourceField: m.sourceField,
      sourceField_type: typeof m.sourceField,
      targetAttribute: m.targetAttribute,
      targetAttribute_type: typeof m.targetAttribute,
      status: m.status,
      confidence: m.confidence,
      mapping_type: m.mapping_type
      // SECURITY FIX: Remove full_object to prevent sensitive data exposure
    }))
  });

  // SECURITY FIX: Remove per-item logging in production to prevent data leaks
  if (DEBUG_ENABLED) {
    fieldMappings.slice(0, 3).forEach((m, index) => { // Only log first 3 items
      debugLog(`🔍 Mapping ${index}:`, {
        sourceField: m.sourceField,
        targetAttribute: m.targetAttribute,
        status: m.status,
        mapping_type: m.mapping_type
        // SECURITY FIX: Remove detailed field inspection to prevent sensitive data exposure
      });
    });
  }

  // Improved categorization logic:
  // 1. Approved mappings go to the approved column
  // 2. High confidence pending mappings (AI suggested) go to autoMapped column
  // 3. Unmapped, rejected, or no target mappings go to unmapped column
  // 4. Low confidence pending mappings that still have a target go to autoMapped (as suggestions)
  const approved = fieldMappings.filter(m => m.status === 'approved');

  const autoMapped = fieldMappings.filter(m => {
    // Include pending mappings that have a target field and aren't explicitly unmapped
    return m.status === 'pending' &&
           m.targetAttribute &&
           m.targetAttribute !== '' &&
           m.targetAttribute !== 'unmapped' &&
           m.mapping_type !== 'unmapped';
  });

  const unmapped = fieldMappings.filter(m => {
    // Include rejected, explicitly unmapped, or fields without targets
    return m.status === 'rejected' ||
           m.mapping_type === 'unmapped' ||
           !m.targetAttribute ||
           m.targetAttribute === '' ||
           m.targetAttribute === 'unmapped';
  });

  // SECURITY FIX: Use secure debug logging for bucket information
  debugLog('🔍 ThreeColumnFieldMapper - Buckets:', {
    autoMapped: autoMapped.length,
    unmapped: unmapped.length,
    approved: approved.length,
    approved_sample: approved.slice(0, 3).map(m => ({
      targetAttribute: m.targetAttribute,
      sourceField: m.sourceField,
      status: m.status
    }))
  });

  return { autoMapped, unmapped, approved };
};

export const filterMappingsBySearch = (buckets: MappingBuckets, searchTerm: string): MappingBuckets => {
  if (!searchTerm) return buckets;

  const filterBySearch = (mappings: FieldMapping[]) =>
    mappings.filter(m =>
      m.sourceField.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.targetAttribute && m.targetAttribute.toLowerCase().includes(searchTerm.toLowerCase()))
    );

  return {
    autoMapped: filterBySearch(buckets.autoMapped),
    unmapped: filterBySearch(buckets.unmapped),
    approved: filterBySearch(buckets.approved)
  };
};

export const calculateProgress = (buckets: MappingBuckets, totalMappings: number): ProgressInfo => {
  return {
    total: totalMappings,
    approved: buckets.approved.length,
    pending: buckets.autoMapped.length + buckets.unmapped.length
  };
};

export const formatFieldValue = (field: unknown): string => {
  if (typeof field === 'string') {
    return field;
  } else if (typeof field === 'object' && field !== null) {
    return JSON.stringify(field);
  } else {
    return String(field || 'Unknown Field');
  }
};

export const formatTargetAttribute = (targetAttribute: unknown): string => {
  if (typeof targetAttribute === 'string') {
    return targetAttribute || 'No target mapping';
  } else if (typeof targetAttribute === 'object' && targetAttribute !== null) {
    return JSON.stringify(targetAttribute);
  } else {
    return String(targetAttribute || 'No target mapping');
  }
};
