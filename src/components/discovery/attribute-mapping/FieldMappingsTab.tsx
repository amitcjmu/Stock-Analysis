import React, { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle, X, RefreshCw, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../config/api';

interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  action?: 'ignore' | 'delete';
}

interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  is_custom?: boolean;
}

interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject') => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
}

const ITEMS_PER_PAGE = 6;

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onMappingChange
}) => {
  const [availableFields, setAvailableFields] = useState<TargetField[]>([]);
  const [loadingFields, setLoadingFields] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [openDropdowns, setOpenDropdowns] = useState<Record<string, boolean>>({});

  // Load available target fields on component mount
  useEffect(() => {
    fetchAvailableFields();
  }, []);

  const fetchAvailableFields = async () => {
    try {
      setLoadingFields(true);
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS);
      if (response && response.fields) {
        setAvailableFields(response.fields);
      }
    } catch (error) {
      console.error('Failed to load available target fields:', error);
      // Fallback to basic fields if API fails
      setAvailableFields([
        { name: 'hostname', type: 'string', required: true, description: 'Asset hostname' },
        { name: 'asset_name', type: 'string', required: false, description: 'Asset name' },
        { name: 'asset_type', type: 'string', required: true, description: 'Asset type' },
        { name: 'ip_address', type: 'string', required: false, description: 'IP address' },
        { name: 'environment', type: 'string', required: true, description: 'Environment' },
        { name: 'operating_system', type: 'string', required: false, description: 'Operating system' }
      ]);
    } finally {
      setLoadingFields(false);
    }
  };

  // Calculate pagination
  const totalPages = Math.ceil(fieldMappings.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentMappings = fieldMappings.slice(startIndex, endIndex);

  const handleTargetFieldChange = (mappingId: string, newTarget: string) => {
    setOpenDropdowns(prev => ({ ...prev, [mappingId]: false }));
    if (onMappingChange) {
      onMappingChange(mappingId, newTarget);
    }
  };

  const toggleDropdown = (mappingId: string) => {
    setOpenDropdowns(prev => ({ 
      ...prev, 
      [mappingId]: !prev[mappingId] 
    }));
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getMappingStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-50 border-green-200';
      case 'rejected': return 'bg-red-50 border-red-200';
      default: return 'bg-white border-gray-200';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Field Mapping Suggestions</h2>
        {isAnalyzing && (
          <div className="flex items-center space-x-2 text-blue-600">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI analyzing...</span>
          </div>
        )}
      </div>
      
      {/* Scrollable container for mappings */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {currentMappings.map((mapping) => (
          <div key={mapping.id} className={`border rounded-lg p-4 ${getMappingStatusColor(mapping.status)}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-2">
                  <h4 className="font-medium text-gray-900">{mapping.sourceField}</h4>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  
                  {/* Dropdown for target field selection */}
                  <div className="relative">
                    <button
                      onClick={() => toggleDropdown(mapping.id)}
                      disabled={mapping.status === 'approved' || mapping.status === 'rejected'}
                      className={`flex items-center space-x-2 px-3 py-1 rounded-lg border ${
                        mapping.status === 'pending' 
                          ? 'bg-white border-gray-300 hover:border-blue-500 cursor-pointer' 
                          : 'bg-gray-100 border-gray-200 cursor-not-allowed'
                      }`}
                    >
                      <span className="font-medium text-blue-600">{mapping.targetAttribute}</span>
                      {mapping.status === 'pending' && (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                    
                    {/* Dropdown menu */}
                    {openDropdowns[mapping.id] && mapping.status === 'pending' && (
                      <div className="absolute z-10 mt-1 w-64 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {loadingFields ? (
                          <div className="p-3 text-center text-gray-500">Loading fields...</div>
                        ) : (
                          <div className="py-1">
                            {availableFields.map((field) => (
                              <button
                                key={field.name}
                                onClick={() => handleTargetFieldChange(mapping.id, field.name)}
                                className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                                  field.name === mapping.targetAttribute ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                                }`}
                              >
                                <div className="flex justify-between items-start">
                                  <div>
                                    <div className="font-medium">{field.name}</div>
                                    <div className="text-xs text-gray-500">{field.description}</div>
                                  </div>
                                  <div className="flex flex-col items-end text-xs">
                                    <span className={`px-1 rounded ${field.required ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                                      {field.required ? 'Required' : 'Optional'}
                                    </span>
                                    {field.is_custom && (
                                      <span className="mt-1 px-1 bg-purple-100 text-purple-700 rounded">Custom</span>
                                    )}
                                  </div>
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(mapping.confidence)}`}>
                    {Math.round(mapping.confidence * 100)}% confidence
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-2">{mapping.ai_reasoning}</p>
                <div className="text-xs text-gray-500">
                  <strong>Sample values:</strong> {mapping.sample_values.join(', ')}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                {mapping.status === 'pending' && (
                  <>
                    <button
                      onClick={() => onMappingAction(mapping.id, 'approve')}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onMappingAction(mapping.id, 'reject')}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Reject
                    </button>
                  </>
                )}
                {mapping.status === 'approved' && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
                {mapping.status === 'rejected' && (
                  <X className="h-5 w-5 text-red-600" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            Showing {startIndex + 1} to {Math.min(endIndex, fieldMappings.length)} of {fieldMappings.length} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            
            <div className="flex space-x-1">
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i + 1}
                  onClick={() => setCurrentPage(i + 1)}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    currentPage === i + 1 
                      ? 'bg-blue-600 text-white' 
                      : 'border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
            
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
      
      {/* Click outside to close dropdowns */}
      {Object.values(openDropdowns).some(Boolean) && (
        <div 
          className="fixed inset-0 z-5" 
          onClick={() => setOpenDropdowns({})}
        />
      )}
    </div>
  );
};

export default FieldMappingsTab; 