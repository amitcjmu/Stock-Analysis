import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Clock, ArrowRight, Target, TrendingUp, RefreshCw, Check, X, Edit2 } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../hooks/use-toast';
import { Button } from '../../../components/ui/button';

interface CriticalAttribute {
  name: string;
  description: string;
  category: string;
  required: boolean;
  status: 'mapped' | 'unmapped' | 'partially_mapped';
  mapped_to?: string;
  source_field?: string;
  confidence?: number;
  quality_score?: number;
  completeness_percentage?: number;
  mapping_type?: 'direct' | 'calculated' | 'manual' | 'derived';
  ai_suggestion?: string;
  business_impact?: 'high' | 'medium' | 'low';
  migration_critical?: boolean;
}

interface CriticalAttributesTabProps {
  criticalAttributes: CriticalAttribute[];
  onRefreshCriticalData?: () => void;
  isLoading?: boolean;
  isAnalyzing?: boolean;
  fieldMappings?: any[];
  onAttributeUpdate?: (attributeName: string, updates: Partial<CriticalAttribute>) => void;
  sessionInfo?: {
    sessionId: string | null;
    flowId: string | null;
    availableDataImports: any[];
    selectedDataImportId: string | null;
    hasMultipleSessions: boolean;
  };
}

const CriticalAttributesTab: React.FC<CriticalAttributesTabProps> = ({
  criticalAttributes: externalCriticalAttributes,
  onRefreshCriticalData,
  isLoading: externalLoading = false,
  isAnalyzing = false,
  fieldMappings = [],
  onAttributeUpdate,
  sessionInfo
}) => {
  // Use external data instead of internal state
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [processingMappings, setProcessingMappings] = useState<Set<string>>(new Set());
  
  const { user } = useAuth();
  const { toast } = useToast();

  // 🔧 FIX: Use external critical attributes data instead of internal state
  const criticalAttributes = externalCriticalAttributes;

  // Watch for field mapping changes and update critical attributes
  useEffect(() => {
    if (onAttributeUpdate) {
      updateCriticalAttributesFromMappings();
    }
  }, [fieldMappings, onAttributeUpdate]);

  // Update critical attributes based on approved/rejected mappings
  const updateCriticalAttributesFromMappings = () => {
    if (!fieldMappings.length || !criticalAttributes.length || !onAttributeUpdate) return;
    
    fieldMappings.forEach(mapping => {
      const matchingAttribute = criticalAttributes.find(attr => 
        attr.name.toLowerCase() === mapping.targetAttribute.toLowerCase() ||
        attr.mapped_to?.toLowerCase() === mapping.sourceField.toLowerCase()
      );
      
      if (matchingAttribute && mapping.status === 'approved') {
        onAttributeUpdate(matchingAttribute.name, {
          status: 'mapped',
          mapped_to: mapping.sourceField,
          source_field: mapping.sourceField,
          confidence: mapping.confidence,
          quality_score: Math.round(mapping.confidence * 100),
          completeness_percentage: 100,
          mapping_type: 'manual'
        });
      } else if (matchingAttribute && mapping.status === 'rejected') {
        onAttributeUpdate(matchingAttribute.name, {
          status: 'unmapped',
          mapped_to: undefined,
          source_field: undefined,
          confidence: 0,
          quality_score: 0,
          completeness_percentage: 0
        });
      }
    });
  };

  // 🔧 FIX: Use external refresh function instead of making separate API calls
  const refreshCriticalAttributes = async () => {
    if (onRefreshCriticalData) {
      setLoading(true);
      try {
        await onRefreshCriticalData();
        setLastRefresh(new Date());
        toast({
          title: "✅ Data Refreshed",
          description: "Critical attributes updated from latest data analysis",
        });
      } catch (error) {
        console.error('Failed to refresh critical attributes:', error);
        toast({
          title: "❌ Refresh Failed",
          description: "Failed to refresh critical attributes. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    }
  };

  // Get unique categories
  const getCategories = () => {
    const categories = Array.from(new Set(criticalAttributes.map(attr => attr.category))).sort();
    return ['all', ...categories];
  };

  // Filter attributes by category
  const getFilteredAttributes = () => {
    let filtered = criticalAttributes;
    
    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(attr => attr.category === selectedCategory);
    }
    
    // Hide completed mappings (mapped attributes that have been processed)
    // Only show unmapped and partially_mapped attributes that need action
    filtered = filtered.filter(attr => 
      attr.status !== 'mapped' || !attr.source_field
    );
    
    return filtered;
  };

  // Calculate overall statistics
  const getStatistics = () => {
    const filtered = getFilteredAttributes();
    const mapped = filtered.filter(attr => attr.status === 'mapped').length;
    const unmapped = filtered.filter(attr => attr.status === 'unmapped').length;
    const partiallyMapped = filtered.filter(attr => attr.status === 'partially_mapped').length;
    const migrationCritical = filtered.filter(attr => attr.migration_critical).length;
    
    const overallCompleteness = filtered.length > 0 
      ? Math.round((mapped / filtered.length) * 100)
      : 0;

    const avgQualityScore = filtered.length > 0
      ? Math.round(filtered.reduce((sum, attr) => sum + (attr.quality_score || 0), 0) / filtered.length)
      : 0;

    return {
      total: filtered.length,
      mapped,
      unmapped,
      partiallyMapped,
      migrationCritical,
      overallCompleteness,
      avgQualityScore
    };
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'mapped':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'partially_mapped':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'mapped':
        return 'bg-green-50 border-green-200';
      case 'partially_mapped':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-red-50 border-red-200';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      identification: 'bg-blue-100 text-blue-800',
      technical: 'bg-green-100 text-green-800',
      network: 'bg-purple-100 text-purple-800',
      environment: 'bg-yellow-100 text-yellow-800',
      business: 'bg-orange-100 text-orange-800',
      application: 'bg-pink-100 text-pink-800',
      migration: 'bg-indigo-100 text-indigo-800',
      cost: 'bg-red-100 text-red-800',
      risk: 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  const getBusinessImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const stats = getStatistics();
  const filteredAttributes = getFilteredAttributes();

  // Handle mapping approval/rejection for critical attributes
  const handleMappingAction = async (attributeName: string, action: 'approve' | 'reject') => {
    try {
      setProcessingMappings(prev => new Set(prev).add(attributeName));
      
      // Find the related field mapping
      const relatedMapping = fieldMappings.find(mapping => 
        mapping.targetAttribute.toLowerCase() === attributeName.toLowerCase()
      );
      
      if (!relatedMapping) {
        toast({
          title: 'Error',
          description: 'No field mapping found for this attribute',
          variant: 'destructive'
        });
        return;
      }

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_type: 'field_mapping_action',
          action: action,
          mapping_data: {
            source_field: relatedMapping.sourceField,
            target_field: relatedMapping.targetAttribute,
            confidence: relatedMapping.confidence,
            data_import_id: "0b3c1932-78ac-4675-ba07-a50bbe4ca577" // use known import ID
          }
        })
      });

      if (response.status === 'success') {
        toast({ 
          title: action === 'approve' ? 'Mapping approved' : 'Mapping rejected',
          description: `Critical attribute "${attributeName}" has been ${action}d`
        });
        
        // Update local state
        onAttributeUpdate(attributeName, {
          status: action === 'approve' ? 'mapped' as const : 'unmapped' as const,
          quality_score: action === 'approve' ? Math.min(95, (relatedMapping.confidence || 0.8) * 100) : 0,
          completeness_percentage: action === 'approve' ? 100 : 0
        });
      }
    } catch (error) {
      console.error('Error handling mapping action:', error);
      toast({ 
        title: 'Error', 
        description: `Failed to ${action} mapping for ${attributeName}`,
        variant: 'destructive'
      });
    } finally {
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        newSet.delete(attributeName);
        return newSet;
      });
    }
  };

  // Handle alternative field selection
  const handleAlternativeMapping = async (attributeName: string, newSourceField: string) => {
    try {
      setProcessingMappings(prev => new Set(prev).add(attributeName));

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_type: 'field_mapping_change',
          mapping_id: `${attributeName}_${Date.now()}`,
          new_mapping: {
            source_field: newSourceField,
            target_field: attributeName,
            mapping_type: 'manual'
          },
          context: {
            page: 'critical-attributes',
            user_id: user?.id,
            attribute_name: attributeName
          }
        })
      });

      if (response.status === 'success') {
        toast({ 
          title: 'Mapping updated',
          description: `Critical attribute "${attributeName}" mapped to "${newSourceField}"`
        });
        
        // Update local state
        onAttributeUpdate(attributeName, {
          status: 'mapped' as const,
          mapped_to: newSourceField,
          source_field: newSourceField,
          mapping_type: 'manual' as const,
          quality_score: 90,
          completeness_percentage: 100
        });
      }
    } catch (error) {
      console.error('Error updating mapping:', error);
      toast({ 
        title: 'Error', 
        description: `Failed to update mapping for ${attributeName}`,
        variant: 'destructive'
      });
    } finally {
      setProcessingMappings(prev => {
        const newSet = new Set(prev);
        newSet.delete(attributeName);
        return newSet;
      });
    }
  };

  return (
    <div className="p-6 space-y-6">


      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Critical Attributes Mapping</h2>
        <div className="flex items-center space-x-3">
          <Button
            onClick={refreshCriticalAttributes}
            disabled={loading || externalLoading}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${(loading || externalLoading) ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Statistics Dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Total Attributes</p>
              <p className="text-2xl font-bold text-blue-900">{stats.total}</p>
            </div>
            <Target className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Mapped</p>
              <p className="text-2xl font-bold text-green-900">{stats.mapped}</p>
              <p className="text-xs text-green-600">{stats.overallCompleteness}% complete</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-yellow-600 font-medium">Quality Score</p>
              <p className="text-2xl font-bold text-yellow-900">{stats.avgQualityScore}%</p>
              <p className="text-xs text-yellow-600">Average mapping quality</p>
            </div>
            <TrendingUp className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-600 font-medium">Migration Critical</p>
              <p className="text-2xl font-bold text-red-900">{stats.migrationCritical}</p>
              <p className="text-xs text-red-600">Required for assessment</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex items-center space-x-4 mb-6">
        <label className="text-sm font-medium text-gray-700">Filter by Category:</label>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          {getCategories().map(category => (
            <option key={category} value={category}>
              {category === 'all' ? 'All Categories' : category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>
        <div className="text-sm text-gray-500">
          Last updated: {lastRefresh.toLocaleTimeString()}
        </div>
      </div>

      {/* Critical Attributes List */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {filteredAttributes.map((attribute, index) => (
          <div key={index} className={`border rounded-lg p-4 ${getStatusColor(attribute.status)}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-2">
                  {getStatusIcon(attribute.status)}
                  <h4 className="font-medium text-gray-900">{attribute.name}</h4>
                  
                  {/* Show mapping if available */}
                  {attribute.mapped_to && (
                    <>
                      <ArrowRight className="h-4 w-4 text-gray-400" />
                      <span className="text-sm font-medium text-blue-600">{attribute.mapped_to}</span>
                    </>
                  )}
                  
                  {/* Category badge */}
                  <span className={`text-xs px-2 py-1 rounded ${getCategoryColor(attribute.category)}`}>
                    {attribute.category.replace('_', ' ')}
                  </span>
                  
                  {/* Migration critical badge */}
                  {attribute.migration_critical && (
                    <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
                      Migration Critical
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{attribute.description}</p>
                
                {/* Mapping details */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Status:</span>
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                      attribute.status === 'mapped' ? 'bg-green-100 text-green-700' :
                      attribute.status === 'partially_mapped' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {attribute.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  {attribute.confidence && (
                    <div>
                      <span className="font-medium text-gray-700">Confidence:</span>
                      <span className="ml-2 text-gray-900">{Math.round(attribute.confidence * 100)}%</span>
                    </div>
                  )}
                  
                  {attribute.quality_score && (
                    <div>
                      <span className="font-medium text-gray-700">Quality:</span>
                      <span className="ml-2 text-gray-900">{attribute.quality_score}%</span>
                    </div>
                  )}
                  
                  {attribute.mapping_type && (
                    <div>
                      <span className="font-medium text-gray-700">Type:</span>
                      <span className={`ml-2 px-2 py-1 rounded text-xs ${
                        attribute.mapping_type === 'direct' ? 'bg-blue-100 text-blue-700' :
                        attribute.mapping_type === 'calculated' ? 'bg-purple-100 text-purple-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {attribute.mapping_type}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Business impact */}
                {attribute.business_impact && (
                  <div className="mt-3 flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700">Business Impact:</span>
                    <span className={`text-xs px-2 py-1 rounded ${getBusinessImpactColor(attribute.business_impact)}`}>
                      {attribute.business_impact.toUpperCase()}
                    </span>
                  </div>
                )}
                
                {/* AI suggestion */}
                {attribute.ai_suggestion && (
                  <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
                    <strong>AI Suggestion:</strong> {attribute.ai_suggestion}
                  </div>
                )}
                
                {/* Interactive Controls */}
                {attribute.status !== 'mapped' && (
                  <div className="mt-4 flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-700">Actions:</span>
                    
                    {/* Approve/Reject buttons if there's a suggested mapping */}
                    {attribute.source_field && (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleMappingAction(attribute.name, 'approve')}
                          disabled={processingMappings.has(attribute.name)}
                          className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          <Check className="h-3 w-3" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => handleMappingAction(attribute.name, 'reject')}
                          disabled={processingMappings.has(attribute.name)}
                          className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          <X className="h-3 w-3" />
                          <span>Reject</span>
                        </button>
                      </div>
                    )}
                    
                    {/* Alternative mapping selector */}
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-600">Map to:</span>
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            handleAlternativeMapping(attribute.name, e.target.value);
                            e.target.value = ''; // Reset selection
                          }
                        }}
                        disabled={processingMappings.has(attribute.name)}
                        className="text-xs px-2 py-1 border border-gray-300 rounded disabled:opacity-50"
                      >
                        <option value="">Select field...</option>
                        {fieldMappings.map((mapping, idx) => (
                          <option key={idx} value={mapping.sourceField}>
                            {mapping.sourceField}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    {processingMappings.has(attribute.name) && (
                      <div className="flex items-center space-x-1 text-blue-600">
                        <RefreshCw className="h-3 w-3 animate-spin" />
                        <span className="text-xs">Processing...</span>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Show success message for mapped attributes */}
                {attribute.status === 'mapped' && (
                  <div className="mt-4 flex items-center space-x-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm">Successfully mapped to {attribute.mapped_to}</span>
                  </div>
                )}
              </div>
              
              {/* Progress indicator */}
              {attribute.completeness_percentage !== undefined && (
                <div className="flex flex-col items-end ml-4">
                  <div className="text-xs text-gray-500 mb-1">Completeness</div>
                  <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-300 ${
                        attribute.completeness_percentage >= 80 ? 'bg-green-500' :
                        attribute.completeness_percentage >= 60 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${attribute.completeness_percentage}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-700 mt-1">
                    {attribute.completeness_percentage}%
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {filteredAttributes.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No critical attributes found for the selected category.</p>
        </div>
      )}
    </div>
  );
};

export default CriticalAttributesTab; 