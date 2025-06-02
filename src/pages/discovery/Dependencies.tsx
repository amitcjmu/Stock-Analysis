import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { Network, Database, Server, ArrowRight, RefreshCw, Filter, Search, MapPin, Activity, AlertTriangle, CheckCircle, Clock, Settings, Eye } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

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
      validated_dependencies: number;
      needs_review: number;
      confidence_distribution: Record<string, number>;
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
  };
  clarification_questions: any[];
  dependency_recommendations: any[];
}

const Dependencies = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [dependencyData, setDependencyData] = useState<DependencyAnalysisData | null>(null);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedStrength, setSelectedStrength] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showGraph, setShowGraph] = useState(true);
  const [graphViewMode, setGraphViewMode] = useState<'applications' | 'infrastructure'>('applications');

  useEffect(() => {
    fetchDependencyAnalysis();
    // Trigger agent analysis after initial data load
    setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
  }, []);

  const fetchDependencyAnalysis = async () => {
    try {
      setIsLoading(true);
      
      // Get assets for dependency analysis
      const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`);
      const assets = assetsResponse?.assets || [];
      
      // Get applications for cross-app mapping
      let applications = [];
      try {
        const applicationsResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS);
        applications = applicationsResponse?.applications || [];
      } catch (appError) {
        console.warn('Could not fetch applications for dependency analysis:', appError);
      }

      // Perform dependency analysis
      const dependencyAnalysis = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.DEPENDENCY_ANALYSIS, {
        method: 'POST',
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
        setDependencyData(dependencyAnalysis.dependency_intelligence);
        
        // Trigger agent analysis with dependency context
        await triggerAgentAnalysis(dependencyAnalysis.dependency_intelligence);
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

  const filteredDependencies = dependencyData?.cross_application_mapping?.cross_app_dependencies || [];
  const dependencyGraph = dependencyData?.cross_application_mapping?.dependency_graph;
  const applicationClusters = dependencyData?.cross_application_mapping?.application_clusters || [];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex">
        <div className="flex-1">
          <main className="p-8">
            <div className="max-w-full mx-auto">
              {/* Header */}
              <div className="mb-8">
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
              {showGraph && dependencyGraph && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Dependency Graph</h2>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center bg-gray-50">
                    <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Interactive Dependency Graph</h3>
                    <p className="text-gray-600 mb-4">
                      {dependencyGraph.nodes.length} nodes, {dependencyGraph.edges.length} connections
                    </p>
                    <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-blue-500 rounded"></div>
                        <span>Applications ({dependencyGraph.nodes.filter(n => n.type === 'application').length})</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-green-500 rounded"></div>
                        <span>Servers ({dependencyGraph.nodes.filter(n => n.type === 'server').length})</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-purple-500 rounded"></div>
                        <span>Databases ({dependencyGraph.nodes.filter(n => n.type === 'database').length})</span>
                      </div>
                    </div>
                    <div className="mt-4 text-sm text-gray-500">
                      <p>Graph visualization will be implemented with D3.js or similar library</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Application Clusters */}
              {applicationClusters.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Application Clusters</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {applicationClusters.map((cluster) => (
                      <div key={cluster.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-medium text-gray-900">{cluster.name}</h3>
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            Wave {cluster.migration_sequence}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <div className="text-sm text-gray-600">
                            {cluster.applications.length} applications
                          </div>
                          <div className="text-sm text-gray-600">
                            Complexity: <span className="font-medium">{cluster.complexity_score.toFixed(1)}</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {cluster.applications.slice(0, 3).map((app, idx) => (
                              <span key={idx} className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                                {app}
                              </span>
                            ))}
                            {cluster.applications.length > 3 && (
                              <span className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded">
                                +{cluster.applications.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Migration Recommendations */}
              {dependencyData?.impact_analysis?.migration_recommendations && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Migration Recommendations</h2>
                  <div className="space-y-3">
                    {dependencyData.impact_analysis.migration_recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                        <p className="text-sm text-blue-800">{recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependencies Table */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Cross-Application Dependencies</h3>
                  <p className="text-sm text-gray-600 mt-1">Dependencies that span multiple applications and require coordination</p>
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
                              <button className="text-blue-600 hover:text-blue-800">
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
      </div>
    </div>
  );
};

export default Dependencies;
