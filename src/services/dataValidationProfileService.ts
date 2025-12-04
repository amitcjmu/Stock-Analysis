/**
 * Data Validation Profile Service
 *
 * API service for intelligent data profiling during the Data Validation phase.
 * Implements ADR-038: Multi-value detection, field length analysis, quality scoring.
 *
 * Related: ADR-038, Issue #1204, Issue #1210
 */

import { apiCall } from '@/config/api';

// ==============================================================================
// Type Definitions
// ==============================================================================

export interface QualityScores {
  completeness: number;
  consistency: number;
  constraint_compliance: number;
  overall: number;
}

export interface DataProfileSummary {
  total_records: number;
  total_fields: number;
  quality_scores: QualityScores;
}

export interface DataIssueSample {
  record_index: number;
  value?: string;
  value_length?: number;
  preview?: string;
  delimiter?: string;
  item_count?: number;
}

export interface DataIssue {
  severity: 'critical' | 'warning' | 'info';
  field: string;
  issue: string;
  schema_limit?: number;
  max_found?: number;
  exceeds_by?: number;
  affected_count?: number;
  delimiter?: string;
  null_percentage?: number;
  samples?: DataIssueSample[];
  recommendations?: string[];
  recommendation?: string;
  category?: string;
  is_multi_valued?: boolean;
}

export interface DataProfileIssues {
  critical: DataIssue[];
  warnings: DataIssue[];
  info: DataIssue[];
}

export interface FieldProfile {
  min_length: number;
  max_length: number;
  avg_length: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_capped: boolean;
  total_records: number;
  non_null_records: number;
}

export interface DataProfileResponse {
  generated_at: string;
  summary: DataProfileSummary;
  issues: DataProfileIssues;
  field_profiles: Record<string, FieldProfile>;
  user_action_required: boolean;
  blocking_issues: number;
}

export interface DataProfileWrapper {
  success: boolean;
  flow_id: string;
  data_profile?: DataProfileResponse;
  error?: string;
  message?: string;
}

export interface FieldDecision {
  field_name: string;
  action: 'split' | 'truncate' | 'skip' | 'keep' | 'first_value';
  custom_delimiter?: string;
}

export interface DataProfileDecisionsRequest {
  decisions: FieldDecision[];
  proceed_with_warnings: boolean;
}

export interface DataProfileDecisionsResponse {
  success: boolean;
  flow_id: string;
  decisions_applied: number;
  message: string;
  next_phase?: string;
  warnings?: string[];
}

export interface MultiValueFieldResult {
  field: string;
  is_multi_valued: boolean;
  affected_count: number;
  delimiter?: string;
  samples: DataIssueSample[];
  recommendation: string;
}

export interface MultiValueDetectionResponse {
  success: boolean;
  flow_id: string;
  results: MultiValueFieldResult[];
}

export interface LengthViolationResult {
  severity: 'critical';
  field: string;
  issue: string;
  schema_limit: number;
  max_found: number;
  exceeds_by: number;
  affected_count: number;
  samples: DataIssueSample[];
  recommendations: string[];
}

export interface LengthValidationResponse {
  success: boolean;
  flow_id: string;
  violations: LengthViolationResult[];
  total_violations: number;
}

// ==============================================================================
// Service Class
// ==============================================================================

export class DataValidationProfileService {
  /**
   * Get comprehensive data profile for a discovery flow.
   *
   * Generates intelligent data analysis including:
   * - Full dataset analysis (all records)
   * - Multi-value detection (comma/semicolon/pipe-separated)
   * - Field length analysis against schema constraints
   * - Quality scoring (completeness, consistency, compliance)
   */
  static async getDataProfile(flowId: string): Promise<DataProfileWrapper> {
    try {
      const response = await apiCall(
        `/unified-discovery/flows/${flowId}/data-profile`,
        { method: 'GET' },
        true
      );

      return response;
    } catch (error) {
      console.error('Failed to get data profile:', error);
      throw new Error(
        `Failed to get data profile: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Submit user decisions for handling data profile issues.
   *
   * Accepts decisions for each field with issues (split, truncate, skip, keep).
   * Stores decisions in flow state for use during data cleansing phase.
   */
  static async submitDecisions(
    flowId: string,
    decisions: FieldDecision[],
    proceedWithWarnings: boolean = false
  ): Promise<DataProfileDecisionsResponse> {
    try {
      const request: DataProfileDecisionsRequest = {
        decisions,
        proceed_with_warnings: proceedWithWarnings,
      };

      const response = await apiCall(
        `/unified-discovery/flows/${flowId}/data-profile/decisions`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        },
        true
      );

      return response;
    } catch (error) {
      console.error('Failed to submit data profile decisions:', error);
      throw new Error(
        `Failed to submit decisions: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Quick check for multi-valued fields without full profiling.
   *
   * Useful for field mapping preview to detect comma/semicolon/pipe-separated values.
   */
  static async checkMultiValues(
    flowId: string,
    fieldName?: string
  ): Promise<MultiValueDetectionResponse> {
    try {
      const url = fieldName
        ? `/unified-discovery/flows/${flowId}/multi-value-check?field_name=${encodeURIComponent(fieldName)}`
        : `/unified-discovery/flows/${flowId}/multi-value-check`;

      const response = await apiCall(url, { method: 'GET' }, true);

      return response;
    } catch (error) {
      console.error('Failed to check multi-values:', error);
      throw new Error(
        `Failed to check multi-values: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Quick check for field length violations without full profiling.
   *
   * Validates field values against Asset model schema constraints.
   */
  static async checkFieldLengths(
    flowId: string
  ): Promise<LengthValidationResponse> {
    try {
      const response = await apiCall(
        `/unified-discovery/flows/${flowId}/length-check`,
        { method: 'GET' },
        true
      );

      return response;
    } catch (error) {
      console.error('Failed to check field lengths:', error);
      throw new Error(
        `Failed to check field lengths: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Mark data validation phase as complete without decisions.
   *
   * Used when there are no critical issues and user wants to proceed.
   */
  static async markComplete(
    flowId: string,
    acknowledgeWarnings: boolean = false
  ): Promise<{ success: boolean; flow_id: string; message: string; next_phase: string }> {
    try {
      const response = await apiCall(
        `/unified-discovery/flows/${flowId}/data-validation/complete`,
        {
          method: 'POST',
          body: JSON.stringify({ acknowledge_warnings: acknowledgeWarnings }),
        },
        true
      );

      return response;
    } catch (error) {
      console.error('Failed to mark validation complete:', error);
      throw new Error(
        `Failed to mark validation complete: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }
}

// Default export for convenience
export default DataValidationProfileService;
