import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import type { FieldMapping } from './useFieldMappings';
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
 * NOW REACTIVE TO AGENT DECISIONS VIA SSE
 */
export const useAttributeMappingActions = (
  flow: {
    id?: string;
    status?: string;
    phases?: Record<string, boolean>;
  } | null,
  fieldMappings: FieldMapping[],
  refresh: () => Promise<void>,
  refetchFieldMappings: () => Promise<FieldMapping[]>
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
      const flowId = flow?.flow_id || flow?.id;
      console.log('🆔 Flow ID:', flowId);

      if (flowId) {
        // Check if we have VALID field mappings (not just placeholder mappings with "Unknown Field")
        const hasValidFieldMappings = fieldMappings &&
          fieldMappings.length > 0 &&
          fieldMappings.some(m => m.sourceField && m.sourceField !== 'Unknown Field');

        console.log('🔍 Has valid field mappings:', hasValidFieldMappings);
        console.log('📊 Field mappings sample:', fieldMappings?.slice(0, 3));

        if (!hasValidFieldMappings) {
          // No valid field mappings exist - use execute to trigger field mapping phase
          console.log('🔁 No valid field mappings found - executing field mapping phase');
          console.log('📊 Current mappings:', fieldMappings?.slice(0, 3));
          const result = await apiCall(`/unified-discovery/flow/${flowId}/execute`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });
          console.log('✅ Field mapping phase execution triggered:', result);
        } else {
          // Valid field mappings exist - normal resume flow
          console.log('▶️ Resuming flow with existing valid field mappings');
          const result = await apiCall(`/unified-discovery/flow/${flowId}/resume`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            },
            body: JSON.stringify({
              user_approval: true,
              approval_timestamp: new Date().toISOString(),
              notes: 'User triggered field mapping continuation'
            })
          });
          console.log('✅ CrewAI Flow resumed successfully:', result);
        }

        // Refresh the flow data to get updated state
        await refresh();
      } else {
        console.error('❌ No flow ID available - cannot trigger field mapping analysis');
        console.log('📋 Flow object:', flow);
      }
    } catch (error) {
      console.error('❌ Failed to trigger field mapping analysis:', error);
    }
  }, [flow, fieldMappings, refresh, getAuthHeaders]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);

      // Find the mapping
      const mapping = fieldMappings.find((m) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }

      // Create URL with proper query parameters - using simplified endpoint
      const approvalNote = encodeURIComponent('User approved mapping from UI');
      const approvalUrl = `/api/v1/field-mapping/approve/${mappingId}?approved=true&approval_note=${approvalNote}`;

      // Make API call to approve the specific mapping
      const approvalResult = await apiCall(approvalUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });

      console.log('✅ Mapping approved successfully:', approvalResult);

      // Show success feedback
      if (typeof window !== 'undefined' && (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast) {
        (window as Window & { showSuccessToast?: (message: string) => void }).showSuccessToast(`Mapping approved: ${mapping.sourceField} → ${mapping.targetAttribute}`);
      }

      // Add delay before refetching to prevent rate limiting
      setTimeout(async () => {
        try {
          console.log('🔄 Refetching field mappings to update UI...');
          // Force a fresh refetch by invalidating the query cache
          await refetchFieldMappings();
        } catch (refetchError) {
          console.error('⚠️ Failed to refetch mappings:', refetchError);
        }
      }, 1000); // 1 second delay

    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);

      // Show error toast if available
      if (typeof window !== 'undefined' && (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to approve mapping';
        (window as Window & { showErrorToast?: (message: string) => void }).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings, getAuthHeaders, refetchFieldMappings]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);

      // For discovery flow field mappings, we don't reject individual mappings
      // The user should edit the mapping instead
      console.log('ℹ️ To change a field mapping, please edit it directly');

      // Show info message
      if (typeof window !== 'undefined' && (window as Window & { showInfoToast?: (message: string) => void }).showInfoToast) {
        (window as Window & { showInfoToast?: (message: string) => void }).showInfoToast('To change a field mapping, please edit it directly in the dropdown.');
      }

    } catch (error) {
      console.error('❌ Error in reject handler:', error);
    }
  }, []);

  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    try {
      console.log(`🔄 Changing mapping: ${mappingId} -> ${newTarget}`);

      // Find the mapping in the current data
      const mapping = fieldMappings.find((m) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }

      // For discovery flow, field mapping changes are stored locally
      // and applied when the user clicks "Continue to Data Cleansing"
      console.log('ℹ️ Field mapping change will be applied when continuing to data cleansing phase');

      // Update local state to reflect the change
      // The parent component should handle this state update
      // For now, just show feedback
      if (typeof window !== 'undefined' && (window as Window & { showInfoToast?: (message: string) => void }).showInfoToast) {
        (window as Window & { showInfoToast?: (message: string) => void }).showInfoToast(`Field mapping updated: ${mapping.sourceField} → ${newTarget}`);
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
  }, [fieldMappings]);

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

  // Agent-driven decision for continuing to data cleansing
  const canContinueToDataCleansing = useCallback(() => {
    // Check if flow phase is already complete
    if (flow?.phases?.attribute_mapping === true) {
      return true;
    }

    // NO MORE HARDCODED RULES - Check agent decision
    if (!agentDecision) {
      console.log('⏳ Waiting for agent decision on field mappings...');
      return false;
    }

    // Agent says we can proceed
    if (agentDecision.action === 'proceed') {
      console.log(`✅ Agent recommends proceeding: ${agentDecision.reasoning}`);
      return true;
    }

    // Agent says we need user review
    if (agentDecision.action === 'pause') {
      console.log(`⏸️ Agent requires user review: ${agentDecision.reasoning}`);

      // Check if user has met agent's requirements
      if (agentDecision.metadata?.approval_requirements && fieldMappings.length > 0) {
        const approvedMappings = fieldMappings.filter(m => m.status === 'approved').length;
        const totalMappings = fieldMappings.length;
        const approvalPercentage = (approvedMappings / totalMappings) * 100;

        // Check against agent-specified threshold (not hardcoded 90%)
        const requiredPercentage = agentDecision.metadata.approval_requirements.minimum_approval_percentage || 0;

        // Check critical fields if required
        if (agentDecision.metadata.approval_requirements.critical_fields_required) {
          const criticalFields = agentDecision.metadata.critical_fields || [];
          const allCriticalFieldsMapped = criticalFields.every(field =>
            fieldMappings.some(m => m.sourceField === field && m.status === 'approved')
          );

          if (!allCriticalFieldsMapped) {
            console.log('❌ Not all critical fields are mapped and approved');
            return false;
          }
        }

        const meetsRequirements = approvalPercentage >= requiredPercentage;
        console.log(`📊 Approval status: ${approvalPercentage.toFixed(1)}% (agent requires ${requiredPercentage}%)`);

        return meetsRequirements;
      }

      return false;
    }

    // Agent says to skip or fail
    if (agentDecision.action === 'skip') {
      console.log(`⏭️ Agent recommends skipping field mapping: ${agentDecision.reasoning}`);
      return true; // Allow proceeding if agent says to skip
    }

    if (agentDecision.action === 'fail') {
      console.log(`❌ Agent detected critical issue: ${agentDecision.reasoning}`);
      return false;
    }

    // Default to false if no clear decision
    return false;
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
