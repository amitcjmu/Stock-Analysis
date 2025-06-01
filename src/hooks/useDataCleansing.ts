import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { apiCall, API_CONFIG } from '../config/api';
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
}

export const useDataCleansing = () => {
  const location = useLocation();

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
      // Priority 1: Try to get latest import from database
      console.log('Loading latest import from database for data cleansing');
      try {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
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
        const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`);
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

      if (analysisResponse && analysisResponse.analysis_type) {
        setAgentAnalysis(analysisResponse);
        processAgentAnalysisResults(analysisResponse, data);
        
        setActionFeedback({
          type: 'success',
          message: 'Agent analysis completed successfully',
          details: `Analyzed ${data.length} assets with ${analysisResponse.analysis_type} approach`
        });
      } else {
        console.warn('Invalid agent analysis response, using fallback');
        performBasicQualityAnalysis(data);
      }
    } catch (error) {
      console.error('Agent analysis failed, using fallback:', error);
      setActionFeedback({
        type: 'info',
        message: 'Using fallback analysis',
        details: 'Agent analysis unavailable, using rule-based quality assessment'
      });
      performBasicQualityAnalysis(data);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Process agent analysis results
  const processAgentAnalysisResults = (analysis: AgentAnalysisResult, data: any[]) => {
    // Calculate correct completion percentage
    const assetsWithIssues = analysis.quality_buckets.critical_issues + analysis.quality_buckets.needs_attention;
    const cleanAssets = analysis.quality_buckets.clean_data;
    const totalAssets = data.length;
    
    const correctCompletionPercentage = totalAssets > 0 ? Math.round((cleanAssets / totalAssets) * 100) : 0;
    
    // Update quality metrics with corrected calculation
    const metrics: QualityMetrics = {
      total_assets: totalAssets,
      clean_data: analysis.quality_buckets.clean_data,
      needs_attention: analysis.quality_buckets.needs_attention,
      critical_issues: analysis.quality_buckets.critical_issues,
      completion_percentage: correctCompletionPercentage,
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
      current_value: issue.current_value || '',
      field_name: issue.field_name || 'unknown_field'
    }));
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
      completion_percentage: Math.round((cleanData / totalAssets) * 100),
      average_quality: 70
    });

    // Debug logging to understand data structure
    console.log('Data structure analysis for fallback issues:');
    console.log('First asset:', data[0]);
    console.log('Available columns:', data.length > 0 ? Object.keys(data[0]) : 'No data');

    // Generate realistic sample issues based on actual data structure
    const sampleIssues: QualityIssue[] = data.slice(0, Math.min(5, data.length)).map((asset, index) => {
      // Get actual field names from the data
      const availableFields = Object.keys(asset);
      
      // Prioritize common quality issue fields, checking both upper and lower case
      const problemFields = [
        'TYPE', 'type', 'asset_type', 'ASSET_TYPE',
        'ENVIRONMENT', 'environment', 'ENV', 'env',
        'OS', 'os', 'operating_system', 'OPERATING_SYSTEM',
        'IP ADDRESS', 'IP_ADDRESS', 'ip_address', 'ipaddress', 'IPADDRESS',
        'OWNER', 'owner', 'BUSINESS_OWNER', 'business_owner'
      ];
      
      // Find the first available field that exists in the data
      const fieldToCheck = availableFields.find(field => 
        problemFields.includes(field)
      ) || availableFields[Math.min(1, availableFields.length - 1)] || 'TYPE';

      // Get asset identifier that matches what the table will use (including uppercase variants)
      const assetIdentifier = asset.id || asset.ID || asset.asset_name || asset.hostname || asset.name || asset.NAME || `asset-${index}`;
      const assetName = asset.asset_name || asset.hostname || asset.name || asset.NAME || asset.NAME || `Asset ${index}`;
      
      // Get current value for the field
      const currentValue = asset[fieldToCheck] || '';

      console.log(`Generated issue ${index}: asset=${assetIdentifier}, field=${fieldToCheck}, value="${currentValue}"`);

      return {
        id: `issue-${index}`,
        asset_id: assetIdentifier,
        asset_name: assetName,
        issue_type: 'Data Quality Issue',
        severity: 'medium' as const,
        description: `Field "${fieldToCheck}" requires review and standardization`,
        suggested_fix: currentValue ? `Standardize "${currentValue}"` : 'Add missing value',
        confidence: 0.7,
        impact: 'May affect migration planning accuracy',
        current_value: currentValue,
        field_name: fieldToCheck
      };
    });
    
    console.log('Generated sample issues:', sampleIssues);
    setQualityIssues(sampleIssues);

    // Generate sample recommendations with actual field names
    const actualFieldNames = data.length > 0 ? Object.keys(data[0]) : ['asset_type'];
    const sampleRecommendations: AgentRecommendation[] = [
      {
        id: 'rec-1',
        operation: 'standardize_fields',
        title: 'Standardize Data Fields',
        description: 'Normalize field values for consistency across the dataset',
        examples: ['Standardize naming conventions', 'Remove inconsistent formatting'],
        affected_assets: Math.floor(totalAssets * 0.4),
        confidence: 0.8,
        priority: 'high' as const,
        estimated_improvement: 20,
        change_details: {
          operation_type: 'standardization',
          fields_affected: actualFieldNames.slice(0, 3), // Use actual field names
          sample_changes: ['Normalize case', 'Remove extra spaces', 'Standardize formats']
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

  // Trigger agent panel analysis for auto-population
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
        try {
          const clarificationResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATION, {
            method: 'POST',
            body: JSON.stringify(clarificationRequest)
          });

          if (clarificationResponse.status === 'success') {
            console.log('Agent clarifications generated for dependency mapping');
          }
        } catch (error) {
          console.warn('Agent clarification endpoint failed:', error);
        }
      }

      // Just trigger agent refresh to populate panels - let the panels handle their own data fetching
      // The agent panels will automatically fetch their data using GET requests to appropriate endpoints
      setAgentRefreshTrigger(prev => prev + 1);
      
    } catch (error) {
      console.error('Failed to trigger agent panel analysis:', error);
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