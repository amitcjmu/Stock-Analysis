/**
 * Three Column Field Mapper Component
 * 
 * Main component that orchestrates field mapping display and interactions.
 * 
 * This file has been modularized for better maintainability.
 * Individual modules are located in this directory.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { CheckCircle, AlertCircle, Clock, Search, RefreshCw, ArrowRight } from 'lucide-react';
import { useAuth } from '../../../../../../contexts/AuthContext';

declare global {
  interface Window {
    showWarningToast?: (message: string) => void;
  }
}

// Modularized components and utilities
import AutoMappedCard from './AutoMappedCard';
import NeedsReviewCard from './NeedsReviewCard';
import ApprovedCard from './ApprovedCard';
import ColumnHeader from './ColumnHeader';
import BulkActions from './BulkActions';
import { ThreeColumnFieldMapperProps } from './types';
import { 
  categorizeMappings, 
  filterMappingsBySearch, 
  calculateProgress 
} from './mappingUtils';
import { 
  createBulkApproveHandler, 
  createBulkRejectHandler 
} from './bulkOperations';

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
  const [expandedReasonings, setExpandedReasonings] = useState<Set<string>>(new Set());

  // Categorize mappings into buckets
  const buckets = useMemo(() => categorizeMappings(fieldMappings), [fieldMappings]);

  // Filter mappings based on search
  const filteredBuckets = useMemo(() => 
    filterMappingsBySearch(buckets, searchTerm), 
    [buckets, searchTerm]
  );

  // Create bulk operation handlers
  const handleBulkApprove = useCallback(
    createBulkApproveHandler({
      fieldMappings,
      client,
      engagement,
      lastBulkOperationTime,
      setLastBulkOperationTime,
      setProcessingMappings,
      onRefresh
    }),
    [fieldMappings, client, engagement, lastBulkOperationTime, onRefresh]
  );

  const handleBulkReject = useCallback(
    createBulkRejectHandler({
      client,
      engagement,
      lastBulkOperationTime,
      setLastBulkOperationTime,
      setProcessingMappings,
      onRefresh
    }),
    [client, engagement, lastBulkOperationTime, onRefresh]
  );

  const handleApprove = async (mappingId: string) => {
    if (processingMappings.has(mappingId)) {
      return; // Already processing this mapping
    }
    
    // Check if this is a placeholder or fallback mapping that shouldn't be approved via API
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (mapping && (mapping.is_placeholder || mapping.is_fallback)) {
      console.warn('Cannot approve placeholder or fallback mapping via API:', mappingId);
      if (typeof window !== 'undefined' && window.showWarningToast) {
        window.showWarningToast('This field mapping needs to be configured before approval.');
      }
      return;
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

  const toggleReasoningExpansion = (mappingId: string) => {
    setExpandedReasonings(prev => {
      const newSet = new Set(prev);
      if (newSet.has(mappingId)) {
        newSet.delete(mappingId);
      } else {
        newSet.add(mappingId);
      }
      return newSet;
    });
  };

  const progress = calculateProgress(buckets, fieldMappings.length);

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
              <AutoMappedCard 
                key={mapping.id} 
                mapping={mapping}
                onApprove={handleApprove}
                onReject={handleReject}
                isProcessing={processingMappings.has(mapping.id)}
                expandedReasonings={expandedReasonings}
                onToggleReasoning={toggleReasoningExpansion}
              />
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
              <NeedsReviewCard 
                key={mapping.id} 
                mapping={mapping}
                availableFields={availableFields}
                onMappingChange={onMappingChange}
                onApprove={handleApprove}
              />
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
      <BulkActions
        buckets={buckets}
        onBulkApprove={handleBulkApprove}
        onBulkReject={handleBulkReject}
        processingMappings={processingMappings}
        lastBulkOperationTime={lastBulkOperationTime}
        client={client}
        engagement={engagement}
      />
    </div>
  );
};

export default ThreeColumnFieldMapper;