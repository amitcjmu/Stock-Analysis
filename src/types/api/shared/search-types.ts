/**
 * Search API Types
 * 
 * Types for search operations, advanced search, and search results.
 */

import { BaseApiRequest, BaseApiResponse, PaginationInfo } from './base-types';
import { MultiTenantContext } from './tenant-types';
import { SortParameter, FilterParameter, AggregationRequest, AggregationResult } from './query-types';

// Basic search
export interface SearchRequest extends BaseApiRequest {
  query: string;
  type?: string[];
  filters?: FilterParameter[];
  sort?: SortParameter[];
  page?: number;
  pageSize?: number;
  highlight?: boolean;
  facets?: string[];
  boost?: BoostParameter[];
  context: MultiTenantContext;
}

export interface SearchResponse<T> extends BaseApiResponse<SearchResult<T>[]> {
  data: SearchResult<T>[];
  query: string;
  took: number;
  totalHits: number;
  maxScore: number;
  facets?: SearchFacet[];
  suggestions?: SearchSuggestion[];
  pagination: PaginationInfo;
}

// Advanced search
export interface AdvancedSearchRequest extends BaseApiRequest {
  criteria: SearchCriteria;
  aggregations?: AggregationRequest[];
  highlight?: HighlightOptions;
  sort?: SortParameter[];
  page?: number;
  pageSize?: number;
  context: MultiTenantContext;
}

export interface AdvancedSearchResponse<T> extends BaseApiResponse<SearchResult<T>[]> {
  data: SearchResult<T>[];
  aggregations?: AggregationResult[];
  suggestions?: SearchSuggestion[];
  statistics: SearchStatistics;
  pagination: PaginationInfo;
}

// Search supporting types
export interface SearchResult<T> {
  item: T;
  score: number;
  highlights?: SearchHighlight[];
  explanation?: SearchExplanation;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface SearchHighlight {
  field: string;
  fragments: string[];
}

export interface SearchExplanation {
  value: number;
  description: string;
  details?: SearchExplanation[];
}

export interface SearchFacet {
  name: string;
  type: string;
  buckets: SearchFacetBucket[];
  missing?: number;
  other?: number;
}

export interface SearchFacetBucket {
  key: unknown;
  label?: string;
  count: number;
  selected?: boolean;
}

export interface SearchSuggestion {
  text: string;
  score: number;
  type: 'term' | 'phrase' | 'completion';
  highlight?: string;
}

export interface SearchStatistics {
  totalHits: number;
  maxScore: number;
  took: number;
  timedOut: boolean;
  shards: ShardStatistics;
}

export interface ShardStatistics {
  total: number;
  successful: number;
  skipped: number;
  failed: number;
}

export interface SearchCriteria {
  query?: string;
  must?: SearchClause[];
  should?: SearchClause[];
  mustNot?: SearchClause[];
  filter?: SearchClause[];
  minimumShouldMatch?: number | string;
}

export interface SearchClause {
  type: 'term' | 'match' | 'range' | 'exists' | 'wildcard' | 'regex' | 'fuzzy';
  field?: string;
  value?: unknown;
  operator?: string;
  boost?: number;
  options?: Record<string, string | number | boolean | null>;
}

export interface HighlightOptions {
  enabled: boolean;
  fields?: string[];
  fragmentSize?: number;
  numberOfFragments?: number;
  preTags?: string[];
  postTags?: string[];
  requireFieldMatch?: boolean;
}

export interface BoostParameter {
  field: string;
  boost: number;
  condition?: Record<string, string | number | boolean | null>;
}