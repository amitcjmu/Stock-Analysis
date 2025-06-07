import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, CheckCircle, XCircle, Target, Brain, RefreshCw } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import RawDataTable from '../../components/discovery/RawDataTable';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import { apiCall, API_CONFIG } from '../../config/api';
import { useAppContext } from '../../hooks/useContext';

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

// Critical attributes data from API
interface CriticalAttributeStatus {
  name: string;
  description: string;
  category: string;
  required: boolean;
  status: 'mapped' | 'partially_mapped' | 'unmapped';
  mapped_to: string | null;
  source_field: string | null;
  confidence: number | null;
  quality_score: number;
  completeness_percentage: number;
  mapping_type: string | null;
  ai_suggestion: string | null;
  business_impact: string;
  migration_critical: boolean;
}

interface CriticalAttributesData {
  attributes: CriticalAttributeStatus[];
  statistics: {
    total_attributes: number;
    mapped_count: number;
    pending_count: number;
    unmapped_count: number;
    migration_critical_count: number;
    migration_critical_mapped: number;
    overall_completeness: number;
    avg_quality_score: number;
    assessment_ready: boolean;
  };
  recommendations: {
    next_priority: string;
    assessment_readiness: string;
    quality_improvement: string;
  };
  last_updated: string;
}

// Critical attributes definition (fallback for display)
const CRITICAL_ATTRIBUTES = {
  asset_name: { field: "Asset Name", category: "identity" },
  hostname: { field: "Hostname", category: "identity" },
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
  const { getContextHeaders, context } = useAppContext();

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

  // Critical Attributes specific state
  const [criticalAttributesData, setCriticalAttributesData] = useState<CriticalAttributesData | null>(null);
  const [isRefreshingCriticalAttributes, setIsRefreshingCriticalAttributes] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<string>('');

  // Load data on component mount
  useEffect(() => {
    fetchImportedData();
    // Initial load of critical attributes data
    fetchCriticalAttributesData();
  }, []);

  // Refetch data when context changes (client/engagement/session)
  useEffect(() => {
    if (context.client && context.engagement) {
      console.log('🔄 Context changed, refetching attribute mapping data for:', {
        client: context.client.name,
        engagement: context.engagement.name,
        session: context.session?.session_display_name || 'None'
      });
      
      // Refetch imported data for new context
      fetchImportedData();
      
      // Refresh critical attributes if that tab is active
      if (activeTab === 'critical') {
        refreshCriticalAttributes();
      }
    }
  }, [context.client, context.engagement, context.session, context.viewMode]);

  // Fetch critical attributes data from API
  const fetchCriticalAttributesData = async () => {
    try {
      const contextHeaders = getContextHeaders();
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS, {
        headers: contextHeaders
      });
      
      if (response) {
        setCriticalAttributesData(response);
        setLastRefreshTime(new Date().toLocaleTimeString());
        console.log('✅ Critical attributes data refreshed:', response.statistics);
        return response;
      }
    } catch (error) {
      console.error('Failed to fetch critical attributes data:', error);
      return null;
    }
  };

  // Manual refresh function for critical attributes
  const refreshCriticalAttributes = async () => {
    setIsRefreshingCriticalAttributes(true);
    try {
      await fetchCriticalAttributesData();
    } finally {
      setIsRefreshingCriticalAttributes(false);
    }
  };

  // Enhanced tab change handler with auto-refresh
  const handleTabChange = async (newTab: string) => {
    setActiveTab(newTab);
    
    // Auto-refresh critical attributes when switching to that tab
    if (newTab === 'critical') {
      console.log('🔄 Switching to Critical Attributes tab - auto-refreshing data');
      await refreshCriticalAttributes();
    }
  };

  // Fetch imported data from database or previous step
  const fetchImportedData = async () => {
    try {
      const contextHeaders = getContextHeaders();
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
          const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.GET_IMPORT}/${state.import_session_id}`, {
            headers: contextHeaders
          });
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
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT, {
          headers: contextHeaders
        });
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
      const contextHeaders = getContextHeaders();
      
      // Agent-driven field mapping analysis
      console.log('Requesting agent analysis for columns:', columns);
      console.log('Sample data for analysis:', sampleData.slice(0, 2));
      
      const agentResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          data_source: {
            columns: columns,
            sample_data: sampleData.slice(0, 10)
          },
          analysis_type: 'field_mapping_analysis',
          page_context: 'attribute-mapping'
        })
      });

      console.log('Agent analysis response:', agentResponse);

      let mappings: FieldMapping[] = [];
      
      if (agentResponse.agent_analysis && agentResponse.agent_analysis.suggestions) {
        console.log('Using agent-generated field mapping suggestions');
        // Use agent recommendations from suggestions
        mappings = agentResponse.agent_analysis.suggestions.map((suggestion: any, index: number) => ({
          id: `mapping-${index}`,
          sourceField: suggestion.source_field,
          targetAttribute: suggestion.suggested_mappings[0], // Use first suggested mapping
          confidence: suggestion.confidence,
          mapping_type: 'direct' as const,
          sample_values: extractSampleValues(suggestion.source_field, sampleData, 3),
          status: 'pending' as const,
          ai_reasoning: `Agent analysis: ${suggestion.mapping_type} mapping with ${Math.round(suggestion.confidence * 100)}% confidence`
        }));
        
        setCrewAnalysis([{
          agent: "Field Mapping Specialist",
          task: "Intelligent field mapping with content analysis",
          findings: [
            `Analyzed ${columns.length} fields from imported data`,
            `Identified ${mappings.length} potential mappings using content analysis`,
            `Applied AI-driven pattern recognition instead of hardcoded rules`
          ],
          recommendations: [
            "Review high-confidence mappings for approval",
            "Verify critical attribute mappings align with business requirements",
            "Approve mappings to enable AI learning for future improvements"
          ],
          confidence: agentResponse.agent_analysis.confidence || 0.85
        }]);
      } else {
        console.log('Agent analysis did not return mappings, creating unmapped entries for user selection');
        // Fallback: Create unmapped entries for user selection
        mappings = columns.map((column, index) => ({
          id: `mapping-${index}`,
          sourceField: column,
          targetAttribute: 'unmapped',
          confidence: 0,
          mapping_type: 'calculated' as const,
          sample_values: extractSampleValues(column, sampleData, 3),
          status: 'pending' as const,
          ai_reasoning: 'Agent analysis failed - please select mapping manually'
        }));
      }

      console.log('Final field mappings:', mappings);
      setFieldMappings(mappings);
      updateMappingProgress(mappings);
      
      // Trigger agent panel analysis after field mappings are generated
      await triggerAgentPanelAnalysis(mappings, sampleData);
      
    } catch (error) {
      console.error('Agent analysis failed, using fallback:', error);
      // Fallback: Create unmapped entries for user selection
      const mappings = columns.map((column, index) => ({
        id: `mapping-${index}`,
        sourceField: column,
        targetAttribute: 'unmapped',
        confidence: 0,
        mapping_type: 'direct' as const,
        sample_values: extractSampleValues(column, sampleData, 3),
        status: 'pending' as const,
        ai_reasoning: 'Agent analysis failed - please select mapping manually'
      }));
      
      setFieldMappings(mappings);
      updateMappingProgress(mappings);
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

  // Find best attribute match using agent analysis instead of hardcoded patterns
  const findBestAttributeMatch = (column: string, sampleData: any[]) => {
    // Let the agents analyze the data content rather than using hardcoded patterns
    // This will be replaced by agent analysis in generateFieldMappings()
    return null; // No hardcoded matching - let agents decide
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
      // **NEW: Persist mapping to database first**
      const contextHeaders = getContextHeaders();
      const mappingData = {
        source_field: mapping.sourceField,
        target_field: mapping.targetAttribute,
        mapping_type: mapping.mapping_type || 'direct',
        confidence_score: mapping.confidence,
        is_user_defined: action === 'approve',
        status: action === 'approve' ? 'approved' : 'rejected',
        sample_values: mapping.sample_values,
        user_feedback: action === 'approve' ? 'User approved mapping' : 'User rejected mapping',
        original_ai_suggestion: mapping.targetAttribute,
        validation_rules: {},
        transformation_logic: {}
      };

      // Create the mapping record in database
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.DATA_IMPORT}/imports/latest/field-mappings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify(mappingData)
      });

      console.log(`✅ Persisted mapping to database: ${mapping.sourceField} → ${mapping.targetAttribute} (${action})`);

      // Send learning feedback to agents
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
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
      console.error(`Failed to persist mapping: ${error}`);
      // Continue with local state update even if persistence fails
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
    
    // Refresh critical attributes data if user is on that tab or will see it
    if (activeTab === 'critical') {
      console.log('🔄 Mapping updated - refreshing critical attributes');
      await refreshCriticalAttributes();
    } else {
      // Refresh data silently for when user switches to critical tab
      await fetchCriticalAttributesData();
    }
  };

  // Handle mapping target field changes from dropdown
  const handleMappingChange = async (mappingId: string, newTarget: string) => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // **NEW: Persist updated mapping to database**
      const contextHeaders = getContextHeaders();
      const mappingData = {
        source_field: mapping.sourceField,
        target_field: newTarget,
        mapping_type: 'manual',
        confidence_score: 0.9, // High confidence for user selections
        is_user_defined: true,
        status: 'approved', // Auto-approve user selections
        sample_values: mapping.sample_values,
        user_feedback: `User changed target from '${mapping.targetAttribute}' to '${newTarget}'`,
        original_ai_suggestion: mapping.targetAttribute,
        validation_rules: {},
        transformation_logic: {}
      };

      // Create the updated mapping record in database
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.DATA_IMPORT}/imports/latest/field-mappings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify(mappingData)
      });

      console.log(`✅ Persisted mapping change to database: ${mapping.sourceField} → ${newTarget}`);

      // Send learning feedback to agents about the manual change
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
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
      console.error(`Failed to persist mapping change: ${error}`);
      // Continue with local state update even if persistence fails
    }

    // Update local state with new target
    const updatedMappings = fieldMappings.map(m => 
      m.id === mappingId ? { 
        ...m, 
        targetAttribute: newTarget,
        status: 'approved' as const, // Auto-approve user selections
        confidence: 0.9, // High confidence for user selections
        ai_reasoning: `User selected '${newTarget}' from available options (originally suggested '${mapping.targetAttribute}')`
      } : m
    );
    
    setFieldMappings(updatedMappings);
    updateMappingProgress(updatedMappings);
    
    // Trigger agent refresh after user action
    setAgentRefreshTrigger(prev => prev + 1);
    
    // Refresh critical attributes data if user is on that tab or will see it
    if (activeTab === 'critical') {
      console.log('🔄 Mapping changed - refreshing critical attributes');
      await refreshCriticalAttributes();
    } else {
      // Refresh data silently for when user switches to critical tab
      await fetchCriticalAttributesData();
    }
  };

  // Update mapping progress
  const updateMappingProgress = (mappings: FieldMapping[]) => {
    const total = mappings.length;
    const mapped = mappings.filter(m => m.status === 'approved').length;
    
    // Define the most critical fields required for migration assessment
    const requiredCriticalFields = ['asset_name', 'asset_type', 'environment'];
    const mappedCriticalFields = mappings.filter(m => 
      m.status === 'approved' && requiredCriticalFields.includes(m.targetAttribute)
    );
    const criticalMapped = mappedCriticalFields.length;
    
    const accuracy = mapped > 0 ? mappings.filter(m => m.status === 'approved' && m.confidence >= 0.7).length / mapped : 0;

    setMappingProgress({
      total,
      mapped,
      critical_mapped: criticalMapped,
      accuracy
    });
  };

  // Get missing critical fields for user guidance
  const getMissingCriticalFields = () => {
    const requiredCriticalFields = ['asset_name', 'asset_type', 'environment'];
    const mappedCriticalFields = fieldMappings
      .filter(m => m.status === 'approved' && requiredCriticalFields.includes(m.targetAttribute))
      .map(m => m.targetAttribute);
    
    return requiredCriticalFields.filter(field => !mappedCriticalFields.includes(field));
  };

  // Check if we can continue to data cleansing
  const canContinueToDataCleansing = () => {
    const unmappedCriticalFields = getMissingCriticalFields();
    // Enable continue by default unless there are more than 5 critical fields unmapped
    return unmappedCriticalFields.length <= 5;
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
                
                {/* Clarification about data count differences */}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center mt-0.5">
                      <span className="text-xs font-medium text-blue-600">i</span>
                    </div>
                    <div className="text-sm text-blue-800">
                      <strong>Data vs Discovery Overview:</strong> This page shows <strong>raw import records</strong> that need field mapping. 
                      The Discovery Overview shows <strong>processed assets</strong> that have been classified and mapped. 
                      Some data may already be processed while new imports await mapping.
                    </div>
                  </div>
                </div>
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
                <div className="mt-2 text-sm text-blue-600">
                  Last updated: {lastRefreshTime || 'Never'} • Real-time data from database
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={refreshCriticalAttributes}
                  disabled={isRefreshingCriticalAttributes}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    isRefreshingCriticalAttributes 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
                  }`}
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshingCriticalAttributes ? 'animate-spin' : ''}`} />
                  <span>{isRefreshingCriticalAttributes ? 'Refreshing...' : 'Refresh Analysis'}</span>
                </button>
                <div className="text-right">
                  <div className="text-2xl font-bold text-indigo-600">
                    {criticalAttributesData ? Math.round(criticalAttributesData.statistics.overall_completeness) : Math.round(mappingProgress.accuracy * 100)}%
                  </div>
                  <div className="text-sm text-gray-600">Mapping Accuracy</div>
                </div>
              </div>
            </div>
            
            {/* Enhanced Statistics Dashboard with Real-time Data */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-600 font-medium">Total Critical</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {criticalAttributesData ? criticalAttributesData.statistics.total_attributes : Object.keys(CRITICAL_ATTRIBUTES).length}
                    </p>
                  </div>
                  <Target className="h-8 w-8 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Mapped</p>
                    <p className="text-2xl font-bold text-green-900">
                      {criticalAttributesData ? criticalAttributesData.statistics.mapped_count : mappingProgress.critical_mapped}
                    </p>
                    <p className="text-xs text-green-600">
                      {criticalAttributesData 
                        ? Math.round(criticalAttributesData.statistics.overall_completeness)
                        : Math.round((mappingProgress.critical_mapped / Object.keys(CRITICAL_ATTRIBUTES).length) * 100)
                      }% complete
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-500" />
                </div>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-yellow-600 font-medium">Pending</p>
                    <p className="text-2xl font-bold text-yellow-900">
                      {criticalAttributesData 
                        ? criticalAttributesData.statistics.pending_count 
                        : fieldMappings.filter(m => 
                            Object.keys(CRITICAL_ATTRIBUTES).includes(m.targetAttribute) && 
                            m.status === 'pending'
                          ).length
                      }
                    </p>
                  </div>
                  <XCircle className="h-8 w-8 text-yellow-500" />
                </div>
              </div>
              
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-red-600 font-medium">Unmapped</p>
                    <p className="text-2xl font-bold text-red-900">
                      {criticalAttributesData 
                        ? criticalAttributesData.statistics.unmapped_count 
                        : Object.keys(CRITICAL_ATTRIBUTES).length - mappingProgress.critical_mapped
                      }
                    </p>
                  </div>
                  <XCircle className="h-8 w-8 text-red-500" />
                </div>
              </div>
            </div>

            {/* Real-time Mapping Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {criticalAttributesData ? (
                criticalAttributesData.attributes.map((attr) => {
                  const isMapped = attr.status === 'mapped';
                  const isPending = attr.status === 'partially_mapped';
                  const isRejected = attr.status === 'unmapped' && !attr.ai_suggestion;
                
                  return (
                    <div key={attr.name} className={`border rounded-lg p-4 transition-all duration-300 ${
                      isMapped ? 'border-green-200 bg-green-50 shadow-md' : 
                      isPending ? 'border-yellow-200 bg-yellow-50' :
                      isRejected ? 'border-red-200 bg-red-50' :
                      'border-gray-200 bg-gray-50'
                    }`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">
                            {CRITICAL_ATTRIBUTES[attr.name as keyof typeof CRITICAL_ATTRIBUTES]?.field || attr.name}
                          </h3>
                          <div className="flex items-center space-x-2 mt-1">
                            <p className="text-sm text-gray-600 capitalize">{attr.category}</p>
                            {attr.required ? (
                              <span className="px-1 py-0.5 bg-red-100 text-red-700 text-xs rounded">Required</span>
                            ) : (
                              <span className="px-1 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">Important</span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col items-center space-y-1">
                          {isMapped ? (
                            <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                          ) : isPending ? (
                            <div className="h-5 w-5 border-2 border-yellow-500 rounded-full animate-pulse flex-shrink-0" />
                          ) : isRejected ? (
                            <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                          ) : (
                            <div className="h-5 w-5 border-2 border-gray-300 rounded-full flex-shrink-0" />
                          )}
                          {attr.confidence && (
                            <div className="text-xs text-center">
                              <div className="font-medium">
                                {Math.round(attr.confidence * 100)}%
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {isMapped && attr.source_field && (
                        <div className="space-y-2 border-t border-green-200 pt-3">
                          <div className="text-sm">
                            <span className="text-gray-600">✅ Mapped to: </span>
                            <span className="font-medium text-gray-900">{attr.source_field}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <div>
                              <span className="text-gray-600">Confidence: </span>
                              <span className={`font-medium ${
                                attr.confidence && attr.confidence >= 0.8 ? 'text-green-600' :
                                attr.confidence && attr.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {attr.confidence ? Math.round(attr.confidence * 100) : 0}%
                              </span>
                            </div>
                            {attr.mapping_type && (
                              <span className={`px-2 py-1 text-xs rounded ${
                                attr.mapping_type === 'direct' ? 'bg-blue-100 text-blue-700' :
                                'bg-purple-100 text-purple-700'
                              }`}>
                                {attr.mapping_type}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            Quality Score: {attr.quality_score}% • Completeness: {attr.completeness_percentage}%
                          </div>
                        </div>
                      )}
                      
                      {isPending && attr.source_field && (
                        <div className="space-y-2 border-t border-yellow-200 pt-3">
                          <div className="text-sm">
                            <span className="text-gray-600">⏳ Pending: </span>
                            <span className="font-medium text-gray-900">{attr.source_field}</span>
                          </div>
                          <div className="text-xs text-yellow-700 bg-yellow-100 p-2 rounded">
                            Awaiting approval in Field Mappings tab
                          </div>
                        </div>
                      )}
                      
                      {!isMapped && !isPending && attr.ai_suggestion && (
                        <div className="space-y-2 border-t border-blue-200 pt-3">
                          <div className="text-sm text-blue-700 bg-blue-50 p-2 rounded">
                            💡 AI Suggestion: {attr.ai_suggestion}
                          </div>
                        </div>
                      )}
                      
                      {!isMapped && !isPending && !attr.ai_suggestion && (
                        <div className="text-sm text-gray-500 border-t border-gray-200 pt-3">
                          ❓ Not mapped yet. {attr.required ? 
                            'Required for migration assessment.' : 
                            'Recommended for complete analysis.'
                          }
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                // Fallback to local state if API data not available
                Object.entries(CRITICAL_ATTRIBUTES).map(([key, attr]) => {
                  const mappedField = fieldMappings.find(m => 
                    m.targetAttribute === key && m.status === 'approved'
                  );
                  const pendingField = fieldMappings.find(m => 
                    m.targetAttribute === key && m.status === 'pending'
                  );
                  
                  const isMapped = !!mappedField;
                  const isPending = !!pendingField;
                  
                  return (
                    <div key={key} className={`border rounded-lg p-4 transition-all duration-300 ${
                      isMapped ? 'border-green-200 bg-green-50 shadow-md' : 
                      isPending ? 'border-yellow-200 bg-yellow-50' :
                      'border-gray-200 bg-gray-50'
                    }`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{attr.field}</h3>
                          <div className="flex items-center space-x-2 mt-1">
                            <p className="text-sm text-gray-600 capitalize">{attr.category}</p>
                            <span className="px-1 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">Loading...</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-center space-y-1">
                          <div className="h-5 w-5 border-2 border-gray-300 rounded-full animate-pulse flex-shrink-0" />
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 border-t border-gray-200 pt-3">
                        Loading real-time data...
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            {/* Enhanced Requirements Panel with Real-time Updates */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Migration Assessment Readiness */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Target className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-900 mb-2">Migration Assessment Readiness</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-blue-800">Critical fields mapped:</span>
                        <span className="font-medium text-blue-900">
                          {criticalAttributesData 
                            ? `${criticalAttributesData.statistics.migration_critical_mapped}/${criticalAttributesData.statistics.migration_critical_count}` 
                            : `${mappingProgress.critical_mapped}/${Object.keys(CRITICAL_ATTRIBUTES).length}`
                          }
                        </span>
                      </div>
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ 
                            width: `${criticalAttributesData 
                              ? (criticalAttributesData.statistics.migration_critical_mapped / criticalAttributesData.statistics.migration_critical_count) * 100
                              : (mappingProgress.critical_mapped / Object.keys(CRITICAL_ATTRIBUTES).length) * 100
                            }%` 
                          }}
                        />
                      </div>
                      <div className="text-sm text-blue-700">
                        {(criticalAttributesData ? criticalAttributesData.statistics.assessment_ready : mappingProgress.critical_mapped >= 3) ? (
                          <span className="flex items-center space-x-1">
                            <CheckCircle className="h-4 w-4" />
                            <span>✅ Ready for Assessment Phase</span>
                          </span>
                        ) : (
                          <span>
                            ⏳ {criticalAttributesData 
                              ? criticalAttributesData.recommendations.assessment_readiness 
                              : `Map ${3 - mappingProgress.critical_mapped} more critical field(s) to proceed`
                            }
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mapping Quality Insights */}
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Brain className="h-5 w-5 text-purple-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="font-medium text-purple-900 mb-2">AI Mapping Intelligence</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-purple-800">Average confidence:</span>
                        <span className="font-medium text-purple-900">
                          {criticalAttributesData 
                            ? Math.round(criticalAttributesData.statistics.avg_quality_score)
                            : fieldMappings.filter(m => m.status === 'approved').length > 0 
                              ? Math.round(
                                  fieldMappings
                                    .filter(m => m.status === 'approved')
                                    .reduce((sum, m) => sum + m.confidence, 0) / 
                                  fieldMappings.filter(m => m.status === 'approved').length * 100
                                )
                              : 0
                          }%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-purple-800">Mappings processed:</span>
                        <span className="font-medium text-purple-900">
                          {criticalAttributesData 
                            ? criticalAttributesData.statistics.mapped_count + criticalAttributesData.statistics.pending_count
                            : fieldMappings.filter(m => m.status !== 'pending').length
                          }
                        </span>
                      </div>
                      <div className="text-sm text-purple-700">
                        🧠 {criticalAttributesData?.last_updated 
                          ? `Last updated: ${new Date(criticalAttributesData.last_updated).toLocaleTimeString()}`
                          : 'AI learning from your mapping decisions in real-time'
                        }
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Priority Actions Panel */}
            {(criticalAttributesData ? !criticalAttributesData.statistics.assessment_ready : mappingProgress.critical_mapped < 3) && (
              <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ArrowRight className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium text-orange-900 mb-2">Next Steps to Complete Assessment Readiness</h4>
                    <div className="text-sm text-orange-800 space-y-1">
                      {criticalAttributesData ? (
                        <>
                          <div className="font-medium text-orange-900 mb-2">
                            {criticalAttributesData.recommendations.next_priority}
                          </div>
                          {criticalAttributesData.attributes
                            .filter(attr => attr.migration_critical && attr.status === 'unmapped')
                            .slice(0, 3)
                            .map(attr => (
                              <div key={attr.name}>
                                • {attr.required ? '🔴' : '🟡'} Map <strong>{CRITICAL_ATTRIBUTES[attr.name as keyof typeof CRITICAL_ATTRIBUTES]?.field || attr.name}</strong> field
                                {attr.ai_suggestion && <div className="ml-4 text-xs text-blue-700">💡 {attr.ai_suggestion}</div>}
                              </div>
                            ))
                          }
                          <div className="mt-2 pt-2 border-t border-orange-200">
                            <span className="font-medium">📊 Quality:</span> {criticalAttributesData.recommendations.quality_improvement}
                          </div>
                        </>
                      ) : (
                        <>
                          {!fieldMappings.find(m => m.targetAttribute === 'asset_name' && m.status === 'approved') && (
                            <div>• ✅ Map <strong>Asset Name</strong> field for asset identification</div>
                          )}
                          {!fieldMappings.find(m => m.targetAttribute === 'asset_type' && m.status === 'approved') && (
                            <div>• 🎯 Map <strong>Asset Type</strong> field for 6R strategy selection</div>
                          )}
                          {!fieldMappings.find(m => m.targetAttribute === 'environment' && m.status === 'approved') && (
                            <div>• 🌐 Map <strong>Environment</strong> field for wave planning</div>
                          )}
                          <div className="mt-2 pt-2 border-t border-orange-200">
                            <span className="font-medium">💡 Tip:</span> Review pending mappings in the Field Mappings tab to approve suggested matches
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
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
                {/* Header with Breadcrumbs */}
                <div className="mb-8">
                  <div className="mb-4">
                    <ContextBreadcrumbs showContextSelector={true} />
                  </div>
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
                <NavigationTabs activeTab={activeTab} onTabChange={handleTabChange} />

                {/* Tab Content */}
                {renderTabContent()}

                {/* Continue Button */}
                <div className="flex justify-center">
                  <button
                    onClick={handleContinueToDataCleansing}
                    disabled={!canContinueToDataCleansing()}
                    className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors ${
                      canContinueToDataCleansing()
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <span>Continue to Data Cleansing</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </div>
                
                {!canContinueToDataCleansing() && (
                  <div className="text-center text-sm text-gray-600 mt-2">
                    <p>Too many critical fields unmapped: {getMissingCriticalFields().slice(0, 5).map(field => CRITICAL_ATTRIBUTES[field as keyof typeof CRITICAL_ATTRIBUTES]?.field || field).join(', ')}{getMissingCriticalFields().length > 5 ? '...' : ''}</p>
                    <p className="text-xs mt-1">Please map more critical fields (maximum 5 can remain unmapped)</p>
                  </div>
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