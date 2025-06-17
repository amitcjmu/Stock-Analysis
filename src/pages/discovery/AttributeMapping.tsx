import React, { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Upload, RefreshCw } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useCriticalAttributes } from '../../hooks/useAttributeMapping';
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
  const { toast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('mappings');

  const {
    data: criticalAttributesData,
    isLoading: isLoadingCriticalAttributes,
    isError: isErrorCriticalAttributes,
    refetch: refetchCriticalAttributes,
  } = useCriticalAttributes();
  
  const isLoading = isLoadingCriticalAttributes;
  const isAnalyzing = false; // Placeholder

  const handleRefreshCriticalAttributes = useCallback(() => {
    refetchCriticalAttributes();
    toast({ title: 'Refreshing data...' });
  }, [refetchCriticalAttributes, toast]);

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
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 p-6 overflow-y-auto">
          <ContextBreadcrumbs />
          
          <div className="mt-6">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">Attribute Mapping</h1>
              <p className="text-gray-600 mt-1">
                Map imported CMDB fields to the AI Force critical attributes for migration.
              </p>
            </div>

            {/* Progress Dashboard */}
            <ProgressDashboard
              mappingProgress={{
                total: mappingProgress.total,
                mapped: mappingProgress.mapped,
                critical_mapped: mappingProgress.critical_mapped,
                accuracy: mappingProgress.accuracy
              }}
              isLoading={isAnalyzing}
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

        {/* Right Sidebar - Agent Panels */}
        <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4 space-y-4">
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
