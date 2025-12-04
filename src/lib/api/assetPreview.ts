/**
 * Asset Preview API Service
 *
 * Issue #907: API service for previewing and approving assets before database creation
 * Endpoints: GET /api/v1/asset-preview/{flow_id}, POST /api/v1/asset-preview/{flow_id}/approve
 *
 * CC: Added regenerate capability to refresh stale previews from current cleansed data
 */

import { apiCall } from '@/config/api';

export interface AssetPreviewData {
  id?: string;
  name: string;
  asset_type: string;
  description?: string;
  operating_system?: string;
  os_version?: string;
  hostname?: string;
  ip_address?: string;
  environment?: string;
  location?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;
}

export interface AssetPreviewResponse {
  flow_id: string;
  assets_preview: AssetPreviewData[];
  count: number;
  status: 'preview_ready' | 'assets_already_created' | 'no_data';
  message?: string;
  regenerated?: boolean;
}

export interface ApproveAssetsResponse {
  flow_id: string;
  approved_count: number;
  status: string;
  message: string;
}

/**
 * Get asset preview for a flow
 *
 * CC: Added regenerate parameter to refresh preview from current cleansed data
 *
 * @param flow_id - Master flow UUID
 * @param regenerate - If true, forces regeneration of preview from current raw_import_records
 */
export const getAssetPreview = async (
  flow_id: string,
  regenerate: boolean = false
): Promise<AssetPreviewResponse> => {
  const url = regenerate
    ? `/api/v1/asset-preview/${flow_id}?regenerate=true`
    : `/api/v1/asset-preview/${flow_id}`;

  return apiCall(url, {
    method: 'GET',
  });
};

/**
 * Approve selected assets for creation
 *
 * CRITICAL FIX (Issue #1072): Now accepts updated asset data to preserve user edits
 */
export const approveAssets = async (
  flow_id: string,
  payload: { assetIds: string[]; updatedAssets?: AssetPreviewData[] }
): Promise<ApproveAssetsResponse> => {
  return apiCall(`/api/v1/asset-preview/${flow_id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      approved_asset_ids: payload.assetIds,
      updated_assets: payload.updatedAssets || [],
    }),
  });
};

export const assetPreviewService = {
  getPreview: getAssetPreview,
  approveAssets: approveAssets,
};
