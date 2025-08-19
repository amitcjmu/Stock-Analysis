import React from 'react'
import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { RefreshCw } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../../config/api';
import { useAuth } from '../../../../contexts/AuthContext';
import type { FieldMappingsTabProps, FilterOptions, RejectionDialogState } from './types'
import type { FieldMapping, TargetField } from './types'
import MappingFilters from './MappingFilters';
import FieldMappingsList from './FieldMappingsList';
import MappingPagination from './MappingPagination';
import RejectionDialog from './RejectionDialog';

const ITEMS_PER_PAGE = 15;

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onMappingChange
}) => {
  const { getAuthHeaders } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);
  const [loadingFields, setLoadingFields] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [openDropdowns, setOpenDropdowns] = useState<Record<string, boolean>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [approvingMappings, setApprovingMappings] = useState<Set<string>>(new Set());
  const [rejectingMappings, setRejectingMappings] = useState<Set<string>>(new Set());
  const [rejectionDialog, setRejectionDialog] = useState<RejectionDialogState>({
    isOpen: false,
    mappingId: '',
    sourceField: '',
    targetField: ''
  });

  // Filter options - show all by default, but allow filtering
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    showApproved: true,
    showRejected: false,
    showPending: true
  });

  const fetchAvailableFields = useCallback(async () => {
    // Check if we already have fields cached to prevent unnecessary calls
    if (availableFields.length > 0) {
      console.log('📋 Available fields already loaded, skipping fetch');
      return;
    }

    try {
      setLoadingFields(true);

      // Get auth headers including context from AuthContext
      const authHeaders = getAuthHeaders();

      // Also check for persisted user context selection
      const userContextData = localStorage.getItem('user_context_selection');
      if (userContextData) {
        try {
          const context = JSON.parse(userContextData);
          if (context.clientId && !authHeaders['X-Client-Account-Id']) {
            authHeaders['X-Client-Account-Id'] = context.clientId;
          }
          if (context.engagementId && !authHeaders['X-Engagement-Id']) {
            authHeaders['X-Engagement-Id'] = context.engagementId;
          }
        } catch (err) {
          console.warn('Failed to parse stored context:', err);
        }
      }

      if (process.env.NODE_ENV !== 'production') {
        console.log('🔧 Fetching available fields', {
          endpoint: API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS,
          method: 'GET'
        });
      }

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS, {
        method: 'GET',
        headers: authHeaders
      });

      if (response && response.fields) {
        // Ensure all fields have category property and deduplicate by name
        const fieldsWithCategories = response.fields.map((field: TargetField) => ({
          ...field,
          category: field.category || 'uncategorized'
        }));

        // Deduplicate fields by name to prevent dropdown errors
        const uniqueFields = fieldsWithCategories.reduce((acc: TargetField[], field: TargetField) => {
          const existingField = acc.find(f => f.name === field.name);
          if (!existingField) {
            acc.push(field);
          } else {
            // If duplicate exists, prefer the one with more complete information
            if (field.description && !existingField.description) {
              const index = acc.findIndex(f => f.name === field.name);
              acc[index] = field;
            }
          }
          return acc;
        }, []);

        setAvailableFields(uniqueFields);
        console.log(`📋 Loaded ${uniqueFields.length} unique available target fields across ${Object.keys(response.categories || {}).length} categories`);
      } else {
        console.warn('No fields returned from API, using fallback');
        throw new Error('No fields in response');
      }
    } catch (error) {
      console.error('Failed to load available target fields:', error);

      // If it's a rate limit error, just log it and don't throw
      if (error && typeof error === 'object' && 'status' in error && (error as {status: number}).status === 429) {
        console.warn('Rate limited on available fields - will use cached data if available');
        return;
      }

      // For other errors, still don't break the component
      console.warn('Using fallback behavior due to API error');
    } finally {
      setLoadingFields(false);
    }
  }, [availableFields.length, getAuthHeaders]);

  // Load available target fields on component mount - with debouncing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchAvailableFields();
    }, 500); // 500ms debounce

    return () => clearTimeout(debounceTimer);
  }, [fetchAvailableFields]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent): void => {
      const target = event.target as Element;
      if (!target.closest('.dropdown-container')) {
        setOpenDropdowns({});
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Debug logging for field mappings
  console.log('🔍 FieldMappingsTab received:', {
    fieldMappings: fieldMappings,
    isArray: Array.isArray(fieldMappings),
    length: fieldMappings?.length,
    sample: fieldMappings?.[0]
  });

  // Early return if no field mappings
  if (!Array.isArray(fieldMappings) || fieldMappings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8 text-center">
        <p className="text-gray-500">
          {!Array.isArray(fieldMappings) ? 'Loading field mappings...' : 'No field mappings available yet.'}
        </p>
        <div className="mt-4 text-xs text-gray-400">
          Debug: {JSON.stringify({ fieldMappings: fieldMappings?.slice(0, 2), isArray: Array.isArray(fieldMappings) })}
        </div>
      </div>
    );
  }

  // Force field mappings to be editable if they're in "suggested" status
  const editableFieldMappings = fieldMappings.map((mapping: FieldMapping) => ({
    ...mapping,
    status: mapping.status === 'suggested' ? 'pending' : mapping.status || 'pending'
  }));

  // Apply filters
  const filteredMappings = editableFieldMappings.filter((mapping: FieldMapping) => {
    if (mapping.status === 'approved' && !filterOptions.showApproved) return false;
    if (mapping.status === 'rejected' && !filterOptions.showRejected) return false;
    if ((mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) && !filterOptions.showPending) return false;
    return true;
  });

  // Calculate pagination using filtered mappings
  const totalPages = Math.ceil(filteredMappings.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;

  // Calculate mapping counts for filters
  const mappingCounts = {
    pending: editableFieldMappings.filter(m => m.status === 'pending' || m.status === 'suggested' || !m.status).length,
    approved: editableFieldMappings.filter(m => m.status === 'approved').length,
    rejected: editableFieldMappings.filter(m => m.status === 'rejected').length
  };

  const handleTargetFieldChange = (mappingId: string, newTarget: string): void => {
    setOpenDropdowns(prev => ({ ...prev, [mappingId]: false }));
    if (onMappingChange) {
      onMappingChange(mappingId, newTarget);
    }
  };

  const toggleDropdown = (mappingId: string): unknown => {
    setOpenDropdowns(prev => ({
      ...prev,
      [mappingId]: !prev[mappingId]
    }));
    // Reset filters when opening dropdown
    if (!openDropdowns[mappingId]) {
      setSelectedCategory('all');
      setSearchTerm('');
    }
  };

  const handleApproveMapping = async (mappingId: string): void => {
    setApprovingMappings(prev => new Set(prev).add(mappingId));
    try {
      await onMappingAction(mappingId, 'approve');
    } catch (error) {
      console.error('Failed to approve mapping:', error);
    } finally {
      setApprovingMappings(prev => {
        const next = new Set(prev);
        next.delete(mappingId);
        return next;
      });
    }
  };

  const handleRejectMapping = async (mappingId: string, reason?: string): void => {
    setRejectingMappings(prev => new Set(prev).add(mappingId));
    try {
      await onMappingAction(mappingId, 'reject', reason);
      setRejectionDialog({
        isOpen: false,
        mappingId: '',
        sourceField: '',
        targetField: ''
      });
    } catch (error) {
      console.error('Failed to reject mapping:', error);
    } finally {
      setRejectingMappings(prev => {
        const next = new Set(prev);
        next.delete(mappingId);
        return next;
      });
    }
  };

  const handleRejectMappingDialog = (mappingId: string, sourceField: string, targetField: string): void => {
    setRejectionDialog({
      isOpen: true,
      mappingId,
      sourceField,
      targetField
    });
  };

  const handleRejectionConfirm = (reason: string): void => {
    handleRejectMapping(rejectionDialog.mappingId, reason);
  };

  const handleRejectionCancel = (): void => {
    setRejectionDialog({
      isOpen: false,
      mappingId: '',
      sourceField: '',
      targetField: ''
    });
  };

  const getCategories = (): unknown => {
    if (!Array.isArray(availableFields) || availableFields.length === 0) {
      return ['all'];
    }
    const categories = Array.from(new Set(availableFields.map(field => field.category))).sort();
    return ['all', ...categories];
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Field Mapping Suggestions</h2>
          <p className="text-sm text-gray-600 mt-1">
            {Array.isArray(availableFields) ? availableFields.length : 0} available target fields across {getCategories().length - 1} categories
          </p>
        </div>
        {isAnalyzing && (
          <div className="flex items-center space-x-2 text-blue-600">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI analyzing...</span>
          </div>
        )}
      </div>

      <MappingFilters
        filterOptions={filterOptions}
        onFilterChange={setFilterOptions}
        mappingCounts={mappingCounts}
      />

      <FieldMappingsList
        fieldMappings={filteredMappings}
        currentPage={currentPage}
        itemsPerPage={ITEMS_PER_PAGE}
        availableFields={availableFields}
        openDropdowns={openDropdowns}
        approvingMappings={approvingMappings}
        rejectingMappings={rejectingMappings}
        onToggleDropdown={toggleDropdown}
        onTargetFieldChange={handleTargetFieldChange}
        onApproveMapping={handleApproveMapping}
        onRejectMapping={handleRejectMappingDialog}
        selectedCategory={selectedCategory}
        searchTerm={searchTerm}
        loadingFields={loadingFields}
        onCategoryChange={setSelectedCategory}
        onSearchTermChange={setSearchTerm}
      />

      <MappingPagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={editableFieldMappings.length}
        filteredItems={filteredMappings.length}
        startIndex={startIndex}
        endIndex={endIndex}
        onPageChange={setCurrentPage}
      />

      <RejectionDialog
        isOpen={rejectionDialog.isOpen}
        mappingId={rejectionDialog.mappingId}
        sourceField={rejectionDialog.sourceField}
        targetField={rejectionDialog.targetField}
        onConfirm={handleRejectionConfirm}
        onCancel={handleRejectionCancel}
      />
    </div>
  );
};

export default FieldMappingsTab;
