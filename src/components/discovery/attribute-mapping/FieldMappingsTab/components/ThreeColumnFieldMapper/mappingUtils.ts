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
const debugLog = (message: string, data?: unknown) => {
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
      source_field: m.source_field,
      source_field_type: typeof m.source_field,
      target_field: m.target_field,
      target_field_type: typeof m.target_field,
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
        source_field: m.source_field,
        target_field: m.target_field,
        status: m.status,
        mapping_type: m.mapping_type
        // SECURITY FIX: Remove detailed field inspection to prevent sensitive data exposure
      });
    });
  }

  // Improved categorization logic:
  // 1. Approved mappings go to the approved column ONLY
  // 2. High confidence pending mappings (AI suggested) go to autoMapped column
  // 3. Unmapped, rejected, or no target mappings go to unmapped column (Needs Review)
  // 4. CRITICAL: Items should only appear in ONE column based on their status
  const approved = fieldMappings.filter(m => m.status === 'approved');

  const autoMapped = fieldMappings.filter(m => {
    // Include pending or suggested mappings that have a target field and aren't explicitly unmapped
    // BUT EXCLUDE approved items (they go in approved column only)
    return m.status !== 'approved' &&
           m.status !== 'rejected' &&
           (m.status === 'pending' || m.status === 'suggested') &&
           m.target_field &&
           m.target_field !== '' &&
           m.target_field !== 'unmapped' &&
           m.target_field !== 'Unassigned' &&
           m.mapping_type !== 'unmapped';
  });

  const unmapped = fieldMappings.filter(m => {
    // Include rejected, explicitly unmapped, or fields without proper targets
    // BUT EXCLUDE approved items (they go in approved column only)
    return m.status !== 'approved' &&
           (m.status === 'rejected' ||
            m.mapping_type === 'unmapped' ||
            !m.target_field ||
            m.target_field === '' ||
            m.target_field === 'unmapped' ||
            m.target_field === 'Unassigned');
  });

  // SECURITY FIX: Use secure debug logging for bucket information
  debugLog('🔍 ThreeColumnFieldMapper - Buckets:', {
    autoMapped: autoMapped.length,
    unmapped: unmapped.length,
    approved: approved.length,
    approved_sample: approved.slice(0, 3).map(m => ({
      target_field: m.target_field,
      source_field: m.source_field,
      status: m.status
    }))
  });

  return { autoMapped, unmapped, approved };
};

export const filterMappingsBySearch = (buckets: MappingBuckets, searchTerm: string): MappingBuckets => {
  if (!searchTerm) return buckets;

  const filterBySearch = (mappings: FieldMapping[]) =>
    mappings.filter(m =>
      m.source_field.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.target_field && m.target_field.toLowerCase().includes(searchTerm.toLowerCase()))
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

export const formatTargetAttribute = (target_field: unknown): string => {
  if (typeof target_field === 'string') {
    return target_field || 'No target mapping';
  } else if (typeof target_field === 'object' && target_field !== null) {
    return JSON.stringify(target_field);
  } else {
    return String(target_field || 'No target mapping');
  }
};
