/**
 * Mapping Utilities
 * 
 * Functions for categorizing mappings, filtering, and state management.
 */

import { FieldMapping } from '../../types';
import { MappingBuckets, ProgressInfo } from './types';

export const categorizeMappings = (fieldMappings: FieldMapping[]): MappingBuckets => {
  console.log('🔍 ThreeColumnFieldMapper - Field mappings data:', {
    total_mappings: fieldMappings.length,
    sample_mappings: fieldMappings.slice(0, 3).map(m => ({
      id: m.id,
      sourceField: m.sourceField,
      sourceField_type: typeof m.sourceField,
      sourceField_value: m.sourceField,
      targetAttribute: m.targetAttribute,
      targetAttribute_type: typeof m.targetAttribute,
      status: m.status,
      confidence: m.confidence,
      mapping_type: m.mapping_type,
      full_object: m
    }))
  });
  
  const autoMapped = fieldMappings.filter(m => m.status === 'pending' && m.confidence > 0.7);
  const unmapped = fieldMappings.filter(m => {
    return m.status === 'rejected' || (m.status === 'pending' && m.confidence <= 0.7) || m.mapping_type === 'unmapped';
  });
  const approved = fieldMappings.filter(m => m.status === 'approved');

  console.log('🔍 ThreeColumnFieldMapper - Buckets:', {
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