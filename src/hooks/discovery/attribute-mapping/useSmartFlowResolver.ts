import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';

interface ImportData {
  id: string;
  master_flow_id: string;
  status: string;
  [key: string]: unknown;
}

interface UseSmartFlowResolverResult {
  resolvedFlowId: string | null;
  isResolving: boolean;
  error: Error | null;
  importData: ImportData | null;
  resolutionMethod: 'direct-flow' | 'import-resolved' | 'recent-flow' | null;
}

/**
 * Smart flow resolver that handles all flow detection scenarios:
 * 1. If provided ID is a valid flow ID - use it directly
 * 2. If provided ID is an import ID - resolve it to flow ID
 * 3. If no ID provided - find the most recent/appropriate flow
 */
export function useSmartFlowResolver(providedId?: string): UseSmartFlowResolverResult {
  const [resolvedFlowId, setResolvedFlowId] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [importData, setImportData] = useState<ImportData | null>(null);
  const [resolutionMethod, setResolutionMethod] = useState<UseSmartFlowResolverResult['resolutionMethod']>(null);
  const { client, engagement } = useAuth();

  useEffect(() => {
    if (!client?.id || !engagement?.id) {
      return;
    }

    const resolveFlow = async () => {
      setIsResolving(true);
      setError(null);

      try {
        // Case 1: ID is provided
        if (providedId) {
          // Check if it's already a valid flow ID (UUID v4 format)
          const isValidFlowId = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(providedId);

          if (isValidFlowId) {
            console.log(`✅ ${providedId} is already a valid flow ID`);
            setResolvedFlowId(providedId);
            setResolutionMethod('direct-flow');
            setIsResolving(false);
            return;
          }

          // Otherwise, try to resolve it as an import ID
          console.log(`🔍 Attempting to resolve import ID ${providedId} to flow ID`);

          try {
            const headers: Record<string, string> = {};
            if (client?.account_id) {
              headers['X-Client-Account-ID'] = client.account_id;
            }
            if (engagement?.id) {
              headers['X-Engagement-ID'] = engagement.id;
            }

            const response = await apiCall(`/api/v1/data-import/imports/${providedId}`, {
              method: 'GET',
              headers
            });

            if (response && response.master_flow_id) {
              console.log(`✅ Resolved import ID ${providedId} to flow ID ${response.master_flow_id}`);
              setResolvedFlowId(response.master_flow_id);
              setImportData(response);
              setResolutionMethod('import-resolved');
              setIsResolving(false);
              return;
            }
          } catch (err) {
            // If we get a 404, this might be an invalid ID
            if (err && typeof err === 'object' && 'status' in err && err.status === 404) {
              console.log(`⚠️ ${providedId} not found as import ID`);
            } else {
              console.error(`❌ Error resolving import ID ${providedId}:`, err);
            }
            // Fall through to find recent flow
          }
        }

        // Case 2: No ID provided or resolution failed - find most recent appropriate flow
        console.log('🔍 Finding most recent discovery flow for attribute mapping');

        const activeFlows = await masterFlowServiceExtended.getActiveDiscoveryFlows(
          client.id,
          engagement.id
        );

        if (!activeFlows || activeFlows.length === 0) {
          console.log('📭 No active discovery flows found');
          setResolvedFlowId(null);
          setResolutionMethod(null);
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
        if (!targetFlow && sortedFlows.length > 0) {
          targetFlow = sortedFlows[0];
        }

        if (targetFlow) {
          console.log(`✅ Found recent flow for attribute mapping: ${targetFlow.flowId}`, {
            phase: targetFlow.currentPhase,
            status: targetFlow.status,
            progress: targetFlow.progress
          });
          setResolvedFlowId(targetFlow.flowId);
          setResolutionMethod('recent-flow');
        } else {
          console.log('⚠️ No suitable flow found');
          setResolvedFlowId(null);
          setResolutionMethod(null);
        }
      } catch (err) {
        console.error('❌ Error in smart flow resolver:', err);
        setError(err as Error);
        setResolvedFlowId(null);
        setResolutionMethod(null);
      } finally {
        setIsResolving(false);
      }
    };

    resolveFlow();
  }, [providedId, client?.id, engagement?.id]);

  return {
    resolvedFlowId,
    isResolving,
    error,
    importData,
    resolutionMethod
  };
}
