import React, { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Upload, RefreshCw, Zap } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useAgenticCriticalAttributes, useTriggerFieldMappingCrew } from '../../hooks/useAttributeMapping';
import { apiCall, API_CONFIG } from '../../config/api';

import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import NoDataPlaceholder from '../../components/NoDataPlaceholder';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import CriticalAttributesTab from '../../components/discovery/attribute-mapping/CriticalAttributesTab';
import ImportedDataTab from '../../components/discovery/attribute-mapping/ImportedDataTab';
import TrainingProgressTab from '../../components/discovery/attribute-mapping/TrainingProgressTab';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import Sidebar from '../../components/Sidebar';

const AttributeMapping: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('mappings');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // 🤖 Use AGENTIC critical attributes (agent-driven intelligence)
  const { 
    data: criticalAttributesData, 
    isLoading, 
    isError: isErrorCriticalAttributes,
    refetch: refetchCriticalAttributes 
  } = useAgenticCriticalAttributes();

  // Hook to manually trigger Field Mapping Crew analysis
  const triggerFieldMappingCrew = useTriggerFieldMappingCrew();

  const handleRefreshCriticalAttributes = useCallback(() => {
    refetchCriticalAttributes();
  }, [refetchCriticalAttributes]);

  // 🤖 NEW: Trigger Field Mapping Crew Analysis
  const handleTriggerAgentAnalysis = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Field Mapping Crew Activated",
        description: "AI agents are analyzing your data to determine critical attributes...",
      });

      await triggerFieldMappingCrew.mutateAsync();

      toast({
        title: "✅ Agent Analysis Complete",
        description: "Field Mapping Crew has determined critical attributes based on your data patterns.",
      });
    } catch (error) {
      console.error('Failed to trigger agent analysis:', error);
      toast({
        title: "❌ Agent Analysis Failed",
        description: "Failed to trigger Field Mapping Crew analysis. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [triggerFieldMappingCrew, toast]);

  // Handle mapping approval/rejection
  const handleMappingAction = useCallback(async (mappingId: string, action: 'approve' | 'reject') => {
    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_type: 'field_mapping_action',
          mapping_id: mappingId,
          action: action,
          context: {
            page: 'attribute-mapping',
            user_id: user?.id
          }
        })
      });

      if (response.status === 'success') {
        toast({ 
          title: action === 'approve' ? 'Mapping approved' : 'Mapping rejected',
          description: 'AI will learn from this feedback'
        });
        // Refresh the data
        refetchCriticalAttributes();
      }
    } catch (error) {
      console.error('Error handling mapping action:', error);
      toast({ 
        title: 'Error', 
        description: 'Failed to process mapping action',
        variant: 'destructive'
      });
    }
  }, [user, toast, refetchCriticalAttributes]);

  // Handle mapping changes
  const handleMappingChange = useCallback(async (mappingId: string, newMapping: any) => {
    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_type: 'field_mapping_change',
          mapping_id: mappingId,
          new_mapping: newMapping,
          context: {
            page: 'attribute-mapping',
            user_id: user?.id
          }
        })
      });

      if (response.status === 'success') {
        toast({ 
          title: 'Mapping updated',
          description: 'Changes saved successfully'
        });
        // Refresh the data
        refetchCriticalAttributes();
      }
    } catch (error) {
      console.error('Error handling mapping change:', error);
      toast({ 
        title: 'Error', 
        description: 'Failed to save mapping changes',
        variant: 'destructive'
      });
    }
  }, [user, toast, refetchCriticalAttributes]);

  const mappingProgress = useMemo(() => {
    if (!criticalAttributesData || !criticalAttributesData.statistics) {
      return { total: 0, mapped: 0, critical_mapped: 0, accuracy: 0 };
    }
    const { statistics } = criticalAttributesData;
    return {
      total: statistics.total_attributes,
      mapped: statistics.mapped_count,
      critical_mapped: statistics.migration_critical_mapped,
      accuracy: statistics.avg_quality_score,
    };
  }, [criticalAttributesData]);

  // Mock field mappings data for now - this should come from a separate API call
  const fieldMappings = [
    {
      id: '1',
      sourceField: 'server_name',
      targetAttribute: 'hostname',
      confidence: 0.95,
      mapping_type: 'direct' as const,
      sample_values: ['server-01', 'server-02'],
      status: 'pending' as const,
      ai_reasoning: 'Direct mapping based on field name similarity'
    },
    {
      id: '2',
      sourceField: 'ip_addr',
      targetAttribute: 'ip_address',
      confidence: 0.90,
      mapping_type: 'direct' as const,
      sample_values: ['192.168.1.1', '192.168.1.2'],
      status: 'approved' as const,
      ai_reasoning: 'IP address format detected'
    }
  ];

  // Mock crew analysis data
  const crewAnalysis = [
    {
      agent: 'Field Mapping Agent',
      task: 'Analyze field mappings',
      findings: ['Found 18 potential field mappings', 'High confidence on technical fields'],
      recommendations: ['Review business fields manually', 'Approve technical mappings'],
      confidence: 0.85
    }
  ];

  // Transform critical attributes to match component interface
  const transformedCriticalAttributes = criticalAttributesData?.attributes?.map(attr => ({
    ...attr,
    mapping_type: (attr.mapping_type as 'direct' | 'calculated' | 'manual' | 'derived') || undefined,
    business_impact: attr.business_impact as 'high' | 'medium' | 'low'
  })) || [];

  // Render tab content based on active tab
  const renderTabContent = () => {
    switch (activeTab) {
      case 'data':
        return <ImportedDataTab />;
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
          <CriticalAttributesTab
            criticalAttributes={transformedCriticalAttributes}
            isAnalyzing={isAnalyzing}
            fieldMappings={fieldMappings}
          />
        );
      case 'progress':
        return <TrainingProgressTab />;
      default:
        return (
          <FieldMappingsTab
            fieldMappings={fieldMappings}
            isAnalyzing={isAnalyzing}
            onMappingAction={handleMappingAction}
            onMappingChange={handleMappingChange}
          />
        );
    }
  };

  if (isErrorCriticalAttributes) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6">
            <ContextBreadcrumbs />
            <div className="mt-6">
              <NoDataPlaceholder
                title="Error Loading Data"
                description="There was an error loading the attribute mapping data. Please try refreshing the page."
                actions={
                  <Button onClick={handleRefreshCriticalAttributes} className="bg-blue-600 hover:bg-blue-700 text-white">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                  </Button>
                }
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6">
            <ContextBreadcrumbs />
            <div className="mt-6">
              <div className="bg-white rounded-lg shadow-sm p-8">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
                  <div className="space-y-3">
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                    <div className="h-4 bg-gray-200 rounded w-4/6"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!criticalAttributesData || mappingProgress.total === 0) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6">
            <ContextBreadcrumbs />
            <div className="mt-6">
              <NoDataPlaceholder
                title="No Data Available"
                description="No critical attributes data found. Please upload and process your data first."
                actions={
                  <Button onClick={() => window.location.href = '/discovery/data-import'} className="bg-blue-600 hover:bg-blue-700 text-white">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Data
                  </Button>
                }
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto">
            <ContextBreadcrumbs />
            
            <div className="mt-6">
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Attribute Mapping</h1>
                <p className="text-gray-600 mt-1">
                  AI agents dynamically determine critical attributes based on your data patterns.
                </p>
                
                {/* Agent Status Indicator */}
                {criticalAttributesData?.agent_status && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Zap className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">
                          {criticalAttributesData.agent_status.discovery_flow_active ? 
                            '🤖 Field Mapping Crew Analyzing...' : 
                            '✅ Agent Analysis Complete'
                          }
                        </span>
                      </div>
                      
                      {!criticalAttributesData.agent_status.discovery_flow_active && 
                       criticalAttributesData.statistics.total_attributes === 0 && (
                        <Button 
                          onClick={handleTriggerAgentAnalysis}
                          disabled={isAnalyzing}
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          <Zap className="mr-2 h-4 w-4" />
                          {isAnalyzing ? 'Analyzing...' : 'Trigger Agent Analysis'}
                        </Button>
                      )}
                    </div>
                    
                    {criticalAttributesData.analysis_progress && (
                      <p className="text-xs text-blue-700 mt-1">
                        {criticalAttributesData.analysis_progress.current_task} 
                        {criticalAttributesData.analysis_progress.estimated_completion && 
                         ` (${criticalAttributesData.analysis_progress.estimated_completion})`}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Progress Dashboard */}
              <ProgressDashboard
                mappingProgress={{
                  total: mappingProgress.total,
                  mapped: mappingProgress.mapped,
                  critical_mapped: mappingProgress.critical_mapped,
                  accuracy: mappingProgress.accuracy
                }}
                isLoading={isAnalyzing || criticalAttributesData?.agent_status?.discovery_flow_active}
              />

              {/* Navigation Tabs */}
              <NavigationTabs
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />

              {/* Tab Content */}
              {renderTabContent()}

              {/* CrewAI Analysis */}
              <CrewAnalysisPanel
                crewAnalysis={crewAnalysis}
              />

              {/* Continue Button */}
              <div className="mt-8 flex justify-center">
                <Link to="/discovery/data-cleansing">
                  <Button size="lg" className="px-8">
                    Continue to Data Cleansing
                    <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Agent Panels */}
        <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-4">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">🤖 Agent Intelligence</h2>
              <p className="text-sm text-gray-600">AI agents analyze your data to determine critical attributes</p>
              
              {/* Agent Status Summary */}
              {criticalAttributesData?.agent_status && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Field Mapping Crew:</span>
                      <span className={`font-medium ${
                        criticalAttributesData.agent_status.field_mapping_crew_status === 'completed' ? 'text-green-600' :
                        criticalAttributesData.agent_status.field_mapping_crew_status === 'analyzing' ? 'text-blue-600' :
                        'text-gray-600'
                      }`}>
                        {criticalAttributesData.agent_status.field_mapping_crew_status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Learning System:</span>
                      <span className="font-medium text-green-600">
                        {criticalAttributesData.agent_status.learning_system_status}
                      </span>
                    </div>
                    {criticalAttributesData.agent_status.crew_agents_used && (
                      <div className="mt-2">
                        <span className="text-gray-600 text-xs">Active Agents:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {criticalAttributesData.agent_status.crew_agents_used.map((agent, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                              {agent}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Crew Insights */}
              {criticalAttributesData?.crew_insights && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg">
                  <h3 className="text-sm font-medium text-green-900 mb-2">Crew Analysis Insights</h3>
                  <div className="text-xs space-y-1">
                    <div><span className="text-green-700">Method:</span> {criticalAttributesData.crew_insights.analysis_method}</div>
                    <div><span className="text-green-700">Confidence:</span> {criticalAttributesData.crew_insights.confidence_level}</div>
                    <div><span className="text-green-700">Learning Applied:</span> {criticalAttributesData.crew_insights.learning_applied ? '✅ Yes' : '❌ No'}</div>
                  </div>
                  <p className="text-xs text-green-700 mt-2">{criticalAttributesData.crew_insights.crew_result_summary}</p>
                </div>
              )}
            </div>
            
            <AgentClarificationPanel pageContext="attribute-mapping" />
            <DataClassificationDisplay pageContext="attribute-mapping" />
            <AgentInsightsSection pageContext="attribute-mapping" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributeMapping;
