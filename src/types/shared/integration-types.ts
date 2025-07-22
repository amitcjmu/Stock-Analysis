/**
 * Shared Integration Type Definitions
 * 
 * Standardized types for external API integrations, adapters, and connectors
 * to replace any types in integration layer code
 */

import { ApiResponse, ApiError } from './api-types';
import { ConfigurationValue } from './config-types';
import { BaseMetadata } from './metadata-types';

/**
 * Generic external API integration response wrapper
 */
export interface ExternalIntegrationResponse<TData = unknown> extends ApiResponse<TData> {
  /** External service identifier */
  serviceId?: string;
  /** Integration protocol used */
  protocol?: 'REST' | 'GraphQL' | 'SOAP' | 'gRPC' | 'WebSocket';
  /** External API version */
  apiVersion?: string;
  /** Rate limit information from external service */
  rateLimitInfo?: {
    remaining: number;
    resetTime: string;
    limit: number;
  };
}

/**
 * External service configuration for adapters
 */
export interface ExternalServiceConfig extends BaseMetadata {
  /** Service endpoint URL */
  endpoint: string;
  /** Authentication configuration */
  authentication: {
    type: 'bearer' | 'api_key' | 'basic' | 'oauth' | 'custom';
    credentials: Record<string, string>;
    refreshable?: boolean;
  };
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Retry configuration */
  retry?: {
    attempts: number;
    backoffMs: number;
    retryOnStatus: number[];
  };
  /** Custom headers for all requests */
  headers?: Record<string, string>;
}

/**
 * Data transformation mapping for external integrations
 */
export interface DataTransformationMapping {
  /** Source field path (dot notation supported) */
  sourceField: string;
  /** Target field path in internal format */
  targetField: string;
  /** Transformation function type */
  transform?: 'uppercase' | 'lowercase' | 'trim' | 'parse_date' | 'parse_number' | 'custom';
  /** Custom transformation function name */
  customTransform?: string;
  /** Default value if source is null/undefined */
  defaultValue?: ConfigurationValue;
  /** Whether field is required */
  required?: boolean;
  /** Validation rules */
  validation?: {
    type?: 'string' | 'number' | 'boolean' | 'date' | 'email' | 'url';
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    allowedValues?: ConfigurationValue[];
  };
}

/**
 * External connector interface for third-party integrations
 */
export interface ExternalConnector {
  /** Unique connector identifier */
  connectorId: string;
  /** Connector display name */
  name: string;
  /** Connector type/category */
  type: 'database' | 'api' | 'file' | 'messaging' | 'streaming' | 'cloud_service';
  /** Connection configuration */
  config: ExternalServiceConfig;
  /** Data transformation mappings */
  mappings?: DataTransformationMapping[];
  /** Connector status */
  status: 'connected' | 'disconnected' | 'error' | 'configuring';
  /** Last successful connection timestamp */
  lastConnected?: string;
  /** Connection health check interval in seconds */
  healthCheckInterval?: number;
}

/**
 * External API request payload with validation
 */
export interface ExternalApiRequestPayload {
  /** Request method */
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Request endpoint path */
  path: string;
  /** Query parameters */
  queryParams?: Record<string, string | number | boolean>;
  /** Request body */
  body?: Record<string, unknown> | string | FormData;
  /** Additional headers */
  headers?: Record<string, string>;
  /** Request-specific timeout override */
  timeout?: number;
}

/**
 * Adapter interface for external service integration
 */
export interface ExternalServiceAdapter<TInput = unknown, TOutput = unknown> {
  /** Adapter identifier */
  adapterId: string;
  /** Service configuration */
  config: ExternalServiceConfig;
  /** Connect to external service */
  connect(): Promise<boolean>;
  /** Disconnect from external service */
  disconnect(): Promise<void>;
  /** Test connection health */
  healthCheck(): Promise<boolean>;
  /** Transform data from external format to internal format */
  transformInbound(data: TInput): Promise<TOutput>;
  /** Transform data from internal format to external format */
  transformOutbound(data: TOutput): Promise<TInput>;
  /** Execute external API request */
  executeRequest(payload: ExternalApiRequestPayload): Promise<ExternalIntegrationResponse>;
  /** Get adapter status */
  getStatus(): Promise<{
    connected: boolean;
    lastHealth: string;
    errorCount: number;
    lastError?: ApiError;
  }>;
}

/**
 * Bridge interface for connecting different external systems
 */
export interface ExternalBridge<TSourceData = unknown, TTargetData = unknown> {
  /** Bridge identifier */
  bridgeId: string;
  /** Source system adapter */
  sourceAdapter: ExternalServiceAdapter<TSourceData, unknown>;
  /** Target system adapter */
  targetAdapter: ExternalServiceAdapter<unknown, TTargetData>;
  /** Data synchronization configuration */
  syncConfig: {
    direction: 'source_to_target' | 'target_to_source' | 'bidirectional';
    schedule?: string; // Cron expression
    batchSize?: number;
    conflictResolution?: 'source_wins' | 'target_wins' | 'merge' | 'manual';
  };
  /** Execute data bridge synchronization */
  executeBridge(): Promise<{
    success: boolean;
    recordsProcessed: number;
    errors: ApiError[];
    summary: Record<string, unknown>;
  }>;
}

/**
 * Middleware interface for request/response processing
 */
export interface ExternalIntegrationMiddleware {
  /** Middleware identifier */
  middlewareId: string;
  /** Processing priority (lower numbers execute first) */
  priority: number;
  /** Process outbound request */
  processRequest?(
    payload: ExternalApiRequestPayload,
    context: Record<string, unknown>
  ): Promise<ExternalApiRequestPayload>;
  /** Process inbound response */
  processResponse?(
    response: ExternalIntegrationResponse,
    context: Record<string, unknown>
  ): Promise<ExternalIntegrationResponse>;
  /** Handle integration errors */
  handleError?(
    error: ApiError,
    context: Record<string, unknown>
  ): Promise<ApiError | null>;
}

/**
 * External integration event for monitoring and auditing
 */
export interface ExternalIntegrationEvent {
  /** Event unique identifier */
  eventId: string;
  /** Integration component that generated the event */
  source: string;
  /** Event type */
  type: 'connection' | 'request' | 'response' | 'error' | 'transformation' | 'sync';
  /** Event severity level */
  level: 'debug' | 'info' | 'warn' | 'error' | 'critical';
  /** Event timestamp */
  timestamp: string;
  /** Event message */
  message: string;
  /** Event metadata */
  metadata?: Record<string, unknown>;
  /** Associated request/response data */
  data?: {
    request?: ExternalApiRequestPayload;
    response?: ExternalIntegrationResponse;
    error?: ApiError;
  };
}

/**
 * Integration orchestrator for managing multiple external connections
 */
export interface ExternalIntegrationOrchestrator {
  /** Orchestrator identifier */
  orchestratorId: string;
  /** Registered adapters */
  adapters: Map<string, ExternalServiceAdapter>;
  /** Active bridges */
  bridges: Map<string, ExternalBridge>;
  /** Middleware stack */
  middleware: ExternalIntegrationMiddleware[];
  /** Register a new adapter */
  registerAdapter(adapter: ExternalServiceAdapter): Promise<void>;
  /** Register a new bridge */
  registerBridge(bridge: ExternalBridge): Promise<void>;
  /** Add middleware to the stack */
  addMiddleware(middleware: ExternalIntegrationMiddleware): void;
  /** Execute orchestrated integration workflow */
  executeWorkflow(workflowId: string, context: Record<string, unknown>): Promise<{
    success: boolean;
    results: Record<string, unknown>;
    events: ExternalIntegrationEvent[];
  }>;
  /** Get orchestrator health status */
  getHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    adapters: Record<string, boolean>;
    bridges: Record<string, boolean>;
    lastCheck: string;
  }>;
}