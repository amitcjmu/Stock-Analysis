/**
 * Asset Conflict Resolution API Service
 *
 * Handles API communication for duplicate asset conflict detection and resolution.
 * Integrates with backend endpoints at /api/v1/asset-conflicts/
 *
 * CC: All API calls use snake_case fields (no transformation) per API_REQUEST_PATTERNS.md
 */

import { apiCall } from '@/config/api';
import type {
  AssetConflict,
  BulkConflictResolutionRequest,
  ConflictResolutionResponse,
} from '@/types/assetConflict';

/**
 * List pending asset conflicts for a discovery flow
 *
 * GET /api/v1/asset-conflicts/list
 *
 * @param flow_id - Discovery flow UUID (master flow ID)
 * @param data_import_id - Optional filter by specific data import
 * @returns Array of conflict details with side-by-side comparison
 */
export async function listAssetConflicts(
  flow_id: string,
  data_import_id?: string
): Promise<AssetConflict[]> {
  try {
    // Build query parameters for GET request
    const params = new URLSearchParams({ flow_id });
    if (data_import_id) {
      params.append('data_import_id', data_import_id);
    }

    // GET request uses query parameters (per API_REQUEST_PATTERNS.md)
    const response = await apiCall(
      `/api/v1/asset-conflicts/list?${params.toString()}`,
      { method: 'GET' }
    );

    // Backend returns array of AssetConflictDetail
    return response as AssetConflict[];
  } catch (error) {
    console.error('Failed to list asset conflicts:', error);
    throw error;
  }
}

/**
 * Resolve multiple conflicts in bulk
 *
 * POST /api/v1/asset-conflicts/resolve-bulk
 *
 * CRITICAL: POST must use request body (NOT query params) per API_REQUEST_PATTERNS.md
 *
 * @param request - Bulk resolution request with array of resolutions
 * @returns Resolution response with success count and errors
 */
export async function resolveAssetConflicts(
  request: BulkConflictResolutionRequest
): Promise<ConflictResolutionResponse> {
  try {
    // POST request MUST use request body (per API_REQUEST_PATTERNS.md)
    const response = await apiCall('/api/v1/asset-conflicts/resolve-bulk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request), // ✅ CORRECT - using request body
    });

    return response as ConflictResolutionResponse;
  } catch (error) {
    console.error('Failed to resolve asset conflicts:', error);
    throw error;
  }
}

/**
 * Convenience wrapper for single conflict resolution
 */
export async function resolveSingleConflict(
  conflict_id: string,
  resolution_action: 'keep_existing' | 'replace_with_new' | 'merge',
  merge_field_selections?: Record<string, 'existing' | 'new'>
): Promise<ConflictResolutionResponse> {
  return resolveAssetConflicts({
    resolutions: [
      {
        conflict_id,
        resolution_action,
        merge_field_selections,
      },
    ],
  });
}

/**
 * Asset Conflict Service - default export
 */
export const assetConflictService = {
  listConflicts: listAssetConflicts,
  resolveConflicts: resolveAssetConflicts,
  resolveSingle: resolveSingleConflict,
};
