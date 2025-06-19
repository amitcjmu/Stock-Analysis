import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useToast } from '../use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';
import { useDiscoveryFlowState } from '../useDiscoveryFlowState';
import { useDataCleansingAnalysis } from '../useDataCleansingAnalysis';

// Types
interface DataCleansingProgress {
  total_records: number;
  cleaned_records: number;
  quality_score: number;
  completion_percentage: number;
  issues_resolved: number;
  crew_completion_status: Record<string, boolean>;
}

interface QualityIssue {
  id: string;
  field: string;
  issue_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_records: number;
  recommendation: string;
  agent_source: string;
  status: 'pending' | 'resolved' | 'ignored';
}

interface CleansingRecommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  fields: string[];
  agent_source: string;
  implementation_steps: string[];
  status: 'pending' | 'applied' | 'rejected';
}

export const useDataCleansingLogic = () => {
  const location = useLocation();
  const { user, client, engagement } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [issueStatuses, setIssueStatuses] = useState<Record<string, 'pending' | 'resolved' | 'ignored'>>({});
  const [recommendationStatuses, setRecommendationStatuses] = useState<Record<string, 'pending' | 'applied' | 'rejected'>>({});
  const uploadProcessedRef = useRef(false);

  // Data hooks
  const { 
    data: cleansingData, 
    isLoading: isCleansingLoading, 
    error: cleansingError,
    refetch: refetchCleansing
  } = useDataCleansingAnalysis();

  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executePhase
  } = useDiscoveryFlowState();

  // Derived data
  const qualityIssues = useMemo(() => {
    if (!cleansingData?.quality_issues) return [];
    return cleansingData.quality_issues.map(issue => ({
      ...issue,
      status: issueStatuses[issue.id] || issue.status
    }));
  }, [cleansingData, issueStatuses]);

  const agentRecommendations = useMemo(() => {
    if (!cleansingData?.recommendations) return [];
    return cleansingData.recommendations.map(rec => ({
      ...rec,
      status: recommendationStatuses[rec.id] || rec.status
    }));
  }, [cleansingData, recommendationStatuses]);

  const cleansingProgress = useMemo((): DataCleansingProgress => {
    if (!cleansingData?.statistics && !cleansingData?.metrics) {
      return { 
        total_records: 0, 
        cleaned_records: 0, 
        quality_score: 0, 
        completion_percentage: 0,
        issues_resolved: 0,
        crew_completion_status: {}
      };
    }
    
    const stats = cleansingData.statistics || cleansingData.metrics;
    return {
      total_records: stats.total_records || 0,
      cleaned_records: cleansingData.metrics?.cleaned_records || 0,
      quality_score: stats.quality_score || stats.data_quality_score || 0,
      completion_percentage: stats.completion_percentage || 0,
      issues_resolved: cleansingData.metrics?.quality_issues_resolved || 0,
      crew_completion_status: {
        data_cleansing: stats.completion_percentage >= 80
      }
    };
  }, [cleansingData]);

  // Initialize from navigation state
  useEffect(() => {
    const handleNavigationFromAttributeMapping = async () => {
      if (!client || !engagement) return;
      
      const state = location.state as any;
      
      if (state?.from_phase === 'field_mapping' && state?.flow_session_id && !uploadProcessedRef.current) {
        uploadProcessedRef.current = true;
        
        try {
          setIsAnalyzing(true);
          
          toast({
            title: "🚀 Data Cleansing Phase Started",
            description: "Initializing Data Quality Manager and Standardization Specialist...",
          });

          if (state.flow_session_id) {
            await executePhase('data_cleansing', { 
              session_id: state.flow_session_id,
              previous_phase: 'field_mapping',
              mapping_progress: state.mapping_progress,
              client_account_id: client.id,
              engagement_id: engagement.id
            });
          }

          setTimeout(() => {
            refetchCleansing();
          }, 2000);

          toast({
            title: "✅ Data Cleansing Analysis Started",
            description: "Crew is analyzing data quality issues and standardization opportunities.",
          });

        } catch (error) {
          console.error('❌ Failed to initialize Data Cleansing phase:', error);
          toast({
            title: "❌ Phase Initialization Failed",
            description: "Could not start Data Cleansing phase. Please try manually triggering analysis.",
            variant: "destructive"
          });
        } finally {
          setIsAnalyzing(false);
        }
      }
    };
    
    handleNavigationFromAttributeMapping();
  }, [client, engagement, executePhase, toast, refetchCleansing, location.state]);

  // Event handlers
  const handleTriggerDataCleansingCrew = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Triggering Data Cleansing Analysis",
        description: "Starting data quality analysis and standardization review...",
      });

      // Force refresh the data cleansing analysis
      await refetchCleansing();
      
      toast({
        title: "✅ Data Cleansing Analysis Refreshed",
        description: "Data quality analysis has been updated with latest information.",
      });

    } catch (error) {
      console.error('❌ Failed to refresh data cleansing analysis:', error);
      toast({
        title: "❌ Analysis Refresh Failed",
        description: "Could not refresh data cleansing analysis. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [refetchCleansing, toast]);

  const handleResolveIssue = useCallback(async (issueId: string, action: 'resolve' | 'ignore') => {
    const issue = qualityIssues.find(i => i.id === issueId);
    if (!issue) return;

    setIssueStatuses(prev => ({
      ...prev,
      [issueId]: action === 'resolve' ? 'resolved' : 'ignored'
    }));

    try {
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'data_quality_issue_resolution',
          action: action,
          issue_data: {
            field: issue.field,
            issue_type: issue.issue_type,
            severity: issue.severity,
            resolution: action === 'resolve' ? 'fixed' : 'acknowledged'
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: action === 'resolve' ? 'Issue Resolved' : 'Issue Ignored',
          description: `Quality issue "${issue.field}" has been ${action}d.`
        });
        
        await refetchCleansing();
        queryClient.invalidateQueries({ queryKey: ['data-cleansing-analysis'] });
      }
    } catch (error) {
      console.error(`❌ Error ${action}ing issue:`, error);
      setIssueStatuses(prev => ({
        ...prev,
        [issueId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: `Failed to ${action} issue. Please try again.`,
        variant: 'destructive'
      });
    }
  }, [qualityIssues, toast, refetchCleansing, queryClient]);

  const handleApplyRecommendation = useCallback(async (recommendationId: string, action: 'apply' | 'reject') => {
    const recommendation = agentRecommendations.find(r => r.id === recommendationId);
    if (!recommendation) return;

    setRecommendationStatuses(prev => ({
      ...prev,
      [recommendationId]: action === 'apply' ? 'applied' : 'rejected'
    }));

    try {
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'data_cleansing_recommendation',
          action: action,
          recommendation_data: {
            type: recommendation.type,
            title: recommendation.title,
            fields: recommendation.fields,
            priority: recommendation.priority
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: action === 'apply' ? 'Recommendation Applied' : 'Recommendation Rejected',
          description: `Cleansing recommendation "${recommendation.title}" has been ${action === 'apply' ? 'applied' : 'rejected'}.`
        });
        
        await refetchCleansing();
        queryClient.invalidateQueries({ queryKey: ['data-cleansing-analysis'] });
      }
    } catch (error) {
      console.error(`❌ Error ${action}ing recommendation:`, error);
      setRecommendationStatuses(prev => ({
        ...prev,
        [recommendationId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: `Failed to ${action} recommendation. Please try again.`,
        variant: 'destructive'
      });
    }
  }, [agentRecommendations, toast, refetchCleansing, queryClient]);

  // Navigation helpers
  const canContinueToInventory = () => {
    return flowState?.phase_completion?.data_cleansing || 
           (cleansingProgress.completion_percentage >= 60 && cleansingProgress.quality_score >= 70);
  };

  return {
    // Data
    cleansingData,
    qualityIssues,
    agentRecommendations,
    cleansingProgress,
    flowState,
    
    // Loading states
    isCleansingLoading,
    isFlowStateLoading,
    isAnalyzing,
    
    // Errors
    cleansingError,
    flowStateError,
    
    // Actions
    handleTriggerDataCleansingCrew,
    handleResolveIssue,
    handleApplyRecommendation,
    refetchCleansing: () => refetchCleansing(),
    canContinueToInventory,
  };
}; 