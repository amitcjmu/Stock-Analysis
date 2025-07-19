/**
 * Bulk Operations Logic
 * 
 * Functions for handling bulk approve and bulk reject operations with retry logic and error handling.
 */

import { FieldMapping } from '../../types';
import { BulkOperationResult } from './types';

export const createBulkApproveHandler = (
  fieldMappings: FieldMapping[],
  client: any,
  engagement: any,
  lastBulkOperationTime: number,
  setLastBulkOperationTime: (time: number) => void,
  setProcessingMappings: React.Dispatch<React.SetStateAction<Set<string>>>,
  onRefresh?: () => void
) => {
  return async (mappingIds: string[]) => {
    if (mappingIds.length === 0) return;
    
    // Filter out placeholder and fallback mappings that shouldn't be approved via API
    const validMappingIds = mappingIds.filter(id => {
      const mapping = fieldMappings.find(m => m.id === id);
      return !(mapping && ((mapping as any).is_placeholder || (mapping as any).is_fallback));
    });
    
    if (validMappingIds.length === 0) {
      if (typeof window !== 'undefined' && (window as any).showWarningToast) {
        (window as any).showWarningToast('No valid mappings to approve. Please configure unmapped fields first.');
      }
      return;
    }
    
    if (validMappingIds.length < mappingIds.length) {
      console.log(`⚠️ Filtered out ${mappingIds.length - validMappingIds.length} placeholder/fallback mappings from bulk approval`);
    }
    
    // Check authentication before proceeding
    if (!client?.id || !engagement?.id) {
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        (window as any).showErrorToast('Authentication required. Please log in to continue.');
      }
      return;
    }
    
    // Prevent concurrent bulk operations
    const now = Date.now();
    if (now - lastBulkOperationTime < 5000) { // 5 second cooldown
      if (typeof window !== 'undefined' && (window as any).showWarningToast) {
        (window as any).showWarningToast('Please wait before performing another bulk operation.');
      }
      return;
    }
    setLastBulkOperationTime(now);
    
    const maxRetries = 3;
    const baseDelay = 2000; // 2 seconds
    
    const attemptBulkApproval = async (attempt: number = 0): Promise<BulkOperationResult> => {
      try {
        console.log(`🔄 Bulk approving mappings (attempt ${attempt + 1}/${maxRetries + 1}):`, mappingIds);
        
        // Call bulk approval API with filtered IDs
        const { apiCall } = await import('../../../../../../config/api');
        
        const response = await apiCall('/api/v1/data-import/field-mapping/approval/approve-mappings', {
          method: 'POST',
          includeContext: true, // Use centralized context handling
          body: JSON.stringify({
            mapping_ids: validMappingIds, // Use filtered IDs
            approved: true,
            approval_note: 'Bulk approved from UI'
          })
        });
        
        console.log('✅ Bulk approval response:', response);
        return response;
        
      } catch (error) {
        console.error(`❌ Bulk approval attempt ${attempt + 1} failed:`, error);
        
        // Check if it's a rate limit error and we have retries left
        if (attempt < maxRetries && error instanceof Error && 
            (error.message.includes('429') || error.message.includes('Too Many Requests') || 
             error.message.includes('Rate limit'))) {
          
          const delay = baseDelay * Math.pow(2, attempt); // Exponential backoff
          console.log(`⏳ Rate limited, waiting ${delay}ms before retry...`);
          
          // Show user feedback about retry
          if (typeof window !== 'undefined' && (window as any).showInfoToast) {
            (window as any).showInfoToast(`Rate limited, retrying in ${delay/1000} seconds...`);
          }
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptBulkApproval(attempt + 1);
        }
        
        // Re-throw if not rate limited or no retries left
        throw error;
      }
    };
    
    try {
      // Add all valid mappings to processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        validMappingIds.forEach(id => newSet.add(id));
        return newSet;
      });
      
      // Attempt bulk approval with retry logic
      const response = await attemptBulkApproval();
      
      // Show success message
      if (typeof window !== 'undefined' && (window as any).showSuccessToast) {
        (window as any).showSuccessToast(`Successfully approved ${response.successful_updates} mappings`);
      }
      
      // Refresh the data
      if (onRefresh) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        onRefresh();
      }
      
    } catch (error) {
      console.error('❌ Bulk approval failed after all retries:', error);
      
      // Handle specific error types
      let errorMessage = 'Failed to approve mappings. Please try again.';
      if (error instanceof Error) {
        if (error.message.includes('429') || error.message.includes('Too Many Requests')) {
          errorMessage = 'Rate limit exceeded. Please wait a few minutes and try again.';
        } else if (error.message.includes('401') || error.message.includes('403')) {
          errorMessage = 'Authentication error. Please refresh the page and try again.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        (window as any).showErrorToast(errorMessage);
      }
    } finally {
      // Remove all valid mappings from processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        validMappingIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    }
  };
};

export const createBulkRejectHandler = (
  client: any,
  engagement: any,
  lastBulkOperationTime: number,
  setLastBulkOperationTime: (time: number) => void,
  setProcessingMappings: React.Dispatch<React.SetStateAction<Set<string>>>,
  onRefresh?: () => void
) => {
  return async (mappingIds: string[]) => {
    if (mappingIds.length === 0) return;
    
    // Check authentication before proceeding
    if (!client?.id || !engagement?.id) {
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        (window as any).showErrorToast('Authentication required. Please log in to continue.');
      }
      return;
    }
    
    // Prevent concurrent bulk operations
    const now = Date.now();
    if (now - lastBulkOperationTime < 5000) { // 5 second cooldown
      if (typeof window !== 'undefined' && (window as any).showWarningToast) {
        (window as any).showWarningToast('Please wait before performing another bulk operation.');
      }
      return;
    }
    setLastBulkOperationTime(now);
    
    const maxRetries = 3;
    const baseDelay = 2000; // 2 seconds
    
    const attemptBulkRejection = async (attempt: number = 0): Promise<BulkOperationResult> => {
      try {
        console.log(`🔄 Bulk rejecting mappings (attempt ${attempt + 1}/${maxRetries + 1}):`, mappingIds);
        
        // Call bulk rejection API
        const { apiCall } = await import('../../../../../../config/api');
        
        const response = await apiCall('/api/v1/data-import/field-mapping/approval/approve-mappings', {
          method: 'POST',
          includeContext: true, // Use centralized context handling
          body: JSON.stringify({
            mapping_ids: mappingIds,
            approved: false,
            approval_note: 'Bulk rejected from UI'
          })
        });
        
        console.log('✅ Bulk rejection response:', response);
        return response;
        
      } catch (error) {
        console.error(`❌ Bulk rejection attempt ${attempt + 1} failed:`, error);
        
        // Check if it's a rate limit error and we have retries left
        if (attempt < maxRetries && error instanceof Error && 
            (error.message.includes('429') || error.message.includes('Too Many Requests') || 
             error.message.includes('Rate limit'))) {
          
          const delay = baseDelay * Math.pow(2, attempt); // Exponential backoff
          console.log(`⏳ Rate limited, waiting ${delay}ms before retry...`);
          
          // Show user feedback about retry
          if (typeof window !== 'undefined' && (window as any).showInfoToast) {
            (window as any).showInfoToast(`Rate limited, retrying in ${delay/1000} seconds...`);
          }
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptBulkRejection(attempt + 1);
        }
        
        // Re-throw if not rate limited or no retries left
        throw error;
      }
    };
    
    try {
      // Add all mappings to processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        mappingIds.forEach(id => newSet.add(id));
        return newSet;
      });
      
      // Attempt bulk rejection with retry logic
      const response = await attemptBulkRejection();
      
      // Show success message
      if (typeof window !== 'undefined' && (window as any).showSuccessToast) {
        (window as any).showSuccessToast(`Successfully rejected ${response.successful_updates} mappings`);
      }
      
      // Refresh the data
      if (onRefresh) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        onRefresh();
      }
      
    } catch (error) {
      console.error('❌ Bulk rejection failed after all retries:', error);
      
      // Handle specific error types
      let errorMessage = 'Failed to reject mappings. Please try again.';
      if (error instanceof Error) {
        if (error.message.includes('429') || error.message.includes('Too Many Requests')) {
          errorMessage = 'Rate limit exceeded. Please wait a few minutes and try again.';
        } else if (error.message.includes('401') || error.message.includes('403')) {
          errorMessage = 'Authentication error. Please refresh the page and try again.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        (window as any).showErrorToast(errorMessage);
      }
    } finally {
      // Remove all mappings from processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        mappingIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    }
  };
};