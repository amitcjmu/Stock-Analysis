/**
 * Asset API Client
 *
 * Provides a clean interface for asset-related API operations
 * using the unified Asset model.
 */

import { apiCall, API_CONFIG } from '../../config/api';
import type {
  Asset,
  AssetListResponse,
  AssetSummary,
  AssetFilterParams,
  BulkAssetUpdate
} from '../../types/asset';

export class AssetAPI {
  /**
   * Get a paginated list of assets with optional filtering
   */
  static async getAssets(params: AssetFilterParams = {}): Promise<AssetListResponse> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());
    if (params.asset_type && params.asset_type !== 'all') queryParams.append('asset_type', params.asset_type);
    if (params.environment && params.environment !== 'all') queryParams.append('environment', params.environment);
    if (params.department && params.department !== 'all') queryParams.append('department', params.department);
    if (params.business_criticality && params.business_criticality !== 'all') queryParams.append('business_criticality', params.business_criticality);
    if (params.search) queryParams.append('search', params.search);

    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${queryParams}`;
    return await apiCall(endpoint);
  }

  /**
   * Get asset summary statistics
   */
  static async getAssetSummary(filters: Omit<AssetFilterParams, 'page' | 'page_size'> = {}): Promise<AssetSummary> {
    const queryParams = new URLSearchParams();

    if (filters.asset_type && filters.asset_type !== 'all') queryParams.append('asset_type', filters.asset_type);
    if (filters.environment && filters.environment !== 'all') queryParams.append('environment', filters.environment);
    if (filters.department && filters.department !== 'all') queryParams.append('department', filters.department);
    if (filters.business_criticality && filters.business_criticality !== 'all') queryParams.append('business_criticality', filters.business_criticality);
    if (filters.search) queryParams.append('search', filters.search);

    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/summary?${queryParams}`;
    return await apiCall(endpoint);
  }

  /**
   * Get a single asset by ID
   */
  static async getAsset(id: number): Promise<Asset> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${id}`;
    return await apiCall(endpoint);
  }

  /**
   * Create a new asset
   */
  static async createAsset(asset: Omit<Asset, 'id' | 'created_at' | 'updated_at'>): Promise<Asset> {
    const endpoint = API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS;
    return await apiCall(endpoint, {
      method: 'POST',
      body: JSON.stringify(asset)
    });
  }

  /**
   * Update an existing asset
   */
  static async updateAsset(id: number, updates: Partial<Asset>): Promise<Asset> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${id}`;
    return await apiCall(endpoint, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  /**
   * Delete an asset
   */
  static async deleteAsset(id: number): Promise<void> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${id}`;
    await apiCall(endpoint, {
      method: 'DELETE'
    });
  }

  /**
   * Bulk update multiple assets
   */
  static async bulkUpdateAssets(bulkUpdate: BulkAssetUpdate): Promise<{ updated_count: number }> {
    const endpoint = API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_BULK;
    return await apiCall(endpoint, {
      method: 'PUT',
      body: JSON.stringify(bulkUpdate)
    });
  }

  /**
   * Bulk delete multiple assets
   */
  static async bulkDeleteAssets(assetIds: string[]): Promise<{ deleted_count: number }> {
    const endpoint = API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_BULK;
    return await apiCall(endpoint, {
      method: 'DELETE',
      body: JSON.stringify({ asset_ids: assetIds })
    });
  }

  /**
   * Clean up duplicate assets
   */
  static async cleanupDuplicates(): Promise<{ removed_count: number; kept_count: number }> {
    const endpoint = API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS_CLEANUP;
    return await apiCall(endpoint, {
      method: 'POST'
    });
  }

  /**
   * Export assets to CSV
   */
  static async exportAssets(filters: AssetFilterParams = {}): Promise<Blob> {
    const queryParams = new URLSearchParams();

    if (filters.asset_type && filters.asset_type !== 'all') queryParams.append('asset_type', filters.asset_type);
    if (filters.environment && filters.environment !== 'all') queryParams.append('environment', filters.environment);
    if (filters.department && filters.department !== 'all') queryParams.append('department', filters.department);
    if (filters.business_criticality && filters.business_criticality !== 'all') queryParams.append('business_criticality', filters.business_criticality);
    if (filters.search) queryParams.append('search', filters.search);

    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/export?${queryParams}`;
    const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': 'Bearer demo_token' // This should come from auth context in production
      }
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status} - ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Update a single field on an asset (Issue #911: AI Grid inline editing)
   */
  static async updateAssetField(
    asset_id: number,
    field_name: string,
    field_value: string | number | boolean | null
  ): Promise<Asset> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${asset_id}/fields/${field_name}`;

    return await apiCall(endpoint, {
      method: 'PATCH',
      body: { value: field_value }
    });
  }

  /**
   * Bulk update a single field on multiple assets (Issue #911: AI Grid bulk editing)
   */
  static async bulkUpdateAssetField(
    asset_ids: number[],
    field_name: string,
    field_value: string | number | boolean | null
  ): Promise<{ updated_count: number }> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/bulk-update`;
    return await apiCall(endpoint, {
      method: 'PATCH',
      body: JSON.stringify({
        updates: asset_ids.map(asset_id => ({
          asset_id,
          field_name,
          value: field_value
        }))
      })
    });
  }

  /**
   * Soft delete an asset (Issue #912: Soft delete functionality)
   */
  static async softDeleteAsset(asset_id: number): Promise<void> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${asset_id}`;
    await apiCall(endpoint, {
      method: 'DELETE'
    });
  }

  /**
   * Restore a soft-deleted asset (Issue #912: Soft delete functionality)
   */
  static async restoreAsset(asset_id: number): Promise<Asset> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${asset_id}/restore`;
    return await apiCall(endpoint, {
      method: 'POST'
    });
  }

  /**
   * Bulk soft delete multiple assets (Issue #912: Soft delete functionality)
   */
  static async bulkSoftDelete(asset_ids: number[]): Promise<{ deleted_count: number }> {
    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/bulk-delete`;
    return await apiCall(endpoint, {
      method: 'DELETE',
      body: JSON.stringify({
        asset_ids
      })
    });
  }

  /**
   * Get deleted (soft-deleted) assets (Issue #912: Trash view)
   */
  static async getDeletedAssets(flow_id?: string): Promise<Asset[]> {
    const queryParams = new URLSearchParams();
    if (flow_id) queryParams.append('flow_id', flow_id);
    queryParams.append('deleted', 'true');

    const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?${queryParams}`;
    const response = await apiCall<AssetListResponse>(endpoint);
    return response.assets;
  }
}
