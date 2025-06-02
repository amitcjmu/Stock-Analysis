import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, CheckCircle, XCircle, Target, Brain } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import RawDataTable from '../../components/discovery/RawDataTable';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import { apiCall, API_CONFIG } from '../../config/api';

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
}

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
}

interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  accuracy: number;
}

// Critical attributes definition
const CRITICAL_ATTRIBUTES = {
  asset_name: { field: "Asset Name", category: "identity" },
  asset_type: { field: "Asset Type", category: "technical" },
  environment: { field: "Environment", category: "business" },
  business_criticality: { field: "Business Criticality", category: "business" },
  department: { field: "Department", category: "governance" },
  ip_address: { field: "IP Address", category: "network" },
  operating_system: { field: "Operating System", category: "technical" }
};

const AttributeMapping = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // State management
  const [importedData, setImportedData] = useState<any[]>([]);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [crewAnalysis, setCrewAnalysis] = useState<CrewAnalysis[]>([]);
  const [activeTab, setActiveTab] = useState('data');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mappingProgress, setMappingProgress] = useState<MappingProgress>({
    total: 0,
    mapped: 0,
    critical_mapped: 0,
    accuracy: 0
  });
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  // Load data on component mount
  useEffect(() => {
    fetchImportedData();
  }, []);

  // Fetch imported data from database or previous step
  const fetchImportedData = async () => {
    try {
      const state = location.state as any;
      
      // Priority 1: Direct data from navigation state
      if (state?.importedData && state.importedData.length > 0) {
        console.log('Using imported data from navigation state');
        setImportedData(state.importedData);
        const columns = Object.keys(state.importedData[0] || {});
        if (columns.length > 0) {
          await generateFieldMappings(columns, state.importedData.slice(0, 10));
        }
        return;
      }
      
      // Priority 2: Load from database using session ID
      if (state?.import_session_id) {
        console.log('Loading data from database using session ID:', state.import_session_id);
        try {
          const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.GET_IMPORT}/${state.import_session_id}`);
          if (response.success && response.data.length > 0) {
            setImportedData(response.data);
            const columns = Object.keys(response.data[0] || {});
            if (columns.length > 0) {
              await generateFieldMappings(columns, response.data.slice(0, 10));
            }
            return;
          }
        } catch (error) {
          console.warn('Failed to load data from specific session, trying latest import:', error);
        }
      }
      
      // Priority 3: Load latest import from database
      console.log('Loading latest import from database');
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
        if (response.success && response.data.length > 0) {
          console.log(`Loaded ${response.data.length} records from latest import session ${response.import_session_id}`);
          setImportedData(response.data);
          const columns = Object.keys(response.data[0] || {});
          if (columns.length > 0) {
            await generateFieldMappings(columns, response.data.slice(0, 10));
          }
          return;
        }
      } catch (error) {
        console.warn('Database import not available, checking localStorage for compatibility');
      }
      
      // Priority 4: Fallback to localStorage for compatibility (silent operation)
      const storedData = localStorage.getItem('imported_assets');
      if (storedData) {
        try {
          const data = JSON.parse(storedData);
          console.log(`✅ Found ${data.length} records in localStorage`);
          setImportedData(data);
          const columns = Object.keys(data[0] || {});
          if (columns.length > 0) {
            await generateFieldMappings(columns, data.slice(0, 10));
          }
          return;
        } catch (parseError) {
          console.warn('Invalid localStorage data, clearing and redirecting to import');
          localStorage.removeItem('imported_assets');
        }
      }
      
      // No data found anywhere
      console.warn('No imported data found in any location');
      setImportedData([]);
      
    } catch (error) {
      console.error('Failed to fetch imported data:', error);
      setImportedData([]);
    }
  };

  // Generate AI-powered field mappings
  const generateFieldMappings = async (columns: string[], sampleData: any[]) => {
    try {
      setIsAnalyzing(true);
      
      // Agent-driven field mapping analysis
      const agentResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        body: JSON.stringify({
          data_source: {
            columns: columns,
            sample_data: sampleData.slice(0, 10)
          },
          analysis_type: 'field_mapping_analysis',
          page_context: 'attribute-mapping'
        })
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
          const match = findBestAttributeMatch(column, sampleData);
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
      
      // Trigger agent panel analysis after field mappings are generated
      await triggerAgentPanelAnalysis(mappings, sampleData);
      
    } catch (error) {
      console.error('Agent analysis failed, using fallback:', error);
      // Fallback mapping logic
      const mappings = columns.map((column, index) => {
        const match = findBestAttributeMatch(column, sampleData);
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
      
      // Trigger agent panel analysis even in fallback mode
      await triggerAgentPanelAnalysis(mappings, sampleData);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Trigger agent panel analysis after field mappings are generated
  const triggerAgentPanelAnalysis = async (mappings: FieldMapping[], sampleData: any[]) => {
    try {
      // Trigger comprehensive agent analysis for attribute mapping page
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        body: JSON.stringify({
          data_source: {
            file_data: sampleData.slice(0, 20), // Send sample data for classification
            columns: mappings.map(m => m.sourceField),
            metadata: {
              file_name: "attribute_mapping_data.csv",
              mapping_context: "attribute-mapping",
              field_mappings: mappings.map(m => ({
                source: m.sourceField,
                target: m.targetAttribute,
                confidence: m.confidence,
                status: m.status
              }))
            }
          },
          analysis_type: 'data_source_analysis',
          page_context: 'attribute-mapping'
        })
      });
      
      // Trigger refresh after agent analysis
      setTimeout(() => {
        setAgentRefreshTrigger(prev => prev + 1);
      }, 2000); // Give agents time to process
      
    } catch (error) {
      console.error('Agent panel analysis failed:', error);
    }
  };

  // Find best attribute match using pattern recognition
  const findBestAttributeMatch = (column: string, sampleData: any[]) => {
    const columnLower = column.toLowerCase();
    
    // Direct name matching
    for (const [key, attr] of Object.entries(CRITICAL_ATTRIBUTES)) {
      const attrName = key.toLowerCase();
      if (columnLower.includes(attrName) || attrName.includes(columnLower)) {
        return { attribute: key, confidence: 0.9, reasoning: `Direct match with ${attr.field}` };
      }
    }
    
    // Default to unmapped
    return { attribute: 'unmapped', confidence: 0, reasoning: 'No clear pattern detected' };
  };

  // Extract sample values from column
  const extractSampleValues = (column: string, data: any[], count: number) => {
    return data.slice(0, count).map(row => String(row[column] || '')).filter(val => val);
  };

  // Handle mapping actions with agent learning
  const handleMappingAction = async (mappingId: string, action: 'approve' | 'reject') => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send learning feedback to agents
              await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        body: JSON.stringify({
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
        })
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
    
    // Trigger agent refresh after user action
    setAgentRefreshTrigger(prev => prev + 1);
  };

  // Handle mapping target field changes from dropdown
  const handleMappingChange = async (mappingId: string, newTarget: string) => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send learning feedback to agents about the manual change
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        body: JSON.stringify({
          learning_type: 'field_mapping_correction',
          original_prediction: {
            source_field: mapping.sourceField,
            target_attribute: mapping.targetAttribute,
            confidence: mapping.confidence
          },
          user_correction: {
            new_target_attribute: newTarget,
            feedback_type: 'manual_change',
            reason: 'User selected different target field from dropdown'
          },
          context: {
            sample_values: mapping.sample_values,
            reasoning: mapping.ai_reasoning,
            available_alternatives: 'dropdown_selection'
          },
          page_context: 'attribute-mapping'
        })
      });
    } catch (error) {
      console.log('Agent learning unavailable:', error);
    }

    // Update local state with new target
    const updatedMappings = fieldMappings.map(m => 
      m.id === mappingId ? { 
        ...m, 
        targetAttribute: newTarget,
        status: 'pending' as const, // Reset to pending since user changed it
        confidence: 0.9, // High confidence for user selections
        ai_reasoning: `User selected '${newTarget}' from available options (originally suggested '${mapping.targetAttribute}')`
      } : m
    );
    
    setFieldMappings(updatedMappings);
    updateMappingProgress(updatedMappings);
    
    // Trigger agent refresh after user action
    setAgentRefreshTrigger(prev => prev + 1);
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

  // Render tab content based on active tab
  const renderTabContent = () => {
    switch (activeTab) {
      case 'data':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Imported Data Review</h2>
                <p className="text-gray-600 mt-1">
                  Review your imported data before setting up attribute mappings
                </p>
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
                <p className="text-gray-600 mb-4">No data available for mapping.</p>
                <button
                  onClick={() => navigate('/discovery/data-import')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Go to Data Import
                </button>
              </div>
            )}
          </div>
        );
      case 'mappings':
        return (
          <FieldMappingsTab
            fieldMappings={fieldMappings}
            isAnalyzing={isAnalyzing}
            onMappingAction={handleMappingAction}
            onMappingChange={handleMappingChange}
          />
        );
      case 'critical':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Critical Attributes Analysis</h2>
                <p className="text-gray-600 mt-1">
                  Review and validate critical attributes mapped for migration assessment
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-indigo-600">
                  {Math.round(mappingProgress.accuracy * 100)}%
                </div>
                <div className="text-sm text-gray-600">Mapping Accuracy</div>
              </div>
            </div>
            
            {/* Critical Attributes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(CRITICAL_ATTRIBUTES).map(([key, attr]) => {
                const mappedField = fieldMappings.find(m => 
                  m.targetAttribute === key && m.status === 'approved'
                );
                const isMapped = !!mappedField;
                
                return (
                  <div key={key} className={`border rounded-lg p-4 ${
                    isMapped ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
                  }`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{attr.field}</h3>
                        <p className="text-sm text-gray-600 capitalize">{attr.category}</p>
                      </div>
                      {isMapped ? (
                        <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                      ) : (
                        <XCircle className="h-5 w-5 text-gray-400 flex-shrink-0" />
                      )}
                    </div>
                    
                    {isMapped ? (
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-gray-600">Mapped to: </span>
                          <span className="font-medium text-gray-900">{mappedField.sourceField}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Confidence: </span>
                          <span className={`font-medium ${
                            mappedField.confidence >= 0.8 ? 'text-green-600' :
                            mappedField.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {Math.round(mappedField.confidence * 100)}%
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          Sample values: {mappedField.sample_values.slice(0, 2).join(', ')}
                          {mappedField.sample_values.length > 2 && '...'}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        Not mapped yet. Required for migration assessment.
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Critical Mapping Requirements */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <Target className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-blue-900 mb-2">Migration Assessment Requirements</h4>
                  <p className="text-sm text-blue-800 mb-3">
                    Map at least 3 critical attributes to proceed to the assessment phase. 
                    Currently mapped: <span className="font-medium">{mappingProgress.critical_mapped}</span>
                  </p>
                  {mappingProgress.critical_mapped < 3 && (
                    <div className="text-sm text-blue-700">
                      <strong>Priority fields to map:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Asset Name or Hostname (for identification)</li>
                        <li>Asset Type (for 6R strategy selection)</li>
                        <li>Environment or Department (for wave planning)</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      case 'progress':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">AI Training Progress</h2>
                <p className="text-gray-600 mt-1">
                  Monitor AI learning and field mapping intelligence development
                </p>
              </div>
            </div>
            
            {/* Learning Progress Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Field Mapping Intelligence */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-gray-900">Field Mapping Intelligence</h3>
                  <Brain className="h-5 w-5 text-indigo-500" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Pattern Recognition</span>
                    <span className="text-sm font-medium text-green-600">
                      {Math.round(mappingProgress.accuracy * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${mappingProgress.accuracy * 100}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Fields Learned</span>
                    <span className="text-sm font-medium text-blue-600">
                      {fieldMappings.filter(m => m.status === 'approved').length}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(fieldMappings.filter(m => m.status === 'approved').length / Math.max(fieldMappings.length, 1)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
              
              {/* Data Quality Intelligence */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-gray-900">Data Quality Intelligence</h3>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Classification Accuracy</span>
                    <span className="text-sm font-medium text-green-600">
                      {fieldMappings.length > 0 ? Math.round((fieldMappings.filter(m => m.confidence >= 0.7).length / fieldMappings.length) * 100) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${fieldMappings.length > 0 ? (fieldMappings.filter(m => m.confidence >= 0.7).length / fieldMappings.length) * 100 : 0}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Learning Examples</span>
                    <span className="text-sm font-medium text-purple-600">
                      {fieldMappings.filter(m => m.status !== 'pending').length}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${fieldMappings.length > 0 ? (fieldMappings.filter(m => m.status !== 'pending').length / fieldMappings.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Training History */}
            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-4">Recent Training Activity</h3>
              <div className="space-y-3">
                {fieldMappings.filter(m => m.status !== 'pending').slice(-5).map((mapping, index) => (
                  <div key={mapping.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        Learned: {mapping.sourceField} → {mapping.targetAttribute}
                      </div>
                      <div className="text-xs text-gray-500">
                        {mapping.ai_reasoning || 'Pattern-based mapping'}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        mapping.status === 'approved' ? 'bg-green-100 text-green-700' :
                        mapping.status === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {mapping.status}
                      </span>
                      <span className={`text-xs font-medium ${
                        mapping.confidence >= 0.8 ? 'text-green-600' :
                        mapping.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {Math.round(mapping.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
                
                {fieldMappings.filter(m => m.status !== 'pending').length === 0 && (
                  <div className="text-center py-6 text-gray-500">
                    <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No training examples yet. Start approving field mappings to train the AI.</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* AI Learning Tips */}
            <div className="mt-6 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <Brain className="h-5 w-5 text-indigo-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-indigo-900 mb-2">Improve AI Learning</h4>
                  <ul className="text-sm text-indigo-800 space-y-1">
                    <li>• Approve accurate field mappings to teach the AI your data patterns</li>
                    <li>• Reject incorrect mappings to prevent the AI from learning bad patterns</li>
                    <li>• Manually adjust mappings when needed - the AI will learn from your corrections</li>
                    <li>• The more examples you provide, the better the AI becomes at future mappings</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
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
                <ProgressDashboard mappingProgress={mappingProgress} />

                {/* AI Crew Analysis */}
                <CrewAnalysisPanel crewAnalysis={crewAnalysis} />

                {/* Navigation Tabs */}
                <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />

                {/* Tab Content */}
                {renderTabContent()}

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
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Mapping question answered:', questionId, response);
                  // Trigger re-analysis of field mappings with agent learning
                  if (importedData.length > 0) {
                    const columns = Object.keys(importedData[0]);
                    generateFieldMappings(columns, importedData.slice(0, 5));
                  }
                  // Trigger agent refresh after user interaction
                  setAgentRefreshTrigger(prev => prev + 1);
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="attribute-mapping"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
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
                  // Trigger agent refresh after user interaction
                  setAgentRefreshTrigger(prev => prev + 1);
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="attribute-mapping"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onInsightAction={(insightId, action) => {
                  console.log('Mapping insight action:', insightId, action);
                  // Apply agent recommendations to field mappings
                  if (action === 'helpful') {
                    // Boost confidence of related mappings
                    console.log('Applying agent recommendations for mapping improvement');
                  }
                  // Trigger agent refresh after user interaction
                  setAgentRefreshTrigger(prev => prev + 1);
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