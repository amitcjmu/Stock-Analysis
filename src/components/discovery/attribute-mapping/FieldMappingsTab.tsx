import React, { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle, X, RefreshCw, ChevronDown, ChevronLeft, ChevronRight, Tag } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';

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
  category: string;
  is_custom?: boolean;
}

interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
}

interface RejectionDialogProps {
  isOpen: boolean;
  mappingId: string;
  sourceField: string;
  targetField: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}

const RejectionDialog: React.FC<RejectionDialogProps> = ({
  isOpen,
  mappingId,
  sourceField,
  targetField,
  onConfirm,
  onCancel
}) => {
  const [reason, setReason] = useState('');
  const [selectedReason, setSelectedReason] = useState('');

  const commonReasons = [
    'Incorrect field mapping',
    'Wrong data type',
    'Field not relevant for migration',
    'Better alternative available',
    'Data quality concerns',
    'Security/privacy concerns',
    'Custom field needed'
  ];

  const handleConfirm = () => {
    const finalReason = selectedReason || reason || 'User rejected this mapping';
    onConfirm(finalReason);
    setReason('');
    setSelectedReason('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold mb-4">Reject Field Mapping</h3>
        <p className="text-gray-600 mb-4">
          Why are you rejecting the mapping of <strong>{sourceField}</strong> to <strong>{targetField}</strong>?
        </p>
        
        <div className="space-y-3 mb-4">
          <label className="block text-sm font-medium text-gray-700">Common reasons:</label>
          {commonReasons.map((commonReason) => (
            <label key={commonReason} className="flex items-center">
              <input
                type="radio"
                name="rejectionReason"
                value={commonReason}
                checked={selectedReason === commonReason}
                onChange={(e) => setSelectedReason(e.target.value)}
                className="mr-2"
              />
              <span className="text-sm">{commonReason}</span>
            </label>
          ))}
          <label className="flex items-center">
            <input
              type="radio"
              name="rejectionReason"
              value="custom"
              checked={selectedReason === 'custom'}
              onChange={(e) => setSelectedReason(e.target.value)}
              className="mr-2"
            />
            <span className="text-sm">Other (specify below)</span>
          </label>
        </div>

        {selectedReason === 'custom' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom reason:
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Please explain why this mapping is incorrect..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Reject Mapping
          </button>
        </div>
      </div>
    </div>
  );
};

const ITEMS_PER_PAGE = 6;

// Category colors for visual organization
const CATEGORY_COLORS: Record<string, string> = {
  identification: 'bg-blue-100 text-blue-800',
  technical: 'bg-green-100 text-green-800',
  network: 'bg-purple-100 text-purple-800',
  environment: 'bg-yellow-100 text-yellow-800',
  business: 'bg-orange-100 text-orange-800',
  application: 'bg-pink-100 text-pink-800',
  migration: 'bg-indigo-100 text-indigo-800',
  cost: 'bg-red-100 text-red-800',
  risk: 'bg-gray-100 text-gray-800',
  dependencies: 'bg-cyan-100 text-cyan-800',
  performance: 'bg-teal-100 text-teal-800',
  discovery: 'bg-lime-100 text-lime-800',
  ai_insights: 'bg-violet-100 text-violet-800'
};

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

  // Load available target fields on component mount
  useEffect(() => {
    fetchAvailableFields();
  }, []);

  // Filter options - show all by default, but allow filtering
  const [showApproved, setShowApproved] = useState(true);
  const [showRejected, setShowRejected] = useState(false);
  const [showPending, setShowPending] = useState(true);

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
  const editableFieldMappings = fieldMappings.map((mapping: any) => ({
    ...mapping,
    status: mapping.status === 'suggested' ? 'pending' : mapping.status || 'pending'
  }));
  
  // Apply filters
  const filteredMappings = editableFieldMappings.filter((mapping: any) => {
    if (mapping.status === 'approved' && !showApproved) return false;
    if (mapping.status === 'rejected' && !showRejected) return false;
    if ((mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) && !showPending) return false;
    return true;
  });

  // This check is now handled above before processing

  const fetchAvailableFields = async () => {
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
      
      console.log('🔧 Fetching available fields with headers:', authHeaders);
      
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS, {
        method: 'GET',
        headers: authHeaders
      });
      
      if (response && response.fields) {
        // Ensure all fields have category property and deduplicate by name
        const fieldsWithCategories = response.fields.map((field: any) => ({
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
      // Enhanced fallback with categories and deduplication
      const fallbackFields = [
        { name: 'name', type: 'string', required: true, description: 'Asset name or identifier', category: 'identification' },
        { name: 'hostname', type: 'string', required: true, description: 'Asset hostname', category: 'identification' },
        { name: 'owner', type: 'string', required: false, description: 'Asset owner', category: 'business' },
        { name: 'asset_name', type: 'string', required: false, description: 'Asset name', category: 'identification' },
        { name: 'asset_type', type: 'enum', required: true, description: 'Asset type', category: 'technical' },
        { name: 'ip_address', type: 'string', required: false, description: 'IP address', category: 'network' },
        { name: 'environment', type: 'string', required: true, description: 'Environment', category: 'environment' },
        { name: 'operating_system', type: 'string', required: false, description: 'Operating system', category: 'technical' },
        { name: 'cpu_cores', type: 'integer', required: false, description: 'CPU cores', category: 'technical' },
        { name: 'memory_gb', type: 'number', required: false, description: 'Memory in GB', category: 'technical' },
        { name: 'department', type: 'string', required: false, description: 'Department', category: 'business' },
        { name: 'business_owner', type: 'string', required: false, description: 'Business owner', category: 'business' }
      ];
      
      // Apply the same deduplication logic to fallback fields
      const uniqueFallbackFields = fallbackFields.reduce((acc: TargetField[], field: TargetField) => {
        const existingField = acc.find(f => f.name === field.name);
        if (!existingField) {
          acc.push(field);
        }
        return acc;
      }, []);
      
      setAvailableFields(uniqueFallbackFields);
    } finally {
      setLoadingFields(false);
    }
  };

  // Get unique categories from available fields
  const getCategories = () => {
    if (!Array.isArray(availableFields) || availableFields.length === 0) {
      return ['all'];
    }
    const categories = Array.from(new Set(availableFields.map(field => field.category))).sort();
    return ['all', ...categories];
  };

  // Filter fields by category and search term
  const getFilteredFields = () => {
    if (!Array.isArray(availableFields) || availableFields.length === 0) {
      return [];
    }
    
    let filtered = availableFields;
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(field => field.category === selectedCategory);
    }
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(field => 
        field.name.toLowerCase().includes(term) ||
        field.description.toLowerCase().includes(term) ||
        field.category.toLowerCase().includes(term)
      );
    }
    
    return filtered.sort((a, b) => {
      // Sort by required first, then by name
      if (a.required && !b.required) return -1;
      if (!a.required && b.required) return 1;
      return a.name.localeCompare(b.name);
    });
  };

  // Calculate pagination using filtered mappings
  const totalPages = Math.ceil(filteredMappings.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentMappings = filteredMappings.slice(startIndex, endIndex);

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
    // Reset filters when opening dropdown
    if (!openDropdowns[mappingId]) {
      setSelectedCategory('all');
      setSearchTerm('');
    }
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

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category] || 'bg-gray-100 text-gray-700';
  };

  const handleRejectionConfirm = (reason: string) => {
    onMappingAction(rejectionDialog.mappingId, 'reject', reason);
    setRejectionDialog({
      isOpen: false,
      mappingId: '',
      sourceField: '',
      targetField: ''
    });
  };

  const handleRejectionCancel = () => {
    setRejectionDialog({
      isOpen: false,
      mappingId: '',
      sourceField: '',
      targetField: ''
    });
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
      
      {/* Filter controls */}
      <div className="mb-4 flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
        <span className="text-sm font-medium text-gray-700">Show:</span>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={showPending}
            onChange={(e) => setShowPending(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm text-gray-600">Pending ({editableFieldMappings.filter(m => m.status === 'pending' || m.status === 'suggested' || !m.status).length})</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={showApproved}
            onChange={(e) => setShowApproved(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm text-gray-600">Approved ({editableFieldMappings.filter(m => m.status === 'approved').length})</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={showRejected}
            onChange={(e) => setShowRejected(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm text-gray-600">Rejected ({editableFieldMappings.filter(m => m.status === 'rejected').length})</span>
        </label>
      </div>

      {filteredMappings.length === 0 ? (
        <div className="text-center py-10">
          <Tag className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No Field Mappings</h3>
          <p className="mt-1 text-sm text-gray-500">
            {editableFieldMappings.length === 0 
              ? 'No automated field mappings were generated. You can manually map fields or analyze your data again.'
              : 'No mappings match your current filter criteria. Try adjusting the filters above.'
            }
          </p>
        </div>
      ) : (
        <>
          {/* Scrollable container for mappings */}
          <div className="space-y-4 max-h-[500px] overflow-y-auto">
            {currentMappings.map((mapping) => (
              <div key={mapping.id} className={`border rounded-lg p-4 ${getMappingStatusColor(mapping.status)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-2">
                      <h4 className="font-medium text-gray-900">{mapping.sourceField}</h4>
                      <ArrowRight className="h-4 w-4 text-gray-400" />
                      
                      {/* Enhanced dropdown for target field selection */}
                      <div className="relative">
                        <button
                          onClick={() => toggleDropdown(mapping.id)}
                          disabled={mapping.status === 'approved' || mapping.status === 'rejected'}
                          className={`flex items-center space-x-2 px-3 py-1 rounded-lg border ${
                            mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status
                              ? 'bg-white border-gray-300 hover:border-blue-500 cursor-pointer' 
                              : mapping.status === 'approved'
                              ? 'bg-green-50 border-green-200 cursor-not-allowed'
                              : 'bg-red-50 border-red-200 cursor-not-allowed'
                          }`}
                        >
                          <span className="text-xs bg-gray-100 px-1 rounded">{mapping.status || 'unknown'}</span>
                          <span className={`font-medium ${
                            mapping.status === 'pending' ? 'text-blue-600' :
                            mapping.status === 'approved' ? 'text-green-700' : 'text-red-700'
                          }`}>
                            {mapping.targetAttribute}
                          </span>
                          {mapping.status === 'pending' && (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          )}
                          {mapping.status === 'approved' && (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          )}
                          {mapping.status === 'rejected' && (
                            <X className="h-4 w-4 text-red-600" />
                          )}
                        </button>
                        
                        {/* Enhanced dropdown menu with categories and search */}
                        {openDropdowns[mapping.id] && (mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) && (
                          <div className="absolute z-10 mt-1 w-80 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-hidden">
                            {loadingFields ? (
                              <div className="p-3 text-center text-gray-500">Loading fields...</div>
                            ) : (
                              <>
                                {/* Search and category filter */}
                                <div className="p-3 border-b border-gray-200 space-y-2">
                                  <input
                                    type="text"
                                    placeholder="Search fields..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                  />
                                  <select
                                    value={selectedCategory}
                                    onChange={(e) => setSelectedCategory(e.target.value)}
                                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                  >
                                    {getCategories().map(category => (
                                      <option key={category} value={category}>
                                        {category === 'all' ? 'All Categories' : category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                                
                                {/* Fields list */}
                                <div className="max-h-64 overflow-y-auto">
                                  {getFilteredFields().length === 0 ? (
                                    <div className="p-3 text-center text-gray-500 text-sm">
                                      No fields match your search criteria
                                    </div>
                                  ) : (
                                    <div className="py-1">
                                      {getFilteredFields().map((field) => (
                                        <button
                                          key={field.name}
                                          onClick={() => handleTargetFieldChange(mapping.id, field.name)}
                                          className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                                            field.name === mapping.targetAttribute ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                                          }`}
                                        >
                                          <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                              <div className="font-medium">{field.name}</div>
                                              <div className="text-xs text-gray-500 mt-1">{field.description}</div>
                                            </div>
                                            <div className="flex flex-col items-end space-y-1 ml-2">
                                              <span className={`text-xs px-1 py-0.5 rounded ${getCategoryColor(field.category)}`}>
                                                {field.category.replace('_', ' ')}
                                              </span>
                                              <span className={`px-1 py-0.5 text-xs rounded ${field.required ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                                                {field.required ? 'Required' : 'Optional'}
                                              </span>
                                              {field.is_custom && (
                                                <span className="px-1 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Custom</span>
                                              )}
                                            </div>
                                          </div>
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {/* Show current field category if mapped */}
                      {mapping.targetAttribute !== 'unmapped' && Array.isArray(availableFields) && (
                        <span className={`text-xs px-2 py-1 rounded ${getCategoryColor(availableFields.find(f => f.name === mapping.targetAttribute)?.category || 'unknown')}`}>
                          {availableFields.find(f => f.name === mapping.targetAttribute)?.category?.replace('_', ' ') || 'Unknown'}
                        </span>
                      )}
                    </div>
                    
                    {/* Confidence and sample values */}
                    <div className="flex items-center space-x-4 mb-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(mapping.confidence)}`}>
                        {Math.round(mapping.confidence * 100)}% confidence
                      </span>
                      {Array.isArray(mapping.sample_values) && mapping.sample_values.length > 0 && (
                        <div className="text-xs text-gray-500">
                          Sample: {mapping.sample_values.slice(0, 3).join(', ')}
                          {mapping.sample_values.length > 3 && '...'}
                        </div>
                      )}
                    </div>
                    
                    {/* AI reasoning */}
                    {mapping.ai_reasoning && (
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                        <strong>AI Analysis:</strong> {mapping.ai_reasoning}
                      </div>
                    )}
                  </div>
                  
                  {/* Action buttons */}
                  {(mapping.status === 'pending' || mapping.status === 'suggested' || !mapping.status) && (
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => onMappingAction(mapping.id, 'approve')}
                        className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                        title="Approve mapping"
                      >
                        <CheckCircle className="h-3 w-3" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => setRejectionDialog({
                          isOpen: true,
                          mappingId: mapping.id,
                          sourceField: mapping.sourceField,
                          targetField: mapping.targetAttribute
                        })}
                        className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50"
                        title="Reject mapping"
                      >
                        <X className="h-3 w-3" />
                        <span>Reject</span>
                      </button>
                    </div>
                  )}
                  
                  {/* Status indicator for completed mappings */}
                  {mapping.status !== 'pending' && (
                    <div className={`px-2 py-1 text-xs rounded-full ${
                      mapping.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {mapping.status}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">{startIndex + 1}</span> to <span className="font-medium">{Math.min(endIndex, filteredMappings.length)}</span> of <span className="font-medium">{filteredMappings.length}</span> results
                {filteredMappings.length !== editableFieldMappings.length && (
                  <span className="ml-2 text-gray-500">(filtered from {editableFieldMappings.length} total)</span>
                )}
              </p>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
      
      {/* Rejection Dialog */}
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