/**
 * Asset Preview API Service
 *
 * Issue #907: API service for previewing and approving assets before database creation
 * Endpoints: GET /api/v1/asset-preview/{flow_id}, POST /api/v1/asset-preview/{flow_id}/approve
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
  status: 'preview_ready' | 'assets_already_created';
  message?: string;
}

export interface ApproveAssetsResponse {
  flow_id: string;
  approved_count: number;
  status: string;
  message: string;
}

/**
 * Get asset preview for a flow
 */
export const getAssetPreview = async (
  flow_id: string
): Promise<AssetPreviewResponse> => {
  return apiCall(`/api/v1/asset-preview/${flow_id}`, {
    method: 'GET',
  });
};

/**
 * Approve selected assets for creation
 */
export const approveAssets = async (
  flow_id: string,
  asset_ids: string[]
): Promise<ApproveAssetsResponse> => {
  return apiCall(`/api/v1/asset-preview/${flow_id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_asset_ids: asset_ids }), // Pydantic model expects object
  });
};

export const assetPreviewService = {
  getPreview: getAssetPreview,
  approveAssets: approveAssets,
};
