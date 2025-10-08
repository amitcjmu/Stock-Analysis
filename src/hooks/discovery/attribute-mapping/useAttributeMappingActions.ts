/**
 * ⚠️ CRITICAL API PATTERN - DO NOT MODIFY WITHOUT READING:
 * ================================================================
 * ALL POST/PUT/DELETE endpoints in this file MUST use REQUEST BODY, not query parameters!
 *
 * ❌ WRONG (causes 422 errors):
 * const url = `/api/endpoint?param1=value1&param2=value2`;
 * await apiCall(url, { method: 'POST' });
 *
 * ✅ CORRECT:
 * const url = `/api/endpoint`;
 * await apiCall(url, {
 *   method: 'POST',
 *   body: JSON.stringify({ param1: 'value1', param2: 'value2' })
 * });
 *
 * BACKEND EXPECTS: Request bodies matching Pydantic schemas
 * NEVER use URLSearchParams for POST/PUT/DELETE - only for GET requests
 * This has been fixed multiple times (Sep 2024, Oct 2024, Nov 2024)
 * ================================================================
 */

import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import type { FieldMapping } from '@/types/api/discovery/field-mapping-types';
import type { DiscoveryFlowData } from '@/types/discovery';
import type { FlowUpdate } from '../../useFlowUpdates'
import { useFlowUpdates } from '../../useFlowUpdates'

// Agent decision structure from backend
interface AgentDecision {
  action: 'proceed' | 'pause' | 'skip' | 'retry' | 'fail';
  next_phase: string;
  confidence: number;
  reasoning: string;
  metadata?: {
    threshold?: number;
    critical_fields?: string[];
    user_action?: string;
    approval_requirements?: {
      minimum_approval_percentage?: number;
      critical_fields_required?: boolean;
      confidence_threshold?: number;
    };
  };
  timestamp: string;
}

export interface AttributeMappingActionsResult {
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: Record<string, unknown>) => Promise<void>;
  handleDataImportSelection: (importId: string) => Promise<void>;
  canContinueToDataCleansing: () => boolean;
  checkMappingApprovalStatus: (dataImportId: string) => Promise<{
    approved: boolean;
    total_mappings: number;
    approved_mappings: number;
    approval_percentage: number;
    critical_fields_mapped: boolean;
  } | null>;
  agentDecision: AgentDecision | null;
  agentReasoning: string | null;
}

/**
 * Hook for attribute mapping user actions and workflow operations
 * Handles approval, rejection, mapping changes, and navigation
 * Uses practical field validation for flow continuation (not agent-dependent)
 */
export const useAttributeMappingActions = (
  flow: {
    id?: string;
    status?: string;
    phases?: Record<string, boolean>;
  } | null,
  fieldMappings: FieldMapping[],
  refresh: () => Promise<void>,
  refetchFieldMappings: () => Promise<FieldMapping[]>,
  onMappingChange?: (mappingId: string, newTarget: string) => void
): AttributeMappingActionsResult => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();

  // Subscribe to real-time agent decisions via SSE
  const { data: flowUpdate } = useFlowUpdates(flow?.id, {
    enableSSE: true,
    enablePolling: false, // Prefer SSE for real-time updates
  });

  // Extract agent decision from flow updates
  const agentDecision = useMemo<AgentDecision | null>(() => {
    if (!flowUpdate?.data?.agent_decision) return null;

    // Look for field mapping agent decision in the flow update
    const decision = flowUpdate.data.agent_decision;
    if (decision && decision.phase === 'field_mapping') {
      return decision;
    }

    // Also check for nested decision data
    if (flowUpdate.data.field_mapping_decision) {
      return flowUpdate.data.field_mapping_decision;
    }

    return null;
  }, [flowUpdate]);

  // Extract agent reasoning for display
  const agentReasoning = useMemo<string | null>(() => {
    if (!agentDecision) return null;

    // Build user-friendly reasoning message
    const parts: string[] = [];

    // Add main reasoning
    parts.push(agentDecision.reasoning);

    // Add confidence level
    parts.push(`(Confidence: ${(agentDecision.confidence * 100).toFixed(0)}%)`);

    // Add specific requirements if any
    if (agentDecision.metadata?.approval_requirements) {
      const reqs = agentDecision.metadata.approval_requirements;
      if (reqs.minimum_approval_percentage) {
        parts.push(`Requires ${reqs.minimum_approval_percentage}% field approval`);
      }
      if (reqs.critical_fields_required) {
        parts.push('All critical fields must be mapped');
      }
    }

    return parts.join(' ');
  }, [agentDecision]);

  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      console.log('🔄 Triggering field mapping analysis');
      console.log('📋 Flow object:', flow);

      // Fix: Use flow_id instead of id (property name mismatch)
      const flowId = (flow as FlowUpdate | DiscoveryFlowData | { id: string })?.flow_id || ('id' in flow ? flow.id : undefined);
      console.log('🆔 Flow ID:', flowId);

      if (flowId) {
        // Keep manual trigger available, but do not auto-trigger on navigation
        console.log('🔁 Executing field mapping phase');
        console.log('📊 Current mappings:', fieldMappings?.slice(0, 3));

        const result = await apiCall(`/api/v1/unified-discovery/flows/${flowId}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({ phase: 'field_mapping_suggestions', phase_input: {}, force: false })
        });

        console.log('✅ Field mapping phase execution triggered:', result);

        // Refresh the flow data to get updated state
        await refresh();
      } else {
        console.error('❌ No flow ID available - cannot trigger field mapping analysis');
        console.log('📋 Flow object:', flow);

        // Show user-friendly error message for missing flow ID
        if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
          (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast('No flow ID available. Please refresh the page and try again.');
        }

        throw new Error('No flow ID available - cannot trigger field mapping analysis');
      }
    } catch (error) {
      console.error('❌ Failed to trigger field mapping analysis:', error);

      // Show user-friendly error message
      if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
        const errorMessage = error instanceof Error
          ? `Failed to trigger field mapping: ${error.message}`
          : 'Failed to trigger field mapping analysis. Please try again.';
        (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast(errorMessage);
      }

      // Re-throw for component error handling
      throw error;
    }
  }, [flow, refresh, getAuthHeaders, fieldMappings]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);

      // Find the mapping
      const mapping = fieldMappings.find((m) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }

      // IMPORTANT: Use REQUEST BODY, not query params (see file header for details)
      const approvalUrl = `/api/v1/data-import/field-mappings/${mappingId}/approve`;

      // Create request body according to backend's LearningApprovalRequest Pydantic schema
      // DO NOT use query parameters - will cause 422 error
      const requestBody = {
        approval_note: 'User approved mapping from UI',
        learn_from_approval: true,
        metadata: {
          approved_via: 'UI',
          flow_id: flow?.flow_id || flow?.id
        }
      };

      // Make API call to approve the specific mapping
      const approvalResult = await apiCall(approvalUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          // Add flow ID header for discovery operations
          'X-Flow-ID': flow?.flow_id || ''
        },
        body: JSON.stringify(requestBody)
      });

      console.log('✅ Mapping approved successfully:', approvalResult);

      // Show success feedback
      if (typeof window !== 'undefined' && (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast) {
        (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast(`Mapping approved: ${mapping.source_field} → ${mapping.target_field}`);
      }

      // Immediately refetch to get updated data
      try {
        console.log('🔄 Refetching field mappings to update UI...');
        // Force a fresh refetch by invalidating the query cache
        await refetchFieldMappings();
      } catch (refetchError) {
        console.error('⚠️ Failed to refetch mappings:', refetchError);
      }

    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);

      // Show error toast if available
      if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to approve mapping';
        (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings, getAuthHeaders, refetchFieldMappings, flow?.flow_id, flow?.id]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId} with reason: ${rejectionReason || 'No reason provided'}`);

      // Find the mapping to reject
      const mapping = fieldMappings.find((m) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }

      // IMPORTANT: Use REQUEST BODY, not query params (see file header for details)
      const rejectUrl = `/api/v1/data-import/field-mappings/${mappingId}/reject`;

      // Create request body according to backend's LearningRejectionRequest Pydantic schema
      // DO NOT use query parameters - will cause 422 error
      const requestBody = {
        rejection_reason: rejectionReason || 'User rejected mapping from UI',
        metadata: {
          rejected_via: 'UI',
          flow_id: flow?.flow_id || flow?.id
        }
      };

      // Make API call to reject the specific mapping
      const rejectResult = await apiCall(rejectUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          // Add flow ID header for discovery operations
          'X-Flow-ID': flow?.flow_id || ''
        },
        body: JSON.stringify(requestBody)
      });

      console.log('✅ Mapping rejected successfully:', rejectResult);

      // Show success feedback
      if (typeof window !== 'undefined' && (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast) {
        (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast(`Mapping rejected: ${mapping.source_field}`);
      }

      // Immediately refetch to get updated data
      try {
        console.log('🔄 Refetching field mappings to update UI...');
        // Force a fresh refetch by invalidating the query cache
        await refetchFieldMappings();
      } catch (refetchError) {
        console.error('⚠️ Failed to refetch mappings:', refetchError);
      }

    } catch (error) {
      console.error('❌ Error in reject handler:', error);

      // Show error toast if available
      if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to reject mapping';
        (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings, getAuthHeaders, refetchFieldMappings, flow?.flow_id, flow?.id]);

  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    try {
      console.log(`🔄 Changing mapping: ${mappingId} -> ${newTarget}`);

      // Find the mapping in the current data
      const mapping = fieldMappings.find((m) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }

      // IMPORTANT: Use REQUEST BODY for PUT request (see file header for details)
      const updateUrl = `/api/v1/data-import/field-mappings/mappings/${mappingId}`;
      // DO NOT use query parameters - will cause 422 error
      const updatePayload = {
        target_field: newTarget,
        source_field: mapping.source_field,
        confidence_score: mapping.confidence_score || 0.7
      };

      console.log('📤 Updating field mapping:', updatePayload);

      const updateResult = await apiCall(updateUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          // Add flow ID header for discovery operations
          'X-Flow-ID': flow?.flow_id || ''
        },
        body: JSON.stringify(updatePayload)
      });

      console.log('✅ Field mapping updated successfully:', updateResult);

      // Show success feedback
      if (typeof window !== 'undefined' && (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast) {
        (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast(`Field mapping updated: ${mapping.source_field} → ${newTarget}`);
      }

      // Refetch field mappings to ensure UI is in sync
      try {
        console.log('🔄 Refetching field mappings after update...');
        await refetchFieldMappings();
      } catch (refetchError) {
        console.error('⚠️ Failed to refetch mappings after update:', refetchError);
      }

    } catch (error) {
      console.error('❌ Failed to update mapping:', error);

      // Show error toast if available
      if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update mapping';
        (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast(errorMessage);
      }

      // Re-throw for component error handling
      throw error;
    }
  }, [fieldMappings, getAuthHeaders, flow, refetchFieldMappings]);

  const handleAttributeUpdate = useCallback(async (attributeId: string, updates: Record<string, unknown>) => {
    try {
      console.log(`🔄 Updating attribute: ${attributeId}`, updates);
      // TODO: Implement attribute update logic
    } catch (error) {
      console.error('❌ Failed to update attribute:', error);
    }
  }, []);

  const handleDataImportSelection = useCallback(async (importId: string) => {
    try {
      console.log(`🔄 Selecting data import: ${importId}`);
      // Navigate to the selected flow
      navigate(`/discovery/attribute-mapping/${importId}`);
    } catch (error) {
      console.error('❌ Failed to select data import:', error);
    }
  }, [navigate]);

  const checkMappingApprovalStatus = useCallback(async (dataImportId: string) => {
    try {
      const result = await apiCall(`/data-import/mappings/approval-status/${dataImportId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });

      return result;

    } catch (error) {
      console.error('❌ Failed to check mapping approval status:', error);
      return null;
    }
  }, [getAuthHeaders]);

  // Practical validation for continuing to data cleansing - no dependency on agent decisions
  const canContinueToDataCleansing = useCallback(() => {
    // Ensure we have field mappings first - critical check
    if (!fieldMappings || fieldMappings.length === 0) {
      console.log('❌ No field mappings available - cannot continue');
      return false;
    }

    // Get approved mappings
    const approvedMappings = fieldMappings.filter(m => m.status === 'approved');

    // Must have at least some approved mappings - even if phase was previously completed
    if (approvedMappings.length === 0) {
      console.log('❌ No approved mappings - need at least some fields approved');
      // Don't allow continuing even if the phase was marked complete before
      return false;
    }

    // Check if flow phase is already complete (moved after approval check)
    if (flow?.phases?.attribute_mapping === true) {
      console.log('✅ Flow phase already complete and has approved mappings - can continue');
      return true;
    }

    // Check for minimum required fields: name is required, type is optional but recommended
    const hasNameField = approvedMappings.some(m => {
      const targetField = m.target_field?.toLowerCase() || '';
      return targetField.includes('name') || targetField.includes('asset_name');
    });

    const hasTypeField = approvedMappings.some(m => {
      const targetField = m.target_field?.toLowerCase() || '';
      return targetField.includes('type') || targetField.includes('asset_type');
    });

    // Only name field is strictly required for asset creation
    if (!hasNameField) {
      console.log(`❌ Missing required field: name field must be mapped`);
      console.log('   Required: at least one field containing "name" or "asset_name"');
      return false;
    }

    // Type field is optional but recommended - log warning if missing
    if (!hasTypeField) {
      console.log(`⚠️ Warning: No type field mapped - assets will have undefined type`);
      console.log('   Recommended: map a field containing "type" or "asset_type" for better categorization');
    }

    // Check for minimum approval percentage
    // IMPORTANT: This must match FIELD_MAPPING_APPROVAL_THRESHOLD in backend (default 60%)
    // See: backend/app/utils/flow_constants/thresholds.py
    const approvalPercentage = (approvedMappings.length / fieldMappings.length) * 100;
    const minimumPercentage = 60; // Must match backend default

    if (approvalPercentage < minimumPercentage) {
      console.log(`❌ Only ${approvalPercentage.toFixed(1)}% approved, need at least ${minimumPercentage}%`);
      return false;
    }

    console.log(`✅ Can continue: ${approvedMappings.length}/${fieldMappings.length} fields approved (${approvalPercentage.toFixed(1)}%)`);
    console.log(`   Required field present: name=${hasNameField}${!hasTypeField ? ' (type field missing but optional)' : `, type=${hasTypeField}`}`);

    // Optional: If agent decision is available and supports our decision, log it
    if (agentDecision) {
      console.log(`ℹ️ Agent recommendation: ${agentDecision.action} - ${agentDecision.reasoning}`);
    }

    return true;
  }, [flow, fieldMappings, agentDecision]);

  return {
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    canContinueToDataCleansing,
    checkMappingApprovalStatus,
    agentDecision,
    agentReasoning
  };
};
