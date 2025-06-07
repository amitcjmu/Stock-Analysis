import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { apiCall, API_CONFIG } from '../config/api';
import { useAppContext } from './useContext';
import { QualityIssue } from '../components/discovery/data-cleansing/QualityIssuesSummary';
import { AgentRecommendation } from '../components/discovery/data-cleansing/RecommendationsSummary';
import { ActionFeedback } from '../components/discovery/data-cleansing/ActionFeedback';

interface QualityMetrics {
  total_assets: number;
  clean_data: number;
  needs_attention: number;
  critical_issues: number;
  completion_percentage: number;
  average_quality: number;
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
  total_assets: number;
}

export const useDataCleansing = () => {
  const location = useLocation();
  const { getContextHeaders } = useAppContext();

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
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<ActionFeedback | null>(null);

  // Clear feedback after 5 seconds
  useEffect(() => {
    if (actionFeedback) {
      const timer = setTimeout(() => setActionFeedback(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [actionFeedback]);

  // Load data on component mount
  useEffect(() => {
    const initializeDataCleansing = async () => {
      try {
        setIsLoading(true);
        
        // Check if we came from Attribute Mapping with context
        const state = location.state as any;
        console.log('DataCleansing initialization - location state:', state);
        
        if (state?.fromAttributeMapping && state?.importedData && Array.isArray(state.importedData) && state.importedData.length > 0) {
          setFromAttributeMapping(true);
          setRawData(state.importedData);
          console.log('✅ Received data from Attribute Mapping:', state.importedData.length, 'records');
          console.log('Sample record structure:', state.importedData[0]);
          
          // Perform agent-driven quality analysis
          try {
            await performAgentQualityAnalysis(state.importedData);
          } catch (analysisError) {
            console.error('Agent analysis failed, continuing with fallback:', analysisError);
            // Still continue - fallback analysis will be used
          }
          
          // Trigger agent analysis for panels with relatedCMDBrecords detection
          try {
            await triggerAgentPanelAnalysis(state.importedData);
          } catch (panelError) {
            console.warn('Agent panel analysis failed:', panelError);
            // Non-critical, continue without agent panels
          }
        } else {
          // Try to load from localStorage or backend
          console.log('No data from attribute mapping, loading from storage');
          await loadDataFromStorage();
        }
      } catch (error) {
        console.error('Failed to initialize data cleansing:', error);
        console.error('Error details:', {
          message: error instanceof Error ? error.message : 'Unknown error',
          stack: error instanceof Error ? error.stack : undefined,
          locationState: location.state
        });
        
        setActionFeedback({
          type: 'error',
          message: 'Failed to load data',
          details: `${error instanceof Error ? error.message : 'Unknown error occurred'}. Please check browser console for details.`
        });
        // Still set empty state to prevent infinite loading
        setEmptyState();
      } finally {
        setIsLoading(false);
      }
    };

    initializeDataCleansing();
  }, []);

  // Load data from database or backend
  const loadDataFromStorage = async () => {
    try {
      const contextHeaders = getContextHeaders();
      
      // Priority 1: Try to get latest import from database
      console.log('Loading latest import from database for data cleansing');
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT, {
          headers: contextHeaders
        });
        if (response && response.success && response.data && Array.isArray(response.data) && response.data.length > 0) {
          console.log(`Loaded ${response.data.length} records from latest import session ${response.import_session_id}`);
          setRawData(response.data);
          await performAgentQualityAnalysis(response.data);
          return;
        } else {
          console.log('No data in latest import response');
        }
      } catch (error) {
        console.warn('Failed to load data from database, trying backend assets:', error);
      }

      // Priority 2: Fallback to existing assets in backend
      try {
        const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`, {
          headers: contextHeaders
        });
        if (assetsResponse && assetsResponse.assets && Array.isArray(assetsResponse.assets) && assetsResponse.assets.length > 0) {
          console.log(`Loaded ${assetsResponse.assets.length} assets from backend inventory`);
          setRawData(assetsResponse.assets);
          await performAgentQualityAnalysis(assetsResponse.assets);
          return;
        } else {
          console.log('No assets in backend inventory response');
        }
      } catch (error) {
        console.warn('Failed to load assets from backend, trying localStorage:', error);
      }

      // Priority 3: Fallback to localStorage for compatibility (temporary)
      try {
        console.log('Falling back to localStorage for data cleansing');
        const storedData = localStorage.getItem('imported_assets');
        if (storedData) {
          const data = JSON.parse(storedData);
          if (Array.isArray(data) && data.length > 0) {
            console.log(`Loaded ${data.length} records from localStorage fallback`);
            setRawData(data);
            await performAgentQualityAnalysis(data);
            return;
          } else {
            console.log('Invalid data in localStorage');
          }
        } else {
          console.log('No data in localStorage');
        }
      } catch (error) {
        console.warn('Failed to load from localStorage:', error);
      }

      // No data available
      console.warn('No data found for data cleansing from any source');
      setActionFeedback({
        type: 'info',
        message: 'No data available',
        details: 'Please import data from the CMDB Import page or go through Attribute Mapping first'
      });
      setEmptyState();
    } catch (error) {
      console.error('Failed to load data from all sources:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to load data',
        details: error instanceof Error ? error.message : 'Unknown error occurred'
      });
      setEmptyState();
    }
  };

  // Perform agent-driven quality analysis
  const performAgentQualityAnalysis = async (data: any[]) => {
    try {
      setIsAnalyzing(true);
      const contextHeaders = getContextHeaders();
      
      console.log('Starting agent-driven quality analysis for', data.length, 'records');

      const analysisRequest = {
        assets: data,
        analysis_type: 'data_quality',
        settings: {
          run_full_analysis: true,
          include_recommendations: true,
          include_agent_insights: true,
          confidence_threshold: 0.7
        }
      };

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYZE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify(analysisRequest)
      });

      if (response && response.success) {
        console.log('✅ Agent analysis completed successfully:', response.analysis);
        
        // Process the comprehensive agent analysis results
        processAgentAnalysisResults(response.analysis, data);
        
        setActionFeedback({
          type: 'success',
          message: 'Quality analysis completed',
          details: `Analyzed ${data.length} assets with ${response.analysis.agent_confidence}% confidence`
        });
      } else {
        console.warn('⚠️ Agent analysis failed, using fallback rules');
        throw new Error(response?.error || 'Agent analysis returned no results');
      }
    } catch (error) {
      console.error('Agent analysis failed:', error);
      console.log('🔄 Falling back to rule-based quality analysis');
      
      // Fallback to simplified analysis
      performFallbackQualityAnalysis(data);
      
      setActionFeedback({
        type: 'warning',
        message: 'Used fallback quality analysis',
        details: 'Agent-driven analysis unavailable, using rule-based assessment'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Process agent analysis results
  const processAgentAnalysisResults = (analysis: AgentAnalysisResult, data: any[]) => {
    // Calculate correct completion percentage based on actual issues found
    const totalAssets = data.length;
    const totalIssues = analysis.priority_issues ? analysis.priority_issues.length : 0;
    const assetsWithIssues = new Set(analysis.priority_issues?.map(issue => issue.asset_id) || []).size;
    const cleanAssets = Math.max(0, totalAssets - assetsWithIssues);
    const correctCompletionPercentage = totalAssets > 0 ? Math.round((cleanAssets / totalAssets) * 100) : 0;
    
    // Debug the incoming data structure
    console.log('🔍 Processing backend analysis:', {
      analysisType: analysis.analysis_type,
      totalAssets,
      issuesFound: totalIssues,
      assetsWithIssues,
      cleanAssets,
      completionPercentage: correctCompletionPercentage,
      sampleIssue: analysis.priority_issues?.[0]
    });
    
    // Update quality metrics with corrected calculation  
    const metrics: QualityMetrics = {
      total_assets: totalAssets,
      clean_data: cleanAssets,
      needs_attention: Math.min(assetsWithIssues, totalAssets - cleanAssets),
      critical_issues: Math.max(0, totalAssets - cleanAssets - assetsWithIssues),
      completion_percentage: correctCompletionPercentage,
      average_quality: analysis.quality_assessment?.average_quality || 0
    };
    setQualityMetrics(metrics);

    // Transform priority issues to quality issues with enhanced details
    const issues: QualityIssue[] = analysis.priority_issues.map((issue, index) => {
      console.log(`🔍 Processing issue ${index}:`, issue);
      
      return {
        id: `backend-issue-${index}`,
        asset_id: issue.asset_id || `asset-${index}`, 
        asset_name: issue.asset_name || `Asset ${index}`,
        issue_type: issue.issue || issue.issue_type || 'Quality Issue',
        severity: issue.severity || 'medium',
        description: issue.issue || issue.description || 'Quality issue detected',
        suggested_fix: issue.suggested_fix || 'Review and correct manually', 
        confidence: issue.confidence || 0.8,
        impact: issue.impact || 'Data quality improvement',
        current_value: issue.current_value || '',
        field_name: issue.field_name || 'unknown_field'
      };
    });
    
    console.log('✅ Generated quality issues from backend:', issues);
    setQualityIssues(issues);

    // Enhanced agent recommendations with detailed explanations
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
        examples: examples,
        affected_assets: (typeof rec === 'object' ? rec.affected_assets : undefined) || Math.floor(data.length * 0.3),
        confidence: (typeof rec === 'object' ? rec.confidence : undefined) || analysis.agent_confidence,
        priority: (typeof rec === 'object' ? rec.priority : undefined) || 'medium',
        estimated_improvement: (typeof rec === 'object' ? rec.estimated_improvement : undefined) || 15,
        change_details: {
          operation_type: (typeof rec === 'object' ? rec.operation : rec) || 'standardization',
          fields_affected: (typeof rec === 'object' ? rec.fields_affected : undefined) || ['asset_type', 'environment'],
          sample_changes: examples
        }
      };
    });
    setAgentRecommendations(recommendations);
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

  // Trigger agent panel analysis with context
  const triggerAgentPanelAnalysis = async (data: any[]) => {
    try {
      const contextHeaders = getContextHeaders();
      
      console.log('Triggering agent panel analysis for data cleansing context');
      
      // Prepare analysis data for cleansing-specific insights
      const analysisData = {
        assets: data,
        analysis_context: 'data_cleansing',
        focus_areas: ['data_quality', 'normalization', 'dependencies'],
        additional_context: {
          phase: 'data_cleansing',
          previous_steps: ['import', 'attribute_mapping'],
          user_workflow: 'discovery_pipeline'
        }
      };

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...contextHeaders
        },
        body: JSON.stringify(analysisData)
      });

      if (response && response.agent_analysis) {
        console.log('✅ Agent panel analysis completed for data cleansing');
        // The agent analysis will automatically trigger the agent panel components
        // via the global agent state management
      } else {
        console.warn('Agent panel analysis returned no results');
      }
    } catch (error) {
      console.warn('Agent panel analysis failed:', error);
      // Non-critical - continue without agent insights
    }
  };

  // Enhanced fix issue handler with inline editing support
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
          completion_percentage: newCompletionPercentage
        };
      });

      // Show success feedback
      setActionFeedback({
        type: 'success',
        message: 'Quality issue resolved successfully',
        details: `Fixed ${issue.issue_type} for ${issue.asset_name}`
      });
      
    } catch (error) {
      console.error('Failed to fix issue:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to fix quality issue',
        details: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    }
  };

  // Enhanced apply recommendation with detailed feedback
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
          
          // Show success feedback
          setActionFeedback({
            type: 'success',
            message: 'Recommendation applied successfully',
            details: `${changesApplied} assets updated with ${recommendation.title}`
          });
        } else {
          setActionFeedback({
            type: 'info',
            message: 'No changes were needed',
            details: 'All assets already meet the recommendation criteria'
          });
        }
      }
    } catch (error) {
      console.error('Failed to apply recommendation:', error);
      setActionFeedback({
        type: 'error',
        message: 'Failed to apply recommendation',
        details: error instanceof Error ? error.message : 'Unknown error occurred'
      });
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

  return {
    // State
    rawData,
    qualityMetrics,
    qualityIssues,
    agentRecommendations,
    agentAnalysis,
    isLoading,
    isAnalyzing,
    fromAttributeMapping,
    agentRefreshTrigger,
    selectedIssue,
    selectedRecommendation,
    actionFeedback,
    
    // Actions
    setSelectedIssue,
    setSelectedRecommendation,
    handleFixIssue,
    handleApplyRecommendation,
    handleRefreshAnalysis,
    setActionFeedback
  };
}; 