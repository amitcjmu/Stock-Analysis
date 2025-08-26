/**
 * Canonical Application Types - Application Identity and Deduplication
 *
 * These interfaces support the application deduplication system that allows
 * users to enter free-form application names while detecting and preventing
 * duplicates across multi-tenant boundaries.
 */

export interface CanonicalApplication {
  id: string;
  client_account_id: string;
  engagement_id: string;
  canonical_name: string;
  description?: string;
  variants: ApplicationVariant[];
  collection_history: CollectionHistoryEntry[];
  metadata: ApplicationMetadata;
  created_at: string;
  updated_at: string;
}

export interface ApplicationVariant {
  id: string;
  canonical_application_id: string;
  variant_name: string;
  normalized_name: string; // Lowercased, trimmed version for matching
  similarity_score: number; // Confidence score when matched
  source: ApplicationVariantSource;
  asset_id?: string; // Link to Asset if from discovery
  collection_flow_id?: string; // Link to collection where it was added
  created_by?: string;
  created_at: string;
}

export interface ApplicationMetadata {
  total_variants: number;
  last_collected_at?: string;
  collection_count: number;
  primary_environment?: string;
  business_criticality?: string;
  tags?: string[];
}

export interface CollectionHistoryEntry {
  id: string;
  collection_flow_id: string;
  flow_name?: string;
  collected_at: string;
  status: 'completed' | 'in_progress' | 'failed';
  variant_name: string;
  collector?: string;
}

export type ApplicationVariantSource =
  | 'discovery'
  | 'collection_manual'
  | 'collection_import'
  | 'admin_created';

export interface SimilarityMatch {
  canonical_application: CanonicalApplication;
  confidence_score: number;
  matching_variants: ApplicationVariant[];
  match_type: SimilarityMatchType;
  match_reasons: string[];
}

export type SimilarityMatchType =
  | 'exact'
  | 'case_insensitive'
  | 'fuzzy_high'
  | 'fuzzy_medium'
  | 'fuzzy_low'
  | 'partial_token'
  | 'acronym';

export interface ApplicationSuggestion {
  id: string;
  canonical_application: CanonicalApplication;
  display_text: string;
  confidence_score: number;
  match_type: SimilarityMatchType;
  highlighted_text?: string; // HTML with <mark> tags for highlighting
}

export interface SimilaritySearchRequest {
  query: string;
  client_account_id: string;
  engagement_id: string;
  min_confidence?: number;
  max_results?: number;
  include_variants?: boolean;
}

export interface SimilaritySearchResponse {
  matches: SimilarityMatch[];
  suggestions: ApplicationSuggestion[];
  search_metadata: {
    query: string;
    total_canonical_apps: number;
    search_duration_ms: number;
    algorithms_used: string[];
  };
}

export interface CreateCanonicalApplicationRequest {
  canonical_name: string;
  description?: string;
  initial_variant_name?: string;
  source: ApplicationVariantSource;
  metadata?: Partial<ApplicationMetadata>;
}

export interface LinkToCanonicalApplicationRequest {
  canonical_application_id: string;
  variant_name: string;
  source: ApplicationVariantSource;
  collection_flow_id?: string;
}

// UI State Types
export interface ApplicationInputState {
  value: string;
  suggestions: ApplicationSuggestion[];
  is_loading: boolean;
  show_suggestions: boolean;
  selected_index: number;
  error?: string;
}

export interface DuplicateDetectionState {
  is_open: boolean;
  user_input: string;
  detected_matches: SimilarityMatch[];
  selected_match?: SimilarityMatch;
  user_decision?: DuplicateDecision;
}

export type DuplicateDecision =
  | 'use_existing'
  | 'create_new'
  | 'cancelled';

export interface ApplicationDeduplicationConfig {
  confidence_thresholds: {
    auto_suggest: number; // 0.95+ - Green checkmark, auto-suggest
    duplicate_warning: number; // 0.80+ - Yellow warning, show modal
    suggestion_dropdown: number; // 0.60+ - Gray suggestion in dropdown
    min_confidence: number; // 0.40+ - Minimum to consider
  };
  debounce_ms: number;
  max_suggestions: number;
  cache_duration_ms: number;
}

export const DEFAULT_DEDUPLICATION_CONFIG: ApplicationDeduplicationConfig = {
  confidence_thresholds: {
    auto_suggest: 0.95,
    duplicate_warning: 0.80,
    suggestion_dropdown: 0.60,
    min_confidence: 0.40,
  },
  debounce_ms: 300,
  max_suggestions: 8,
  cache_duration_ms: 5 * 60 * 1000, // 5 minutes
};

// Collection Integration Types
export interface CanonicalApplicationSelection {
  canonical_application_id: string;
  canonical_name: string;
  variant_name: string; // The specific variant name user entered/selected
  selection_method: 'autocomplete' | 'manual_entry' | 'duplicate_resolution';
}

export interface CollectionFlowApplicationConfig {
  canonical_applications: CanonicalApplicationSelection[];
  total_applications: number;
  deduplication_stats: {
    duplicates_detected: number;
    duplicates_resolved: number;
    new_applications_created: number;
  };
}
