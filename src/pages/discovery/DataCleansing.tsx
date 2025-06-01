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
import { apiCall, API_CONFIG } from '../../config/api';

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
  current_value?: string;
  field_name?: string;
}

interface AgentRecommendation {
  id: string;
  operation: string;
  title: string;
  description: string;
  examples: string[];
  affected_assets: number;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  estimated_improvement: number;
  change_details: {
    operation_type: string;
    fields_affected: string[];
    sample_changes: string[];
  };
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
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

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
        
        // Fix 2: Trigger agent analysis for panels with relatedCMDBrecords detection
        await triggerAgentPanelAnalysis(state.importedData);
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

  // Load data from database or backend
  const loadDataFromStorage = async () => {
    try {
      // Priority 1: Try to get latest import from database
      console.log('Loading latest import from database for data cleansing');
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
        if (response.success && response.data.length > 0) {
          console.log(`Loaded ${response.data.length} records from latest import session ${response.import_session_id}`);
          setRawData(response.data);
          await performAgentQualityAnalysis(response.data);
          return;
        }
      } catch (error) {
        console.warn('Failed to load data from database, trying backend assets:', error);
      }

      // Priority 2: Fallback to existing assets in backend
      const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`);
      if (assetsResponse.assets && assetsResponse.assets.length > 0) {
        console.log(`Loaded ${assetsResponse.assets.length} assets from backend inventory`);
        setRawData(assetsResponse.assets);
        await performAgentQualityAnalysis(assetsResponse.assets);
        return;
      }

      // Priority 3: Fallback to localStorage for compatibility (temporary)
      console.log('Falling back to localStorage for data cleansing');
      const storedData = localStorage.getItem('imported_assets');
      if (storedData) {
        const data = JSON.parse(storedData);
        console.log(`Loaded ${data.length} records from localStorage fallback`);
        setRawData(data);
        await performAgentQualityAnalysis(data);
        return;
      }

      // No data available
      console.warn('No data found for data cleansing');
      setEmptyState();
    } catch (error) {
      console.error('Failed to load data from all sources:', error);
      setEmptyState();
    }
  };

  // Perform agent-driven quality analysis
  const performAgentQualityAnalysis = async (data: any[]) => {
    try {
      setIsAnalyzing(true);
      
      // Call agent quality analysis endpoint
      const analysisResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.DATA_CLEANUP_ANALYZE, {
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
    // Fix 1: Correct Data Quality Progress % calculation
    // The completion_percentage should be based on assets WITHOUT issues, not total quality score
    const assetsWithIssues = analysis.quality_buckets.critical_issues + analysis.quality_buckets.needs_attention;
    const cleanAssets = analysis.quality_buckets.clean_data;
    const totalAssets = data.length;
    
    // Correct calculation: percentage of clean assets to total assets
    const correctCompletionPercentage = totalAssets > 0 ? Math.round((cleanAssets / totalAssets) * 100) : 0;
    
    // Update quality metrics with corrected calculation
    const metrics: QualityMetrics = {
      total_assets: totalAssets,
      clean_data: analysis.quality_buckets.clean_data,
      needs_attention: analysis.quality_buckets.needs_attention,
      critical_issues: analysis.quality_buckets.critical_issues,
      completion_percentage: correctCompletionPercentage, // Fixed: now shows % of assets without issues
      average_quality: analysis.quality_assessment?.average_quality || 0
    };
    setQualityMetrics(metrics);

    // Transform priority issues to quality issues with enhanced details
    const issues: QualityIssue[] = analysis.priority_issues.map((issue, index) => ({
      id: `issue-${index}`,
      asset_id: issue.asset_id || `asset-${index}`,
      asset_name: issue.asset_name || `Asset ${index}`,
      issue_type: issue.issue || issue.issue_type || 'Quality Issue',
      severity: issue.severity || 'medium',
      description: issue.description || issue.issue || 'Quality issue detected',
      suggested_fix: issue.suggested_fix || 'Review and correct manually',
      confidence: issue.confidence || 0.8,
      impact: issue.impact || 'Data quality improvement',
      // Fix 3: Add inline editing support
      current_value: issue.current_value || '',
      field_name: issue.field_name || 'unknown_field'
    }));
    setQualityIssues(issues);

    // Fix 4: Enhanced agent recommendations with detailed explanations
    const recommendations: AgentRecommendation[] = analysis.cleansing_recommendations.map((rec, index) => {
      // Enhance recommendations with specific details and examples
      let enhancedDescription: string;
      let examples: string[] = [];
      
      if (typeof rec === 'string') {
        switch (rec) {
          case 'standardize_asset_types':
            enhancedDescription = 'Standardize inconsistent asset type values to use consistent naming conventions (e.g., "Server", "Database", "Application")';
            examples = [
              'Change "srv" → "Server"',
              'Change "db" → "Database"', 
              'Change "app" → "Application"'
            ];
            break;
          case 'normalize_environments':
            enhancedDescription = 'Normalize environment names to standard values (Production, Staging, Development, Test)';
            examples = [
              'Change "prod" → "Production"',
              'Change "dev" → "Development"',
              'Change "qa" → "Test"'
            ];
            break;
          case 'fix_hostname_format':
            enhancedDescription = 'Standardize hostname formats to follow consistent naming patterns and remove invalid characters';
            examples = [
              'Change "server01.local" → "server01"',
              'Change "SRV_001" → "srv-001"',
              'Remove special characters and standardize case'
            ];
            break;
          default:
            enhancedDescription = rec;
        }
      } else {
        // Handle object type recommendations
        enhancedDescription = rec.description || `Recommendation ${index + 1}`;
        if (rec.examples) {
          examples = Array.isArray(rec.examples) ? rec.examples : [];
        }
      }
      
      return {
        id: `rec-${index}`,
        operation: (typeof rec === 'object' ? rec.operation : undefined) || analysis.suggested_operations[index] || 'cleanup',
        title: (typeof rec === 'object' ? rec.title : undefined) || `Recommendation ${index + 1}`,
        description: enhancedDescription,
        examples: examples, // Add examples for clarity
        affected_assets: (typeof rec === 'object' ? rec.affected_assets : undefined) || Math.floor(data.length * 0.3),
        confidence: (typeof rec === 'object' ? rec.confidence : undefined) || analysis.agent_confidence,
        priority: (typeof rec === 'object' ? rec.priority : undefined) || 'medium',
        estimated_improvement: (typeof rec === 'object' ? rec.estimated_improvement : undefined) || 15,
        // Add specific change details
        change_details: {
          operation_type: (typeof rec === 'object' ? rec.operation : rec) || 'standardization',
          fields_affected: (typeof rec === 'object' ? rec.fields_affected : undefined) || ['asset_type', 'environment'],
          sample_changes: examples
        }
      };
    });
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
        examples: [],
        affected_assets: Math.floor(totalAssets * 0.4),
        confidence: 0.8,
        priority: 'high' as const,
        estimated_improvement: 20,
        change_details: {
          operation_type: 'standardization',
          fields_affected: ['asset_type'],
          sample_changes: []
        }
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

  // Fix 3: Enhanced fix issue handler with inline editing support
  const handleFixIssue = async (issueId: string, customValue?: string) => {
    try {
      const issue = qualityIssues.find(i => i.id === issueId);
      if (!issue) return;

      // If custom value provided, use it; otherwise use suggested fix
      const valueToApply = customValue || issue.suggested_fix;
      console.log('Applying fix for issue:', issue, 'with value:', valueToApply);
      
      // Apply the fix to the actual data
      if (issue.field_name && rawData.length > 0) {
        const updatedData = rawData.map(asset => {
          if (asset.asset_name === issue.asset_name || asset.hostname === issue.asset_name) {
            return {
              ...asset,
              [issue.field_name]: valueToApply
            };
          }
          return asset;
        });
        setRawData(updatedData);
      }
      
      // Remove the issue from the list
      setQualityIssues(prev => prev.filter(i => i.id !== issueId));
      
      // Update metrics with correct calculation
      setQualityMetrics(prev => {
        const newCriticalIssues = Math.max(0, prev.critical_issues - 1);
        const newCleanData = prev.clean_data + 1;
        const newCompletionPercentage = prev.total_assets > 0 ? 
          Math.round((newCleanData / prev.total_assets) * 100) : 0;
        
        return {
          ...prev,
          critical_issues: newCriticalIssues,
          clean_data: newCleanData,
          completion_percentage: newCompletionPercentage // Correct calculation
        };
      });
    } catch (error) {
      console.error('Failed to fix issue:', error);
    }
  };

  // Fix 4: Enhanced apply recommendation with detailed feedback
  const handleApplyRecommendation = async (recommendationId: string) => {
    try {
      const recommendation = agentRecommendations.find(r => r.id === recommendationId);
      if (!recommendation) return;

      console.log('Applying recommendation:', recommendation);
      
      // Apply the recommendation to the data based on operation type
      if (recommendation.change_details && rawData.length > 0) {
        const { operation_type, fields_affected } = recommendation.change_details;
        
        let updatedData = [...rawData];
        let changesApplied = 0;
        
        switch (operation_type) {
          case 'standardization':
            updatedData = rawData.map(asset => {
              let updated = { ...asset };
              let changed = false;
              
              fields_affected.forEach(field => {
                if (updated[field]) {
                  const originalValue = updated[field];
                  const standardizedValue = standardizeValue(field, originalValue);
                  if (standardizedValue !== originalValue) {
                    updated[field] = standardizedValue;
                    changed = true;
                  }
                }
              });
              
              if (changed) changesApplied++;
              return updated;
            });
            break;
          default:
            console.log('Unknown operation type:', operation_type);
        }
        
        if (changesApplied > 0) {
          setRawData(updatedData);
          
          // Update metrics
          setQualityMetrics(prev => {
            const newCleanData = Math.min(prev.total_assets, prev.clean_data + changesApplied);
            const newNeedsAttention = Math.max(0, prev.needs_attention - changesApplied);
            const newCompletionPercentage = prev.total_assets > 0 ? 
              Math.round((newCleanData / prev.total_assets) * 100) : 0;
            
            return {
              ...prev,
              clean_data: newCleanData,
              needs_attention: newNeedsAttention,
              completion_percentage: newCompletionPercentage
            };
          });
          
          // Remove the applied recommendation
          setAgentRecommendations(prev => prev.filter(r => r.id !== recommendationId));
          
          alert(`Recommendation applied successfully! ${changesApplied} assets updated.`);
        }
      }
    } catch (error) {
      console.error('Failed to apply recommendation:', error);
      alert('Failed to apply recommendation. Please try again.');
    }
  };

  // Helper function to standardize values
  const standardizeValue = (field: string, value: string) => {
    if (!value || typeof value !== 'string') return value;
    
    const lowerValue = value.toLowerCase().trim();
    
    switch (field) {
      case 'asset_type':
        if (['srv', 'server', 'host'].includes(lowerValue)) return 'Server';
        if (['db', 'database', 'sql'].includes(lowerValue)) return 'Database';
        if (['app', 'application', 'service'].includes(lowerValue)) return 'Application';
        break;
      case 'environment':
        if (['prod', 'production', 'live'].includes(lowerValue)) return 'Production';
        if (['dev', 'development'].includes(lowerValue)) return 'Development';
        if (['test', 'testing', 'qa'].includes(lowerValue)) return 'Test';
        if (['stage', 'staging', 'preprod'].includes(lowerValue)) return 'Staging';
        break;
    }
    
    return value;
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

  // Fix 2: Trigger agent panel analysis for auto-population
  const triggerAgentPanelAnalysis = async (data: any[]) => {
    try {
      // Check for relatedCMDBrecords that should be mapped as dependencies
      const assetsWithRelatedRecords = data.filter(asset => 
        asset.relatedCMDBrecords || asset.related_cmdb_records || asset.dependencies
      );

      if (assetsWithRelatedRecords.length > 0) {
        // Generate agent clarifications for unmapped dependencies
        const clarificationRequest = {
          page_context: 'data-cleansing',
          analysis_type: 'dependency_mapping_review',
          data_source: {
            assets_with_dependencies: assetsWithRelatedRecords,
            total_assets: data.length,
            context: 'data_cleansing_review'
          }
        };

        // Call agent clarification endpoint
        const clarificationResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATION, {
          method: 'POST',
          body: JSON.stringify(clarificationRequest)
        });

        if (clarificationResponse.status === 'success') {
          console.log('Agent clarifications generated for dependency mapping');
        }
      }

      // Generate data classifications for quality review
      const classificationRequest = {
        page_context: 'data-cleansing',
        data_items: data.slice(0, 20), // Sample for classification
        classification_focus: 'quality_assessment'
      };

      const classificationResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS, {
        method: 'POST',
        body: JSON.stringify(classificationRequest)
      });

      if (classificationResponse.status === 'success') {
        console.log('Data classifications generated for quality review');
      }

      // Trigger agent refresh to populate panels
      setAgentRefreshTrigger(prev => prev + 1);
      
    } catch (error) {
      console.error('Failed to trigger agent panel analysis:', error);
    }
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
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Cleansing question answered:', questionId, response);
                  // Fix 5: Handle dependency mapping clarifications
                  if (response.includes('dependency') || response.includes('related')) {
                    // Update raw data to include dependency mappings
                    const updatedData = rawData.map(asset => {
                      if (asset.relatedCMDBrecords && !asset.dependencies) {
                        return {
                          ...asset,
                          dependencies: asset.relatedCMDBrecords.split(',').map((dep: string) => dep.trim())
                        };
                      }
                      return asset;
                    });
                    setRawData(updatedData);
                  }
                  // Trigger re-analysis with agent learning
                  if (rawData.length > 0) {
                    performAgentQualityAnalysis(rawData);
                  }
                  // Refresh agent panels
                  setAgentRefreshTrigger(prev => prev + 1);
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="data-cleansing"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Data classification updated:', itemId, newClassification);
                  // Update quality metrics based on classification
                  if (newClassification === 'good_data') {
                    setQualityMetrics(prev => ({
                      ...prev,
                      clean_data: prev.clean_data + 1,
                      needs_attention: Math.max(0, prev.needs_attention - 1),
                      completion_percentage: prev.total_assets > 0 ? 
                        Math.round(((prev.clean_data + 1) / prev.total_assets) * 100) : 0
                    }));
                  }
                  // Refresh agent panels
                  setAgentRefreshTrigger(prev => prev + 1);
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="data-cleansing"
                refreshTrigger={agentRefreshTrigger}
                isProcessing={isAnalyzing}
                onInsightAction={(insightId, action) => {
                  console.log('Cleansing insight action:', insightId, action);
                  // Apply agent recommendations for data quality improvement
                  if (action === 'helpful') {
                    console.log('Applying agent recommendations for quality improvement');
                    // Boost quality metrics slightly for helpful insights
                    setQualityMetrics(prev => ({
                      ...prev,
                      average_quality: Math.min(100, prev.average_quality + 2)
                    }));
                  }
                  // Refresh agent panels
                  setAgentRefreshTrigger(prev => prev + 1);
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