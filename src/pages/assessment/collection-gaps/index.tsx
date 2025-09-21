/**
 * Collection Gaps Enhanced Metrics Dashboard
 *
 * Main entry point for Collection Gaps Phase 2 features with comprehensive
 * completeness metrics, lifecycle dates, RTO/RPO indicators
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

// Layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// UI components
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Icons
import {
  BarChart3,
  Calendar,
  Shield,
  Settings,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Zap,
  Target,
  Info
} from 'lucide-react';

// Services
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';

// Types
import type { CompletenessMetrics, CompletenessCategory } from '@/components/collection/types';

interface GapsMetrics {
  vendor_products: {
    total_assets: number;
    mapped_products: number;
    completion_percentage: number;
    missing_lifecycle_dates: number;
  };
  maintenance_windows: {
    total_windows: number;
    upcoming_windows: number;
    coverage_percentage: number;
    conflict_count: number;
  };
  governance: {
    total_requirements: number;
    approved_count: number;
    pending_exceptions: number;
    compliance_score: number;
  };
  rto_rpo: {
    assets_with_rto: number;
    assets_with_rpo: number;
    critical_gaps: number;
    average_rto_hours: number;
    average_rpo_hours: number;
  };
}

const CollectionGapsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { user } = useAuth();

  const flowId = searchParams.get('flowId') || '';
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Fetch completeness metrics
  const { data: completenessData, isLoading: completenessLoading, error: completenessError } = useQuery({
    queryKey: ['collection-gaps-completeness', flowId, refreshTrigger],
    queryFn: () => collectionFlowApi.getCompletenessMetrics(flowId),
    enabled: !!flowId,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000
  });

  // Mock data for gaps metrics (will be replaced with actual API call)
  const { data: gapsMetrics, isLoading: gapsLoading } = useQuery({
    queryKey: ['collection-gaps-metrics', flowId, refreshTrigger],
    queryFn: async (): Promise<GapsMetrics> => {
      // This will be replaced with actual API call to /api/v1/collection/gaps/metrics
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      return {
        vendor_products: {
          total_assets: 150,
          mapped_products: 128,
          completion_percentage: 85.3,
          missing_lifecycle_dates: 22
        },
        maintenance_windows: {
          total_windows: 8,
          upcoming_windows: 3,
          coverage_percentage: 92.5,
          conflict_count: 1
        },
        governance: {
          total_requirements: 12,
          approved_count: 10,
          pending_exceptions: 3,
          compliance_score: 83.3
        },
        rto_rpo: {
          assets_with_rto: 142,
          assets_with_rpo: 138,
          critical_gaps: 8,
          average_rto_hours: 4.2,
          average_rpo_hours: 1.8
        }
      };
    },
    enabled: !!flowId,
    refetchInterval: 30000,
    staleTime: 10000
  });

  const handleRefresh = async () => {
    if (!flowId) return;

    try {
      await collectionFlowApi.refreshCompletenessMetrics(flowId);
      setRefreshTrigger(prev => prev + 1);
      toast({
        title: 'Metrics Refreshed',
        description: 'Collection gaps metrics have been updated with the latest data.'
      });
    } catch (error) {
      console.error('Failed to refresh metrics:', error);
      toast({
        title: 'Refresh Failed',
        description: 'Unable to refresh metrics. Please try again.',
        variant: 'destructive'
      });
    }
  };

  const getCompletionColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompletionBadgeVariant = (percentage: number) => {
    if (percentage >= 90) return 'default';
    if (percentage >= 70) return 'secondary';
    return 'destructive';
  };

  if (!flowId) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Flow ID is required to view collection gaps dashboard. Please navigate from an active collection flow.
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Collection Gaps Dashboard</h1>
                <p className="text-muted-foreground">
                  Enhanced data collection areas: vendor products, maintenance windows, governance, and resilience metrics
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleRefresh}
                  variant="outline"
                  disabled={completenessLoading || gapsLoading}
                  className="flex items-center gap-2"
                >
                  <TrendingUp className="h-4 w-4" />
                  Refresh Metrics
                </Button>
              </div>
            </div>

            {/* Error handling */}
            {completenessError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load completeness metrics. Please try refreshing the page.
                </AlertDescription>
              </Alert>
            )}

            {/* Overall Completion Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Overall Collection Completeness
                </CardTitle>
              </CardHeader>
              <CardContent>
                {completenessLoading ? (
                  <div className="space-y-3">
                    <div className="h-6 bg-gray-100 rounded animate-pulse" />
                    <div className="h-4 bg-gray-100 rounded animate-pulse w-3/4" />
                  </div>
                ) : completenessData ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-3xl font-bold">
                          {completenessData.overall_completion}%
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {completenessData.completed_fields} of {completenessData.total_fields} fields completed
                        </div>
                      </div>
                      <Badge variant={getCompletionBadgeVariant(completenessData.overall_completion)}>
                        {completenessData.overall_completion >= 90 ? 'Excellent' :
                         completenessData.overall_completion >= 70 ? 'Good' : 'Needs Attention'}
                      </Badge>
                    </div>
                    <Progress value={completenessData.overall_completion} className="h-2" />
                    <div className="text-xs text-muted-foreground">
                      Last updated: {new Date(completenessData.last_updated).toLocaleString()}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    No completeness data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tabs for different feature areas */}
            <Tabs defaultValue="overview" className="space-y-6">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="vendor-products">Vendor Products</TabsTrigger>
                <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
                <TabsTrigger value="governance">Governance</TabsTrigger>
                <TabsTrigger value="resilience">Resilience</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                        onClick={() => navigate(`/assessment/collection-gaps/vendor-products?flowId=${flowId}`)}>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-2">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <Database className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Vendor Products</p>
                          <p className="text-2xl font-bold">
                            {gapsMetrics?.vendor_products.completion_percentage.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="mt-2">
                        <Progress value={gapsMetrics?.vendor_products.completion_percentage || 0} className="h-1" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                        onClick={() => navigate(`/assessment/collection-gaps/maintenance-windows?flowId=${flowId}`)}>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-2">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <Calendar className="h-6 w-6 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Maintenance Windows</p>
                          <p className="text-2xl font-bold">
                            {gapsMetrics?.maintenance_windows.coverage_percentage.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="mt-2">
                        <Progress value={gapsMetrics?.maintenance_windows.coverage_percentage || 0} className="h-1" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                        onClick={() => navigate(`/assessment/collection-gaps/governance?flowId=${flowId}`)}>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-2">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <Shield className="h-6 w-6 text-purple-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Governance</p>
                          <p className="text-2xl font-bold">
                            {gapsMetrics?.governance.compliance_score.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="mt-2">
                        <Progress value={gapsMetrics?.governance.compliance_score || 0} className="h-1" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-2">
                        <div className="p-2 bg-orange-100 rounded-lg">
                          <Zap className="h-6 w-6 text-orange-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">RTO/RPO Coverage</p>
                          <p className="text-2xl font-bold">
                            {gapsMetrics?.rto_rpo.assets_with_rto || 0}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">
                        Critical gaps: {gapsMetrics?.rto_rpo.critical_gaps || 0}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Completion Categories */}
                <Card>
                  <CardHeader>
                    <CardTitle>Collection Categories</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {completenessLoading ? (
                      <div className="space-y-3">
                        {[...Array(4)].map((_, i) => (
                          <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                        ))}
                      </div>
                    ) : completenessData?.categories ? (
                      <div className="space-y-4">
                        {completenessData.categories.map((category: CompletenessCategory) => (
                          <div key={category.id} className="flex items-center justify-between p-4 border rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium">{category.name}</h4>
                                <Badge variant={
                                  category.status === 'complete' ? 'default' :
                                  category.status === 'partial' ? 'secondary' :
                                  category.status === 'missing' ? 'destructive' : 'outline'
                                }>
                                  {category.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">{category.description}</p>
                              <div className="mt-2">
                                <Progress value={category.completion_percentage} className="h-2" />
                              </div>
                            </div>
                            <div className="text-right ml-4">
                              <div className={`text-lg font-semibold ${getCompletionColor(category.completion_percentage)}`}>
                                {category.completion_percentage}%
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {category.completed_fields.length} / {category.required_fields.length} fields
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        No category data available
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Other tab contents will be implemented in their respective pages */}
              <TabsContent value="vendor-products">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <Database className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-lg font-medium">Vendor Products Management</h3>
                      <p className="mt-1 text-sm text-gray-500 mb-4">
                        Search, create, and manage vendor product mappings for your assets.
                      </p>
                      <Button onClick={() => navigate(`/assessment/collection-gaps/vendor-products?flowId=${flowId}`)}>
                        Manage Vendor Products
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="maintenance">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <Calendar className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-lg font-medium">Maintenance Windows</h3>
                      <p className="mt-1 text-sm text-gray-500 mb-4">
                        Create and manage maintenance windows with conflict detection.
                      </p>
                      <Button onClick={() => navigate(`/assessment/collection-gaps/maintenance-windows?flowId=${flowId}`)}>
                        Manage Maintenance Windows
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="governance">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <Shield className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-lg font-medium">Governance & Exceptions</h3>
                      <p className="mt-1 text-sm text-gray-500 mb-4">
                        Submit approval requests and manage migration exceptions.
                      </p>
                      <Button onClick={() => navigate(`/assessment/collection-gaps/governance?flowId=${flowId}`)}>
                        Manage Governance
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="resilience">
                <Card>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-lg font-medium mb-4">RTO Metrics</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Assets with RTO defined:</span>
                            <span className="font-medium">{gapsMetrics?.rto_rpo.assets_with_rto || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Average RTO:</span>
                            <span className="font-medium">{gapsMetrics?.rto_rpo.average_rto_hours || 0}h</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h3 className="text-lg font-medium mb-4">RPO Metrics</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Assets with RPO defined:</span>
                            <span className="font-medium">{gapsMetrics?.rto_rpo.assets_with_rpo || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Average RPO:</span>
                            <span className="font-medium">{gapsMetrics?.rto_rpo.average_rpo_hours || 0}h</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {gapsMetrics?.rto_rpo.critical_gaps > 0 && (
                      <Alert className="mt-4">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          {gapsMetrics.rto_rpo.critical_gaps} assets have critical RTO/RPO gaps that need attention.
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionGapsDashboard;
