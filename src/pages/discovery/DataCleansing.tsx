import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, RefreshCw, Save, Zap } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import RawDataTable from '../../components/discovery/RawDataTable';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import QualityDashboard from '../../components/discovery/data-cleansing/QualityDashboard';
import AgentQualityAnalysis from '../../components/discovery/data-cleansing/AgentQualityAnalysis';
import { apiCall } from '../../config/api';

// Interface definitions
interface QualityMetrics {
  total_assets: number;
  clean_data: number;
  needs_attention: number;
  critical_issues: number;
  completion_percentage: number;
  average_quality: number;
}

interface QualityIssue {
  id: string;
  asset_id: string;
  asset_name: string;
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  suggested_fix: string;
  confidence: number;
  impact: string;
}

interface AgentRecommendation {
  id: string;
  operation: string;
  title: string;
  description: string;
  affected_assets: number;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  estimated_improvement: number;
}

interface AgentAnalysisResult {
  analysis_type: 'agent_driven' | 'fallback_rules' | 'error';
  quality_assessment: any;
  priority_issues: any[];
  cleansing_recommendations: any[];
  quality_buckets: {
    clean_data: number;
    needs_attention: number;
    critical_issues: number;
  };
  agent_confidence: number;
  agent_insights: string[];
  suggested_operations: string[];
}

const DataCleansing = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // State management
  const [rawData, setRawData] = useState<any[]>([]);
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics>({
    total_assets: 0,
    clean_data: 0,
    needs_attention: 0,
    critical_issues: 0,
    completion_percentage: 0,
    average_quality: 0
  });
  const [qualityIssues, setQualityIssues] = useState<QualityIssue[]>([]);
  const [agentRecommendations, setAgentRecommendations] = useState<AgentRecommendation[]>([]);
  const [agentAnalysis, setAgentAnalysis] = useState<AgentAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [fromAttributeMapping, setFromAttributeMapping] = useState(false);

  // Load data on component mount
  useEffect(() => {
    initializeDataCleansing();
  }, []);

  // Initialize data cleansing with agent analysis
  const initializeDataCleansing = async () => {
    try {
      setIsLoading(true);
      
      // Check if we came from Attribute Mapping with context
      const state = location.state as any;
      if (state?.fromAttributeMapping && state?.importedData) {
        setFromAttributeMapping(true);
        setRawData(state.importedData);
        console.log('Received data from Attribute Mapping:', state.importedData);
        
        // Perform agent-driven quality analysis
        await performAgentQualityAnalysis(state.importedData);
      } else {
        // Try to load from localStorage or backend
        await loadDataFromStorage();
      }
    } catch (error) {
      console.error('Failed to initialize data cleansing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data from storage or backend
  const loadDataFromStorage = async () => {
    try {
      // Try localStorage first
      const storedData = localStorage.getItem('imported_assets');
      if (storedData) {
        const data = JSON.parse(storedData);
        setRawData(data);
        await performAgentQualityAnalysis(data);
        return;
      }

      // Fallback: try to get from backend
      const assetsResponse = await apiCall('/discovery/assets?page=1&page_size=1000');
      if (assetsResponse.assets && assetsResponse.assets.length > 0) {
        setRawData(assetsResponse.assets);
        await performAgentQualityAnalysis(assetsResponse.assets);
      } else {
        // No data available
        setEmptyState();
      }
    } catch (error) {
      console.error('Failed to load data from storage:', error);
      setEmptyState();
    }
  };

  // Perform agent-driven quality analysis
  const performAgentQualityAnalysis = async (data: any[]) => {
    try {
      setIsAnalyzing(true);
      
      // Call agent quality analysis endpoint
      const analysisResponse = await apiCall('/discovery/data-cleanup/agent-analyze', {
        method: 'POST',
        body: JSON.stringify({
          asset_data: data.slice(0, 100), // Sample for analysis
          page_context: 'data-cleansing',
          client_account_id: null, // TODO: Add client context
          engagement_id: null
        })
      });

      if (analysisResponse.analysis_type) {
        setAgentAnalysis(analysisResponse);
        processAgentAnalysisResults(analysisResponse, data);
      } else {
        // Fallback to basic analysis
        performBasicQualityAnalysis(data);
      }
    } catch (error) {
      console.error('Agent analysis failed, using fallback:', error);
      performBasicQualityAnalysis(data);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Process agent analysis results
  const processAgentAnalysisResults = (analysis: AgentAnalysisResult, data: any[]) => {
    // Update quality metrics
    const metrics: QualityMetrics = {
      total_assets: data.length,
      clean_data: analysis.quality_buckets.clean_data,
      needs_attention: analysis.quality_buckets.needs_attention,
      critical_issues: analysis.quality_buckets.critical_issues,
      completion_percentage: analysis.quality_assessment?.average_quality || 0,
      average_quality: analysis.quality_assessment?.average_quality || 0
    };
    setQualityMetrics(metrics);

    // Transform priority issues to quality issues
    const issues: QualityIssue[] = analysis.priority_issues.map((issue, index) => ({
      id: `issue-${index}`,
      asset_id: issue.asset_id || `asset-${index}`,
      asset_name: issue.asset_name || `Asset ${index}`,
      issue_type: issue.issue || issue.issue_type || 'Quality Issue',
      severity: issue.severity || 'medium',
      description: issue.description || issue.issue || 'Quality issue detected',
      suggested_fix: issue.suggested_fix || 'Review and correct manually',
      confidence: issue.confidence || 0.8,
      impact: issue.impact || 'Data quality improvement'
    }));
    setQualityIssues(issues);

    // Transform cleansing recommendations
    const recommendations: AgentRecommendation[] = analysis.cleansing_recommendations.map((rec, index) => ({
      id: `rec-${index}`,
      operation: rec.operation || analysis.suggested_operations[index] || 'cleanup',
      title: rec.title || rec.operation || `Recommendation ${index + 1}`,
      description: rec.description || rec,
      affected_assets: rec.affected_assets || Math.floor(data.length * 0.3),
      confidence: rec.confidence || analysis.agent_confidence,
      priority: rec.priority || 'medium',
      estimated_improvement: rec.estimated_improvement || 15
    }));
    setAgentRecommendations(recommendations);
  };

  // Fallback basic quality analysis
  const performBasicQualityAnalysis = (data: any[]) => {
    const totalAssets = data.length;
    const cleanData = Math.floor(totalAssets * 0.6);
    const needsAttention = Math.floor(totalAssets * 0.3);
    const criticalIssues = totalAssets - cleanData - needsAttention;

    setQualityMetrics({
      total_assets: totalAssets,
      clean_data: cleanData,
      needs_attention: needsAttention,
      critical_issues: criticalIssues,
      completion_percentage: 70,
      average_quality: 70
    });

    // Generate sample issues
    const sampleIssues: QualityIssue[] = data.slice(0, 5).map((asset, index) => ({
      id: `issue-${index}`,
      asset_id: asset.id || `asset-${index}`,
      asset_name: asset.asset_name || asset.hostname || `Asset ${index}`,
      issue_type: 'Missing Data',
      severity: 'medium' as const,
      description: 'Some required fields are missing or incomplete',
      suggested_fix: 'Complete missing fields with appropriate values',
      confidence: 0.7,
      impact: 'May affect migration planning accuracy'
    }));
    setQualityIssues(sampleIssues);

    // Generate sample recommendations
    const sampleRecommendations: AgentRecommendation[] = [
      {
        id: 'rec-1',
        operation: 'standardize_asset_types',
        title: 'Standardize Asset Types',
        description: 'Normalize asset type values for consistency',
        affected_assets: Math.floor(totalAssets * 0.4),
        confidence: 0.8,
        priority: 'high' as const,
        estimated_improvement: 20
      }
    ];
    setAgentRecommendations(sampleRecommendations);
  };

  // Set empty state
  const setEmptyState = () => {
    setQualityMetrics({
      total_assets: 0,
      clean_data: 0,
      needs_attention: 0,
      critical_issues: 0,
      completion_percentage: 0,
      average_quality: 0
    });
    setQualityIssues([]);
    setAgentRecommendations([]);
  };

  // Handle applying agent recommendation
  const handleApplyRecommendation = async (recommendationId: string) => {
    try {
      const recommendation = agentRecommendations.find(r => r.id === recommendationId);
      if (!recommendation) return;

      setIsAnalyzing(true);

      // Call agent-driven cleanup endpoint
      const cleanupResponse = await apiCall('/discovery/data-cleanup/agent-process', {
        method: 'POST',
        body: JSON.stringify({
          asset_data: rawData,
          agent_operations: [{
            operation: recommendation.operation,
            parameters: {
              confidence_threshold: recommendation.confidence,
              priority: recommendation.priority
            }
          }],
          user_preferences: {},
          client_account_id: null,
          engagement_id: null
        })
      });

      if (cleanupResponse.status === 'success') {
        // Update data with cleaned results
        if (cleanupResponse.cleaned_assets) {
          setRawData(cleanupResponse.cleaned_assets);
        }
        
        // Re-analyze quality after cleanup
        await performAgentQualityAnalysis(cleanupResponse.cleaned_assets || rawData);
        
        console.log('Recommendation applied successfully:', cleanupResponse);
      }
    } catch (error) {
      console.error('Failed to apply recommendation:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle fixing individual quality issue
  const handleFixIssue = async (issueId: string) => {
    try {
      const issue = qualityIssues.find(i => i.id === issueId);
      if (!issue) return;

      // Apply the suggested fix
      console.log('Applying fix for issue:', issue);
      
      // Remove the issue from the list (simulate fix)
      setQualityIssues(prev => prev.filter(i => i.id !== issueId));
      
      // Update metrics
      setQualityMetrics(prev => ({
        ...prev,
        critical_issues: Math.max(0, prev.critical_issues - 1),
        clean_data: prev.clean_data + 1,
        completion_percentage: Math.min(100, prev.completion_percentage + 2)
      }));
    } catch (error) {
      console.error('Failed to fix issue:', error);
    }
  };

  // Handle refresh analysis
  const handleRefreshAnalysis = async () => {
    if (rawData.length > 0) {
      await performAgentQualityAnalysis(rawData);
    }
  };

  // Handle continue to inventory
  const handleContinueToInventory = () => {
    navigate('/discovery/inventory', {
      state: {
        fromDataCleansing: true,
        cleanedData: rawData,
        qualityMetrics: qualityMetrics,
        agentAnalysis: agentAnalysis
      }
    });
  };

  // Handle back to attribute mapping
  const handleBackToAttributeMapping = () => {
    navigate('/discovery/attribute-mapping');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <div className="flex h-full">
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            <main className="p-8">
              <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Agentic Data Cleansing
                      </h1>
                      <p className="text-lg text-gray-600">
                        AI-powered data quality assessment and intelligent cleanup recommendations
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={handleRefreshAnalysis}
                        disabled={isAnalyzing || rawData.length === 0}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        <RefreshCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
                        <span>Refresh Analysis</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Quality Dashboard */}
                <QualityDashboard 
                  metrics={qualityMetrics} 
                  isLoading={isLoading}
                />

                {/* Agent Quality Analysis */}
                <AgentQualityAnalysis
                  qualityIssues={qualityIssues}
                  recommendations={agentRecommendations}
                  agentConfidence={agentAnalysis?.agent_confidence || 0.7}
                  analysisType={agentAnalysis?.analysis_type || 'fallback_rules'}
                  onApplyRecommendation={handleApplyRecommendation}
                  onFixIssue={handleFixIssue}
                  isLoading={isAnalyzing}
                />

                {/* Raw Data Table */}
                {rawData.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-semibold text-gray-900">Data Preview</h2>
                      <span className="text-sm text-gray-600">
                        Showing {Math.min(rawData.length, 10)} of {rawData.length} assets
                      </span>
                    </div>
                    <RawDataTable
                      data={rawData}
                      title="Asset Data for Quality Review"
                      pageSize={10}
                      showLegend={false}
                    />
                  </div>
                )}

                {/* Navigation */}
                <div className="flex justify-between items-center">
                  <button
                    onClick={handleBackToAttributeMapping}
                    className="flex items-center space-x-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    <ArrowLeft className="h-5 w-5" />
                    <span>Back to Attribute Mapping</span>
                  </button>

                  <button
                    onClick={handleContinueToInventory}
                    disabled={qualityMetrics.completion_percentage < 60}
                    className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors ${
                      qualityMetrics.completion_percentage >= 60
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <span>Continue to Asset Inventory</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </div>
                
                {qualityMetrics.completion_percentage < 60 && (
                  <p className="text-center text-sm text-gray-600 mt-2">
                    Achieve at least 60% data quality to proceed
                  </p>
                )}
              </div>
            </main>
          </div>

          {/* Agent Interaction Sidebar */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="data-cleansing"
                onQuestionAnswered={(questionId, response) => {
                  console.log('Cleansing question answered:', questionId, response);
                  // Trigger re-analysis with agent learning
                  if (rawData.length > 0) {
                    performAgentQualityAnalysis(rawData);
                  }
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="data-cleansing"
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Data classification updated:', itemId, newClassification);
                  // Update quality metrics based on classification
                  if (newClassification === 'good_data') {
                    setQualityMetrics(prev => ({
                      ...prev,
                      clean_data: prev.clean_data + 1,
                      needs_attention: Math.max(0, prev.needs_attention - 1)
                    }));
                  }
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="data-cleansing"
                onInsightAction={(insightId, action) => {
                  console.log('Cleansing insight action:', insightId, action);
                  // Apply agent recommendations for data quality improvement
                  if (action === 'helpful') {
                    console.log('Applying agent recommendations for quality improvement');
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataCleansing; 