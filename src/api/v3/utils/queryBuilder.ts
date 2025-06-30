/**
 * Query Builder Utilities for API v3
 * Helper functions for building query parameters and URLs
 */

import type { QueryParams, PaginationParams, FilterParams } from '../types/common';

/**
 * Build query string from parameters object
 */
export function buildQueryString(params: QueryParams): string {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        // Handle array parameters (e.g., status[]=active&status[]=pending)
        value.forEach(item => searchParams.append(`${key}[]`, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Merge pagination parameters with defaults
 */
export function mergePaginationParams(
  params: PaginationParams = {}
): Required<PaginationParams> {
  return {
    page: params.page ?? 1,
    page_size: params.page_size ?? 20,
    sort_by: params.sort_by ?? 'created_at',
    sort_order: params.sort_order ?? 'desc'
  };
}

/**
 * Validate pagination parameters
 */
export function validatePaginationParams(params: PaginationParams): void {
  if (params.page !== undefined && (params.page < 1 || !Number.isInteger(params.page))) {
    throw new Error('Page must be a positive integer');
  }
  
  if (params.page_size !== undefined && (params.page_size < 1 || params.page_size > 100 || !Number.isInteger(params.page_size))) {
    throw new Error('Page size must be between 1 and 100');
  }
  
  if (params.sort_order !== undefined && !['asc', 'desc'].includes(params.sort_order)) {
    throw new Error('Sort order must be "asc" or "desc"');
  }
}

/**
 * Clean empty values from parameters
 */
export function cleanParams(params: Record<string, any>): Record<string, any> {
  const cleaned: Record<string, any> = {};
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value) && value.length > 0) {
        cleaned[key] = value;
      } else if (!Array.isArray(value)) {
        cleaned[key] = value;
      }
    }
  });
  
  return cleaned;
}

/**
 * Build URL with query parameters
 */
export function buildUrl(baseUrl: string, endpoint: string, params?: QueryParams): string {
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${normalizedEndpoint}`;
  
  if (!params) {
    return url;
  }
  
  const cleanedParams = cleanParams(params);
  const queryString = buildQueryString(cleanedParams);
  
  return `${url}${queryString}`;
}

/**
 * Build filter parameters for list endpoints
 */
export function buildFilterParams(filters: FilterParams): QueryParams {
  const params: QueryParams = {};
  
  if (filters.search) {
    params.search = filters.search;
  }
  
  if (filters.status) {
    params.status = filters.status;
  }
  
  if (filters.created_after) {
    params.created_after = filters.created_after;
  }
  
  if (filters.created_before) {
    params.created_before = filters.created_before;
  }
  
  if (filters.updated_after) {
    params.updated_after = filters.updated_after;
  }
  
  if (filters.updated_before) {
    params.updated_before = filters.updated_before;
  }
  
  return params;
}

/**
 * Convert object to FormData for file uploads
 */
export function buildFormData(data: Record<string, any>): FormData {
  const formData = new FormData();
  
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (value instanceof File || value instanceof Blob) {
        formData.append(key, value);
      } else if (Array.isArray(value)) {
        value.forEach((item, index) => {
          formData.append(`${key}[${index}]`, String(item));
        });
      } else if (typeof value === 'object') {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, String(value));
      }
    }
  });
  
  return formData;
}

/**
 * Parse response pagination info
 */
export function parsePaginationInfo(response: any): {
  hasNext: boolean;
  hasPrevious: boolean;
  totalPages: number;
  currentPage: number;
  totalItems: number;
} {
  return {
    hasNext: response.has_next || false,
    hasPrevious: response.has_previous || false,
    totalPages: Math.ceil((response.total || 0) / (response.page_size || 20)),
    currentPage: response.page || 1,
    totalItems: response.total || 0
  };
}

/**
 * Build search parameters for complex queries
 */
export function buildSearchParams(searchTerm: string, searchFields: string[]): QueryParams {
  if (!searchTerm.trim()) {
    return {};
  }
  
  return {
    search: searchTerm.trim(),
    search_fields: searchFields.join(',')
  };
}

/**
 * Build date range parameters
 */
export function buildDateRangeParams(
  startDate?: Date | string,
  endDate?: Date | string,
  dateField: string = 'created_at'
): QueryParams {
  const params: QueryParams = {};
  
  if (startDate) {
    const startDateStr = startDate instanceof Date ? startDate.toISOString() : startDate;
    params[`${dateField}_after`] = startDateStr;
  }
  
  if (endDate) {
    const endDateStr = endDate instanceof Date ? endDate.toISOString() : endDate;
    params[`${dateField}_before`] = endDateStr;
  }
  
  return params;
}

/**
 * Encode special characters in query parameters
 */
export function encodeQueryParam(value: string): string {
  return encodeURIComponent(value);
}

/**
 * Validate URL format
 */
export function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Extract file extension from filename
 */
export function getFileExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.');
  return lastDotIndex > 0 ? filename.substring(lastDotIndex + 1).toLowerCase() : '';
}

/**
 * Validate file type against allowed types
 */
export function validateFileType(filename: string, allowedTypes: string[]): boolean {
  const extension = getFileExtension(filename);
  return allowedTypes.includes(extension);
}