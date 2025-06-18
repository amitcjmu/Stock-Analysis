import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Upload, RefreshCw, Zap, Brain, Users, Activity, Database } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';

// CrewAI Discovery Flow Integration
import { useDiscoveryWebSocket } from '../../hooks/useDiscoveryWebSocket';
import { useDiscoveryFlowState } from '../../hooks/useDiscoveryFlowState';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import NoDataPlaceholder from '../../components/NoDataPlaceholder';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import CriticalAttributesTab from '../../components/discovery/attribute-mapping/CriticalAttributesTab';
import ImportedDataTab from '../../components/discovery/attribute-mapping/ImportedDataTab';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import Sidebar from '../../components/Sidebar';

// Types from Discovery Flow State
interface DiscoveryFlowState {
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  crew_status: Record<string, any>;
  field_mappings: {
    mappings: Record<string, any>;
    confidence_scores: Record<string, number>;
    unmapped_fields: string[];
    validation_results: Record<string, any>;
    agent_insights: Record<string, any>;
  };
  raw_data: any[];
  asset_inventory: Record<string, any>;
  agent_collaboration_map: Record<string, string[]>;
  shared_memory_id: string;
}

interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  agent_source?: string;
}

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
  crew: string;
  collaboration_insights?: string[];
}

interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

const AttributeMapping: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('mappings');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { toast } = useToast();
  const { user, client, engagement, session } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();

  // Discovery Flow State Integration
  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executeFieldMappingCrew,
    getCrewStatus
  } = useDiscoveryFlowState();

  // WebSocket for real-time crew monitoring
  const {
    flowStatus,
    crewUpdates,
    isConnected: isWebSocketConnected
  } = useDiscoveryWebSocket(flowState?.session_id);

  // Derived state from Discovery Flow
  const fieldMappings = useMemo(() => {
    if (!flowState?.field_mappings?.mappings) return [];
    
    return Object.entries(flowState.field_mappings.mappings).map(([sourceField, mapping]: [string, any]) => ({
      id: `mapping-${sourceField}`,
      sourceField,
      targetAttribute: mapping.target_attribute || 'unmapped',
      confidence: flowState.field_mappings.confidence_scores[sourceField] || 0,
      mapping_type: mapping.mapping_type || 'direct',
      sample_values: mapping.sample_values || [],
      status: mapping.status || 'pending',
      ai_reasoning: mapping.ai_reasoning || flowState.field_mappings.agent_insights[sourceField] || 'Agent analysis pending',
      agent_source: mapping.agent_source || 'Field Mapping Crew'
    }));
  }, [flowState]);

  // Crew Analysis from Discovery Flow State
  const crewAnalysis = useMemo(() => {
    if (!flowState?.crew_status?.field_mapping) return [];
    
    const fieldMappingCrewStatus = flowState.crew_status.field_mapping;
    const analyses: CrewAnalysis[] = [];
    
    // Field Mapping Manager Analysis
    if (fieldMappingCrewStatus.manager_analysis) {
      analyses.push({
        agent: "Field Mapping Manager",
        task: "Coordinate field mapping strategy and agent collaboration",
        findings: fieldMappingCrewStatus.manager_analysis.findings || ["Coordinating field mapping analysis"],
        recommendations: fieldMappingCrewStatus.manager_analysis.recommendations || ["Review agent results for validation"],
        confidence: fieldMappingCrewStatus.manager_analysis.confidence || 0.9,
        crew: "Field Mapping Crew",
        collaboration_insights: fieldMappingCrewStatus.manager_analysis.collaboration_insights
      });
    }
    
    // Schema Analysis Expert Analysis
    if (fieldMappingCrewStatus.schema_expert_analysis) {
      analyses.push({
        agent: "Schema Analysis Expert",
        task: "Analyze data structure semantics and field relationships",
        findings: fieldMappingCrewStatus.schema_expert_analysis.findings || ["Analyzing field semantics"],
        recommendations: fieldMappingCrewStatus.schema_expert_analysis.recommendations || ["Validate field relationships"],
        confidence: fieldMappingCrewStatus.schema_expert_analysis.confidence || 0.85,
        crew: "Field Mapping Crew"
      });
    }
    
    // Attribute Mapping Specialist Analysis
    if (fieldMappingCrewStatus.mapping_specialist_analysis) {
      analyses.push({
        agent: "Attribute Mapping Specialist", 
        task: "Create precise field mappings with confidence scoring",
        findings: fieldMappingCrewStatus.mapping_specialist_analysis.findings || ["Creating field mappings"],
        recommendations: fieldMappingCrewStatus.mapping_specialist_analysis.recommendations || ["Review mapping confidence scores"],
        confidence: fieldMappingCrewStatus.mapping_specialist_analysis.confidence || 0.8,
        crew: "Field Mapping Crew"
      });
    }
    
    return analyses;
  }, [flowState]);

  // Mapping Progress from Discovery Flow State
  const mappingProgress = useMemo(() => {
    if (!flowState || !fieldMappings.length) {
      return { 
        total: 0, 
        mapped: 0, 
        critical_mapped: 0, 
        accuracy: 0,
        crew_completion_status: {}
      };
    }
    
    const totalMappings = fieldMappings.length;
    const mappedCount = fieldMappings.filter(m => m.targetAttribute !== 'unmapped').length;
    const criticalMappings = fieldMappings.filter(m => 
      ['asset_name', 'asset_type', 'hostname', 'ip_address', 'operating_system', 'environment'].includes(m.targetAttribute.toLowerCase())
    ).length;
    const avgConfidence = fieldMappings.length > 0 
      ? fieldMappings.reduce((sum, m) => sum + m.confidence, 0) / fieldMappings.length 
      : 0;
    
    return {
      total: totalMappings,
      mapped: mappedCount,
      critical_mapped: criticalMappings,
      accuracy: Math.round(avgConfidence * 100),
      crew_completion_status: flowState.phase_completion || {}
    };
  }, [fieldMappings, flowState]);

  // Initialize Discovery Flow on component mount
  useEffect(() => {
    const initializeDiscoveryFlow = async () => {
      if (!client || !engagement) return;
      
      try {
        // Check if we have data from navigation state or need to load it
        const state = location.state as any;
        let rawData = [];
        
        if (state?.importedData && state.importedData.length > 0) {
          rawData = state.importedData;
        } else {
          // Load from latest import
          const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
          rawData = latestImportResponse?.data || [];
        }
        
        if (rawData.length === 0) {
          console.warn('No data available for Discovery Flow initialization');
          return;
        }
        
        // Initialize Discovery Flow with data
        await initializeFlow({
          client_account_id: client.id,
          engagement_id: engagement.id,
          user_id: user?.id || 'anonymous',
          raw_data: rawData,
          metadata: {
            source: 'attribute_mapping_page',
            filename: state?.filename || 'imported_data.csv'
          }
        });
        
        console.log('✅ Discovery Flow initialized for AttributeMapping');
        
      } catch (error) {
        console.error('❌ Failed to initialize Discovery Flow:', error);
        toast({
          title: "Flow Initialization Failed",
          description: "Unable to initialize Discovery Flow. Please try importing data first.",
          variant: "destructive"
        });
      }
    };
    
    initializeDiscoveryFlow();
  }, [client, engagement, user, location.state, initializeFlow, toast]);

  // Execute Field Mapping Crew Analysis
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    if (!flowState?.session_id) {
      toast({
        title: "Flow Not Ready",
        description: "Discovery Flow must be initialized first",
        variant: "destructive"
      });
      return;
    }
    
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Field Mapping Crew Activated",
        description: "Manager coordinating Schema Expert and Mapping Specialist...",
      });

      await executeFieldMappingCrew(flowState.session_id);

      toast({
        title: "✅ Field Mapping Crew Complete", 
        description: "Agents have completed field mapping analysis with shared insights.",
      });
    } catch (error) {
      console.error('Failed to execute Field Mapping Crew:', error);
      toast({
        title: "❌ Crew Execution Failed",
        description: "Field Mapping Crew encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [flowState, executeFieldMappingCrew, toast]);

  // Handle mapping actions with agent learning
  const handleMappingAction = useCallback(async (mappingId: string, action: 'approve' | 'reject') => {
    if (!flowState?.session_id) return;
    
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send learning feedback to Discovery Flow
      await apiCall(`/api/v1/discovery/flow/${flowState.session_id}/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'field_mapping_feedback',
          crew: 'field_mapping',
          agent: 'Attribute Mapping Specialist',
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
            reasoning: mapping.ai_reasoning,
            shared_memory_id: flowState.shared_memory_id
          }
        })
      });

      toast({
        title: action === 'approve' ? 'Mapping Approved' : 'Mapping Rejected',
        description: 'Shared memory updated for crew learning'
      });
      
      // Refresh flow state
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
    } catch (error) {
      console.error('Error handling mapping action:', error);
      toast({
        title: 'Error',
        description: 'Failed to process mapping action',
        variant: 'destructive'
      });
    }
  }, [flowState, fieldMappings, toast, queryClient]);

  // Handle mapping changes
  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    if (!flowState?.session_id) return;
    
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      // Send correction to Discovery Flow for shared memory update
      await apiCall(`/api/v1/discovery/flow/${flowState.session_id}/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'field_mapping_correction',
          crew: 'field_mapping',
          agent: 'Attribute Mapping Specialist',
          original_prediction: {
            source_field: mapping.sourceField,
            target_attribute: mapping.targetAttribute,
            confidence: mapping.confidence
          },
          user_correction: {
            new_target_attribute: newTarget,
            feedback_type: 'manual_change',
            reason: 'User selected different target field'
          },
          context: {
            sample_values: mapping.sample_values,
            shared_memory_id: flowState.shared_memory_id
          }
        })
      });

      toast({
        title: 'Mapping Updated',
        description: 'Field mapping updated in shared crew memory'
      });
      
      // Refresh flow state
      queryClient.invalidateQueries({ queryKey: ['discovery-flow-state'] });
      
    } catch (error) {
      console.error('Error handling mapping change:', error);
      toast({
        title: 'Error',
        description: 'Failed to update mapping',
        variant: 'destructive'
      });
    }
  }, [flowState, fieldMappings, toast, queryClient]);

  // Navigate to next phase
  const handleContinueToDataCleansing = useCallback(() => {
    if (!flowState?.session_id) return;
    
    navigate('/discovery/data-cleansing', {
      state: {
        flow_session_id: flowState.session_id,
        flow_state: flowState,
        from_phase: 'field_mapping'
      }
    });
  }, [flowState, navigate]);

  // Check if can continue to next phase
  const canContinueToDataCleansing = () => {
    return flowState?.phase_completion?.field_mapping || 
           (mappingProgress.mapped > 0 && mappingProgress.critical_mapped >= 3);
  };

  const renderTabContent = () => {
    const commonProps = {
      fieldMappings,
      onMappingAction: handleMappingAction,
      onMappingChange: handleMappingChange,
      isLoading: isFlowStateLoading || isAnalyzing,
      flowState,
      crewAnalysis
    };

    switch (activeTab) {
      case 'mappings':
        return (
          <FieldMappingsTab 
            {...commonProps}
            availableTargetFields={flowState?.field_mappings?.validation_results?.available_targets || []}
            sharedMemoryInsights={flowState?.field_mappings?.agent_insights || {}}
          />
        );
      case 'critical':
        return (
          <CriticalAttributesTab 
            {...commonProps}
            criticalAttributes={flowState?.field_mappings?.validation_results?.critical_attributes || []}
            agentRecommendations={crewAnalysis.flatMap(a => a.recommendations)}
          />
        );
      case 'data':
        return (
          <ImportedDataTab 
            data={flowState?.raw_data || []}
            isLoading={isFlowStateLoading}
            dataQualityMetrics={flowState?.crew_status?.field_mapping?.data_quality_analysis}
          />
        );
      default:
        return null;
    }
  };

  // Show loading state while initializing
  if (isFlowStateLoading && !flowState) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-blue-600 animate-pulse mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Initializing Discovery Flow</h2>
            <p className="text-gray-600">Setting up Field Mapping Crew and shared memory...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (flowStateError) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="Discovery Flow Error"
            description={`Failed to initialize Discovery Flow: ${flowStateError.message}`}
            icon={Brain}
            actions={[
              {
                label: "Return to Data Import",
                onClick: () => navigate('/discovery/cmdb-import'),
                variant: "default"
              }
            ]}
          />
        </div>
      </div>
    );
  }

  // Show no data state
  if (!flowState?.raw_data?.length) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="No Data Available"
            description="No data available for field mapping analysis. Please import data first."
            icon={Upload}
            actions={[
              {
                label: "Import Data",
                onClick: () => navigate('/discovery/cmdb-import'),
                variant: "default"
              }
            ]}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Database className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Attribute Mapping</h1>
                <p className="text-gray-600">CrewAI Field Mapping Crew Analysis</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* WebSocket Status */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                isWebSocketConnected ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                <Activity className="h-4 w-4" />
                <span>{isWebSocketConnected ? 'Live Monitoring' : 'Connecting...'}</span>
              </div>
              
              {/* Crew Analysis Button */}
              <Button
                onClick={handleTriggerFieldMappingCrew}
                disabled={isAnalyzing || !flowState?.session_id}
                className="flex items-center space-x-2"
              >
                {isAnalyzing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                <span>{isAnalyzing ? 'Crew Active' : 'Trigger Field Mapping Crew'}</span>
              </Button>
            </div>
          </div>

          {/* Progress Dashboard */}
          <div className="mb-6">
            <ProgressDashboard 
              mappingProgress={mappingProgress} 
              isLoading={isAnalyzing}
              crewStatus={flowState?.crew_status?.field_mapping}
              phaseCompletion={flowState?.phase_completion}
            />
          </div>

          {/* Enhanced Agent Orchestration Panel */}
          {flowState?.session_id && (
            <div className="mb-6">
              <EnhancedAgentOrchestrationPanel
                sessionId={flowState.session_id}
                flowState={flowState}
                currentPhase="field_mapping"
                showOnlyCurrentPhase={true}
              />
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Main Content */}
            <div className="xl:col-span-3">
              {/* Navigation Tabs */}
              <div className="mb-6">
                <NavigationTabs 
                  activeTab={activeTab} 
                  onTabChange={setActiveTab}
                  fieldMappingsCount={fieldMappings.length}
                  criticalAttributesCount={mappingProgress.critical_mapped}
                  importedDataCount={flowState?.raw_data?.length || 0}
                />
              </div>

              {/* Tab Content */}
              <div className="bg-white rounded-lg shadow-md">
                {renderTabContent()}
              </div>

              {/* Continue Button */}
              {canContinueToDataCleansing() && (
                <div className="mt-6 flex justify-end">
                  <Button
                    onClick={handleContinueToDataCleansing}
                    className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                  >
                    <span>Continue to Data Cleansing</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            {/* Right Sidebar */}
            <div className="xl:col-span-1 space-y-6">
              {/* Crew Analysis Panel */}
              {crewAnalysis.length > 0 && (
                <CrewAnalysisPanel 
                  analysis={crewAnalysis}
                  isLoading={isAnalyzing}
                  sharedMemoryInsights={flowState?.field_mappings?.agent_insights}
                />
              )}

              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                sessionId={flowState?.session_id || ''}
                context="attribute-mapping"
                crewContext="field_mapping"
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                sessionId={flowState?.session_id || ''}
                context="attribute-mapping"
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                sessionId={flowState?.session_id || ''}
                context="attribute-mapping"
                agentCollaborationMap={flowState?.agent_collaboration_map?.field_mapping || []}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributeMapping;
