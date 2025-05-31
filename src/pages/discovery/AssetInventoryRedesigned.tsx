import React, { useState, useEffect } from 'react';
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
import { apiCall } from '../../config/api';

interface AssetInventoryData {
  status: string;
  analysis_timestamp: string;
  total_assets: number;
  asset_metrics: {
    total_count: number;
    by_type: Record<string, number>;
    by_environment: Record<string, number>;
    by_criticality: Record<string, number>;
    by_status: Record<string, number>;
  };
  workflow_analysis: {
    discovery: Record<string, number>;
    mapping: Record<string, number>;
    cleanup: Record<string, number>;
    assessment_ready: Record<string, number>;
    completion_percentages: {
      discovery: number;
      mapping: number;
      cleanup: number;
      assessment_ready: number;
    };
  };
  data_quality: {
    overall_score: number;
    completeness_by_field: Record<string, number>;
    missing_critical_data: Array<{
      asset_id: string;
      asset_name: string;
      missing_fields: string[];
      completeness: number;
    }>;
  };
  migration_readiness: {
    ready_for_assessment: number;
    needs_more_data: number;
    has_dependencies: number;
    needs_modernization: number;
    readiness_by_type: Record<string, any>;
  };
  dependency_analysis: {
    total_dependencies: number;
    application_dependencies: number;
    server_dependencies: number;
    database_dependencies: number;
    complex_dependency_chains: Array<any>;
    orphaned_assets: string[];
  };
  ai_insights: {
    available: boolean;
    analysis_result?: any;
    confidence_score?: number;
  };
  recommendations: Array<{
    type: string;
    priority: string;
    title: string;
    description: string;
    action: string;
    affected_assets?: number;
  }>;
  assessment_ready: {
    ready: boolean;
    overall_score: number;
    criteria: {
      mapping_completion: { current: number; required: number; met: boolean };
      cleanup_completion: { current: number; required: number; met: boolean };
      data_quality: { current: number; required: number; met: boolean };
    };
    next_steps: string[];
  };
}

const AssetInventoryRedesigned: React.FC = () => {
  const [data, setData] = useState<AssetInventoryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchInventoryAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall('/api/v1/discovery/assets/comprehensive-analysis', {
        method: 'GET'
      });
      
      setData(response);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      setError(`Failed to load asset inventory analysis: ${err}`);
      console.error('Asset inventory analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInventoryAnalysis();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'ready':
        return 'text-green-600 bg-green-100';
      case 'in_progress':
      case 'partial':
        return 'text-yellow-600 bg-yellow-100';
      case 'pending':
      case 'not_ready':
        return 'text-gray-600 bg-gray-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-100 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const ProgressBar: React.FC<{ percentage: number; color?: string }> = ({ 
    percentage, 
    color = 'bg-blue-500' 
  }) => (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full transition-all duration-300 ${color}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  );

  const MetricCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color?: string;
    subtitle?: string;
  }> = ({ title, value, icon, color = 'text-blue-600', subtitle }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full bg-gray-50 ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-red-800">Error Loading Asset Inventory</h3>
                <p className="text-red-600 mt-1">{error}</p>
                <button
                  onClick={fetchInventoryAnalysis}
                  className="mt-3 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Asset Inventory Analysis</h1>
            <p className="text-gray-600 mt-1">
              Comprehensive migration readiness assessment • Last updated: {lastUpdated}
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={fetchInventoryAnalysis}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Analysis
            </button>
          </div>
        </div>

        {/* Assessment Readiness Banner */}
        <div className={`rounded-lg border-2 p-6 mb-8 ${
          data.assessment_ready.ready 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {data.assessment_ready.ready ? (
                <CheckCircle className="h-8 w-8 text-green-600 mr-4" />
              ) : (
                <Clock className="h-8 w-8 text-yellow-600 mr-4" />
              )}
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {data.assessment_ready.ready 
                    ? '🎉 Ready for Assessment Phase!' 
                    : '⚠️ Assessment Preparation Needed'
                  }
                </h2>
                <p className="text-gray-600 mt-1">
                  Overall readiness score: {data.assessment_ready.overall_score.toFixed(1)}%
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {data.assessment_ready.ready ? 'PROCEED' : 'PREPARE'}
              </div>
            </div>
          </div>
          
          {/* Readiness Criteria */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            {Object.entries(data.assessment_ready.criteria).map(([key, criteria]) => (
              <div key={key} className="bg-white rounded-lg p-4 border">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">
                    {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  {criteria.met ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <Clock className="h-5 w-5 text-yellow-600" />
                  )}
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  {criteria.current.toFixed(1)}% / {criteria.required}% required
                </div>
                <ProgressBar 
                  percentage={criteria.current} 
                  color={criteria.met ? 'bg-green-500' : 'bg-yellow-500'}
                />
              </div>
            ))}
          </div>

          {/* Next Steps */}
          {data.assessment_ready.next_steps.length > 0 && (
            <div className="mt-6 p-4 bg-white rounded-lg border">
              <h3 className="font-medium text-gray-900 mb-3">📋 Next Steps:</h3>
              <ul className="space-y-2">
                {data.assessment_ready.next_steps.map((step, index) => (
                  <li key={index} className="flex items-center text-sm text-gray-700">
                    <ArrowRight className="h-4 w-4 mr-2 text-blue-600" />
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Assets"
            value={data.total_assets}
            icon={<Layers className="h-6 w-6" />}
            color="text-blue-600"
            subtitle="Discovered and cataloged"
          />
          <MetricCard
            title="Data Quality Score"
            value={`${data.data_quality.overall_score.toFixed(1)}%`}
            icon={<BarChart3 className="h-6 w-6" />}
            color="text-green-600"
            subtitle="Critical fields completeness"
          />
          <MetricCard
            title="Assessment Ready"
            value={data.migration_readiness.ready_for_assessment}
            icon={<Target className="h-6 w-6" />}
            color="text-purple-600"
            subtitle="Ready for 6R analysis"
          />
          <MetricCard
            title="Dependencies"
            value={data.dependency_analysis.total_dependencies}
            icon={<Activity className="h-6 w-6" />}
            color="text-orange-600"
            subtitle="Total relationships mapped"
          />
        </div>

        {/* Workflow Progress */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-blue-600" />
              Workflow Progress
            </h3>
            <div className="space-y-4">
              {Object.entries(data.workflow_analysis.completion_percentages).map(([phase, percentage]) => (
                <div key={phase}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-700">
                      {phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-gray-600">{percentage.toFixed(1)}%</span>
                  </div>
                  <ProgressBar 
                    percentage={percentage}
                    color={percentage >= 80 ? 'bg-green-500' : percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
              Asset Distribution
            </h3>
            <div className="space-y-3">
              {Object.entries(data.asset_metrics.by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center">
                    {type === 'Application' && <FileText className="h-4 w-4 mr-2 text-blue-600" />}
                    {type === 'Server' && <Server className="h-4 w-4 mr-2 text-green-600" />}
                    {type === 'Database' && <Database className="h-4 w-4 mr-2 text-purple-600" />}
                    {!['Application', 'Server', 'Database'].includes(type) && <Settings className="h-4 w-4 mr-2 text-gray-600" />}
                    <span className="text-sm font-medium text-gray-700">{type}</span>
                  </div>
                  <span className="text-sm text-gray-600">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Data Quality & Dependencies */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-yellow-600" />
              Data Quality by Field
            </h3>
            <div className="space-y-3">
              {Object.entries(data.data_quality.completeness_by_field).map(([field, completeness]) => (
                <div key={field}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      {field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-gray-600">{completeness.toFixed(1)}%</span>
                  </div>
                  <ProgressBar 
                    percentage={completeness}
                    color={completeness >= 80 ? 'bg-green-500' : completeness >= 50 ? 'bg-yellow-500' : 'bg-red-500'}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <MapPin className="h-5 w-5 mr-2 text-purple-600" />
              Dependency Analysis
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Application Dependencies</span>
                <span className="text-sm text-gray-600">{data.dependency_analysis.application_dependencies}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Server Dependencies</span>
                <span className="text-sm text-gray-600">{data.dependency_analysis.server_dependencies}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Database Dependencies</span>
                <span className="text-sm text-gray-600">{data.dependency_analysis.database_dependencies}</span>
              </div>
              {data.dependency_analysis.orphaned_assets.length > 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <span className="text-sm font-medium text-yellow-800">
                    ⚠️ {data.dependency_analysis.orphaned_assets.length} Orphaned Assets
                  </span>
                  <p className="text-xs text-yellow-700 mt-1">Applications with no mapped dependencies</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {data.recommendations.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Lightbulb className="h-5 w-5 mr-2 text-yellow-600" />
              AI Recommendations
            </h3>
            <div className="space-y-4">
              {data.recommendations.map((rec, index) => (
                <div 
                  key={index} 
                  className={`p-4 rounded-lg border-2 ${getPriorityColor(rec.priority)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium mr-3 ${getPriorityColor(rec.priority)}`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <h4 className="font-medium text-gray-900">{rec.title}</h4>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                      <p className="text-sm font-medium text-gray-900">
                        🎯 Action: {rec.action}
                      </p>
                      {rec.affected_assets && (
                        <p className="text-xs text-gray-600 mt-1">
                          Affects {rec.affected_assets} assets
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Insights */}
        {data.ai_insights.available && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-purple-600" />
              AI-Powered Insights
              {data.ai_insights.confidence_score && (
                <span className="ml-2 text-sm text-gray-600">
                  (Confidence: {(data.ai_insights.confidence_score * 100).toFixed(0)}%)
                </span>
              )}
            </h3>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-sm text-purple-800">
                🤖 AI analysis complete. {data.total_assets} assets analyzed for migration readiness.
                Review recommendations above and follow the suggested next steps.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetInventoryRedesigned; 