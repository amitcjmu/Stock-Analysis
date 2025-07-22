/**
 * Custom hook for fetching demo data from the backend API.
 * Replaces hardcoded mock data with persistent database-backed demo data.
 */

import { useState, useEffect, useCallback } from 'react';

// Base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEMO_API_BASE = `${API_BASE_URL}/api/v1/demo`;

// Types for the demo data
export interface DemoAsset {
  id: string;
  name: string;
  hostname?: string;
  asset_type?: string;
  description?: string;
  ip_address?: string;
  fqdn?: string;
  environment?: string;
  location?: string;
  datacenter?: string;
  operating_system?: string;
  os_version?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;
  business_owner?: string;
  department?: string;
  application_name?: string;
  technology_stack?: string;
  criticality?: string;
  status?: string;
  six_r_strategy?: string;
  migration_complexity?: string;
  migration_wave?: number;
  sixr_ready?: string;
  dependencies?: string[];
  related_assets?: string[];
  discovery_method?: string;
  discovery_source?: string;
  discovery_timestamp?: string;
  cpu_utilization_percent?: number;
  memory_utilization_percent?: number;
  disk_iops?: number;
  network_throughput_mbps?: number;
  current_monthly_cost?: number;
  estimated_cloud_cost?: number;
  tags?: DemoTag[];
  created_at?: string;
  updated_at?: string;
}

export interface DemoTag {
  id: string;
  name: string;
  category: string;
  description?: string;
  confidence_score?: number;
  assigned_method?: string;
  is_validated?: boolean;
}

export interface DemoSixRAnalysis {
  id: string;
  analysis_name: string;
  description?: string;
  status: string;
  total_assets: number;
  rehost_count: number;
  replatform_count: number;
  refactor_count: number;
  rearchitect_count: number;
  retire_count: number;
  retain_count: number;
  total_current_cost: number;
  total_estimated_cost: number;
  potential_savings: number;
  analysis_results?: unknown;
  recommendations?: unknown;
  created_at?: string;
}

export interface DemoMigrationWave {
  id: string;
  wave_number: number;
  name: string;
  description?: string;
  status: string;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  total_assets: number;
  completed_assets: number;
  failed_assets: number;
  estimated_cost?: number;
  actual_cost?: number;
  estimated_effort_hours?: number;
  actual_effort_hours?: number;
  created_at?: string;
}

export interface DemoEngagement {
  id: string;
  name: string;
  slug: string;
  description?: string;
  status: string;
  priority?: string;
  start_date?: string;
  target_completion_date?: string;
}

export interface DemoClientAccount {
  id: string;
  name: string;
  slug: string;
  description?: string;
  industry?: string;
  company_size?: string;
}

export interface DemoAssetSummary {
  total_assets: number;
  asset_types: Record<string, number>;
  six_r_strategies: Record<string, number>;
  cost_summary: {
    total_current_cost: number;
    total_estimated_cost: number;
    potential_savings: number;
  };
  demo_mode: boolean;
  has_real_data: boolean;
}

export interface AssetFilters {
  asset_type?: string;
  environment?: string;
  criticality?: string;
  six_r_strategy?: string;
  migration_wave?: number;
  limit?: number;
  offset?: number;
}

export interface SimilaritySearchResult {
  source_asset: {
    id: string;
    name: string;
    type?: string;
    description?: string;
  };
  similar_assets: Array<{
    asset: DemoAsset;
    similarity_score: number;
    source_text: string;
  }>;
  total_found: number;
}

// API utility functions
const apiRequest = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  try {
    const response = await fetch(`${DEMO_API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error(`API request error for ${endpoint}:`, error);
    throw error;
  }
};

// Hook for fetching demo assets
export const useDemoAssets = (filters?: AssetFilters) => {
  const [assets, setAssets] = useState<DemoAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      
      if (filters?.asset_type) params.append('asset_type', filters.asset_type);
      if (filters?.environment) params.append('environment', filters.environment);
      if (filters?.criticality) params.append('criticality', filters.criticality);
      if (filters?.six_r_strategy) params.append('six_r_strategy', filters.six_r_strategy);
      if (filters?.migration_wave !== undefined) params.append('migration_wave', filters.migration_wave.toString());
      if (filters?.limit) params.append('limit', filters.limit.toString());
      if (filters?.offset) params.append('offset', filters.offset.toString());

      const queryString = params.toString();
      const endpoint = `/assets${queryString ? `?${queryString}` : ''}`;
      
      const data = await apiRequest<DemoAsset[]>(endpoint);
      setAssets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch assets');
      console.error('Error fetching demo assets:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  return { assets, loading, error, refetch: fetchAssets };
};

// Hook for fetching a single demo asset
export const useDemoAsset = (assetId: string | null) => {
  const [asset, setAsset] = useState<DemoAsset | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAsset = useCallback(async () => {
    if (!assetId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<DemoAsset>(`/assets/${assetId}`);
      setAsset(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch asset');
      console.error('Error fetching demo asset:', err);
    } finally {
      setLoading(false);
    }
  }, [assetId]);

  useEffect(() => {
    fetchAsset();
  }, [fetchAsset]);

  return { asset, loading, error, refetch: fetchAsset };
};

// Hook for fetching demo assets summary
export const useDemoAssetsSummary = () => {
  const [summary, setSummary] = useState<DemoAssetSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<DemoAssetSummary>('/assets/summary');
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch summary');
      console.error('Error fetching demo assets summary:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return { summary, loading, error, refetch: fetchSummary };
};

// Hook for fetching 6R analyses
export const useDemoSixRAnalyses = (limit?: number) => {
  const [analyses, setAnalyses] = useState<DemoSixRAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyses = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (limit) params.append('limit', limit.toString());
      
      const queryString = params.toString();
      const endpoint = `/sixr-analyses${queryString ? `?${queryString}` : ''}`;
      
      const data = await apiRequest<DemoSixRAnalysis[]>(endpoint);
      setAnalyses(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analyses');
      console.error('Error fetching demo 6R analyses:', err);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  return { analyses, loading, error, refetch: fetchAnalyses };
};

// Hook for fetching migration waves
export const useDemoMigrationWaves = (status?: string) => {
  const [waves, setWaves] = useState<DemoMigrationWave[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWaves = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      
      const queryString = params.toString();
      const endpoint = `/migration-waves${queryString ? `?${queryString}` : ''}`;
      
      const data = await apiRequest<DemoMigrationWave[]>(endpoint);
      setWaves(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch migration waves');
      console.error('Error fetching demo migration waves:', err);
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    fetchWaves();
  }, [fetchWaves]);

  return { waves, loading, error, refetch: fetchWaves };
};

// Hook for fetching tags
export const useDemoTags = (category?: string) => {
  const [tags, setTags] = useState<DemoTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTags = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      
      const queryString = params.toString();
      const endpoint = `/tags${queryString ? `?${queryString}` : ''}`;
      
      const data = await apiRequest<DemoTag[]>(endpoint);
      setTags(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tags');
      console.error('Error fetching demo tags:', err);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  return { tags, loading, error, refetch: fetchTags };
};

// Hook for engagement information
export const useDemoEngagement = () => {
  const [engagementInfo, setEngagementInfo] = useState<{
    client_account: DemoClientAccount | null;
    engagement: DemoEngagement | null;
    demo_mode: boolean;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEngagementInfo = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<{
        client_account: DemoClientAccount | null;
        engagement: DemoEngagement | null;
        demo_mode: boolean;
      }>('/engagement-info');
      setEngagementInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch engagement info');
      console.error('Error fetching demo engagement info:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEngagementInfo();
  }, [fetchEngagementInfo]);

  return { engagementInfo, loading, error, refetch: fetchEngagementInfo };
};

// Hook for similarity search
export const useSimilaritySearch = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchSimilarAssets = useCallback(async (
    assetId: string,
    topK: number = 5,
    similarityThreshold: number = 0.7
  ): Promise<SimilaritySearchResult | null> => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        top_k: topK.toString(),
        similarity_threshold: similarityThreshold.toString(),
      });

      const data = await apiRequest<SimilaritySearchResult>(
        `/assets/${assetId}/similarity-search?${params}`,
        { method: 'POST' }
      );
      
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search similar assets');
      console.error('Error searching similar assets:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const searchAssetsByText = useCallback(async (
    queryText: string,
    topK: number = 10,
    similarityThreshold: number = 0.5
  ): Promise<{ query: string; assets: unknown[]; total_found: number } | null> => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        query_text: queryText,
        top_k: topK.toString(),
        similarity_threshold: similarityThreshold.toString(),
      });

      const data = await apiRequest<{
        query: string;
        assets: unknown[];
        total_found: number;
      }>(`/assets/text-search?${params}`, { method: 'POST' });
      
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search assets by text');
      console.error('Error searching assets by text:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const autoTagAsset = useCallback(async (assetId: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<{
        asset_id: string;
        message: string;
        assigned_tags: unknown[];
      }>(`/assets/${assetId}/auto-tag`, { method: 'POST' });
      
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to auto-tag asset');
      console.error('Error auto-tagging asset:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    searchSimilarAssets,
    searchAssetsByText,
    autoTagAsset,
    loading,
    error,
  };
};

// Combined hook for dashboard data
export const useDemoDashboard = () => {
  const { assets, loading: assetsLoading, error: assetsError } = useDemoAssets({ limit: 10 });
  const { summary, loading: summaryLoading, error: summaryError } = useDemoAssetsSummary();
  const { analyses, loading: analysesLoading, error: analysesError } = useDemoSixRAnalyses(1);
  const { waves, loading: wavesLoading, error: wavesError } = useDemoMigrationWaves();
  const { engagementInfo, loading: engagementLoading, error: engagementError } = useDemoEngagement();

  const loading = assetsLoading || summaryLoading || analysesLoading || wavesLoading || engagementLoading;
  const error = assetsError || summaryError || analysesError || wavesError || engagementError;

  return {
    assets,
    summary,
    analyses,
    waves,
    engagementInfo,
    loading,
    error,
  };
}; 