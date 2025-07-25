import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FormInput } from 'lucide-react'
import { BarChart3, RefreshCw, FileUpload, Settings, ArrowRight } from 'lucide-react'

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import AgentLearningInsights from '../../components/discovery/AgentLearningInsights';

// Hooks
import type { DiscoveryMetrics, ApplicationLandscape, InfrastructureLandscape } from '../../hooks/useDiscoveryDashboard'
import { useDiscoveryMetrics, useApplicationLandscape, useInfrastructureLandscape } from '../../hooks/useDiscoveryDashboard'
import { useAuth } from '../../contexts/AuthContext';

// UI Components
import { Button } from '../../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import { useToast } from '../../components/ui/use-toast';

// Types
interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
}

// Default values for loading/error states
const defaultMetrics: DiscoveryMetrics = {
  totalAssets: 0,
  totalApplications: 0,
  applicationToServerMapping: 0,
  dependencyMappingComplete: 0,
  techDebtItems: 0,
  criticalIssues: 0,
  discoveryCompleteness: 0,
  dataQuality: 0
};

const defaultAppLandscape: ApplicationLandscape = {
  applications: [],
  summary: {
    byEnvironment: {},
    byCriticality: {},
    byTechStack: {}
  }
};

const defaultInfraLandscape: InfrastructureLandscape = {
  servers: {
    total: 0,
    physical: 0,
    virtual: 0,
    cloud: 0,
    supportedOS: 0,
    deprecatedOS: 0
  },
  databases: {
    total: 0,
    supportedVersions: 0,
    deprecatedVersions: 0,
    endOfLife: 0
  },
  networks: {
    devices: 0,
    securityDevices: 0,
    storageDevices: 0
  }
};

/**
 * MetricCard component for displaying a single metric with optional icon and description
 */
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  description,
  icon,
  className = ''
}) => (
  <Card className={`flex flex-col h-full ${className}`}>
    <CardHeader className="pb-2">
      <div className="flex items-center justify-between space-x-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && <div className="h-4 w-4 text-muted-foreground" aria-hidden="true">{icon}</div>}
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {description && (
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      )}
    </CardContent>
  </Card>
);

/**
 * ProgressCard component for displaying progress with a visual indicator
 */
const ProgressCard: React.FC<{
  title: string;
  value: number;
  description: string;
}> = ({ title, value, description }) => (
  <Card>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>{Math.round(value)}%</span>
          <span className="text-muted-foreground">Complete</span>
        </div>
        <Progress value={value} className="h-2" />
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </CardContent>
  </Card>
);

/**
 * Main DiscoveryDashboard component that displays discovery metrics and insights
 */
const DiscoveryDashboard: React.FC = () => {
  const { toast } = useToast();
  const { user } = useAuth();

  // Fetch data using React Query hooks
  const {
    data: metrics = defaultMetrics,
    isLoading: isLoadingMetrics,
    isError: isErrorMetrics,
    refetch: refetchMetrics
  } = useDiscoveryMetrics();

  const {
    data: applicationLandscape = defaultAppLandscape,
    isLoading: isLoadingAppLandscape,
    isError: isErrorAppLandscape,
    refetch: refetchAppLandscape
  } = useApplicationLandscape();

  const {
    data: infrastructureLandscape = defaultInfraLandscape,
    isLoading: isLoadingInfraLandscape,
    isError: isErrorInfraLandscape,
    refetch: refetchInfraLandscape
  } = useInfrastructureLandscape();

  // Handle refresh of all data
  const handleRefresh = async () => {
    try {
      await Promise.all([
        refetchMetrics(),
        refetchAppLandscape(),
        refetchInfraLandscape()
      ]);
      toast({
        title: 'Data refreshed',
        description: 'Discovery dashboard data has been updated.'
      });
    } catch (error) {
      console.error('Error refreshing data:', error);
      toast({
        title: 'Error',
        description: 'Failed to refresh data. Please try again.',
        variant: 'destructive'
      });
    }
  };

  // Loading and error states
  const isLoading = isLoadingMetrics || isLoadingAppLandscape || isLoadingInfraLandscape;
  const hasError = isErrorMetrics || isErrorAppLandscape || isErrorInfraLandscape;

  // Render error state if any query fails
  if (hasError) {
    return (
      <div className="flex flex-1 overflow-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Discovery Dashboard</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p>Failed to load dashboard data. Please try again later.</p>
          <Button
            variant="outline"
            className="mt-2"
            onClick={handleRefresh}
            aria-label="Retry loading data"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
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
      <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Discovery Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Overview of your discovery and assessment progress
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
            aria-label="Refresh dashboard data"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Breadcrumbs - This can be removed if the main layout handles it */}
      {/*
      <div className="mb-6">
        <ContextBreadcrumbs />
      </div>
      */}

      {/* Loading State */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-muted/20 animate-pulse rounded-lg" />
          ))}
        </div>
      ) : (
        <>
          {/* Metrics Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
            <MetricCard
              title="Total Assets"
              value={metrics.totalAssets}
              description="Discovered assets"
              icon={<BarChart3 className="h-4 w-4" aria-hidden="true" />}
            />
            <MetricCard
              title="Applications"
              value={metrics.totalApplications}
              description="Discovered applications"
            />
            <MetricCard
              title="Critical Issues"
              value={metrics.criticalIssues}
              description="Requires attention"
              className="border-red-200 bg-red-50"
            />
            <MetricCard
              title="Tech Debt Items"
              value={metrics.techDebtItems}
              description="Identified technical debt"
            />
          </div>

          {/* Progress Section */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-6">
            <ProgressCard
              title="Discovery Progress"
              value={metrics.discoveryCompleteness}
              description={`${metrics.discoveryCompleteness}% of assets discovered and assessed`}
            />
            <ProgressCard
              title="Dependency Mapping"
              value={metrics.dependencyMappingComplete}
              description={`${metrics.dependencyMappingComplete}% of dependencies mapped`}
            />
            <ProgressCard
              title="Data Quality"
              value={metrics.dataQuality}
              description={`${metrics.dataQuality}% data quality score`}
            />
          </div>

          {/* Collection Workflow Options */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Data Collection Workflows</CardTitle>
              <p className="text-sm text-muted-foreground">
                Enhance discovery with additional data collection methods
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <FormInput className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium">Adaptive Collection</p>
                      <p className="text-xs text-muted-foreground">Dynamic forms for detailed data</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/collection/adaptive-forms')}
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <FileUpload className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium">Bulk Upload</p>
                      <p className="text-xs text-muted-foreground">Process multiple applications</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/collection/bulk-upload')}
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-orange-100 rounded-lg">
                      <Settings className="h-4 w-4 text-orange-600" />
                    </div>
                    <div>
                      <p className="font-medium">Data Integration</p>
                      <p className="text-xs text-muted-foreground">Resolve data conflicts</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/collection/data-integration')}
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Collection Progress</p>
                    <p className="text-xs text-muted-foreground">Monitor active collection workflows</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate('/collection/progress')}
                  >
                    View Progress
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Agent Learning Insights */}
          <div className="mb-6">
            <AgentLearningInsights
              metrics={metrics}
              applicationLandscape={applicationLandscape}
              infrastructureLandscape={infrastructureLandscape}
            />
          </div>
        </>
      )}
        </div>
      </div>
    );
};

// Memoize the component to prevent unnecessary re-renders
export default React.memo(DiscoveryDashboard);
