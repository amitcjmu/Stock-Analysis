/**
 * API Type Exports
 *
 * This file re-exports types from the auto-generated OpenAPI schema
 * for convenient consumption throughout the frontend codebase.
 *
 * USAGE:
 *   import type { ApiSchemas, ApiPaths, ApiOperations } from '@/types/generated';
 *   type MyResponse = ApiSchemas['AcceptRecommendationResponse'];
 *
 * REGENERATION:
 *   npm run generate-types
 *
 * DO NOT manually edit api.ts - it is auto-generated from the backend OpenAPI schema.
 */

export type { paths, components, operations, external } from './api';

// Convenience aliases for common usage patterns
import type { paths, components, operations } from './api';

/** All API schema types (request/response bodies) */
export type ApiSchemas = components['schemas'];

/** All API path definitions */
export type ApiPaths = paths;

/** All API operation definitions */
export type ApiOperations = operations;

/**
 * Helper type to extract the response body type for a given operation.
 *
 * @example
 * type HealthResponse = ResponseBody<'health_check_api_v1_health_get'>;
 */
export type ResponseBody<T extends keyof operations> =
  operations[T] extends { responses: { 200: { content: { 'application/json': infer R } } } }
    ? R
    : never;

/**
 * Helper type to extract the request body type for a given operation.
 *
 * @example
 * type CreateFlowRequest = RequestBody<'create_flow_api_v1_flows_post'>;
 */
export type RequestBody<T extends keyof operations> =
  operations[T] extends { requestBody: { content: { 'application/json': infer R } } }
    ? R
    : never;

/**
 * Helper type to extract path parameters for a given operation.
 *
 * @example
 * type FlowParams = PathParams<'get_flow_api_v1_flows__flow_id__get'>;
 */
export type PathParams<T extends keyof operations> =
  operations[T] extends { parameters: { path: infer P } }
    ? P
    : never;

/**
 * Helper type to extract query parameters for a given operation.
 *
 * @example
 * type ListFlowsQuery = QueryParams<'list_flows_api_v1_flows_get'>;
 */
export type QueryParams<T extends keyof operations> =
  operations[T] extends { parameters: { query?: infer Q } }
    ? Q
    : never;
