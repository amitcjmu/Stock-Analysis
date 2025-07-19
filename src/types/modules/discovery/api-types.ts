/**
 * Discovery Flow - API Types Module
 * 
 * API request and response interfaces for Discovery Flow operations.
 * Contains field mapping, flow management, data import, and crew analysis API types.
 * 
 * Generated with CC - Code Companion
 */

import {
  MultiTenantContext,
  ResponseMetadata,
  FlowStatus
} from './base-types';

import {
  FieldMapping,
  FieldMappingInput,
  FlowState,
  CriticalAttribute,
  CrewAnalysis
} from './data-models';

import {
  ValidationOptions,
  ValidationResult,
  FlowConfiguration,
  ImportOptions,
  ImportError,
  AgentInsight
} from './validation-types';

/**
 * API Types Namespace
 */
export namespace API {
  /**
   * Field mapping API request
   */
  export interface FieldMappingRequest {
    flowId: string;
    mappings: FieldMappingInput[];
    context: MultiTenantContext;
    validation?: ValidationOptions;
  }

  /**
   * Field mapping API response
   */
  export interface FieldMappingResponse {
    success: boolean;
    data: FieldMapping[];
    metadata: ResponseMetadata;
    validationResults?: ValidationResult[];
  }

  /**
   * Flow initialization API request
   */
  export interface FlowInitializationRequest {
    flowName: string;
    flowDescription?: string;
    context: MultiTenantContext;
    configuration?: FlowConfiguration;
  }

  /**
   * Flow initialization API response
   */
  export interface FlowInitializationResponse {
    success: boolean;
    flowId: string;
    initialState: FlowState;
    metadata: ResponseMetadata;
  }

  /**
   * Flow status API request
   */
  export interface FlowStatusRequest {
    flowId: string;
    context: MultiTenantContext;
    includeDetails?: boolean;
  }

  /**
   * Flow status API response
   */
  export interface FlowStatusResponse {
    flowId: string;
    status: FlowStatus;
    progress: number;
    currentPhase: string;
    nextPhase?: string;
    phaseCompletion: Record<string, boolean>;
    agentInsights?: AgentInsight[];
    errors?: string[];
    warnings?: string[];
    metadata: ResponseMetadata;
  }

  /**
   * Data import API request
   */
  export interface DataImportRequest {
    flowId: string;
    file: File;
    context: MultiTenantContext;
    options?: ImportOptions;
  }

  /**
   * Data import API response
   */
  export interface DataImportResponse {
    success: boolean;
    importId: string;
    recordsProcessed: number;
    recordsValid: number;
    errors?: ImportError[];
    metadata: ResponseMetadata;
  }

  /**
   * Critical attributes API request
   */
  export interface CriticalAttributesRequest {
    flowId: string;
    context: MultiTenantContext;
    includeValidation?: boolean;
  }

  /**
   * Critical attributes API response
   */
  export interface CriticalAttributesResponse {
    success: boolean;
    attributes: CriticalAttribute[];
    validationResults?: ValidationResult[];
    metadata: ResponseMetadata;
  }

  /**
   * Crew analysis API request
   */
  export interface CrewAnalysisRequest {
    flowId: string;
    context: MultiTenantContext;
    analysisType: 'mapping' | 'validation' | 'optimization';
    parameters?: Record<string, any>;
  }

  /**
   * Crew analysis API response
   */
  export interface CrewAnalysisResponse {
    success: boolean;
    analysis: CrewAnalysis[];
    recommendations?: string[];
    metadata: ResponseMetadata;
  }
}