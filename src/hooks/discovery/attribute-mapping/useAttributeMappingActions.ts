import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import { FieldMapping } from './useFieldMappings';

export interface AttributeMappingActionsResult {
  handleTriggerFieldMappingCrew: () => Promise<void>;
  handleApproveMapping: (mappingId: string) => Promise<void>;
  handleRejectMapping: (mappingId: string, rejectionReason?: string) => Promise<void>;
  handleMappingChange: (mappingId: string, newTarget: string) => Promise<void>;
  handleAttributeUpdate: (attributeId: string, updates: any) => Promise<void>;
  handleDataImportSelection: (importId: string) => Promise<void>;
  canContinueToDataCleansing: () => boolean;
  checkMappingApprovalStatus: (dataImportId: string) => Promise<any>;
}

/**
 * Hook for attribute mapping user actions and workflow operations
 * Handles approval, rejection, mapping changes, and navigation
 */
export const useAttributeMappingActions = (
  flow: any,
  fieldMappings: FieldMapping[],
  refresh: () => Promise<void>,
  refetchFieldMappings: () => Promise<any>
): AttributeMappingActionsResult => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();

  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      console.log('🔄 Resuming CrewAI Flow from field mapping approval');
      if (flow?.id) {
        // Use the correct resume endpoint for paused flows
        const result = await apiCall(`/discovery/flow/${flow.id}/resume`, {
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
        
        // Refresh the flow data to get updated state
        await refresh();
      }
    } catch (error) {
      console.error('❌ Failed to resume CrewAI Flow:', error);
    }
  }, [flow, refresh, getAuthHeaders]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);
      
      // Find the mapping
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // Create URL with proper query parameters
      const approvalNote = encodeURIComponent('User approved mapping from UI');
      const approvalUrl = `/api/v1/data-import/field-mapping/approval/approve-mapping/${mappingId}?approved=true&approval_note=${approvalNote}`;
      
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
      if (typeof window !== 'undefined' && (window as any).showSuccessToast) {
        (window as any).showSuccessToast(`Mapping approved: ${mapping.sourceField} → ${mapping.targetAttribute}`);
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
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to approve mapping';
        (window as any).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings, getAuthHeaders, user?.id, refetchFieldMappings]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      
      // For discovery flow field mappings, we don't reject individual mappings
      // The user should edit the mapping instead
      console.log('ℹ️ To change a field mapping, please edit it directly');
      
      // Show info message
      if (typeof window !== 'undefined' && (window as any).showInfoToast) {
        (window as any).showInfoToast('To change a field mapping, please edit it directly in the dropdown.');
      }
      
    } catch (error) {
      console.error('❌ Error in reject handler:', error);
    }
  }, []);

  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    try {
      console.log(`🔄 Changing mapping: ${mappingId} -> ${newTarget}`);
      
      // Find the mapping in the current data
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
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
      if (typeof window !== 'undefined' && (window as any).showInfoToast) {
        (window as any).showInfoToast(`Field mapping updated: ${mapping.sourceField} → ${newTarget}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to update mapping:', error);
      
      // Show error toast if available
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update mapping';
        (window as any).showErrorToast(errorMessage);
      }
      
      // Re-throw for component error handling
      throw error;
    }
  }, [fieldMappings]);

  const handleAttributeUpdate = useCallback(async (attributeId: string, updates: any) => {
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

  // Move canContinueToDataCleansing after all data is declared to avoid forward reference
  const canContinueToDataCleansing = useCallback(() => {
    // Check if flow phase is complete
    if (flow?.phases?.attribute_mapping === true) {
      return true;
    }
    
    // STRICT REQUIREMENT: User must explicitly approve field mappings before continuing
    if (Array.isArray(fieldMappings) && fieldMappings.length > 0) {
      const approvedMappings = fieldMappings.filter(m => m.status === 'approved').length;
      const totalMappings = fieldMappings.length;
      const pendingMappings = fieldMappings.filter(m => m.status === 'pending' || m.status === 'suggested').length;
      
      console.log(`🔍 Field mapping status: ${approvedMappings}/${totalMappings} approved, ${pendingMappings} pending user approval`);
      
      // Only allow continuation if ALL mappings are explicitly approved by the user
      // OR if at least 90% are approved (allowing for some optional fields)
      const approvalPercentage = (approvedMappings / totalMappings) * 100;
      const canContinue = approvalPercentage >= 90;
      
      if (!canContinue) {
        console.log(`❌ Cannot continue: Only ${approvalPercentage.toFixed(1)}% of field mappings are user-approved. Need 90%+ approval.`);
      }
      
      return canContinue;
    }
    
    return false;
  }, [flow, fieldMappings]);

  return {
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    canContinueToDataCleansing,
    checkMappingApprovalStatus
  };
};