import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useToast } from '../use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { apiCall, API_CONFIG } from '../../config/api';
import { useDiscoveryFlowState } from '../useDiscoveryFlowState';
import { useAgenticCriticalAttributes } from '../useAttributeMapping';

// Types
interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  agent_source?: string;
}

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
  crew: string;
  collaboration_insights?: string[];
}

interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

export const useAttributeMappingLogic = () => {
  const location = useLocation();
  const { user, client, engagement } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mappingStatuses, setMappingStatuses] = useState<Record<string, 'pending' | 'approved' | 'rejected'>>({});
  const uploadProcessedRef = useRef(false);

  // Data hooks
  const { 
    data: agenticData, 
    isLoading: isAgenticLoading, 
    error: agenticError,
    refetch: refetchAgentic
  } = useAgenticCriticalAttributes();

  const {
    flowState,
    isLoading: isFlowStateLoading,
    error: flowStateError,
    initializeFlow,
    executePhase
  } = useDiscoveryFlowState();

  // Convert agentic critical attributes to field mappings format
  const fieldMappings = useMemo(() => {
    if (!agenticData?.attributes) return [];
    
    return agenticData.attributes.map((attr, index) => {
      const mappingId = `mapping-${attr.name}-${index}`;
      return {
        id: mappingId,
        sourceField: attr.source_field || attr.mapped_to || attr.name,
        targetAttribute: attr.name,
        confidence: attr.confidence || 0.5,
        mapping_type: (attr.mapping_type as 'direct' | 'calculated' | 'manual') || 'direct',
        sample_values: [attr.source_field || attr.mapped_to || attr.name].filter(Boolean),
        status: mappingStatuses[mappingId] || 'pending' as 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted',
        ai_reasoning: attr.ai_suggestion || `${attr.description || 'Field analysis'} (${attr.business_impact || 'medium'} business impact)`,
        agent_source: 'Agentic Analysis'
      };
    });
  }, [agenticData, mappingStatuses]);

  // Create crew analysis from agentic data
  const crewAnalysis = useMemo(() => {
    if (!agenticData?.agent_status) return [];
    
    const analyses: CrewAnalysis[] = [];
    
    if (agenticData.agent_status.crew_agents_used) {
      agenticData.agent_status.crew_agents_used.forEach((agent, index) => {
        analyses.push({
          agent: agent,
          task: "Field mapping and critical attribute analysis",
          findings: [`Analyzed ${agenticData.statistics.total_attributes} attributes`, `Identified ${agenticData.statistics.migration_critical_count} migration-critical fields`],
          recommendations: [agenticData.recommendations.next_priority],
          confidence: agenticData.statistics.avg_quality_score / 100,
          crew: "Field Mapping Crew"
        });
      });
    }
    
    return analyses;
  }, [agenticData]);

  // Calculate mapping progress from agentic data
  const mappingProgress = useMemo(() => {
    if (!agenticData?.statistics) {
      return { 
        total: 0, 
        mapped: 0, 
        critical_mapped: 0, 
        accuracy: 0,
        crew_completion_status: {}
      };
    }
    
    return {
      total: agenticData.statistics.total_attributes,
      mapped: agenticData.statistics.mapped_count,
      critical_mapped: agenticData.statistics.migration_critical_mapped,
      accuracy: agenticData.statistics.avg_quality_score,
      crew_completion_status: {
        field_mapping: agenticData.statistics.assessment_ready
      }
    };
  }, [agenticData]);

  // Convert agentic critical attributes to the format expected by CriticalAttributesTab
  const criticalAttributes = useMemo(() => {
    if (!agenticData?.attributes) return [];
    
    return agenticData.attributes.map(attr => ({
      name: attr.name,
      description: attr.description,
      category: attr.category,
      required: attr.migration_critical || false,
      status: (attr.status === 'mapped' ? 'mapped' : 'unmapped') as 'mapped' | 'unmapped' | 'partially_mapped',
      mapped_to: attr.mapped_to,
      source_field: attr.source_field,
      confidence: attr.confidence,
      quality_score: attr.quality_score,
      completeness_percentage: attr.completeness_percentage,
      mapping_type: (attr.mapping_type as 'direct' | 'calculated' | 'manual' | 'derived') || 'direct',
      ai_suggestion: attr.ai_suggestion,
      business_impact: (attr.business_impact as 'high' | 'medium' | 'low') || 'medium',
      migration_critical: attr.migration_critical || false
    }));
  }, [agenticData]);

  // Initialize from navigation state (from Data Import)
  useEffect(() => {
    const handleUploadedData = async () => {
      if (!client || !engagement) return;

      const state = location.state as any;
      
      if (state?.uploaded && state?.filename && state?.rawData && !uploadProcessedRef.current) {
        uploadProcessedRef.current = true;
        
        try {
          setIsAnalyzing(true);
          
          toast({
            title: "🚀 Attribute Mapping Started",
            description: `Analyzing ${state.filename} with ${state.rawData.length} records...`,
          });

          await initializeFlow.mutateAsync({
            client_account_id: client.id,
            engagement_id: engagement.id,
            user_id: user?.id || 'anonymous',
            raw_data: state.rawData,
            metadata: {
              source: 'file_upload',
              filename: state.filename,
              upload_timestamp: new Date().toISOString()
            },
            configuration: {
              enable_field_mapping: true,
              enable_data_cleansing: false,
              enable_inventory_building: false,
              enable_dependency_analysis: false,
              enable_technical_debt_analysis: false,
              confidence_threshold: 0.7
            }
          });

          setTimeout(() => {
            refetchAgentic();
          }, 2000);

          toast({
            title: "✅ Field Mapping Crew Activated",
            description: "Agents are analyzing field patterns and mapping to critical attributes.",
          });

        } catch (error) {
          console.error('❌ Failed to initialize Discovery Flow:', error);
          toast({
            title: "❌ Flow Initialization Failed",
            description: "Could not start field mapping analysis. Please try manually triggering analysis.",
            variant: "destructive"
          });
        } finally {
          setIsAnalyzing(false);
        }
      }
    };

    handleUploadedData();
  }, [client, engagement, initializeFlow, toast, refetchAgentic, location.state, user]);

  // Event handlers
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      setIsAnalyzing(true);
      toast({
        title: "🤖 Triggering Field Mapping Analysis",
        description: "Starting comprehensive field mapping and critical attribute analysis...",
      });

      if (!flowState?.session_id && !agenticData?.attributes?.length) {
        const latestImportResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT);
        const rawData = latestImportResponse?.data || [];
        
        if (rawData.length === 0) {
          toast({
            title: "❌ No Data Available",
            description: "Please import data first before running field mapping analysis.",
            variant: "destructive"
          });
          return;
        }

        await initializeFlow.mutateAsync({
          client_account_id: client!.id,
          engagement_id: engagement!.id,
          user_id: user?.id || 'anonymous',
          raw_data: rawData,
          metadata: {
            source: 'manual_trigger',
            trigger_timestamp: new Date().toISOString()
          },
          configuration: {
            enable_field_mapping: true,
            enable_data_cleansing: false,
            enable_inventory_building: false,
            enable_dependency_analysis: false,
            enable_technical_debt_analysis: false,
            confidence_threshold: 0.7
          }
        });
      }

      await refetchAgentic();
      toast({
        title: "✅ Analysis Complete", 
        description: "Field mapping analysis has been completed.",
      });
    } catch (error) {
      console.error('Failed to trigger field mapping analysis:', error);
      toast({
        title: "❌ Analysis Failed",
        description: "Field mapping analysis encountered an error. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [refetchAgentic, toast, flowState, agenticData, initializeFlow, client, engagement, user]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    setMappingStatuses(prev => ({
      ...prev,
      [mappingId]: 'approved'
    }));

    try {
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'field_mapping_approval',
          mapping_data: {
            source_field: mapping.sourceField,
            target_attribute: mapping.targetAttribute,
            confidence: mapping.confidence,
            mapping_type: mapping.mapping_type
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: 'Mapping Approved',
          description: `Field mapping "${mapping.sourceField} → ${mapping.targetAttribute}" has been approved.`
        });
        
        await refetchAgentic();
        queryClient.invalidateQueries({ queryKey: ['agentic-critical-attributes'] });
      }
    } catch (error) {
      console.error('❌ Error approving mapping:', error);
      setMappingStatuses(prev => ({
        ...prev,
        [mappingId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: 'Failed to approve mapping. Please try again.',
        variant: 'destructive'
      });
    }
  }, [fieldMappings, toast, refetchAgentic, queryClient]);

  const handleRejectMapping = useCallback(async (mappingId: string) => {
    const mapping = fieldMappings.find(m => m.id === mappingId);
    if (!mapping) return;

    setMappingStatuses(prev => ({
      ...prev,
      [mappingId]: 'rejected'
    }));

    try {
      const response = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learning_type: 'field_mapping_rejection',
          mapping_data: {
            source_field: mapping.sourceField,
            target_attribute: mapping.targetAttribute,
            confidence: mapping.confidence,
            mapping_type: mapping.mapping_type,
            rejection_reason: 'user_review'
          }
        })
      });

      if (response.status === 'success') {
        toast({
          title: 'Mapping Rejected',
          description: `Field mapping "${mapping.sourceField} → ${mapping.targetAttribute}" has been rejected.`
        });
        
        await refetchAgentic();
        queryClient.invalidateQueries({ queryKey: ['agentic-critical-attributes'] });
      }
    } catch (error) {
      console.error('❌ Error rejecting mapping:', error);
      setMappingStatuses(prev => ({
        ...prev,
        [mappingId]: 'pending'
      }));
      
      toast({
        title: 'Error',
        description: 'Failed to reject mapping. Please try again.',
        variant: 'destructive'
      });
    }
  }, [fieldMappings, toast, refetchAgentic, queryClient]);

  // Navigation helpers
  const canContinueToDataCleansing = () => {
    return flowState?.phase_completion?.field_mapping || 
           (mappingProgress.accuracy >= 70 && mappingProgress.critical_mapped >= mappingProgress.total * 0.8);
  };

  return {
    // Data
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    
    // Loading states
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    
    // Errors
    agenticError,
    flowStateError,
    
    // Actions
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    refetchAgentic,
    canContinueToDataCleansing,
  };
}; 