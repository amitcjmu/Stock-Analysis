import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../../config/api';
import { useAuth } from '../../../../contexts/AuthContext';

// Components
import { RejectionDialog } from './components/RejectionDialog';
import { FieldMappingCard } from './components/FieldMappingCard';
import { StatusFilters } from './components/StatusFilters';
import { PaginationControls } from './components/PaginationControls';

// Types
import { FieldMappingsTabProps, TargetField } from './types';

const ITEMS_PER_PAGE = 6;

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onMappingChange
}) => {
  const { client, engagement } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);
  const [rejectionDialog, setRejectionDialog] = useState<{
    isOpen: boolean;
    mappingId: string;
    sourceField: string;
    targetField: string;
  }>({
    isOpen: false,
    mappingId: '',
    sourceField: '',
    targetField: ''
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // Filter state
  const [visibleStatuses, setVisibleStatuses] = useState({
    pending: true,
    approved: true,
    rejected: true
  });

  // Load available target fields
  useEffect(() => {
    const fetchAvailableFields = async () => {
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_FIELDS, {
          method: 'GET',
          headers: {
            'X-Client-Account-ID': client?.id?.toString(),
            'X-Engagement-ID': engagement?.id?.toString()
          }
        });

        if (response?.data?.available_fields) {
          setAvailableFields(response.data.available_fields);
        }
      } catch (error) {
        console.error('Error fetching available fields:', error);
      }
    };

    if (client?.id && engagement?.id) {
      fetchAvailableFields();
    }
  }, [client?.id, engagement?.id]);

  // Filter mappings based on visible statuses
  const filteredMappings = fieldMappings.filter(mapping => 
    visibleStatuses[mapping.status as keyof typeof visibleStatuses]
  );

  // Pagination logic
  const totalPages = Math.ceil(filteredMappings.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const currentMappings = filteredMappings.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [visibleStatuses]);

  const handleStatusToggle = (status: string) => {
    setVisibleStatuses(prev => ({
      ...prev,
      [status]: !prev[status as keyof typeof prev]
    }));
  };

  const handleRejectMapping = (mappingId: string, sourceField: string, targetField: string) => {
    setRejectionDialog({
      isOpen: true,
      mappingId,
      sourceField,
      targetField
    });
  };

  const handleConfirmRejection = (reason: string) => {
    onMappingAction(rejectionDialog.mappingId, 'reject', reason);
    setRejectionDialog({
      isOpen: false,
      mappingId: '',
      sourceField: '',
      targetField: ''
    });
  };

  const handleCancelRejection = () => {
    setRejectionDialog({
      isOpen: false,
      mappingId: '',
      sourceField: '',
      targetField: ''
    });
  };

  if (isAnalyzing) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Analyzing field mappings...</p>
          <p className="text-sm text-gray-500 mt-2">
            AI agents are determining the best field mappings for your data
          </p>
        </div>
      </div>
    );
  }

  if (!fieldMappings || fieldMappings.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-2">No field mappings available</p>
        <p className="text-sm text-gray-500">
          Complete the data import to see AI-generated field mappings
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <StatusFilters
        visibleStatuses={visibleStatuses}
        onStatusToggle={handleStatusToggle}
      />

      <div className="grid gap-4">
        {currentMappings.map((mapping) => (
          <FieldMappingCard
            key={mapping.id}
            mapping={mapping}
            availableFields={availableFields}
            onMappingAction={onMappingAction}
            onMappingChange={onMappingChange}
            onReject={handleRejectMapping}
          />
        ))}
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />

      <RejectionDialog
        isOpen={rejectionDialog.isOpen}
        mappingId={rejectionDialog.mappingId}
        sourceField={rejectionDialog.sourceField}
        targetField={rejectionDialog.targetField}
        onConfirm={handleConfirmRejection}
        onCancel={handleCancelRejection}
      />
    </div>
  );
};

export default FieldMappingsTab;