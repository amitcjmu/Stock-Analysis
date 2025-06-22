import React, { useMemo } from 'react';
import { 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Activity,
  TrendingUp,
  BarChart3,
  Users,
  Server,
  Database,
  Layers,
  MapPin,
  Target,
  ArrowRight,
  Filter,
  Search,
  FileText,
  Settings,
  Lightbulb
} from 'lucide-react';

// Hooks
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { useAuth } from '../../contexts/AuthContext';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { Button } from '../../components/ui/button';
import { useToast } from '../../components/ui/use-toast';

// Sub-components
import MetricCard from './components/asset-inventory/MetricCard';
import ProgressBar from './components/asset-inventory/ProgressBar';
import WorkflowProgress from './components/asset-inventory/WorkflowProgress';
import DataQualityPanel from './components/asset-inventory/DataQualityPanel';
import MigrationReadiness from './components/asset-inventory/MigrationReadiness';
import RecommendationsList from './components/asset-inventory/RecommendationsList';
import AssetDistribution from './components/asset-inventory/AssetDistribution';

// Types
type StatusType = 'completed' | 'ready' | 'in_progress' | 'partial' | 'pending' | 'not_ready' | 'failed';
type PriorityType = 'high' | 'medium' | 'low';

const AssetInventoryRedesigned: React.FC = () => {
  const { toast } = useToast();
  const { user } = useAuth();
  
  // Unified discovery flow hook
  const {
    flowState,
    isLoading,
    error,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    executeFlowPhase,
    isExecutingPhase,
    refreshFlow
  } = useUnifiedDiscoveryFlow();

  // Get asset inventory specific data
  const inventoryData = getPhaseData('asset_inventory');
  const isAssetInventoryComplete = isPhaseComplete('asset_inventory');
  const canProceedToDependencies = canProceedToPhase('dependency_analysis');

  // Handle asset inventory execution
  const handleExecuteAssetInventory = async () => {
    try {
      await executeFlowPhase('asset_inventory');
      toast({
        title: 'Success',
        description: 'Asset inventory analysis started.',
      });
    } catch (err) {
      console.error('Failed to execute asset inventory phase:', err);
      toast({
        title: 'Error',
        description: 'Failed to start asset inventory analysis. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Handle refresh with error handling
  const handleRefresh = async () => {
    try {
      await refreshFlow();
      toast({
        title: 'Success',
        description: 'Asset inventory data has been refreshed.',
      });
    } catch (err) {
      console.error('Failed to refresh inventory:', err);
      toast({
        title: 'Error',
        description: 'Failed to refresh inventory data. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Derived state
  const lastUpdated = useMemo(() => {
    const timestamp = (inventoryData && !Array.isArray(inventoryData)) ? inventoryData.analysis_timestamp : null;
    return timestamp 
      ? new Date(timestamp).toLocaleString() 
      : 'Never';
  }, [inventoryData]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !inventoryData) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">
                  Failed to load asset inventory data. {error?.message || 'Please try again later.'}
                </p>
                <div className="mt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRefresh}
                    className="mt-2"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Destructure data for easier access (with safe access)
  const safeInventoryData = (inventoryData && !Array.isArray(inventoryData)) ? inventoryData : {};
  const {
    asset_metrics = { total_count: 0, by_type: {} },
    workflow_analysis = {},
    data_quality = { overall_score: 0 },
    migration_readiness = {},
    dependency_analysis = {},
    recommendations = [],
    assessment_ready = false
  } = safeInventoryData;

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <div className="mb-4 md:mb-0">
              <h1 className="text-2xl font-bold text-gray-900">Asset Inventory</h1>
              <p className="text-sm text-gray-500 mt-1">
                Last updated: {lastUpdated}
              </p>
            </div>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="default" size="sm">
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total Assets"
              value={asset_metrics.total_count.toLocaleString()}
              icon={<Server className="h-6 w-6" />}
              color="text-blue-600"
              subtitle={`${asset_metrics.by_type.server || 0} servers, ${asset_metrics.by_type.application || 0} apps`}
            />
            <MetricCard
              title="Data Quality Score"
              value={`${Math.round(data_quality.overall_score * 100)}%`}
              icon={<BarChart3 className="h-6 w-6" />}
              color={data_quality.overall_score > 0.8 ? 'text-green-600' : data_quality.overall_score > 0.5 ? 'text-yellow-600' : 'text-red-600'}
              subtitle={`${data_quality.missing_critical_data.length} assets with critical issues`}
            />
            <MetricCard
              title="Migration Ready"
              value={`${migration_readiness.ready_for_assessment} Assets`}
              icon={<CheckCircle className="h-6 w-6" />}
              color="text-green-600"
              subtitle={`${Math.round((migration_readiness.ready_for_assessment / asset_metrics.total_count) * 100)}% of total`}
            />
            <MetricCard
              title="Dependencies"
              value={dependency_analysis.total_dependencies.toLocaleString()}
              icon={<Layers className="h-6 w-6" />}
              color="text-purple-600"
              subtitle={`${dependency_analysis.complex_dependency_chains.length} complex chains`}
            />
          </div>

          {/* Workflow Progress */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-gray-900">Migration Workflow Progress</h2>
              <Button variant="ghost" size="sm" className="text-blue-600 hover:bg-blue-50">
                View Details <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <WorkflowProgress workflowAnalysis={workflow_analysis} />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Asset Distribution */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Distribution</h3>
                <AssetDistribution metrics={asset_metrics} />
              </div>

              {/* Data Quality */}
              <DataQualityPanel dataQuality={data_quality} />
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Migration Readiness */}
              <MigrationReadiness 
                readiness={migration_readiness} 
                totalAssets={asset_metrics.total_count} 
              />

              {/* Top Recommendations */}
              <RecommendationsList recommendations={recommendations} />
            </div>
          </div>

          {/* Assessment Readiness */}
          {assessment_ready && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">Assessment Readiness</h2>
                <div className="flex items-center">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    assessment_ready.ready 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {assessment_ready.ready ? 'Ready for Assessment' : 'Not Ready for Assessment'}
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Overall Readiness</span>
                    <span>{Math.round(assessment_ready.overall_score * 100)}%</span>
                  </div>
                  <ProgressBar 
                    percentage={assessment_ready.overall_score * 100} 
                    color={assessment_ready.ready ? 'bg-green-500' : 'bg-yellow-500'}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Mapping Completion</h4>
                    <ProgressBar 
                      percentage={assessment_ready.criteria.mapping_completion.current} 
                      color={assessment_ready.criteria.mapping_completion.met ? 'bg-green-500' : 'bg-yellow-500'}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {assessment_ready.criteria.mapping_completion.met ? '✓' : '✗'}{' '}
                      {assessment_ready.criteria.mapping_completion.current}% (min {assessment_ready.criteria.mapping_completion.required}%)
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Cleanup Completion</h4>
                    <ProgressBar 
                      percentage={assessment_ready.criteria.cleanup_completion.current} 
                      color={assessment_ready.criteria.cleanup_completion.met ? 'bg-green-500' : 'bg-yellow-500'}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {assessment_ready.criteria.cleanup_completion.met ? '✓' : '✗'}{' '}
                      {assessment_ready.criteria.cleanup_completion.current}% (min {assessment_ready.criteria.cleanup_completion.required}%)
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Data Quality</h4>
                    <ProgressBar 
                      percentage={assessment_ready.criteria.data_quality.current} 
                      color={assessment_ready.criteria.data_quality.met ? 'bg-green-500' : 'bg-yellow-500'}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {assessment_ready.criteria.data_quality.met ? '✓' : '✗'}{' '}
                      {assessment_ready.criteria.data_quality.current}% (min {assessment_ready.criteria.data_quality.required}%)
                    </p>
                  </div>
                </div>

                {assessment_ready.next_steps.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Next Steps</h4>
                    <ul className="space-y-2">
                      {assessment_ready.next_steps.map((step, index) => (
                        <li key={index} className="flex items-start">
                          <ArrowRight className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default AssetInventoryRedesigned;
