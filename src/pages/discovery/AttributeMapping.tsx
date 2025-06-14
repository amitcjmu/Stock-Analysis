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
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import FieldMappingsTab from '../../components/discovery/attribute-mapping/FieldMappingsTab';
import CriticalAttributesTab from '../../components/discovery/attribute-mapping/CriticalAttributesTab';

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
  
  return (
    <div className="space-y-6">
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
        <div className="grid grid-cols-12 gap-8">
          <div className="col-span-12 lg:col-span-8">
            <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />
            <div className="mt-4">
              {activeTab === 'field-mappings' && (
                <FieldMappingsTab
                  fieldMappings={fieldMappings}
                  isAnalyzing={isAnalyzing}
                  onMappingAction={() => {}} 
                />
              )}
              {activeTab === 'critical-attributes' && (
                <CriticalAttributesTab
                  criticalAttributes={(criticalAttributesData?.attributes || []).map(attr => ({...attr, mapping_type: attr.mapping_type as any, business_impact: attr.business_impact as any}))}
                  isAnalyzing={isAnalyzing}
                />
              )}
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4">
            <CrewAnalysisPanel 
              crewAnalysis={crewAnalysis}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AttributeMapping;
