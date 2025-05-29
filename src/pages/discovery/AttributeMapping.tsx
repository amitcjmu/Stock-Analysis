import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { 
  Settings, Brain, GraduationCap, CheckCircle, AlertTriangle, 
  ArrowRight, Lightbulb, Save, RefreshCw, Eye,
  ThumbsUp, ThumbsDown, HelpCircle, Wand2
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

interface AttributeMapping {
  id: string;
  sourceField: string;
  sourceValue: string;
  targetField: string;
  suggestedValue: string;
  confidence: number;
  reasoning: string;
  examples: string[];
  status: 'pending' | 'approved' | 'rejected' | 'needs_review';
  assetContext: {
    assetName: string;
    assetType: string;
    department: string;
  };
}

interface FieldDefinition {
  field: string;
  description: string;
  possibleValues: string[];
  examples: string[];
  mappingRules: string[];
}

interface LearningProgress {
  totalMappings: number;
  approvedMappings: number;
  pendingReview: number;
  accuracy: number;
  fieldsCovered: number;
  totalFields: number;
}

const AttributeMapping = () => {
  const [mappings, setMappings] = useState<AttributeMapping[]>([]);
  const [fieldDefinitions, setFieldDefinitions] = useState<FieldDefinition[]>([]);
  const [selectedMapping, setSelectedMapping] = useState<AttributeMapping | null>(null);
  const [activeTab, setActiveTab] = useState('mappings');
  const [filterStatus, setFilterStatus] = useState('pending');
  const [isLoading, setIsLoading] = useState(true);
  const [learningProgress, setLearningProgress] = useState<LearningProgress>({
    totalMappings: 0,
    approvedMappings: 0,
    pendingReview: 0,
    accuracy: 0,
    fieldsCovered: 0,
    totalFields: 0
  });

  useEffect(() => {
    fetchAttributeMappings();
    fetchFieldDefinitions();
    fetchLearningProgress();
  }, []);

  const fetchAttributeMappings = async () => {
    try {
      setIsLoading(true);
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/attribute-mappings`);
      setMappings(response.mappings || []);
    } catch (error) {
      console.error('Failed to fetch attribute mappings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFieldDefinitions = async () => {
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/field-definitions`);
      setFieldDefinitions(response.definitions || []);
    } catch (error) {
      console.error('Failed to fetch field definitions:', error);
    }
  };

  const fetchLearningProgress = async () => {
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/learning-progress`);
      setLearningProgress(response.progress || learningProgress);
    } catch (error) {
      console.error('Failed to fetch learning progress:', error);
    }
  };

  const handleApproveMapping = async (mappingId: string) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/attribute-mappings/${mappingId}/approve`, {
        method: 'POST'
      });
      
      setMappings(prev => prev.map(mapping => 
        mapping.id === mappingId ? { ...mapping, status: 'approved' } : mapping
      ));
      
      // Update progress
      setLearningProgress(prev => ({
        ...prev,
        approvedMappings: prev.approvedMappings + 1,
        pendingReview: prev.pendingReview - 1,
        accuracy: ((prev.approvedMappings + 1) / (prev.totalMappings || 1)) * 100
      }));
      
    } catch (error) {
      console.error('Failed to approve mapping:', error);
    }
  };

  const handleRejectMapping = async (mappingId: string, feedback?: string) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/attribute-mappings/${mappingId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback })
      });
      
      setMappings(prev => prev.map(mapping => 
        mapping.id === mappingId ? { ...mapping, status: 'rejected' } : mapping
      ));
      
    } catch (error) {
      console.error('Failed to reject mapping:', error);
    }
  };

  const handleCustomMapping = async (mappingId: string, customValue: string) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/attribute-mappings/${mappingId}/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customValue })
      });
      
      setMappings(prev => prev.map(mapping => 
        mapping.id === mappingId ? { 
          ...mapping, 
          suggestedValue: customValue,
          status: 'approved'
        } : mapping
      ));
      
    } catch (error) {
      console.error('Failed to set custom mapping:', error);
    }
  };

  const generateNewMappings = async () => {
    try {
      setIsLoading(true);
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/generate-mappings`, {
        method: 'POST'
      });
      await fetchAttributeMappings();
    } catch (error) {
      console.error('Failed to generate new mappings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-100';
      case 'rejected': return 'text-red-600 bg-red-100';
      case 'needs_review': return 'text-orange-600 bg-orange-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const filteredMappings = mappings.filter(mapping => 
    filterStatus === 'all' || mapping.status === filterStatus
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Attribute Mapping & Learning</h1>
              <p className="text-lg text-gray-600">
                Train the AI crew to understand your data's attribute associations and field mappings
              </p>
            </div>

            {/* Learning Progress */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{learningProgress.totalMappings}</h3>
                    <p className="text-xs text-gray-600">Total Mappings</p>
                  </div>
                  <Settings className="h-6 w-6 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-green-600">{learningProgress.approvedMappings}</h3>
                    <p className="text-xs text-gray-600">Approved</p>
                  </div>
                  <CheckCircle className="h-6 w-6 text-green-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-yellow-600">{learningProgress.pendingReview}</h3>
                    <p className="text-xs text-gray-600">Pending Review</p>
                  </div>
                  <AlertTriangle className="h-6 w-6 text-yellow-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-purple-600">{Math.round(learningProgress.accuracy)}%</h3>
                    <p className="text-xs text-gray-600">Accuracy</p>
                  </div>
                  <Brain className="h-6 w-6 text-purple-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-indigo-600">
                      {learningProgress.fieldsCovered}/{learningProgress.totalFields}
                    </h3>
                    <p className="text-xs text-gray-600">Fields Covered</p>
                  </div>
                  <GraduationCap className="h-6 w-6 text-indigo-500" />
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex justify-between items-center">
                <div className="flex space-x-4">
                  <button
                    onClick={generateNewMappings}
                    disabled={isLoading}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    <Wand2 className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Generate New Mappings</span>
                  </button>
                  
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="needs_review">Needs Review</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
                
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Brain className="h-4 w-4" />
                  <span>AI is learning from your feedback</span>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="mb-6">
              <nav className="flex space-x-8">
                {[
                  { id: 'mappings', label: 'Attribute Mappings' },
                  { id: 'definitions', label: 'Field Definitions' },
                  { id: 'rules', label: 'Mapping Rules' }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      activeTab === tab.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Mappings Tab */}
            {activeTab === 'mappings' && (
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Attribute Mapping Suggestions</h2>
                  
                  {filteredMappings.length === 0 ? (
                    <div className="text-center py-12">
                      <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">All Mappings Reviewed</h3>
                      <p className="text-gray-600">Great job! All attribute mappings have been reviewed.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {filteredMappings.map((mapping) => (
                        <div key={mapping.id} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="font-medium text-gray-900">
                                {mapping.assetContext.assetName}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {mapping.assetContext.assetType} • {mapping.assetContext.department}
                              </p>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <div className={`px-2 py-1 rounded-full text-xs ${getConfidenceColor(mapping.confidence)}`}>
                                {Math.round(mapping.confidence * 100)}% confidence
                              </div>
                              <div className={`px-2 py-1 rounded-full text-xs ${getStatusColor(mapping.status)}`}>
                                {mapping.status.replace('_', ' ')}
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div>
                              <label className="text-sm font-medium text-gray-700">Source Field</label>
                              <div className="mt-1 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                                <div className="font-medium">{mapping.sourceField}</div>
                                <div className="text-sm text-gray-600">{mapping.sourceValue}</div>
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-center">
                              <ArrowRight className="h-6 w-6 text-gray-400" />
                            </div>
                            
                            <div>
                              <label className="text-sm font-medium text-gray-700">Suggested Mapping</label>
                              <div className="mt-1 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                <div className="font-medium">{mapping.targetField}</div>
                                <div className="text-sm text-blue-800">{mapping.suggestedValue}</div>
                              </div>
                            </div>
                          </div>
                          
                          <div className="mb-4">
                            <label className="text-sm font-medium text-gray-700">AI Reasoning</label>
                            <div className="mt-1 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                              <div className="flex items-start space-x-2">
                                <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5" />
                                <p className="text-sm text-yellow-800">{mapping.reasoning}</p>
                              </div>
                            </div>
                          </div>
                          
                          {mapping.examples.length > 0 && (
                            <div className="mb-4">
                              <label className="text-sm font-medium text-gray-700">Similar Examples</label>
                              <div className="mt-1 flex flex-wrap gap-2">
                                {mapping.examples.map((example, idx) => (
                                  <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                    {example}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {mapping.status === 'pending' && (
                            <div className="flex justify-end space-x-3">
                              <button
                                onClick={() => handleRejectMapping(mapping.id)}
                                className="flex items-center space-x-2 px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
                              >
                                <ThumbsDown className="h-4 w-4" />
                                <span>Reject</span>
                              </button>
                              
                              <button
                                onClick={() => setSelectedMapping(mapping)}
                                className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                              >
                                <HelpCircle className="h-4 w-4" />
                                <span>Custom Value</span>
                              </button>
                              
                              <button
                                onClick={() => handleApproveMapping(mapping.id)}
                                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                              >
                                <ThumbsUp className="h-4 w-4" />
                                <span>Approve</span>
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Field Definitions Tab */}
            {activeTab === 'definitions' && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Field Definitions</h2>
                <div className="space-y-6">
                  {fieldDefinitions.map((field, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-6">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">{field.field}</h3>
                      <p className="text-gray-600 mb-4">{field.description}</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-gray-700">Possible Values</label>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {field.possibleValues.map((value, idx) => (
                              <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                {value}
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <label className="text-sm font-medium text-gray-700">Examples</label>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {field.examples.map((example, idx) => (
                              <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                                {example}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Mapping Modal */}
            {selectedMapping && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Custom Mapping Value</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Provide a custom value for the field "{selectedMapping.targetField}"
                  </p>
                  
                  <input
                    type="text"
                    placeholder="Enter custom value"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const value = (e.target as HTMLInputElement).value;
                        if (value.trim()) {
                          handleCustomMapping(selectedMapping.id, value.trim());
                          setSelectedMapping(null);
                        }
                      }
                    }}
                  />
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => setSelectedMapping(null)}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => {
                        const input = document.querySelector('input[placeholder="Enter custom value"]') as HTMLInputElement;
                        const value = input?.value?.trim();
                        if (value) {
                          handleCustomMapping(selectedMapping.id, value);
                          setSelectedMapping(null);
                        }
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default AttributeMapping; 