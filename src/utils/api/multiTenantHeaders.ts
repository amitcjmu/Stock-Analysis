/**
 * Multi-tenant header utilities.
 * Provides consistent multi-tenant context management for API requests.
 */

import type { MultiTenantContext, MultiTenantHeaders } from './apiTypes';

export function createMultiTenantHeaders(context: MultiTenantContext): MultiTenantHeaders {
  const headers: MultiTenantHeaders = {};

  if (context.clientAccountId) {
    headers['X-Client-Account-ID'] = context.clientAccountId;
  }

  if (context.engagementId) {
    headers['X-Engagement-ID'] = context.engagementId;
  }

  if (context.userId) {
    headers['X-User-ID'] = context.userId;
  }

  if (context.userRole) {
    headers['X-User-Role'] = context.userRole;
  }

  return headers;
}

export function extractTenantContext(headers: Record<string, string>): MultiTenantContext {
  return {
    clientAccountId: headers['X-Client-Account-ID'] || headers['x-client-account-id'],
    engagementId: headers['X-Engagement-ID'] || headers['x-engagement-id'],
    userId: headers['X-User-ID'] || headers['x-user-id'],
    userRole: headers['X-User-Role'] || headers['x-user-role']
  };
}

export function validateTenantContext(context: MultiTenantContext): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!context.clientAccountId) {
    errors.push('Client Account ID is required');
  }

  if (!context.userId) {
    errors.push('User ID is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}
