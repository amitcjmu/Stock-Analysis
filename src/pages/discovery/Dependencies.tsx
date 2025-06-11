import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Network, Database, Server, ArrowRight, RefreshCw, Filter, Search, MapPin, Activity, AlertTriangle, CheckCircle, Clock, Settings, Eye
} from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { useSession } from '@/contexts/SessionContext';

import { apiCall } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import { ContextBreadcrumbs } from '@/components/context/ContextBreadcrumbs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from '@/components/ui/badge';

interface DependencyItem {
  id: string;
  source_asset: string;
  source_asset_name?: string;
  target: string;
  target_asset_name?: string;
  dependency_type: string;
  dependency_strength?: string;
  confidence: number;
  discovery_method: string;
  validation_status: 'validated' | 'needs_review' | 'conflicted' | 'pending';
  business_impact?: string;
  migration_risk?: string;
}

interface DependencyGraphNode {
  id: string;
  label: string;
  type: 'application' | 'server' | 'database';
  criticality?: string;
  environment?: string;
}

interface DependencyGraphEdge {
  source: string;
  target: string;
  type: string;
  strength: string;
  confidence: number;
}

interface ApplicationCluster {
  id: string;
  name: string;
  applications: string[];
  complexity_score: number;
  migration_sequence: number;
}

interface DependencyAnalysisData {
  dependency_analysis: {
    total_dependencies: number;
    dependency_categories: Record<string, number>;
    dependency_quality: {
      quality_score: number;
      high_confidence_count: number;
      medium_confidence_count: number;
      low_confidence_count: number;
      quality_issues: string[];
    };
    conflict_resolution: {
      conflicts_resolved: number;
      total_dependencies: number;
    };
  };
  cross_application_mapping: {
    cross_app_dependencies: any[];
    application_clusters: ApplicationCluster[];
    dependency_graph: {
      nodes: DependencyGraphNode[];
      edges: DependencyGraphEdge[];
    };
  };
  impact_analysis: {
    impact_summary: {
      total_cross_app_dependencies: number;
      critical_dependencies: number;
      high_impact_dependencies: number;
      dependency_complexity_score: number;
    };
    migration_recommendations: string[];
    dependency_risks: any[];
    impact_categories: {
      critical: any[];
      high: any[];
      medium: any[];
      low: any[];
    };
  };
  clarification_questions: any[];
  dependency_recommendations: any[];
  intelligence_metadata: {
    analysis_confidence: number;
    learning_opportunities: number;
    validation_score: number;
    analysis_timestamp: string;
  };
}

const Dependencies = () => {
  const { getAuthHeaders, currentEngagementId } = useAuth();
  const { activeEngagement } = useSession();
  const queryClient = useQueryClient();

  // UI-only state
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedStrength, setSelectedStrength] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showGraph, setShowGraph] = useState(true);
  const [graphViewMode, setGraphViewMode] = useState<'applications' | 'infrastructure'>('applications');
  const [selectedDependency, setSelectedDependency] = React.useState<any>(null);
  const [showReviewModal, setShowReviewModal] = React.useState(false);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  // Query: fetch dependency analysis
  const {
    data: dependencyData,
    isLoading,
    isError,
    error,
    refetch: refetchDependencyAnalysis
  } = useQuery<DependencyAnalysisData>({
    queryKey: ['dependency-analysis', currentEngagementId],
    queryFn: async () => {
      if (!currentEngagementId) {
        throw new Error("Engagement ID not available");
      }
      const headers = getAuthHeaders();
      const assetsResponse = await apiCall(`/api/v1/discovery/assets?page=1&page_size=1000&engagement_id=${currentEngagementId}`, { headers });
      const assets = assetsResponse.assets || [];
      
      let applications: any[] = [];
      try {
        const applicationsResponse = await apiCall(`/api/v1/discovery/applications?engagement_id=${currentEngagementId}`, { headers });
        applications = applicationsResponse.applications || [];
      } catch (appError) {
        console.warn("Could not fetch applications, proceeding without them.", appError);
      }
      
      const result = await apiCall('/api/v1/discovery/dependency-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: JSON.stringify({
          assets,
          applications,
          user_context: {
            analysis_type: 'comprehensive',
            include_cross_app_mapping: true,
            include_impact_analysis: true,
            engagement_id: currentEngagementId,
          }
        })
      });
      if (!result?.dependency_intelligence) throw new Error('No dependency_intelligence in response');
      return result.dependency_intelligence;
    },
    enabled: !!currentEngagementId,
    retry: 1,
    staleTime: 1000 * 60 * 5,
  });
  
  // Filter dependencies based on controls
  const filteredDependencies = useMemo(() => {
    let deps = dependencyData?.cross_application_mapping?.cross_app_dependencies || [];

    if (selectedFilter !== 'all') {
      deps = deps.filter(d => d.dependency_type === selectedFilter);
    }
    if (selectedStrength !== 'all') {
      deps = deps.filter(d => d.dependency_strength === selectedStrength);
    }
    if (searchTerm) {
      const lowercasedTerm = searchTerm.toLowerCase();
      deps = deps.filter(d =>
        d.source_asset_name?.toLowerCase().includes(lowercasedTerm) ||
        d.target_asset_name?.toLowerCase().includes(lowercasedTerm)
      );
    }
    return deps;
  }, [dependencyData, selectedFilter, selectedStrength, searchTerm]);

  // Filter dependency graph based on filtered dependencies
  const filteredDependencyGraph = useMemo(() => {
    if (!dependencyData?.cross_application_mapping?.dependency_graph) return null;

    const filteredNodes = dependencyData.cross_application_mapping.dependency_graph.nodes.filter(node =>
      filteredDependencies.some(dep => dep.source_asset === node.id || dep.target === node.id)
    );

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));

    const filteredEdges = dependencyData.cross_application_mapping.dependency_graph.edges.filter(edge =>
      filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
    );
    
    return {
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [dependencyData, filteredDependencies]);

  const applicationClusters = dependencyData?.cross_application_mapping?.application_clusters || [];

  useEffect(() => {
    if (dependencyData) {
      console.log('🎯 Component Render - Dependency Data:', {
        total_dependencies: dependencyData.dependency_analysis?.total_dependencies,
        cross_app_deps_count: filteredDependencies.length,
        application_clusters_count: applicationClusters.length,
        graph_nodes_count: filteredDependencyGraph?.nodes?.length || 0,
        graph_edges_count: filteredDependencyGraph?.edges?.length || 0,
      });
    }
  }, [dependencyData, filteredDependencies, applicationClusters, filteredDependencyGraph]);

  const handleReviewDependency = (dependency: any) => {
    setSelectedDependency(dependency);
    setShowReviewModal(true);
  };
  
  const handleSaveDependency = async (updatedDependency: any) => {
    console.log('Saving updated dependency:', updatedDependency);
    setShowReviewModal(false);
    refetchDependencyAnalysis();
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'Critical': return '#DC2626';
      case 'High': return '#F59E0B';
      case 'Medium': return '#3B82F6';
      case 'Low': return '#22C55E';
      default: return '#6B7280';
    }
  };

  const getValidationStatusColor = (status: string): "default" | "destructive" | "outline" | "secondary" => {
    switch (status) {
      case 'validated': return 'secondary';
      case 'needs_review': return 'default';
      case 'conflicted': return 'destructive';
      case 'pending':
      default: return 'outline';
    }
  };

  const getValidationIcon = (status: string) => {
    switch (status) {
      case 'validated': return <CheckCircle className="h-4 w-4 mr-1 inline-block" />;
      case 'needs_review': return <AlertTriangle className="h-4 w-4 mr-1 inline-block" />;
      case 'conflicted': return <AlertTriangle className="h-4 w-4 mr-1 inline-block" />;
      case 'pending':
      default: return <Clock className="h-4 w-4 mr-1 inline-block" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex">
        <div className="flex-1">
          <main className="p-8">
            <div className="max-w-full mx-auto">
              {/* Header with Breadcrumbs */}
              <div className="mb-8">
                <div className="mb-4">
                  <ContextBreadcrumbs />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Dependency Mapping</h1>
                    <p className="text-lg text-gray-600">
                      AI-powered discovery and visualization of asset dependencies
                    </p>
                  </div>
                  <button
                    onClick={() => refetchDependencyAnalysis()}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh Analysis</span>
                  </button>
                </div>

                {isError && (
                  <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
                    <p className="font-bold">Error</p>
                    <p>{(error as any)?.message || "Failed to fetch dependency analysis."}</p>
                  </div>
                )}
              </div>

              {/* Intelligence Status */}
              {dependencyData && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900">
                      Dependency Intelligence Active
                    </span>
                  </div>
                  <p className="text-sm text-blue-700 mt-1">
                    AI analysis complete with {dependencyData.dependency_analysis.total_dependencies} dependencies discovered across {applicationClusters.length} application clusters
                  </p>
                </div>
              )}

              {/* Dependency Stats */}
              {dependencyData && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center space-x-3">
                      <Network className="h-8 w-8 text-blue-500" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-600">Total Dependencies</h3>
                        <p className="text-2xl font-bold text-gray-900">{dependencyData.dependency_analysis.total_dependencies}</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
                        <span className="text-white text-sm font-bold">C</span>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-600">Critical</h3>
                        <p className="text-2xl font-bold text-red-600">{dependencyData.impact_analysis.impact_summary.critical_dependencies}</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                        <span className="text-white text-sm font-bold">H</span>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-600">High Impact</h3>
                        <p className="text-2xl font-bold text-orange-600">{dependencyData.impact_analysis.impact_summary.high_impact_dependencies}</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center space-x-3">
                      <Database className="h-8 w-8 text-purple-500" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-600">App Clusters</h3>
                        <p className="text-2xl font-bold text-purple-600">{applicationClusters.length}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Controls */}
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowGraph(!showGraph)}
                      className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                        showGraph 
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <Network className="h-5 w-5" />
                      <span>Graph View</span>
                    </button>
                    
                    {showGraph && (
                      <select
                        value={graphViewMode}
                        onChange={(e) => setGraphViewMode(e.target.value as 'applications' | 'infrastructure')}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="applications">Application View</option>
                        <option value="infrastructure">Infrastructure View</option>
                      </select>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5 text-gray-400" />
                    <select
                      value={selectedFilter}
                      onChange={(e) => setSelectedFilter(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Types</option>
                      <option value="application">Application</option>
                      <option value="infrastructure">Infrastructure</option>
                      <option value="platform">Platform</option>
                      <option value="security">Security</option>
                    </select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <select
                      value={selectedStrength}
                      onChange={(e) => setSelectedStrength(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Strengths</option>
                      <option value="Critical">Critical</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>

                  <div className="flex-1 max-w-md">
                    <div className="relative">
                      <Search className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Search dependencies..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {isLoading && (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 text-blue-600 animate-spin mx-auto" />
                  <p className="mt-4 text-lg text-gray-600">Running AI Dependency Analysis...</p>
                  <p className="text-sm text-gray-500">This may take a moment.</p>
                </div>
              )}

              {dependencyData && !isLoading && (
                <div className="space-y-8">
                  {showGraph ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Dependency Graph</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="h-[600px] w-full bg-gray-100 rounded-lg flex items-center justify-center">
                          <p className="text-gray-500">Dependency Graph Component not available.</p>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <Card>
                      <CardHeader>
                        <CardTitle>Application Clusters</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {applicationClusters.map(cluster => (
                            <Card key={cluster.id} className="p-4">
                              <h4 className="font-bold">{cluster.name}</h4>
                              <p className="text-sm text-gray-600">Apps: {cluster.applications.length}</p>
                              <p className="text-sm text-gray-600">Complexity: {cluster.complexity_score}</p>
                            </Card>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Dependency Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Source Asset</TableHead>
                            <TableHead></TableHead>
                            <TableHead>Target Asset</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Strength</TableHead>
                            <TableHead>Confidence</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredDependencies.map((dep) => (
                            <TableRow key={dep.id}>
                              <TableCell className="font-medium">{dep.source_asset_name || dep.source_asset}</TableCell>
                              <TableCell><ArrowRight className="h-4 w-4" /></TableCell>
                              <TableCell className="font-medium">{dep.target_asset_name || dep.target}</TableCell>
                              <TableCell>{dep.dependency_type}</TableCell>
                              <TableCell>
                                <Badge style={{ backgroundColor: getStrengthColor(dep.dependency_strength || 'Low'), color: 'white' }} >
                                  {dep.dependency_strength}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Progress value={dep.confidence * 100} className="w-24" />
                              </TableCell>
                              <TableCell>
                                <Badge variant={getValidationStatusColor(dep.validation_status)}>
                                  {getValidationIcon(dep.validation_status)}
                                  {dep.validation_status}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Button variant="outline" size="sm" onClick={() => handleReviewDependency(dep)}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  Review
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {showReviewModal && selectedDependency && (
        <Dialog open={showReviewModal} onOpenChange={setShowReviewModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Review Dependency</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Source Asset</Label>
                  <p className="font-semibold">{selectedDependency.source_asset_name}</p>
                </div>
                <div>
                  <Label>Target Asset</Label>
                  <p className="font-semibold">{selectedDependency.target_asset_name}</p>
                </div>
              </div>
              <div>
                <Label htmlFor="validation_status">Validation Status</Label>
                <Select
                  value={selectedDependency.validation_status}
                  onValueChange={(value) => setSelectedDependency({ ...selectedDependency, validation_status: value })}
                >
                  <SelectTrigger id="validation_status">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="validated">Validated</SelectItem>
                    <SelectItem value="needs_review">Needs Review</SelectItem>
                    <SelectItem value="conflicted">Conflicted</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="notes">Notes</Label>
                <Textarea id="notes" placeholder="Add notes about this dependency..." />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowReviewModal(false)}>Cancel</Button>
                <Button onClick={() => handleSaveDependency(selectedDependency)}>Save</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default Dependencies;
