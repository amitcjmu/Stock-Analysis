import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
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
    } finally {
      setIsAnalyzing(false);
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
          />
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