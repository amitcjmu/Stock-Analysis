/**
 * Applications API Service
 *
 * Provides interface for fetching application data from the Asset table.
 * All field names use snake_case per CLAUDE.md field naming convention.
 *
 * CC Generated Service
 */

import { apiCall, API_CONFIG } from '@/config/api';

// =============================================================================
// Types (snake_case per CLAUDE.md)
// =============================================================================

export interface Application {
  id: string;
  application_name: string | null;
  asset_name: string | null;
  six_r_strategy: string | null;
  tech_stack: string | null;
  complexity_score: number | null;
  asset_type: string | null;
}

export interface ApplicationsListResponse {
  applications: Application[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GetApplicationsParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// =============================================================================
// API Service
// =============================================================================

export const applicationsApi = {
  /**
   * Fetch applications with pagination and optional search
   *
   * @param params Query parameters (page, page_size, search)
   * @returns Paginated list of applications
   */
  async getApplications(
    params: GetApplicationsParams = {}
  ): Promise<ApplicationsListResponse> {
    const queryParams = new URLSearchParams();

    // Add pagination params
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());

    // Add search filter
    if (params.search) queryParams.append('search', params.search);

    const query = queryParams.toString();
    const endpoint = `/api/v1/applications${query ? `?${query}` : ''}`;

    return await apiCall(endpoint);
  },
};
