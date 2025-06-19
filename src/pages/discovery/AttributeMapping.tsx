import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Upload, RefreshCw, Zap, Brain, Users, Activity, Database, ArrowRight } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';

// CrewAI Discovery Flow Integration
// Removed WebSocket dependency - using HTTP polling instead
import { useDiscoveryFlowState } from '../../hooks/useDiscoveryFlowState';
import { useAgenticCriticalAttributes } from '../../hooks/useAttributeMapping';

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
  const [activeTab, setActiveTab] = useState<'mappings' | 'data' | 'critical'>('critical');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { toast } = useToast();
  const { user, client, engagement, session } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();

  // Use the agentic critical attributes as the primary data source
  const { 
    data: agenticData, 
    isLoading: isAgenticLoading, 
    error: agenticError,
    refetch: refetchAgentic
  } = useAgenticCriticalAttributes();

  // Discovery Flow State Integration (secondary, for compatibility)
  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executePhase
  } = useDiscoveryFlowState();

  // Real-time monitoring via HTTP polling (no WebSocket needed)
  const isPollingActive = !!flowState && flowState.overall_status === 'in_progress';

  // Convert agentic critical attributes to field mappings format
  const fieldMappings = useMemo(() => {
    if (!agenticData?.attributes) return [];
    
    return agenticData.attributes.map((attr, index) => ({
      id: `mapping-${attr.name}-${index}`,
      sourceField: attr.source_field || attr.mapped_to || attr.name,
      targetAttribute: attr.name,
      confidence: attr.confidence || 0.5,
      mapping_type: (attr.mapping_type as 'direct' | 'calculated' | 'manual') || 'direct',
      sample_values: [attr.source_field || attr.mapped_to || attr.name].filter(Boolean),
      status: 'pending' as 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted',
      ai_reasoning: attr.ai_suggestion || `${attr.description || 'Field analysis'} (${attr.business_impact || 'medium'} business impact)`,
      agent_source: 'Agentic Analysis'
    }));
  }, [agenticData]);

  // Create crew analysis from agentic data
  const crewAnalysis = useMemo(() => {
    if (!agenticData?.agent_status) return [];
    
    const analyses: CrewAnalysis[] = [];
    
    if (agenticData.agent_status.crew_agents_used) {
      agenticData.agent_status.crew_agents_used.forEach((agent, index) => {
        analyses.push({
          agent: agent,
          task: "Field mapping and critical attribute analysis",
          findings: [`Analyzed ${agenticData.statistics.total_attributes} attributes`, `Identified ${agenticData.statistics.migration_critical_count} migration-critical fields`],
          recommendations: [agenticData.recommendations.next_priority],
          confidence: agenticData.statistics.avg_quality_score / 100,
          crew: "Field Mapping Crew"
        });
      });
    }
    
    return analyses;
  }, [agenticData]);

  // Calculate mapping progress from agentic data
  const mappingProgress = useMemo(() => {
    if (!agenticData?.statistics) {
      return { 
        total: 0, 
        mapped: 0, 
        critical_mapped: 0, 
        accuracy: 0,
        crew_completion_status: {}
      };
    }
    
    return {
      total: agenticData.statistics.total_attributes,
      mapped: agenticData.statistics.mapped_count,
      critical_mapped: agenticData.statistics.migration_critical_mapped,
      accuracy: agenticData.statistics.avg_quality_score,
      crew_completion_status: {
        field_mapping: agenticData.statistics.assessment_ready
      }
    };
  }, [agenticData]);

  // Convert agentic critical attributes to the format expected by CriticalAttributesTab
  const criticalAttributes = useMemo(() => {
    if (!agenticData?.attributes) return [];
    
    return agenticData.attributes.map(attr => ({
      name: attr.name,
      description: attr.description,
      category: attr.category,
      required: attr.migration_critical || false,
      status: (attr.status === 'mapped' ? 'mapped' : 'unmapped') as 'mapped' | 'unmapped' | 'partially_mapped',
      mapped_to: attr.mapped_to,
      source_field: attr.source_field,
      confidence: attr.confidence,
      quality_score: attr.quality_score,
      completeness_percentage: attr.completeness_percentage,
      mapping_type: (attr.mapping_type as 'direct' | 'calculated' | 'manual' | 'derived') || 'direct',
      ai_suggestion: attr.ai_suggestion,
      business_impact: (attr.business_impact as 'high' | 'medium' | 'low') || 'medium',
      migration_critical: attr.migration_critical || false
    }));
  }, [agenticData]);

  // Initialize Discovery Flow on component mount (if needed) - DISABLED to prevent constant requests
  useEffect(() => {
    const checkDataAvailability = async () => {
      if (!client || !engagement) return;
      
      // Only log status, don't automatically initialize flow
      if (agenticData?.attributes?.length > 0) {
        console.log('✅ Using agentic data, Discovery Flow initialization not needed');
        return;
      }
      
      console.log('ℹ️ No agentic data available. User can manually trigger analysis if needed.');
      
      // Check if data is available but don't automatically trigger flow
      try {
        const state = location.state as any;
        let rawData = [];
        
        if (state?.importedData && state.importedData.length > 0) {
          rawData = state.importedData;
          console.log(`ℹ️ Data available from navigation state: ${rawData.length} records`);
        } else {
          // Just check latest import without triggering flow
          try {
            const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
            rawData = latestImportResponse?.data || [];
            if (rawData.length > 0) {
              console.log(`ℹ️ Data available from latest import: ${rawData.length} records`);
            }
          } catch (error) {
            console.warn('Could not check latest import:', error);
          }
        }
        
        if (rawData.length === 0) {
          console.log('ℹ️ No data available for Discovery Flow. Import data first.');
        }
        
      } catch (error) {
        console.error('❌ Failed to check data availability:', error);
      }
    };
    
    // Only check data availability, don't auto-initialize
    checkDataAvailability();
  }, [client, engagement, agenticData]); // Removed dependencies that triggered re-runs

  // Manual trigger for field mapping analysis
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Triggering Field Mapping Analysis",
        description: "Starting field mapping analysis with latest data...",
      });

      // Check if we need to initialize Discovery Flow first
      if (!flowState?.session_id && !agenticData?.attributes?.length) {
        toast({
          title: "🚀 Initializing Discovery Flow",
          description: "Setting up Discovery Flow for field mapping analysis...",
        });

        // Get data from navigation state or latest import
        const state = location.state as any;
        let rawData = [];
        
        if (state?.importedData && state.importedData.length > 0) {
          rawData = state.importedData;
        } else {
          try {
            const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
            rawData = latestImportResponse?.data || [];
          } catch (error) {
            console.warn('Could not load latest import:', error);
          }
        }
        
        if (rawData.length === 0) {
          toast({
            title: "❌ No Data Available",
            description: "Please import CMDB data first before running field mapping analysis.",
            variant: "destructive"
          });
          return;
        }

        // Initialize Discovery Flow with data
        await initializeFlow.mutateAsync({
          client_account_id: client!.id,
          engagement_id: engagement!.id,
          user_id: user?.id || 'anonymous',
          raw_data: rawData,
          metadata: {
            source: 'attribute_mapping_manual_trigger',
            filename: state?.filename || 'imported_data.csv'
          }
        });
        
        console.log('✅ Discovery Flow initialized for manual field mapping analysis');
      }

      // Refetch agentic data to trigger new analysis
      await refetchAgentic();

      toast({
        title: "✅ Analysis Complete", 
        description: "Field mapping analysis has been completed.",
      });
    } catch (error) {
      console.error('Failed to trigger field mapping analysis:', error);
      toast({
        title: "❌ Analysis Failed",
        description: "Field mapping analysis encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [refetchAgentic, toast, flowState, agenticData, initializeFlow, client, engagement, user, location.state]);

  // Manual refresh function for data updates
  const handleManualRefresh = useCallback(async () => {
    try {
      toast({
        title: "🔄 Refreshing Data",
        description: "Fetching latest field mapping data...",
      });

      // Refetch agentic data
      await refetchAgentic();

      toast({
        title: "✅ Data Refreshed", 
        description: "Latest field mapping data has been loaded.",
      });
    } catch (error) {
      console.error('Failed to refresh data:', error);
      toast({
        title: "❌ Refresh Failed",
        description: "Failed to refresh data. Please try again.",
        variant: "destructive"
      });
    }
  }, [refetchAgentic, toast]);

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
    switch (activeTab) {
      case 'mappings':
        return (
          <FieldMappingsTab 
            fieldMappings={fieldMappings}
            isAnalyzing={isAnalyzing}
            onMappingAction={handleMappingAction}
            onMappingChange={handleMappingChange}
          />
        );
      case 'data':
        return (
          <ImportedDataTab />
        );
      case 'critical':
        return (
          <CriticalAttributesTab 
            criticalAttributes={criticalAttributes}
            isAnalyzing={isAnalyzing}
            fieldMappings={fieldMappings}
          />
        );
      default:
        return (
          <div className="p-8 text-center">
            <p className="text-gray-500">Tab content not available</p>
          </div>
        );
    }
  };

  // Show loading state while initializing
  if ((isFlowStateLoading && !flowState) || isAgenticLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-blue-600 animate-pulse mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {isAgenticLoading ? 'Loading Attribute Data' : 'Initializing Discovery Flow'}
            </h2>
            <p className="text-gray-600">
              {isAgenticLoading ? 'Fetching field mapping analysis...' : 'Setting up Field Mapping Crew and shared memory...'}
            </p>
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
            actions={
              <Button 
                onClick={() => navigate('/discovery/cmdb-import')}
                className="flex items-center space-x-2"
              >
                <Database className="h-4 w-4" />
                <span>Return to Data Import</span>
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  // Show no data state
  if (!agenticData?.attributes?.length && !isAgenticLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="No Data Available"
            description="No data available for field mapping analysis. Please import data first."
            actions={
              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  onClick={() => navigate('/discovery/import')}
                  className="flex items-center space-x-2"
                >
                  <Upload className="h-4 w-4" />
                  <span>Import Data</span>
                </Button>
                <Button 
                  onClick={handleTriggerFieldMappingCrew}
                  disabled={isAnalyzing}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  {isAnalyzing ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                  <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Analysis'}</span>
                </Button>
              </div>
            }
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
                <h1 className="text-3xl font-bold text-gray-900">Attribute Mapping & AI Training</h1>
                <p className="text-gray-600">
                  {agenticData?.attributes?.length > 0 
                    ? `${agenticData.statistics.total_attributes} analysis attributes identified from ${flowState?.raw_data?.length || 1} imported record(s) with ${agenticData.statistics.migration_critical_count} migration-critical fields` 
                    : 'Train the AI crew to understand your data\'s attribute associations and field mappings'
                  }
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Data Status with more detail */}
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${
                agenticData?.attributes?.length > 0 ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-600 border border-gray-200'
              }`}>
                <Activity className="h-4 w-4" />
                <span>
                  {agenticData?.attributes?.length > 0 
                    ? `${agenticData.attributes.length} Attributes (${agenticData.statistics.migration_critical_count} Critical)` 
                    : 'No Data Available'
                  }
                </span>
              </div>
              
              {/* Analysis Quality Score */}
              {agenticData?.statistics?.avg_quality_score && (
                <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                  <span className="font-medium">{agenticData.statistics.avg_quality_score}% Quality</span>
                </div>
              )}
              
              {/* Manual Refresh Button */}
              <Button
                onClick={handleManualRefresh}
                disabled={isAgenticLoading}
                variant="outline"
                className="flex items-center space-x-2"
              >
                {isAgenticLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                <span>Refresh Data</span>
              </Button>
              
              {/* Crew Analysis Button */}
              <Button
                onClick={handleTriggerFieldMappingCrew}
                disabled={isAnalyzing}
                className="flex items-center space-x-2"
              >
                {isAnalyzing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Analysis'}</span>
              </Button>
            </div>
          </div>

          {/* Progress Dashboard */}
          <div className="mb-6">
            <ProgressDashboard 
              mappingProgress={mappingProgress} 
              isLoading={isAnalyzing}
            />
          </div>

          {/* Enhanced Agent Orchestration Panel */}
          {flowState?.session_id && (
            <div className="mb-6">
              <EnhancedAgentOrchestrationPanel
                sessionId={flowState.session_id}
                flowState={flowState}
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
                  onTabChange={(tabId: string) => setActiveTab(tabId as 'mappings' | 'data' | 'critical')}
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

            {/* Right Sidebar - Agent UI Bridge */}
            <div className="xl:col-span-1 space-y-6">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="attribute-mapping"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Attribute mapping question answered:', questionId, response);
                  // Trigger field mapping re-analysis based on agent learning
                  refetchAgentic();
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="attribute-mapping"
                refreshTrigger={0}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Field mapping classification updated:', itemId, newClassification);
                  // Update local field mapping data quality classification
                  refetchAgentic();
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="attribute-mapping"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Field mapping insight action:', insightId, action);
                  // Apply agent insights for field mapping optimization
                  if (action === 'apply_insight') {
                    console.log('Applying agent field mapping insights');
                    refetchAgentic();
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
