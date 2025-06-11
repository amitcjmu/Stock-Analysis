import React, { useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, CheckCircle, XCircle, Target, Brain, RefreshCw } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

// Components
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

// Hooks
import { useAuth } from '../../contexts/AuthContext';
import { 
  useCriticalAttributes, 
  useLatestImport, 
  useGenerateFieldMappings,
  useUpdateFieldMapping,
  useAnalyzeData,
  type FieldMapping,
  type CrewAnalysis,
  type CriticalAttributesData
} from '../../api/hooks/useAttributeMapping';

// UI Components
import { Button } from '../../components/ui/button';
import { useToast } from '../../components/ui/use-toast';

// Critical attributes definition (fallback for display)
const CRITICAL_ATTRIBUTES = {
  asset_name: { field: "Asset Name", category: "identity" },
  hostname: { field: "Hostname", category: "identity" },
  department: { field: "Department", category: "governance" },
  ip_address: { field: "IP Address", category: "network" },
  operating_system: { field: "Operating System", category: "technical" }
};

const AttributeMapping = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // State for UI controls
  const [activeTab, setActiveTab] = React.useState('data');
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = React.useState(0);

  // Data fetching with React Query
  const { 
    data: criticalAttributesData, 
    isLoading: isLoadingCriticalAttributes,
    isError: isErrorCriticalAttributes,
    refetch: refetchCriticalAttributes
  } = useCriticalAttributes();

  const { 
    data: importedData = [], 
    isLoading: isLoadingImportedData,
    isError: isErrorImportedData,
    refetch: refetchImportedData
  } = useLatestImport();

  // Mutations
  const { mutateAsync: generateMappings } = useGenerateFieldMappings();
  const { mutateAsync: updateMapping } = useUpdateFieldMapping();
  const { mutateAsync: analyzeData } = useAnalyzeData();

  // Handle tab change with auto-refresh for critical attributes tab
  const handleTabChange = useCallback(async (newTab: string) => {
    setActiveTab(newTab);
    
    if (newTab === 'critical') {
      await refetchCriticalAttributes();
    }
  }, [refetchCriticalAttributes]);

  // Handle refresh of critical attributes
  const handleRefreshCriticalAttributes = useCallback(async () => {
    try {
      await refetchCriticalAttributes();
      toast({
        title: 'Data refreshed',
        description: 'Critical attributes data has been updated.'
      });
    } catch (error) {
      console.error('Failed to refresh critical attributes:', error);
      toast({
        title: 'Error',
        description: 'Failed to refresh critical attributes. Please try again.',
        variant: 'destructive'
      });
    }
  }, [refetchCriticalAttributes, toast]);

  // Handle generation of field mappings
  const handleGenerateMappings = useCallback(async () => {
    if (importedData.length === 0) {
      toast({
        title: 'No data',
        description: 'Please import data before generating mappings.',
        variant: 'destructive'
      });
      return;
    }

    const columns = Object.keys(importedData[0] || {});
    if (columns.length === 0) return;

    try {
      await generateMappings({
        columns,
        sampleData: importedData.slice(0, 10)
      });
      
      toast({
        title: 'Success',
        description: 'Field mappings generated successfully.'
      });
    } catch (error) {
      console.error('Failed to generate mappings:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate field mappings. Please try again.',
        variant: 'destructive'
      });
    }
  }, [generateMappings, importedData, toast]);

  // Handle analysis of data with AI
  const handleAnalyzeData = useCallback(async () => {
    if (importedData.length === 0) {
      toast({
        title: 'No data',
        description: 'Please import data before analyzing.',
        variant: 'destructive'
      });
      return;
    }

    const columns = Object.keys(importedData[0] || {});
    if (columns.length === 0) return;

    try {
      setIsAnalyzing(true);
      await analyzeData({
        columns,
        sampleData: importedData.slice(0, 10)
      });
      
      toast({
        title: 'Analysis complete',
        description: 'Data has been analyzed successfully.'
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      toast({
        title: 'Analysis failed',
        description: 'Failed to analyze data. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [analyzeData, importedData, toast]);

  // Handle mapping update
  const handleUpdateMapping = useCallback(async (id: string, updates: Partial<FieldMapping>) => {
    try {
      await updateMapping({ id, updates });
      toast({
        title: 'Success',
        description: 'Mapping updated successfully.'
      });
    } catch (error) {
      console.error('Failed to update mapping:', error);
      toast({
        title: 'Error',
        description: 'Failed to update mapping. Please try again.',
        variant: 'destructive'
      });
    }
  }, [updateMapping, toast]);

  // Calculate derived state
  const isLoading = isLoadingCriticalAttributes || isLoadingImportedData;
  const hasError = isErrorCriticalAttributes || isErrorImportedData;

  // Memoize derived values
  const mappingProgress = useMemo(() => {
    if (!criticalAttributesData) {
      return {
        total: 0,
        mapped: 0,
        critical_mapped: 0,
        accuracy: 0
      };
    }
    
    const { statistics } = criticalAttributesData;
    return {
      total: statistics.total_attributes,
      mapped: statistics.mapped_count,
      critical_mapped: statistics.migration_critical_mapped,
      accuracy: statistics.avg_quality_score * 100 // Convert to percentage
    };
  }, [criticalAttributesData]);

  // Render loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-screen">
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-auto p-6">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-32 bg-muted/20 animate-pulse rounded-lg" />
              ))}
            </div>
          </main>
        </div>
      </div>
    );
  }

  // Render error state
  if (hasError) {
    return (
      <div className="flex flex-col h-screen">
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <div className="flex-1 overflow-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-2xl font-bold">Attribute Mapping</h1>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p>Failed to load attribute mapping data. Please try again later.</p>
              <Button 
                variant="outline" 
                className="mt-2" 
                onClick={() => {
                  refetchCriticalAttributes();
                  refetchImportedData();
                }}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main render
  return (
    <div className="flex flex-col h-screen">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Attribute Mapping</h1>
              <p className="text-sm text-muted-foreground">
                Map source fields to target attributes for migration
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                onClick={handleRefreshCriticalAttributes}
                disabled={isLoadingCriticalAttributes}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoadingCriticalAttributes ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button 
                onClick={handleGenerateMappings}
                disabled={isLoading || importedData.length === 0}
              >
                Generate Mappings
              </Button>
              <Button 
                variant="secondary"
                onClick={handleAnalyzeData}
                disabled={isLoading || isAnalyzing || importedData.length === 0}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze with AI'}
              </Button>
            </div>
          </div>

          {/* Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Progress Dashboard */}
          <div className="mb-6">
            <ProgressDashboard 
              progress={mappingProgress} 
              onRefresh={handleRefreshCriticalAttributes}
              isLoading={isLoadingCriticalAttributes}
            />
          </div>

          {/* Navigation Tabs */}
          <div className="mb-6">
            <NavigationTabs 
              activeTab={activeTab}
              onTabChange={handleTabChange}
            />
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'data' && (
              <RawDataTable 
                data={importedData} 
                onMappingUpdate={handleUpdateMapping}
              />
            )}
            
            {activeTab === 'mappings' && (
              <FieldMappingsTab 
                mappings={[]} // Will be populated from React Query
                onUpdateMapping={handleUpdateMapping}
                isLoading={isLoading}
              />
            )}
            
            {activeTab === 'analysis' && (
              <CrewAnalysisPanel 
                analysis={[]} // Will be populated from React Query
                isLoading={isAnalyzing}
              />
            )}
            
            {activeTab === 'critical' && criticalAttributesData && (
              <DataClassificationDisplay 
                attributes={criticalAttributesData.attributes}
                statistics={criticalAttributesData.statistics}
                recommendations={criticalAttributesData.recommendations}
                lastUpdated={criticalAttributesData.last_updated}
                onRefresh={handleRefreshCriticalAttributes}
                isLoading={isLoadingCriticalAttributes}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AttributeMapping;
