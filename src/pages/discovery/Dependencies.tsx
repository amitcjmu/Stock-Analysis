import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { Network, Database, Server, ArrowRight, RefreshCw, Filter, Search, MapPin, Activity, AlertTriangle, CheckCircle, Clock, Settings, Eye } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';
import { useAppContext } from '../../hooks/useContext';

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
  const { getContextHeaders, context } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [dependencyData, setDependencyData] = useState<DependencyAnalysisData | null>(null);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedStrength, setSelectedStrength] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showGraph, setShowGraph] = useState(true);
  const [graphViewMode, setGraphViewMode] = useState<'applications' | 'infrastructure'>('applications');
  const [selectedDependency, setSelectedDependency] = React.useState<any>(null);
  const [showReviewModal, setShowReviewModal] = React.useState(false);
  const [editMode, setEditMode] = React.useState(false);

  useEffect(() => {
    fetchDependencyAnalysis();
    // Trigger agent analysis after initial data load
    setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
  }, []);

  // Refetch data when context changes (client/engagement/session)
  useEffect(() => {
    if (context.client && context.engagement) {
      console.log('🔄 Context changed, refetching dependencies data for:', {
        client: context.client.name,
        engagement: context.engagement.name,
        session: context.session?.session_display_name || 'None'
      });
      
      // Refetch dependency analysis for new context
      fetchDependencyAnalysis();
    }
  }, [context.client, context.engagement, context.session, context.viewMode]);

  const fetchDependencyAnalysis = async () => {
    try {
      setIsLoading(true);
      const contextHeaders = getContextHeaders();
      
      // Get assets for dependency analysis
      const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`, {
        headers: contextHeaders
      });
      const assets = assetsResponse?.assets || [];
      
      // Get applications for cross-app mapping
      let applications = [];
      try {
        const applicationsResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS, {
          headers: contextHeaders
        });
        applications = applicationsResponse?.applications || [];
      } catch (appError) {
        console.warn('Could not fetch applications for dependency analysis:', appError);
      }

      // Debug: Log what we're sending to the API
      console.log('🚀 Sending to dependency analysis API:', {
        assets_count: assets.length,
        applications_count: applications.length,
        sample_asset: assets[0],
        user_context: {
          analysis_type: 'comprehensive',
          include_cross_app_mapping: true,
          include_impact_analysis: true
        }
      });

      // Perform dependency analysis
      const dependencyAnalysis = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.DEPENDENCY_ANALYSIS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify({
          assets: assets,
          applications: applications,
          user_context: {
            analysis_type: 'comprehensive',
            include_cross_app_mapping: true,
            include_impact_analysis: true
          }
        }),
      });

      if (dependencyAnalysis?.dependency_intelligence) {
        console.log('🔍 Dependency Analysis Response:', dependencyAnalysis.dependency_intelligence);
        console.log('📊 Cross-app deps count:', dependencyAnalysis.dependency_intelligence.cross_application_mapping?.cross_app_dependencies?.length);
        console.log('🏗️ Application clusters count:', dependencyAnalysis.dependency_intelligence.cross_application_mapping?.application_clusters?.length);
        console.log('📈 Graph nodes count:', dependencyAnalysis.dependency_intelligence.cross_application_mapping?.dependency_graph?.nodes?.length);
        
        // Enhanced debugging - show sample dependency data
        const sampleDeps = dependencyAnalysis.dependency_intelligence.cross_application_mapping?.cross_app_dependencies?.slice(0, 3);
        console.log('🎯 Sample dependencies:', sampleDeps);
        
        setDependencyData(dependencyAnalysis.dependency_intelligence);
        
        // Trigger agent analysis with dependency context
        await triggerAgentAnalysis(dependencyAnalysis.dependency_intelligence);
      } else {
        console.error('❌ No dependency_intelligence in response:', dependencyAnalysis);
      }
    } catch (error) {
      console.error('Failed to fetch dependency analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const triggerAgentAnalysis = async (depData: DependencyAnalysisData) => {
    try {
      // Trigger agent analysis with dependency context
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        body: JSON.stringify({
          page_context: 'dependencies',
          data_context: {
            dependency_analysis: depData.dependency_analysis,
            cross_app_dependencies: depData.cross_application_mapping.cross_app_dependencies.slice(0, 5), // Sample for context
            impact_summary: depData.impact_analysis.impact_summary,
            validation_needs: depData.dependency_analysis.dependency_quality
          },
          analysis_type: 'dependency_mapping'
        }),
      });

      // Refresh agent panels after a moment
      setTimeout(() => {
        setAgentRefreshTrigger(prev => prev + 1);
      }, 1500);
    } catch (error) {
      console.error('Failed to trigger dependency agent analysis:', error);
    }
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'Critical': return 'bg-red-100 text-red-800';
      case 'High': return 'bg-orange-100 text-orange-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getValidationStatusColor = (status: string) => {
    switch (status) {
      case 'validated': return 'bg-green-100 text-green-800';
      case 'needs_review': return 'bg-yellow-100 text-yellow-800';
      case 'conflicted': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getValidationIcon = (status: string) => {
    switch (status) {
      case 'validated': return <CheckCircle className="h-4 w-4" />;
      case 'needs_review': return <Eye className="h-4 w-4" />;
      case 'conflicted': return <AlertTriangle className="h-4 w-4" />;
      case 'pending': return <Clock className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  // Filter dependencies based on controls
  const filteredDependencies = React.useMemo(() => {
    let deps = dependencyData?.cross_application_mapping?.cross_app_dependencies || [];
    
    // Filter by type
    if (selectedFilter !== 'all') {
      deps = deps.filter(dep => dep.dependency?.dependency_type?.includes(selectedFilter));
    }
    
    // Filter by strength/impact
    if (selectedStrength !== 'all') {
      deps = deps.filter(dep => dep.impact_level === selectedStrength.toLowerCase());
    }
    
    // Filter by search term
    if (searchTerm) {
      deps = deps.filter(dep => 
        dep.source_application?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dep.target_application?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return deps;
  }, [dependencyData, selectedFilter, selectedStrength, searchTerm]);

  // Filter dependency graph based on filtered dependencies
  const filteredDependencyGraph = React.useMemo(() => {
    if (!dependencyData?.cross_application_mapping?.dependency_graph) return null;
    
    const originalGraph = dependencyData.cross_application_mapping.dependency_graph;
    
    // Get nodes that are involved in filtered dependencies
    const involvedNodes = new Set<string>();
    filteredDependencies.forEach(dep => {
      involvedNodes.add(dep.source_application);
      involvedNodes.add(dep.target_application);
    });
    
    // Filter nodes
    const filteredNodes = originalGraph.nodes.filter(node => 
      involvedNodes.has(node.id) || involvedNodes.has(node.label)
    );
    
    // Filter edges based on filtered dependencies
    const filteredEdges = originalGraph.edges.filter(edge => {
      const matchingDep = filteredDependencies.find(dep => 
        (dep.source_application === edge.source || dep.source_application === edge.target) &&
        (dep.target_application === edge.target || dep.target_application === edge.source)
      );
      return matchingDep !== undefined;
    });
    
    return {
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [dependencyData, filteredDependencies]);

  const applicationClusters = dependencyData?.cross_application_mapping?.application_clusters || [];

  // Debug logging
  React.useEffect(() => {
    if (dependencyData) {
      console.log('🎯 Component Render - Dependency Data:', {
        total_dependencies: dependencyData.dependency_analysis?.total_dependencies,
        cross_app_deps_count: filteredDependencies.length,
        application_clusters_count: applicationClusters.length,
        graph_nodes_count: filteredDependencyGraph?.nodes?.length || 0,
        graph_edges_count: filteredDependencyGraph?.edges?.length || 0,
      });
      
      // Debug filtered dependencies structure
      console.log('🔍 Raw filteredDependencies:', filteredDependencies);
      console.log('🔍 Full dependencyData structure:', dependencyData);
      
      if (filteredDependencies.length > 0) {
        console.log('📋 Sample dependency fields:', Object.keys(filteredDependencies[0]));
      }
    }
  }, [dependencyData, filteredDependencies.length, applicationClusters.length, filteredDependencyGraph]);

  const handleReviewDependency = (dependency: any) => {
    setSelectedDependency(dependency);
    setShowReviewModal(true);
  };

  const handleSaveDependency = async (updatedDependency: any) => {
    // Here you would call an API to update the dependency
    console.log('Saving updated dependency:', updatedDependency);
    setShowReviewModal(false);
    // Refresh the analysis
    fetchDependencyAnalysis();
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
                  <ContextBreadcrumbs showContextSelector={true} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Dependency Mapping</h1>
                    <p className="text-lg text-gray-600">
                      AI-powered discovery and visualization of asset dependencies
                    </p>
                  </div>
                  <button
                    onClick={fetchDependencyAnalysis}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh Analysis</span>
                  </button>
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
              </div>

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

              {/* Dependency Graph Visualization */}
              {showGraph && filteredDependencyGraph && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Dependency Graph
                    {(selectedFilter !== 'all' || selectedStrength !== 'all' || searchTerm) && (
                      <span className="text-sm font-normal text-gray-500 ml-2">(Filtered)</span>
                    )}
                  </h2>
                  <div className="border border-gray-200 rounded-lg bg-gray-50">
                    <div className="p-4 border-b border-gray-200 bg-white rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{filteredDependencyGraph.nodes.length} nodes</span>
                          <span>{filteredDependencyGraph.edges.length} connections</span>
                          {editMode && <span className="text-blue-600 font-medium">Edit Mode</span>}
                        </div>
                        <div className="flex items-center space-x-6 text-sm">
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                            <span>Applications ({filteredDependencyGraph.nodes.filter(n => n.type === 'application').length})</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span>Servers ({filteredDependencyGraph.nodes.filter(n => n.type === 'server').length})</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                            <span>Databases ({filteredDependencyGraph.nodes.filter(n => n.type === 'database').length})</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Interactive SVG Graph */}
                    <div className="p-6">
                      {filteredDependencyGraph.nodes.length === 0 ? (
                        <div className="text-center py-12">
                          <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                          <h3 className="text-lg font-medium text-gray-900 mb-2">No Dependencies Match Filters</h3>
                          <p className="text-gray-600">Try adjusting your search criteria or filters</p>
                        </div>
                      ) : (
                        <svg width="100%" height="500" viewBox="0 0 1000 500" className="border border-gray-200 rounded bg-white">
                          {/* Define arrow marker for edges */}
                          <defs>
                            <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                                    refX="10" refY="3.5" orient="auto">
                              <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280" />
                            </marker>
                            <marker id="arrowhead-hover" markerWidth="10" markerHeight="7" 
                                    refX="10" refY="3.5" orient="auto">
                              <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6" />
                            </marker>
                          </defs>
                          
                          {/* Calculate shared layout variables */}
                          {(() => {
                            const cols = Math.ceil(Math.sqrt(filteredDependencyGraph.nodes.length));
                            const rows = Math.ceil(filteredDependencyGraph.nodes.length / cols);
                            const nodeSpacingX = 900 / Math.max(cols - 1, 1);
                            const nodeSpacingY = 400 / Math.max(rows - 1, 1);
                            
                            return (
                              <>
                                {/* Render edges (connections) */}
                                {filteredDependencyGraph.edges.map((edge, index) => {
                                  // Use a better grid layout instead of circular
                                  const sourceNode = filteredDependencyGraph.nodes.find(n => n.id === edge.source || n.label === edge.source);
                                  const targetNode = filteredDependencyGraph.nodes.find(n => n.id === edge.target || n.label === edge.target);
                                  
                                  if (!sourceNode || !targetNode) return null;
                                  
                                  const sourceIndex = filteredDependencyGraph.nodes.indexOf(sourceNode);
                                  const targetIndex = filteredDependencyGraph.nodes.indexOf(targetNode);
                                  
                                  const sourceCol = sourceIndex % cols;
                                  const sourceRow = Math.floor(sourceIndex / cols);
                                  const targetCol = targetIndex % cols;
                                  const targetRow = Math.floor(targetIndex / cols);
                                  
                                  const sourceX = 50 + sourceCol * nodeSpacingX;
                                  const sourceY = 50 + sourceRow * nodeSpacingY;
                                  const targetX = 50 + targetCol * nodeSpacingX;
                                  const targetY = 50 + targetRow * nodeSpacingY;
                            
                            // Calculate edge end point (stop before node)
                            const nodeRadius = 30;
                            const dx = targetX - sourceX;
                            const dy = targetY - sourceY;
                            const length = Math.sqrt(dx * dx + dy * dy);
                            const edgeEndX = length > 0 ? targetX - (dx / length) * nodeRadius : targetX;
                            const edgeEndY = length > 0 ? targetY - (dy / length) * nodeRadius : targetY;
                            const edgeStartX = length > 0 ? sourceX + (dx / length) * nodeRadius : sourceX;
                            const edgeStartY = length > 0 ? sourceY + (dy / length) * nodeRadius : sourceY;
                            
                            // Find matching dependency for click handler
                            const matchingDep = filteredDependencies.find(dep => 
                              (dep.source_application === edge.source && dep.target_application === edge.target) ||
                              (dep.source_application === sourceNode.label && dep.target_application === targetNode.label)
                            );
                            
                            return (
                              <g key={`edge-${index}`}>
                                <line
                                  x1={edgeStartX}
                                  y1={edgeStartY}
                                  x2={edgeEndX}
                                  y2={edgeEndY}
                                  stroke="#6B7280"
                                  strokeWidth={edge.strength === 'critical' ? 3 : edge.strength === 'high' ? 2 : 1}
                                  strokeOpacity={0.6}
                                  markerEnd="url(#arrowhead)"
                                  className="cursor-pointer hover:stroke-blue-500 transition-colors"
                                  onClick={() => {
                                    if (matchingDep && editMode) {
                                      handleReviewDependency(matchingDep);
                                    }
                                  }}
                                />
                                {/* Edge label */}
                                <text
                                  x={(edgeStartX + edgeEndX) / 2}
                                  y={(edgeStartY + edgeEndY) / 2 - 5}
                                  textAnchor="middle"
                                  className="text-xs fill-gray-600 pointer-events-none"
                                  fontSize="11"
                                >
                                  {edge.type.replace('_', ' ')}
                                </text>
                                {/* Clickable area for edge */}
                                <line
                                  x1={edgeStartX}
                                  y1={edgeStartY}
                                  x2={edgeEndX}
                                  y2={edgeEndY}
                                  stroke="transparent"
                                  strokeWidth="12"
                                  className="cursor-pointer"
                                  onClick={() => {
                                    if (matchingDep) {
                                      if (editMode) {
                                        handleReviewDependency(matchingDep);
                                      } else {
                                        console.log('Dependency details:', matchingDep);
                                      }
                                    }
                                  }}
                                />
                                  </g>
                                );
                              })}
                              
                              {/* Render nodes */}
                              {filteredDependencyGraph.nodes.map((node, index) => {
                                const col = index % cols;
                                const row = Math.floor(index / cols);
                                
                                const x = 50 + col * nodeSpacingX;
                                const y = 50 + row * nodeSpacingY;
                            
                            const nodeColor = node.type === 'application' ? '#3B82F6' : 
                                            node.type === 'server' ? '#10B981' : '#8B5CF6';
                            
                            return (
                              <g key={`node-${node.id}`} className="cursor-pointer">
                                <circle
                                  cx={x}
                                  cy={y}
                                  r="30"
                                  fill={nodeColor}
                                  stroke="#ffffff"
                                  strokeWidth="3"
                                  className="hover:opacity-80 transition-opacity drop-shadow-md"
                                  onClick={() => {
                                    if (editMode) {
                                      // In edit mode, allow creating new dependencies from this node
                                      console.log('Select node for new dependency:', node);
                                    } else {
                                      console.log('Node details:', node);
                                    }
                                  }}
                                />
                                {/* Node icon/text */}
                                <text
                                  x={x}
                                  y={y}
                                  textAnchor="middle"
                                  dominantBaseline="middle"
                                  className="text-white text-xs pointer-events-none font-medium"
                                  fontSize="12"
                                >
                                  {node.type === 'application' ? '📱' : node.type === 'server' ? '🖥️' : '🗄️'}
                                </text>
                                {/* Node label below */}
                                <text
                                  x={x}
                                  y={y + 50}
                                  textAnchor="middle"
                                  className="text-gray-700 text-sm pointer-events-none font-medium"
                                  fontSize="12"
                                >
                                  {node.label.length > 12 ? node.label.substring(0, 12) + '...' : node.label}
                                </text>
                                {/* Edit mode indicator */}
                                {editMode && (
                                  <circle
                                    cx={x + 20}
                                    cy={y - 20}
                                    r="6"
                                    fill="#F59E0B"
                                    stroke="#ffffff"
                                    strokeWidth="2"
                                    className="pointer-events-none"
                                  />
                                )}
                                </g>
                              );
                            })}
                              </>
                            );
                          })()}
                        </svg>
                      )}
                      
                      <div className="mt-4 flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                          {editMode ? 'Click on dependencies to edit them, or nodes to create new dependencies' : 'Click on dependencies to view details'}
                        </div>
                        <button
                          onClick={() => setEditMode(!editMode)}
                          className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                            editMode 
                              ? 'bg-orange-600 text-white hover:bg-orange-700' 
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          <Settings className="h-4 w-4" />
                          <span>{editMode ? 'Exit Edit Mode' : 'Edit Dependencies'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Application Clusters */}
              {applicationClusters.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Application Clusters</h2>
                  <p className="text-sm text-gray-600 mb-6">Groups of tightly coupled applications based on dependency analysis</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {applicationClusters.map((cluster) => (
                      <div key={cluster.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="mb-3">
                          <h3 className="font-medium text-gray-900">{cluster.name}</h3>
                        </div>
                        <div className="space-y-2">
                          <div className="text-sm text-gray-600">
                            <span className="font-medium">{cluster.applications.length}</span> connected applications
                          </div>
                          <div className="text-sm text-gray-600">
                            Complexity: <span className="font-medium">{cluster.complexity_score.toFixed(1)}</span>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-3">
                            {cluster.applications.slice(0, 4).map((app, idx) => (
                              <span key={idx} className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                {app}
                              </span>
                            ))}
                            {cluster.applications.length > 4 && (
                              <span className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded">
                                +{cluster.applications.length - 4} more
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependencies Table */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Cross-Application Dependencies</h3>
                      <p className="text-sm text-gray-600 mt-1">Dependencies that span multiple applications and require coordination</p>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedDependency({
                          source_application: '',
                          target_application: '',
                          impact_level: 'medium',
                          dependency: {
                            dependency_type: 'application_to_server',
                            confidence: 0.8
                          }
                        });
                        setShowReviewModal(true);
                      }}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>Add Dependency</span>
                    </button>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  {filteredDependencies.length === 0 ? (
                    <div className="text-center py-12">
                      <MapPin className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Cross-Application Dependencies Found</h3>
                      <p className="text-gray-600">Applications appear to be isolated or analysis is in progress</p>
                    </div>
                  ) : (
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source Application</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Relationship</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target Application</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Impact Level</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredDependencies.map((dep, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{dep.source_application}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <ArrowRight className="h-4 w-4" />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{dep.target_application}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs rounded-full ${getStrengthColor(dep.impact_level)}`}>
                                {dep.impact_level}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <button 
                                onClick={() => handleReviewDependency(dep)}
                                className="text-blue-600 hover:text-blue-800 transition-colors"
                              >
                                Review
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>

        {/* Agent Interaction Sidebar */}
        <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
          <div className="p-4 space-y-4">
            {/* Agent Clarification Panel */}
            <AgentClarificationPanel 
              pageContext="dependencies"
              refreshTrigger={agentRefreshTrigger}
              onQuestionAnswered={(questionId, response) => {
                console.log('Dependency question answered:', questionId, response);
                // Refresh dependency analysis after agent learning
                fetchDependencyAnalysis();
              }}
            />

            {/* Data Classification Display */}
            <DataClassificationDisplay 
              pageContext="dependencies"
              refreshTrigger={agentRefreshTrigger}
              onClassificationUpdate={(itemId, newClassification) => {
                console.log('Dependency classification updated:', itemId, newClassification);
              }}
            />

            {/* Agent Insights Section */}
            <AgentInsightsSection 
              pageContext="dependencies"
              refreshTrigger={agentRefreshTrigger}
              onInsightAction={(insightId, action) => {
                console.log('Dependency insight action:', insightId, action);
                if (action === 'apply_insight') {
                  // Apply dependency recommendations
                  console.log('Applying dependency insights');
                }
              }}
            />
          </div>
        </div>

        {/* Dependency Review Modal */}
        {showReviewModal && selectedDependency && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-90vh overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Review Dependency</h3>
                  <button
                    onClick={() => setShowReviewModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Source Application */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Application
                  </label>
                  <input
                    type="text"
                    value={selectedDependency.source_application}
                    onChange={(e) => setSelectedDependency({
                      ...selectedDependency,
                      source_application: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Target Application */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Application
                  </label>
                  <input
                    type="text"
                    value={selectedDependency.target_application}
                    onChange={(e) => setSelectedDependency({
                      ...selectedDependency,
                      target_application: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Dependency Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dependency Type
                  </label>
                  <select
                    value={selectedDependency.dependency?.dependency_type || 'application_to_server'}
                    onChange={(e) => setSelectedDependency({
                      ...selectedDependency,
                      dependency: {
                        ...selectedDependency.dependency,
                        dependency_type: e.target.value
                      }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="application_to_server">Application to Server</option>
                    <option value="application_dependency">Application Dependency</option>
                    <option value="database_connection">Database Connection</option>
                    <option value="network_dependency">Network Dependency</option>
                    <option value="infrastructure_dependency">Infrastructure Dependency</option>
                  </select>
                </div>
                
                {/* Impact Level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Impact Level
                  </label>
                  <select
                    value={selectedDependency.impact_level}
                    onChange={(e) => setSelectedDependency({
                      ...selectedDependency,
                      impact_level: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                
                {/* Confidence */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confidence ({Math.round((selectedDependency.dependency?.confidence || 0) * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={selectedDependency.dependency?.confidence || 0}
                    onChange={(e) => setSelectedDependency({
                      ...selectedDependency,
                      dependency: {
                        ...selectedDependency.dependency,
                        confidence: parseFloat(e.target.value)
                      }
                    })}
                    className="w-full"
                  />
                </div>
                
                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <button
                    onClick={() => {
                      // Delete dependency logic
                      console.log('Delete dependency:', selectedDependency);
                      setShowReviewModal(false);
                    }}
                    className="px-4 py-2 text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Delete Dependency
                  </button>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowReviewModal(false)}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSaveDependency(selectedDependency)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dependencies;
