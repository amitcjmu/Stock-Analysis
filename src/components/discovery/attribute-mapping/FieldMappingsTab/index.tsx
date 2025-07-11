import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../../config/api';
import { useAuth } from '../../../../contexts/AuthContext';

// Components
import ThreeColumnFieldMapper from './components/ThreeColumnFieldMapper';

// Types
import { FieldMappingsTabProps, TargetField } from './types';

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onMappingChange,
  onRefresh
}) => {
  const { client, engagement } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);

  // Load available target fields with error handling
  useEffect(() => {
    const fetchAvailableFields = async () => {
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS, {
          method: 'GET',
          headers: {
            'X-Client-Account-ID': client?.id?.toString(),
            'X-Engagement-ID': engagement?.id?.toString()
          }
        });

        if (response?.fields) {
          setAvailableFields(response.fields);
        } else if (response?.data?.available_fields) {
          setAvailableFields(response.data.available_fields);
        } else {
          // Fallback: provide basic field options
          setAvailableFields([
            { name: 'hostname', type: 'string', required: true, description: 'Server hostname', category: 'identity' },
            { name: 'ip_address', type: 'string', required: true, description: 'IP address', category: 'network' },
            { name: 'operating_system', type: 'string', required: false, description: 'Operating system', category: 'system' },
            { name: 'application_name', type: 'string', required: false, description: 'Application name', category: 'application' }
          ]);
        }
      } catch (error) {
        console.error('Error fetching available fields:', error);
        // Provide fallback fields so the component doesn't break
        setAvailableFields([
          { name: 'hostname', type: 'string', required: true, description: 'Server hostname', category: 'identity' },
          { name: 'ip_address', type: 'string', required: true, description: 'IP address', category: 'network' },
          { name: 'operating_system', type: 'string', required: false, description: 'Operating system', category: 'system' }
        ]);
      }
    };

    if (client?.id && engagement?.id) {
      fetchAvailableFields();
    }
  }, [client?.id, engagement?.id]);

  // Filter mappings based on visible statuses - with safety check
  const safeFieldMappings = Array.isArray(fieldMappings) ? fieldMappings : [];

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

  if (!safeFieldMappings || safeFieldMappings.length === 0) {
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
      <ThreeColumnFieldMapper
        fieldMappings={safeFieldMappings}
        availableFields={availableFields}
        onMappingAction={onMappingAction}
        onMappingChange={onMappingChange}
        onRefresh={onRefresh}
      />
    </div>
  );
};

export default FieldMappingsTab;