import { apiCall } from '@/config/api';
import type {
  CanonicalApplication,
  SimilaritySearchRequest,
  SimilaritySearchResponse,
  CreateCanonicalApplicationRequest,
  LinkToCanonicalApplicationRequest,
  ApplicationSuggestion,
  CollectionHistoryEntry,
  ApplicationVariant,
} from '@/types/collection/canonical-applications';

/**
 * Canonical Applications API Service
 *
 * Handles all API operations for application identity management and deduplication.
 * Includes real-time similarity search, canonical application CRUD operations,
 * and integration with the collection flow system.
 */
class CanonicalApplicationsApi {
  private readonly baseUrl = '/api/v1/canonical-applications';

  /**
   * Get all canonical applications for the current tenant/engagement
   */
  async getCanonicalApplications(params?: {
    limit?: number;
    offset?: number;
    search?: string;
    include_variants?: boolean;
    include_history?: boolean;
  }): Promise<{
    applications: CanonicalApplication[];
    total_count: number;
    has_more: boolean;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.search) searchParams.append('search', params.search);
    if (params?.include_variants) searchParams.append('include_variants', 'true');
    if (params?.include_history) searchParams.append('include_history', 'true');

    const queryString = searchParams.toString();
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;

    return await apiCall(url, { method: 'GET' });
  }

  /**
   * Get a specific canonical application by ID
   */
  async getCanonicalApplication(
    id: string,
    includeVariants: boolean = true,
    includeHistory: boolean = true
  ): Promise<CanonicalApplication> {
    const params = new URLSearchParams();
    if (includeVariants) params.append('include_variants', 'true');
    if (includeHistory) params.append('include_history', 'true');

    return await apiCall(
      `${this.baseUrl}/${id}?${params.toString()}`,
      { method: 'GET' }
    );
  }

  /**
   * Search for similar application names with confidence scoring
   * This is the core deduplication functionality
   */
  async searchSimilar(request: SimilaritySearchRequest): Promise<SimilaritySearchResponse> {
    return await apiCall(`${this.baseUrl}/search-similar`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get autocomplete suggestions for application names
   * Lightweight version of similarity search optimized for real-time typing
   */
  async getSuggestions(
    query: string,
    maxResults: number = 8
  ): Promise<ApplicationSuggestion[]> {
    if (!query.trim() || query.length < 2) {
      return [];
    }

    const params = new URLSearchParams({
      q: query.trim(),
      limit: maxResults.toString(),
    });

    try {
      const response = await apiCall(`${this.baseUrl}/suggestions?${params.toString()}`, {
        method: 'GET',
      });
      return response.suggestions || [];
    } catch (error) {
      console.warn('Failed to fetch application suggestions:', error);
      return [];
    }
  }

  /**
   * Create a new canonical application
   */
  async createCanonicalApplication(
    request: CreateCanonicalApplicationRequest
  ): Promise<CanonicalApplication> {
    return await apiCall(this.baseUrl, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Link a variant name to an existing canonical application
   */
  async linkToCanonicalApplication(
    request: LinkToCanonicalApplicationRequest
  ): Promise<{
    canonical_application: CanonicalApplication;
    created_variant: ApplicationVariant;
  }> {
    return await apiCall(`${this.baseUrl}/link-variant`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Update a canonical application
   */
  async updateCanonicalApplication(
    id: string,
    updates: {
      canonical_name?: string;
      description?: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<CanonicalApplication> {
    return await apiCall(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete a canonical application (admin operation)
   * This will also handle reassignment of variants if needed
   */
  async deleteCanonicalApplication(
    id: string,
    reassignTo?: string
  ): Promise<{ status: string; message: string; reassigned_variants?: number }> {
    const body = reassignTo ? JSON.stringify({ reassign_to: reassignTo }) : undefined;

    return await apiCall(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
      body,
    });
  }

  /**
   * Get collection history for a canonical application
   */
  async getCollectionHistory(
    id: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{
    history: CollectionHistoryEntry[];
    total_count: number;
    has_more: boolean;
  }> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    return await apiCall(
      `${this.baseUrl}/${id}/history?${params.toString()}`,
      { method: 'GET' }
    );
  }

  /**
   * Get variants for a canonical application
   */
  async getVariants(
    id: string,
    includeAssetDetails: boolean = false
  ): Promise<ApplicationVariant[]> {
    const params = new URLSearchParams();
    if (includeAssetDetails) params.append('include_assets', 'true');

    const response = await apiCall(
      `${this.baseUrl}/${id}/variants?${params.toString()}`,
      { method: 'GET' }
    );
    return response.variants || [];
  }

  /**
   * Merge two canonical applications
   * This is an advanced operation for admin users
   */
  async mergeCanonicalApplications(
    primaryId: string,
    secondaryId: string,
    mergeStrategy: 'keep_primary_name' | 'keep_secondary_name' | 'custom_name',
    customName?: string
  ): Promise<{
    merged_application: CanonicalApplication;
    merged_variants_count: number;
    merged_history_count: number;
  }> {
    return await apiCall(`${this.baseUrl}/merge`, {
      method: 'POST',
      body: JSON.stringify({
        primary_id: primaryId,
        secondary_id: secondaryId,
        merge_strategy: mergeStrategy,
        custom_name: customName,
      }),
    });
  }

  /**
   * Get deduplication statistics for the current engagement
   */
  async getDeduplicationStats(): Promise<{
    total_canonical_applications: number;
    total_variants: number;
    duplicates_detected_last_30_days: number;
    duplicates_resolved_last_30_days: number;
    top_variant_sources: Array<{ source: string; count: number }>;
    most_variants_applications: Array<{
      canonical_application: CanonicalApplication;
      variant_count: number;
    }>;
  }> {
    return await apiCall(`${this.baseUrl}/stats`, { method: 'GET' });
  }

  /**
   * Batch process application names from collection flow
   * This handles deduplication for bulk operations
   */
  async batchProcessApplicationNames(
    applicationNames: string[],
    collectionFlowId: string,
    autoResolveThreshold: number = 0.95
  ): Promise<{
    processed_applications: Array<{
      input_name: string;
      canonical_application: CanonicalApplication;
      variant: ApplicationVariant;
      was_auto_resolved: boolean;
      confidence_score?: number;
    }>;
    requires_manual_resolution: Array<{
      input_name: string;
      potential_matches: Array<{
        canonical_application: CanonicalApplication;
        confidence_score: number;
      }>;
    }>;
    processing_stats: {
      total_processed: number;
      auto_resolved: number;
      requires_manual: number;
      new_canonical_created: number;
    };
  }> {
    return await apiCall(`${this.baseUrl}/batch-process`, {
      method: 'POST',
      body: JSON.stringify({
        application_names: applicationNames,
        collection_flow_id: collectionFlowId,
        auto_resolve_threshold: autoResolveThreshold,
      }),
    });
  }
}

export const canonicalApplicationsApi = new CanonicalApplicationsApi();
