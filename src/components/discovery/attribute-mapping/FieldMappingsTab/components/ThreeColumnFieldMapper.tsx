import React, { useState, useMemo, useCallback } from 'react';
import { CheckCircle, XCircle, AlertCircle, Clock, Search, ArrowRight, RefreshCw } from 'lucide-react';
import { EnhancedFieldDropdown } from './EnhancedFieldDropdown';
import { TargetField, FieldMapping } from '../types';
import { useAuth } from '../../../../../contexts/AuthContext';

interface ThreeColumnFieldMapperProps {
  fieldMappings: FieldMapping[];
  availableFields: TargetField[];
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onRefresh?: () => void;
}

const ThreeColumnFieldMapper: React.FC<ThreeColumnFieldMapperProps> = ({
  fieldMappings,
  availableFields,
  onMappingAction,
  onMappingChange,
  onRefresh
}) => {
  const { client, engagement } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectionInput, setShowRejectionInput] = useState<string | null>(null);
  const [processingMappings, setProcessingMappings] = useState<Set<string>>(new Set());
  const [lastRefreshTime, setLastRefreshTime] = useState<number>(0);
  const [lastBulkOperationTime, setLastBulkOperationTime] = useState<number>(0);

  // Categorize mappings into buckets
  const buckets = useMemo(() => {
    console.log('🔍 ThreeColumnFieldMapper - Field mappings data:', {
      total_mappings: fieldMappings.length,
      sample_mappings: fieldMappings.slice(0, 3).map(m => ({
        id: m.id,
        sourceField: m.sourceField,
        targetAttribute: m.targetAttribute,
        status: m.status,
        confidence: m.confidence,
        mapping_type: m.mapping_type
      }))
    });
    
    const autoMapped = fieldMappings.filter(m => m.status === 'pending' && m.confidence > 0.7);
    const unmapped = fieldMappings.filter(m => {
      return m.status === 'rejected' || (m.status === 'pending' && m.confidence <= 0.7) || m.mapping_type === 'unmapped';
    });
    const approved = fieldMappings.filter(m => m.status === 'approved');

    console.log('🔍 ThreeColumnFieldMapper - Buckets:', {
      autoMapped: autoMapped.length,
      unmapped: unmapped.length,
      approved: approved.length,
      approved_sample: approved.slice(0, 3).map(m => ({
        targetAttribute: m.targetAttribute,
        sourceField: m.sourceField,
        status: m.status
      }))
    });

    return { autoMapped, unmapped, approved };
  }, [fieldMappings]);

  // Filter mappings based on search
  const filteredBuckets = useMemo(() => {
    if (!searchTerm) return buckets;
    
    const filterBySearch = (mappings: FieldMapping[]) => 
      mappings.filter(m => 
        m.sourceField.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (m.targetAttribute && m.targetAttribute.toLowerCase().includes(searchTerm.toLowerCase()))
      );

    return {
      autoMapped: filterBySearch(buckets.autoMapped),
      unmapped: filterBySearch(buckets.unmapped),
      approved: filterBySearch(buckets.approved)
    };
  }, [buckets, searchTerm]);

  const handleApprove = async (mappingId: string) => {
    if (processingMappings.has(mappingId)) {
      return; // Already processing this mapping
    }
    
    try {
      setProcessingMappings(prev => new Set(prev).add(mappingId));
      onMappingAction(mappingId, 'approve');
      
      // Remove from processing set after a short delay
      setTimeout(() => {
        setProcessingMappings(prev => {
          const newSet = new Set(prev);
          newSet.delete(mappingId);
          return newSet;
        });
      }, 1000);
    } catch (error) {
      console.error('Error approving mapping:', error);
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        newSet.delete(mappingId);
        return newSet;
      });
    }
  };

  const handleBulkApprove = async (mappingIds: string[]) => {
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
    
    const attemptBulkApproval = async (attempt: number = 0): Promise<any> => {
      try {
        console.log(`🔄 Bulk approving mappings (attempt ${attempt + 1}/${maxRetries + 1}):`, mappingIds);
        
        // Call bulk approval API
        const { apiCall } = await import('../../../../../config/api');
        
        const response = await apiCall('/api/v1/data-import/field-mapping/approval/approve-mappings', {
          method: 'POST',
          includeContext: true, // Use centralized context handling
          body: JSON.stringify({
            mapping_ids: mappingIds,
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
      // Add all mappings to processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        mappingIds.forEach(id => newSet.add(id));
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
      // Remove all mappings from processing set
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        mappingIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    }
  };

  const handleBulkReject = async (mappingIds: string[]) => {
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
    
    const attemptBulkRejection = async (attempt: number = 0): Promise<any> => {
      try {
        console.log(`🔄 Bulk rejecting mappings (attempt ${attempt + 1}/${maxRetries + 1}):`, mappingIds);
        
        // Call bulk rejection API
        const { apiCall } = await import('../../../../../config/api');
        
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

  const handleReject = (mappingId: string) => {
    if (showRejectionInput === mappingId) {
      try {
        onMappingAction(mappingId, 'reject', rejectionReason);
        setShowRejectionInput(null);
        setRejectionReason('');
        
        // Note: Removed automatic refresh - let user manually refresh if needed
        // This prevents page refresh and data loss issues
      } catch (error) {
        console.error('Error rejecting mapping:', error);
      }
    } else {
      setShowRejectionInput(mappingId);
    }
  };

  const handleRefresh = () => {
    const now = Date.now();
    if (now - lastRefreshTime < 10000) {
      // Less than 10 seconds since last refresh
      return;
    }
    
    setLastRefreshTime(now);
    if (onRefresh) {
      onRefresh();
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50';
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.9) return <CheckCircle className="h-4 w-4" />;
    if (confidence >= 0.7) return <AlertCircle className="h-4 w-4" />;
    return <XCircle className="h-4 w-4" />;
  };

  const AutoMappedCard = ({ mapping }: { mapping: FieldMapping }) => (
    <div className="p-4 border rounded-lg transition-all duration-200 hover:shadow-md bg-white border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <span className="font-medium text-gray-900">{mapping.sourceField}</span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
        <span className="text-blue-600 font-medium">{mapping.targetAttribute || 'No target mapping'}</span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {mapping.confidence && (
            <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(mapping.confidence)}`}>
              {getConfidenceIcon(mapping.confidence)}
              {Math.round(mapping.confidence * 100)}% confidence
            </div>
          )}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => handleApprove(mapping.id)}
            disabled={processingMappings.has(mapping.id)}
            className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processingMappings.has(mapping.id) ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => handleReject(mapping.id)}
            disabled={processingMappings.has(mapping.id)}
            className="flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="h-4 w-4" />
          </button>
        </div>
      </div>


      {showRejectionInput === mapping.id && (
        <div className="mt-3 p-3 bg-gray-50 rounded">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Rejection Reason (optional):
          </label>
          <input
            type="text"
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            placeholder="Why is this mapping incorrect?"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => handleReject(mapping.id)}
              className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            >
              Confirm Reject
            </button>
            <button
              onClick={() => setShowRejectionInput(null)}
              className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const NeedsReviewCard = ({ mapping }: { mapping: FieldMapping }) => {
    const [selectedTarget, setSelectedTarget] = useState(mapping.targetAttribute || '');
    
    const handleConfirmMapping = () => {
      if (onMappingChange && selectedTarget !== mapping.targetAttribute) {
        onMappingChange(mapping.id, selectedTarget);
      }
      handleApprove(mapping.id);
    };
    
    const handleFieldChange = useCallback((newValue: string) => {
      setSelectedTarget(newValue);
    }, []);

    return (
      <div className="p-4 border rounded-lg transition-all duration-200 hover:shadow-md bg-white border-gray-200">
        <div className="grid grid-cols-1 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source Field:</label>
            <div className="px-3 py-2 bg-gray-50 rounded border text-sm font-medium">
              {mapping.sourceField}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Map to Asset Table Field:</label>
            <div className="flex gap-2">
              <div className="flex-1">
                <EnhancedFieldDropdown
                  value={selectedTarget}
                  onChange={handleFieldChange}
                  availableFields={availableFields}
                  placeholder="Select target field"
                />
              </div>
              <button
                onClick={handleConfirmMapping}
                className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                disabled={!selectedTarget}
              >
                <CheckCircle className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const ApprovedCard = ({ mapping }: { mapping: FieldMapping }) => (
    <div className="p-4 border rounded-lg transition-all duration-200 bg-green-50 border-green-200">
      <div className="flex items-center gap-2">
        <span className="font-medium text-gray-900">{mapping.sourceField}</span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
        <span className="text-green-600 font-medium">{mapping.targetAttribute || 'No target mapping'}</span>
      </div>
    </div>
  );

  const ColumnHeader = ({ title, count, icon, bgColor }: { title: string; count: number; icon: React.ReactNode; bgColor: string }) => (
    <div className={`${bgColor} p-4 rounded-lg mb-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        <span className="bg-white px-2 py-1 rounded-full text-sm font-medium text-gray-600">
          {count}
        </span>
      </div>
    </div>
  );

  const progress = {
    total: fieldMappings.length,
    approved: buckets.approved.length,
    pending: buckets.autoMapped.length + buckets.unmapped.length
  };

  return (
    <div className="space-y-6">
      {/* Authentication Status */}
      {(!client?.id || !engagement?.id) && (
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">
              Authentication Required
            </span>
            <span className="text-sm text-yellow-600">
              Please log in to perform bulk operations
            </span>
          </div>
        </div>
      )}
      
      {/* Progress Bar */}
      <div className="bg-white p-4 rounded-lg border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Mapping Progress</span>
          <span className="text-sm text-gray-500">
            {progress.approved} of {progress.total} approved
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-green-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(progress.approved / progress.total) * 100}%` }}
          />
        </div>
      </div>

      {/* Search Bar and Refresh Button */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search field mappings..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleRefresh}
          disabled={Date.now() - lastRefreshTime < 10000}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1: Auto-Mapped (High Confidence) */}
        <div>
          <ColumnHeader 
            title="Auto-Mapped"
            count={filteredBuckets.autoMapped.length}
            icon={<CheckCircle className="h-5 w-5 text-blue-600" />}
            bgColor="bg-blue-50 border border-blue-200"
          />
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {filteredBuckets.autoMapped.map(mapping => (
              <AutoMappedCard key={mapping.id} mapping={mapping} />
            ))}
            {filteredBuckets.autoMapped.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No high-confidence mappings</p>
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Unmapped/Rejected (Needs Attention) */}
        <div>
          <ColumnHeader 
            title="Needs Review"
            count={filteredBuckets.unmapped.length}
            icon={<AlertCircle className="h-5 w-5 text-yellow-600" />}
            bgColor="bg-yellow-50 border border-yellow-200"
          />
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {filteredBuckets.unmapped.map(mapping => (
              <NeedsReviewCard key={mapping.id} mapping={mapping} />
            ))}
            {filteredBuckets.unmapped.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">All mappings look good!</p>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Approved (Final List) */}
        <div>
          <ColumnHeader 
            title="Approved"
            count={filteredBuckets.approved.length}
            icon={<CheckCircle className="h-5 w-5 text-green-600" />}
            bgColor="bg-green-50 border border-green-200"
          />
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {filteredBuckets.approved.map(mapping => (
              <ApprovedCard key={mapping.id} mapping={mapping} />
            ))}
            {filteredBuckets.approved.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <ArrowRight className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">Approved mappings will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {buckets.autoMapped.length > 0 && (
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Bulk Actions for {buckets.autoMapped.length} auto-mapped fields
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  const mappingIds = buckets.autoMapped.map(m => m.id);
                  handleBulkApprove(mappingIds);
                }}
                disabled={!client?.id || !engagement?.id || 
                         buckets.autoMapped.some(m => processingMappings.has(m.id)) || 
                         (Date.now() - lastBulkOperationTime < 5000)}
                className="flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircle className="h-4 w-4" />
                {!client?.id || !engagement?.id ? 'Login Required' :
                 buckets.autoMapped.some(m => processingMappings.has(m.id)) ? 'Processing...' : 
                 (Date.now() - lastBulkOperationTime < 5000) ? 'Cooldown...' : 'Approve All'}
              </button>
              <button
                onClick={() => {
                  const mappingIds = buckets.autoMapped.map(m => m.id);
                  handleBulkReject(mappingIds);
                }}
                disabled={!client?.id || !engagement?.id || 
                         buckets.autoMapped.some(m => processingMappings.has(m.id)) || 
                         (Date.now() - lastBulkOperationTime < 5000)}
                className="flex items-center gap-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <XCircle className="h-4 w-4" />
                {!client?.id || !engagement?.id ? 'Login Required' :
                 buckets.autoMapped.some(m => processingMappings.has(m.id)) ? 'Processing...' : 
                 (Date.now() - lastBulkOperationTime < 5000) ? 'Cooldown...' : 'Reject All'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreeColumnFieldMapper;