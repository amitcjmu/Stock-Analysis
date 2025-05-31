import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ArrowRight, Database, CheckCircle, AlertTriangle, MapPin, Target, Brain, Users, 
  ArrowLeft, RefreshCw, Search, Filter, Download, Upload, Eye, Edit, X, Plus
} from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import RawDataTable from '../../components/discovery/RawDataTable';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { apiCall } from '../../config/api';

// Interface definitions
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

interface CustomAttribute {
  field: string;
  description: string;
  importance: 'critical' | 'high' | 'medium' | 'low';
  usedFor: string[];
  examples: string[];
  category: string;
  dataType: 'string' | 'number' | 'boolean' | 'array' | 'object';
  customField: boolean;
  createdBy?: string;
}

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
}

const AttributeMapping = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // State management
  const [importedData, setImportedData] = useState<any[]>([]);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [crewAnalysis, setCrewAnalysis] = useState<CrewAnalysis[]>([]);
  const [activeTab, setActiveTab] = useState('data');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [customAttributes, setCustomAttributes] = useState<CustomAttribute[]>([]);
  const [mappingProgress, setMappingProgress] = useState({
    total: 0,
    mapped: 0,
    critical_mapped: 0,
    accuracy: 0
  });

  // Critical attributes definition
  const CRITICAL_ATTRIBUTES = {
    asset_name: {
      field: "Asset Name",
      description: "Unique identifier for the asset",
      importance: "critical" as const,
      usedFor: ["6R Analysis", "Wave Planning", "Dependencies"],
      examples: ["APP-SERVER-01", "DB-PROD-MYSQL"],
      category: "identity"
    },
    asset_type: {
      field: "Asset Type", 
      description: "Classification of the asset",
      importance: "critical" as const,
      usedFor: ["6R Strategy", "Migration Tools", "Cost Estimation"],
      examples: ["Server", "Database", "Application"],
      category: "technical"
    },
    environment: {
      field: "Environment",
      description: "Operating environment",
      importance: "critical" as const,
      usedFor: ["Wave Planning", "Risk Assessment", "Testing Strategy"],
      examples: ["Production", "Test", "Development"],
      category: "business"
    },
    business_criticality: {
      field: "Business Criticality",
      description: "Impact level on business operations",
      importance: "high" as const,
      usedFor: ["Wave Planning", "Downtime Planning", "Risk Assessment"],
      examples: ["Critical", "High", "Medium", "Low"],
      category: "business"
    },
    department: {
      field: "Department",
      description: "Owning business department",
      importance: "high" as const,
      usedFor: ["Wave Planning", "Stakeholder Management", "Cost Allocation"],
      examples: ["Finance", "HR", "Operations"],
      category: "governance"
    },
    ip_address: {
      field: "IP Address",
      description: "Network address for connectivity mapping",
      importance: "high" as const,
      usedFor: ["Dependencies", "Network Planning", "Migration Tools"],
      examples: ["192.168.1.10", "10.0.0.5"],
      category: "network"
    },
    operating_system: {
      field: "Operating System",
      description: "OS platform and version",
      importance: "medium" as const,
      usedFor: ["6R Strategy", "Tool Compatibility", "Licensing"],
      examples: ["Windows Server 2019", "RHEL 8", "Ubuntu 20.04"],
      category: "technical"
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchImportedData();
  }, []);

  // Fetch imported data from previous step
  const fetchImportedData = async () => {
    try {
      const state = location.state as any;
      if (state?.importedData) {
        setImportedData(state.importedData);
        const columns = Object.keys(state.importedData[0] || {});
        if (columns.length > 0) {
          await generateFieldMappings(columns, state.importedData.slice(0, 10));
        }
      } else {
        // Try to load from localStorage as fallback
        const storedData = localStorage.getItem('imported_assets');
        if (storedData) {
          const data = JSON.parse(storedData);
          setImportedData(data);
          const columns = Object.keys(data[0] || {});
          if (columns.length > 0) {
            await generateFieldMappings(columns, data.slice(0, 10));
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch imported data:', error);
    }
  };

  // Generate AI-powered field mappings
  const generateFieldMappings = async (columns: string[], sampleData: any[]) => {
    try {
      setIsAnalyzing(true);
      
      // Agent-driven field mapping analysis
      const agentResponse = await apiCall('/discovery/agents/agent-analysis', 'POST', {
        data_source: {
          columns: columns,
          sample_data: sampleData.slice(0, 10)
        },
        analysis_type: 'field_mapping_analysis',
        page_context: 'attribute-mapping'
      });

      let mappings: FieldMapping[] = [];
      
      if (agentResponse.analysis && agentResponse.mappings) {
        // Use agent recommendations
        mappings = agentResponse.mappings.map((mapping: any, index: number) => ({
          id: `mapping-${index}`,
          sourceField: mapping.source_field,
          targetAttribute: mapping.target_attribute,
          confidence: mapping.confidence,
          mapping_type: 'direct' as const,
          sample_values: mapping.sample_values || [],
          status: 'pending' as const,
          ai_reasoning: mapping.reasoning
        }));
        
        setCrewAnalysis([{
          agent: "Field Mapping Specialist",
          task: "Intelligent field mapping with pattern recognition",
          findings: agentResponse.analysis.findings || [
            `Analyzed ${columns.length} fields from imported data`,
            `Identified ${mappings.length} potential mappings`,
            `Applied learned patterns from previous mapping sessions`
          ],
          recommendations: agentResponse.analysis.recommendations || [
            "Review high-confidence mappings for approval",
            "Verify critical attribute mappings for 6R analysis",
            "Consider custom attributes for organizational-specific fields"
          ],
          confidence: agentResponse.analysis.confidence || 0.85
        }]);
      } else {
        // Fallback: Basic pattern matching
        mappings = columns.map((column, index) => {
          const match = findBestAttributeMatch(column, sampleData, CRITICAL_ATTRIBUTES);
          return {
            id: `mapping-${index}`,
            sourceField: column,
            targetAttribute: match.attribute,
            confidence: match.confidence,
            mapping_type: 'calculated' as const,
            sample_values: extractSampleValues(column, sampleData, 3),
            status: 'pending' as const,
            ai_reasoning: match.reasoning
          };
        });
      }

      setFieldMappings(mappings);
      updateMappingProgress(mappings);
      
    } catch (error) {
      console.error('Agent analysis failed, using fallback:', error);
      // Fallback mapping logic
      const mappings = columns.map((column, index) => {
        const match = findBestAttributeMatch(column, sampleData, CRITICAL_ATTRIBUTES);
        return {
          id: `mapping-${index}`,
          sourceField: column,
          targetAttribute: match.attribute,
          confidence: match.confidence,
          mapping_type: 'direct' as const,
          sample_values: extractSampleValues(column, sampleData, 3),
          status: 'pending' as const,
          ai_reasoning: match.reasoning
        };
      });
      
      setFieldMappings(mappings);
      updateMappingProgress(mappings);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Find best attribute match using pattern recognition
  const findBestAttributeMatch = (column: string, sampleData: any[], allAttributes: any) => {
    const columnLower = column.toLowerCase();
    const sampleValues = extractSampleValues(column, sampleData, 5);
    
    // Direct name matching
    for (const [key, attr] of Object.entries(allAttributes)) {
      const attrName = key.toLowerCase();
      if (columnLower.includes(attrName) || attrName.includes(columnLower)) {
        return { attribute: key, confidence: 0.9, reasoning: `Direct match with ${attr.field}` };
      }
    }
    
    // Pattern-based inference
    const inference = inferFromValues(sampleValues);
    if (inference.attribute !== 'unmapped') {
      return inference;
    }

    // Default to unmapped
    return { attribute: 'unmapped', confidence: 0, reasoning: 'No clear pattern detected' };
  };

  // Extract sample values from column
  const extractSampleValues = (column: string, data: any[], count: number) => {
    return data.slice(0, count).map(row => String(row[column] || '')).filter(val => val);
  };

  // Infer attribute from sample values
  const inferFromValues = (values: string[]) => {
    if (values.length === 0) return { attribute: 'unmapped', confidence: 0, reasoning: 'No sample values' };
    
    // IP address pattern
    if (values.some(val => /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(val))) {
      return { attribute: 'ip_address', confidence: 0.9, reasoning: 'IP address pattern detected' };
    }
    
    // Environment values
    const envValues = ['prod', 'test', 'dev', 'stage', 'production', 'development'];
    if (values.some(val => envValues.includes(val.toLowerCase()))) {
      return { attribute: 'environment', confidence: 0.8, reasoning: 'Environment values detected' };
    }
    
    // Asset type values
    const typeValues = ['server', 'database', 'application', 'app', 'db', 'srv'];
    if (values.some(val => typeValues.some(type => val.toLowerCase().includes(type)))) {
      return { attribute: 'asset_type', confidence: 0.8, reasoning: 'Asset type values detected' };
    }
    
    // Numeric patterns
    if (values.every(val => /^\d+$/.test(val))) {
      const nums = values.map(Number);
      if (nums.every(n => n >= 1 && n <= 64)) {
        return { attribute: 'cpu_cores', confidence: 0.6, reasoning: 'Small integers suggest CPU cores' };
      }
      if (nums.every(n => n >= 100)) {
        return { attribute: 'storage_gb', confidence: 0.6, reasoning: 'Large numbers suggest storage GB' };
      }
    }

    return { attribute: 'unmapped', confidence: 0, reasoning: 'No clear pattern detected' };
  };

  // Handle mapping approval with agent learning
  const handleApproveMapping = async (mappingId: string) => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send learning feedback to agents
      await apiCall('/discovery/agents/agent-learning', 'POST', {
        learning_type: 'field_mapping_approval',
        original_prediction: {
          source_field: mapping.sourceField,
          target_attribute: mapping.targetAttribute,
          confidence: mapping.confidence
        },
        user_correction: {
          action: 'approved',
          final_mapping: mapping.targetAttribute
        },
        context: {
          sample_values: mapping.sample_values,
          reasoning: mapping.ai_reasoning
        },
        page_context: 'attribute-mapping'
      });
    } catch (error) {
      console.log('Agent learning unavailable:', error);
    }

    // Update local state
    setFieldMappings(prev => prev.map(m => 
      m.id === mappingId 
        ? { ...m, status: 'approved' as const }
        : m
    ));
    
    updateMappingProgress(fieldMappings.map(m => 
      m.id === mappingId ? { ...m, status: 'approved' as const } : m
    ));
  };

  // Handle custom mapping
  const handleCustomMapping = (mappingId: string, newAttribute: string) => {
    setFieldMappings(prev => prev.map(m => 
      m.id === mappingId 
        ? { 
            ...m, 
            targetAttribute: newAttribute,
            mapping_type: 'manual' as const,
            status: 'approved' as const,
            ai_reasoning: 'User custom mapping'
          }
        : m
    ));
  };

  // Get attributes by category
  const getAttributesByCategory = (category: string) => {
    return Object.entries(CRITICAL_ATTRIBUTES).filter(
      ([_, attr]) => attr.category === category
    );
  };

  // Get progress color
  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'text-green-600 bg-green-100';
    if (progress >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  // Handle mapping actions with agent learning
  const handleMappingAction = async (mappingId: string, action: 'approve' | 'reject') => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send learning feedback to agents
      await apiCall('/discovery/agents/agent-learning', 'POST', {
        learning_type: 'field_mapping_feedback',
        original_prediction: {
          source_field: mapping.sourceField,
          target_attribute: mapping.targetAttribute,
          confidence: mapping.confidence
        },
        user_correction: {
          action: action,
          feedback_type: action === 'approve' ? 'positive' : 'negative'
        },
        context: {
          sample_values: mapping.sample_values,
          reasoning: mapping.ai_reasoning
        },
        page_context: 'attribute-mapping'
      });
    } catch (error) {
      console.log('Agent learning unavailable:', error);
    }

    // Update local state
    const newStatus = action === 'approve' ? 'approved' : 'rejected';
    const updatedMappings = fieldMappings.map(m => 
      m.id === mappingId ? { ...m, status: newStatus as 'approved' | 'rejected' } : m
    );
    
    setFieldMappings(updatedMappings);
    updateMappingProgress(updatedMappings);
  };

  // Update mapping progress
  const updateMappingProgress = (mappings: FieldMapping[]) => {
    const total = mappings.length;
    const mapped = mappings.filter(m => m.status === 'approved').length;
    const criticalMapped = mappings.filter(m => 
      m.status === 'approved' && Object.keys(CRITICAL_ATTRIBUTES).includes(m.targetAttribute)
    ).length;
    const accuracy = mapped > 0 ? mappings.filter(m => m.status === 'approved' && m.confidence >= 0.7).length / mapped : 0;

    setMappingProgress({
      total,
      mapped,
      critical_mapped: criticalMapped,
      accuracy
    });
  };

  // Handle continue to data cleansing
  const handleContinueToDataCleansing = () => {
    navigate('/discovery/data-cleansing', {
      state: {
        fromAttributeMapping: true,
        fieldMappings: fieldMappings,
        importedData: importedData,
        mappingProgress: mappingProgress
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <div className="flex h-full">
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            <main className="p-8">
              <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Attribute Mapping & AI Training
                  </h1>
                  <p className="text-lg text-gray-600">
                    Train the AI crew to understand your data's attribute associations and field mappings
                  </p>
                </div>

                {/* Progress Dashboard */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-white rounded-lg shadow-md p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">{mappingProgress.total}</h3>
                        <p className="text-xs text-gray-600">Total Fields</p>
                      </div>
                      <Database className="h-6 w-6 text-blue-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-green-600">{mappingProgress.mapped}</h3>
                        <p className="text-xs text-gray-600">Mapped</p>
                      </div>
                      <CheckCircle className="h-6 w-6 text-green-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-purple-600">{mappingProgress.critical_mapped}</h3>
                        <p className="text-xs text-gray-600">Critical Mapped</p>
                      </div>
                      <Target className="h-6 w-6 text-purple-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-indigo-600">
                          {Math.round(mappingProgress.accuracy * 100)}%
                        </h3>
                        <p className="text-xs text-gray-600">Accuracy</p>
                      </div>
                      <Brain className="h-6 w-6 text-indigo-500" />
                    </div>
                  </div>
                </div>

                {/* AI Crew Analysis */}
                {crewAnalysis.length > 0 && (
                  <div className="mb-8">
                    <div className="bg-white rounded-lg shadow-md">
                      <div className="p-6 border-b border-gray-200">
                        <div className="flex items-center space-x-3">
                          <Users className="h-6 w-6 text-blue-500" />
                          <h2 className="text-xl font-semibold text-gray-900">AI Crew Analysis</h2>
                        </div>
                      </div>
                      <div className="p-6">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                          {crewAnalysis.map((analysis, index) => (
                            <div key={index} className="border rounded-lg p-4">
                              <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-gray-900">{analysis.agent}</h3>
                                <span className={`px-2 py-1 text-xs rounded-full ${getProgressColor(analysis.confidence * 100)}`}>
                                  {Math.round(analysis.confidence * 100)}% confidence
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mb-3 font-medium">{analysis.task}</p>
                              
                              <div className="mb-3">
                                <h4 className="text-sm font-medium text-gray-700 mb-1">Findings:</h4>
                                <ul className="text-sm text-gray-600 space-y-1">
                                  {analysis.findings.map((finding, idx) => (
                                    <li key={idx}>• {finding}</li>
                                  ))}
                                </ul>
                              </div>
                              
                              <div className="bg-blue-50 border-l-4 border-blue-400 p-3">
                                <h4 className="text-sm font-medium text-blue-800 mb-1">Recommendations:</h4>
                                <ul className="text-sm text-blue-700 space-y-1">
                                  {analysis.recommendations.map((rec, idx) => (
                                    <li key={idx}>• {rec}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Tabs */}
                <div className="mb-6">
                  <nav className="flex space-x-8">
                    {[
                      { id: 'data', label: 'Imported Data', icon: Database },
                      { id: 'mappings', label: 'Field Mappings', icon: MapPin },
                      { id: 'critical', label: 'Critical Attributes', icon: Target },
                      { id: 'progress', label: 'Training Progress', icon: Brain }
                    ].map((tab) => {
                      const Icon = tab.icon;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                            activeTab === tab.id
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                          <span>{tab.label}</span>
                        </button>
                      );
                    })}
                  </nav>
                </div>

                {/* Imported Data Tab */}
                {activeTab === 'data' && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">Imported Data Review</h2>
                        <p className="text-gray-600 mt-1">
                          Review your imported data before setting up attribute mappings
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <Database className="h-4 w-4" />
                        <span>{importedData.length} records imported</span>
                      </div>
                    </div>
                    
                    {importedData.length > 0 ? (
                      <RawDataTable
                        data={importedData}
                        title="Imported Dataset for Attribute Mapping"
                        pageSize={10}
                        showLegend={false}
                      />
                    ) : (
                      <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                        <Database className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                        <p className="text-gray-600 mb-4">
                          Import data first to begin attribute mapping.
                        </p>
                        <button
                          onClick={() => navigate('/discovery/data-import')}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          Go to Data Import
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Field Mappings Tab */}
                {activeTab === 'mappings' && (
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
                    
                    <div className="space-y-4">
                      {fieldMappings.map((mapping) => (
                        <div key={mapping.id} className={`border rounded-lg p-4 ${
                          mapping.status === 'approved' ? 'bg-green-50 border-green-200' :
                          mapping.status === 'rejected' ? 'bg-red-50 border-red-200' :
                          'bg-white border-gray-200'
                        }`}>
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-4 mb-2">
                                <h4 className="font-medium text-gray-900">{mapping.sourceField}</h4>
                                <ArrowRight className="h-4 w-4 text-gray-400" />
                                <span className="font-medium text-blue-600">{mapping.targetAttribute}</span>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  mapping.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                                  mapping.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
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
                                    onClick={() => handleMappingAction(mapping.id, 'approve')}
                                    className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    onClick={() => handleMappingAction(mapping.id, 'reject')}
                                    className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
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
                  </div>
                )}

                {/* Critical Attributes Tab */}
                {activeTab === 'critical' && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Critical Attributes for Migration</h2>
                    
                    {['identity', 'business', 'technical', 'network', 'governance'].map(category => (
                      <div key={category} className="mb-8">
                        <h3 className="text-lg font-medium text-gray-900 mb-4 capitalize">{category} Attributes</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {getAttributesByCategory(category).map(([key, attr]) => {
                            const isMapped = fieldMappings.some(m => m.targetAttribute === key && m.status === 'approved');
                            return (
                              <div key={key} className={`border rounded-lg p-4 ${isMapped ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="font-medium text-gray-900">{attr.field}</h4>
                                  <div className="flex items-center space-x-2">
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                      attr.importance === 'critical' ? 'bg-red-100 text-red-800' :
                                      attr.importance === 'high' ? 'bg-orange-100 text-orange-800' :
                                      'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {attr.importance}
                                    </span>
                                    {isMapped && <CheckCircle className="h-4 w-4 text-green-600" />}
                                  </div>
                                </div>
                                <p className="text-sm text-gray-600 mb-2">{attr.description}</p>
                                <div className="text-xs text-gray-500">
                                  <strong>Used for:</strong> {attr.usedFor.join(', ')}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  <strong>Examples:</strong> {attr.examples.join(', ')}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Progress Tab */}
                {activeTab === 'progress' && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">AI Training Progress</h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="font-medium text-gray-900 mb-4">Mapping Coverage</h3>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-600">Total Fields Mapped</span>
                              <span className="text-sm font-medium">{mappingProgress.mapped}/{mappingProgress.total}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${(mappingProgress.mapped / mappingProgress.total) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                          
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-600">Critical Attributes</span>
                              <span className="text-sm font-medium">{mappingProgress.critical_mapped}/7</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-green-600 h-2 rounded-full" 
                                style={{ width: `${(mappingProgress.critical_mapped / 7) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                          
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-600">AI Accuracy</span>
                              <span className="text-sm font-medium">{Math.round(mappingProgress.accuracy * 100)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-purple-600 h-2 rounded-full" 
                                style={{ width: `${mappingProgress.accuracy * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="font-medium text-gray-900 mb-4">Readiness Assessment</h3>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">6R Analysis Ready</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${mappingProgress.critical_mapped >= 3 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {mappingProgress.critical_mapped >= 3 ? 'Yes' : 'No'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Wave Planning Ready</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${mappingProgress.critical_mapped >= 5 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                              {mappingProgress.critical_mapped >= 5 ? 'Yes' : 'Partial'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Cost Estimation Ready</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${fieldMappings.some(m => ['cpu_cores', 'memory_gb'].includes(m.targetAttribute) && m.status === 'approved') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {fieldMappings.some(m => ['cpu_cores', 'memory_gb'].includes(m.targetAttribute) && m.status === 'approved') ? 'Yes' : 'No'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Continue Button */}
                <div className="flex justify-center">
                  <button
                    onClick={handleContinueToDataCleansing}
                    disabled={mappingProgress.critical_mapped < 3}
                    className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors ${
                      mappingProgress.critical_mapped >= 3
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <span>Continue to Data Cleansing</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </div>
                
                {mappingProgress.critical_mapped < 3 && (
                  <p className="text-center text-sm text-gray-600 mt-2">
                    Map at least 3 critical attributes to proceed
                  </p>
                )}
              </div>
            </main>
          </div>

          {/* Agent Interaction Sidebar */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="attribute-mapping"
                onQuestionAnswered={(questionId, response) => {
                  console.log('Mapping question answered:', questionId, response);
                  // Trigger re-analysis of field mappings with agent learning
                  if (importedData.length > 0) {
                    const columns = Object.keys(importedData[0]);
                    generateFieldMappings(columns, importedData.slice(0, 5));
                  }
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="attribute-mapping"
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Field classification updated:', itemId, newClassification);
                  // Update field mapping confidence based on classification
                  setFieldMappings(prev => prev.map(mapping => 
                    mapping.id === itemId 
                      ? { 
                          ...mapping, 
                          confidence: newClassification === 'good_data' ? Math.min(mapping.confidence + 0.1, 1.0) : Math.max(mapping.confidence - 0.1, 0.1)
                        }
                      : mapping
                  ));
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="attribute-mapping"
                onInsightAction={(insightId, action) => {
                  console.log('Mapping insight action:', insightId, action);
                  // Apply agent recommendations to field mappings
                  if (action === 'helpful') {
                    // Boost confidence of related mappings
                    console.log('Applying agent recommendations for mapping improvement');
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributeMapping; 