import React, { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Upload } from 'lucide-react';

import { useToast } from '../../hooks/use-toast';
import { useCriticalAttributes, FieldMapping, CrewAnalysis, CriticalAttributeStatus } from '../../hooks/useAttributeMapping';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import NoDataPlaceholder from '../../components/NoDataPlaceholder';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import CriticalAttributesTab from '../../components/discovery/attribute-mapping/CriticalAttributesTab';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import Sidebar from '../../components/Sidebar';
import { ArrowRight, Brain } from 'lucide-react';
const CRITICAL_ATTRIBUTES = {
  hostname: { field: 'Hostname' },
  os: { field: 'Operating System' },
  ip_address: { field: 'IP Address' },
  environment: { field: 'Environment' },
  owner: { field: 'Owner' },
  department: { field: 'Department' },
  business_criticality: { field: 'Business Criticality' },
  six_r_strategy: { field: '6R Strategy' },
  migration_wave: { field: 'Migration Wave' }
};

const AttributeMapping: React.FC = () => {
  const { toast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('field-mappings');

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

  const crewAnalysis = useMemo((): CrewAnalysis[] => {
    if (!criticalAttributesData?.recommendations) return [];
    
    return [
      {
        agent: 'Migration Strategist',
        task: 'Initial Data Assessment',
        findings: [
          `Assessment readiness: ${criticalAttributesData.recommendations.assessment_readiness}`,
          `Quality improvement suggestion: ${criticalAttributesData.recommendations.quality_improvement}`
        ],
        recommendations: [
          `Next priority: ${criticalAttributesData.recommendations.next_priority}`
        ],
        confidence: 0.95
      }
    ];
  }, [criticalAttributesData]);

  const fieldMappings = useMemo((): FieldMapping[] => {
    if (!criticalAttributesData?.attributes) return [];
    return (criticalAttributesData.attributes).map((attr: CriticalAttributeStatus) => ({
      id: attr.name,
      sourceField: attr.source_field || 'N/A',
      targetAttribute: attr.name,
      confidence: attr.confidence || 0,
      mapping_type: (attr.mapping_type as any) || 'manual',
      sample_values: [],
      status: 'pending',
      ai_reasoning: attr.ai_suggestion || '',
    }));
  }, [criticalAttributesData]);

  const noData = !isLoading && (!criticalAttributesData || !criticalAttributesData.attributes || criticalAttributesData.attributes.length === 0);

  if (isErrorCriticalAttributes) {
    return <div className="p-4 text-red-600 bg-red-50 rounded-md">Error loading attribute mapping data. Please try again.</div>;
  }

  // Tab content renderer
  function renderTabContent() {
    if (activeTab === 'field-mappings') {
      return (
        <FieldMappingsTab
          fieldMappings={fieldMappings}
          isAnalyzing={isAnalyzing}
          onMappingAction={() => {}}
        />
      );
    }
    if (activeTab === 'critical-attributes') {
      return (
        <CriticalAttributesTab
          criticalAttributes={(criticalAttributesData?.attributes || []).map(attr => ({
            ...attr,
            mapping_type: attr.mapping_type as any,
            business_impact: attr.business_impact as any
          }))}
          isAnalyzing={isAnalyzing}
        />
      );
    }
    return null;
  }
  
  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      {/* Main Content */}
      <main className="flex-1 px-8 py-8">
        <ContextBreadcrumbs />
        <div>
          <h1 className="text-2xl font-bold">Attribute Mapping</h1>
          <p className="text-sm text-gray-500">
            Map imported CMDB fields to the AI Force critical attributes for migration.
          </p>
        </div>
        <ProgressDashboard mappingProgress={mappingProgress} isLoading={isLoading} />
        {noData ? (
          <NoDataPlaceholder
            title="No attributes to map"
            description="It looks like you haven't imported any data for this engagement yet. Please import your CMDB data to begin mapping attributes."
            actions={
              <Link to="/discovery/import">
                <Button>
                  <Upload className="mr-2 h-4 w-4" />
                  Go to Data Import
                </Button>
              </Link>
            }
          />
        ) : (
          <>
            <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />
            <div className="mt-4">
              {renderTabContent()}
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
            {/* Continue Button */}
            <div className="flex justify-center mt-8">
              <button
                // onClick={handleContinueToDataCleansing} // TODO: implement navigation
                disabled={false /* TODO: implement canContinueToDataCleansing() logic */}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700`}
              >
                <span>Continue to Data Cleansing</span>
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
            {/* TODO: Add missing critical fields warning if needed */}
            <CrewAnalysisPanel crewAnalysis={crewAnalysis} />
          </>
        )}
      </main>
      {/* Agentic Panels Sidebar */}
      <aside className="hidden xl:flex flex-col w-96 border-l bg-white px-6 py-8 space-y-6">
        <AgentClarificationPanel pageContext="attribute-mapping" />
        <DataClassificationDisplay pageContext="attribute-mapping" />
        <AgentInsightsSection pageContext="attribute-mapping" />
      </aside>
    </div>
  );
};

export default AttributeMapping;
