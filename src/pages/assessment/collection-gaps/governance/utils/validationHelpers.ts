/**
 * Form Validation Helpers
 * Validation utility functions for governance forms
 */

import type { ExceptionFormData, ApprovalFormData } from '../types';

/**
 * Validate exception form data
 */
export function validateExceptionForm(data: ExceptionFormData): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!data.requirement_id) {
    errors.push('Requirement is required');
  }

  if (!data.title || data.title.trim().length === 0) {
    errors.push('Title is required');
  }

  if (!data.justification || data.justification.trim().length === 0) {
    errors.push('Justification is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Validate approval request form data
 */
export function validateApprovalForm(data: ApprovalFormData): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!data.title || data.title.trim().length === 0) {
    errors.push('Title is required');
  }

  if (!data.business_justification || data.business_justification.trim().length === 0) {
    errors.push('Business justification is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}
