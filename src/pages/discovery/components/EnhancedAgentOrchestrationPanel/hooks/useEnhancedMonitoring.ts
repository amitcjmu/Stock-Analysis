import { useState, useEffect, useCallback } from 'react';
import { apiCall } from '@/config/api';
import { CrewProgress, CollaborationData, PlanningData, MemoryAnalytics } from '../types';
import { INITIAL_CREWS } from '../constants';

export const useEnhancedMonitoring = (flowId: string, flowState: any) => {
  const [crews, setCrews] = useState<CrewProgress[]>(INITIAL_CREWS);
  const [collaborationData, setCollaborationData] = useState<CollaborationData | null>(null);
  const [planningData, setPlanningData] = useState<PlanningData | null>(null);
  const [memoryAnalytics, setMemoryAnalytics] = useState<MemoryAnalytics | null>(null);
  const [loading, setLoading] = useState(false);

  const updateCrewsWithMonitoringData = useCallback((monitoringData: any) => {
    if (!monitoringData?.crews) return;

    setCrews(prevCrews => 
      prevCrews.map(crew => {
        const monitoringCrew = monitoringData.crews.find(
          (mc: any) => mc.name === crew.name
        );
        
        if (monitoringCrew) {
          return {
            ...crew,
            status: monitoringCrew.status || crew.status,
            progress: monitoringCrew.progress || crew.progress,
            currentTask: monitoringCrew.current_task || crew.currentTask,
            agents: crew.agents.map(agent => {
              const monitoringAgent = monitoringCrew.agents?.find(
                (ma: any) => ma.name === agent.name
              );
              
              if (monitoringAgent) {
                return {
                  ...agent,
                  status: monitoringAgent.status || agent.status,
                  currentTask: monitoringAgent.current_task || agent.currentTask,
                  performance: monitoringAgent.performance || agent.performance
                };
              }
              
              return agent;
            }),
            collaboration_status: monitoringCrew.collaboration_status || crew.collaboration_status,
            planning_status: monitoringCrew.planning_status || crew.planning_status
          };
        }
        
        return crew;
      })
    );
  }, []);

  const fetchEnhancedData = useCallback(async () => {
    if (!flowId) return;

    setLoading(true);
    try {
      // Fetch collaboration analytics
      const collabResponse = await apiCall('/api/v1/agents/collaboration/analytics', {
        method: 'POST',
        body: JSON.stringify({ flow_id: flowId })
      });
      
      if (collabResponse?.data) {
        setCollaborationData(collabResponse.data);
      }

      // Fetch planning intelligence
      const planningResponse = await apiCall('/api/v1/agents/planning/intelligence', {
        method: 'POST',
        body: JSON.stringify({ flow_id: flowId })
      });
      
      if (planningResponse?.data) {
        setPlanningData(planningResponse.data);
      }

      // Fetch memory analytics
      const memoryResponse = await apiCall('/api/v1/agents/memory/analytics', {
        method: 'POST',
        body: JSON.stringify({ flow_id: flowId })
      });
      
      if (memoryResponse?.data) {
        setMemoryAnalytics(memoryResponse.data);
      }

      // Fetch crew monitoring data
      const monitoringResponse = await apiCall('/api/v1/agents/monitoring/enhanced', {
        method: 'POST',
        body: JSON.stringify({ flow_id: flowId })
      });
      
      if (monitoringResponse?.data) {
        updateCrewsWithMonitoringData(monitoringResponse.data);
      }
    } catch (error) {
      console.error('Error fetching enhanced monitoring data:', error);
    } finally {
      setLoading(false);
    }
  }, [flowId, updateCrewsWithMonitoringData]);

  useEffect(() => {
    // Fetch once on mount only - no auto-polling
    fetchEnhancedData();
  }, [fetchEnhancedData]);

  return {
    crews,
    collaborationData,
    planningData,
    memoryAnalytics,
    loading,
    refresh: fetchEnhancedData
  };
};