import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';

interface UseRecentFlowResolverResult {
  recentFlowId: string | null;
  isResolving: boolean;
  error: Error | null;
}

/**
 * Hook to get the most recent discovery flow when no flow ID is provided
 * This enables the attribute mapping page to work without URL parameters
 */
export function useRecentFlowResolver(): UseRecentFlowResolverResult {
  const [recentFlowId, setRecentFlowId] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { client, engagement } = useAuth();

  useEffect(() => {
    if (!client?.id || !engagement?.id) {
      return;
    }

    const fetchRecentFlow = async () => {
      setIsResolving(true);
      setError(null);

      try {
        console.log('🔍 Fetching recent discovery flow for attribute mapping');

        // Get all active discovery flows
        const activeFlows = await masterFlowServiceExtended.getActiveDiscoveryFlows(
          client.id,
          engagement.id
        );

        if (!activeFlows || activeFlows.length === 0) {
          console.log('📭 No active discovery flows found');
          setRecentFlowId(null);
          return;
        }

        // Sort flows by creation time (most recent first)
        const sortedFlows = [...activeFlows].sort((a, b) => {
          const dateA = new Date(a.startTime || '1970-01-01').getTime();
          const dateB = new Date(b.startTime || '1970-01-01').getTime();
          return dateB - dateA;
        });

        // Find the most suitable flow for attribute mapping
        // Priority 1: Flow in attribute mapping phase
        let targetFlow = sortedFlows.find(flow =>
          flow.currentPhase === 'attribute_mapping' ||
          flow.currentPhase === 'field_mapping'
        );

        // Priority 2: Flow that completed data import and is waiting for approval
        if (!targetFlow) {
          targetFlow = sortedFlows.find(flow =>
            (flow.status === 'waiting_for_approval' ||
             flow.status === 'waiting_for_user_approval' ||
             flow.status === 'paused') &&
            flow.progress >= 20 // At least past data import
          );
        }

        // Priority 3: Any active/running flow
        if (!targetFlow) {
          targetFlow = sortedFlows.find(flow =>
            flow.status === 'running' ||
            flow.status === 'active' ||
            flow.status === 'processing' ||
            flow.status === 'initialized'
          );
        }

        // Priority 4: Most recent flow regardless of status
        if (!targetFlow) {
          targetFlow = sortedFlows[0];
        }

        if (targetFlow) {
          console.log(`✅ Found recent flow for attribute mapping: ${targetFlow.flowId}`, {
            phase: targetFlow.currentPhase,
            status: targetFlow.status,
            progress: targetFlow.progress
          });
          setRecentFlowId(targetFlow.flowId);
        } else {
          console.log('⚠️ No suitable flow found for attribute mapping');
          setRecentFlowId(null);
        }
      } catch (err) {
        console.error('❌ Error fetching recent flow:', err);
        setError(err as Error);
        setRecentFlowId(null);
      } finally {
        setIsResolving(false);
      }
    };

    fetchRecentFlow();
  }, [client?.id, engagement?.id]);

  return {
    recentFlowId,
    isResolving,
    error
  };
}
