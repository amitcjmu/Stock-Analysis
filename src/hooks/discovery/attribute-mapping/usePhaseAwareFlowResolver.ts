import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';
import { useFlowPhases, getPhaseOrder } from '@/hooks/useFlowPhases';

interface ImportData {
  id: string;
  master_flow_id: string;
  status: string;
  [key: string]: unknown;
}

interface UsePhaseAwareFlowResolverResult {
  resolvedFlowId: string | null;
  isResolving: boolean;
  error: Error | null;
  importData: ImportData | null;
  resolutionMethod: 'direct-flow' | 'import-resolved' | 'phase-matched' | 'recent-flow' | null;
}

type DiscoveryPhase =
  | 'data_import'
  | 'attribute_mapping'
  | 'field_mapping'
  | 'field_mapping_approval'
  | 'data_cleansing'
  | 'inventory'
  | 'dependencies';

/**
 * Phase-aware smart flow resolver that handles all flow detection scenarios:
 * 1. If provided ID is a valid flow ID - use it directly
 * 2. If provided ID is an import ID - resolve it to flow ID
 * 3. If no ID provided - find the most appropriate flow for the target phase
 *
 * Per ADR-027: Uses useFlowPhases hook to get phase ordering dynamically from FlowTypeConfig
 *
 * @param providedId - Optional flow ID or import ID from URL
 * @param targetPhase - The phase the page is for (e.g., 'data_cleansing')
 */
export function usePhaseAwareFlowResolver(
  providedId?: string,
  targetPhase: DiscoveryPhase = 'attribute_mapping'
): UsePhaseAwareFlowResolverResult {
  const [resolvedFlowId, setResolvedFlowId] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [importData, setImportData] = useState<ImportData | null>(null);
  const [resolutionMethod, setResolutionMethod] = useState<UsePhaseAwareFlowResolverResult['resolutionMethod']>(null);
  const { client, engagement } = useAuth();

  // Per ADR-027: Fetch dynamic phase configuration from backend
  const { data: discoveryPhases, isLoading: isPhasesLoading } = useFlowPhases('discovery');

  useEffect(() => {
    // Wait for phase configuration to load
    if (isPhasesLoading || !discoveryPhases) {
      return;
    }

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
            console.log(`✅ [${targetPhase}] ${providedId} is already a valid flow ID`);
            setResolvedFlowId(providedId);
            setResolutionMethod('direct-flow');
            setIsResolving(false);
            return;
          }

          // Otherwise, try to resolve it as an import ID
          console.log(`🔍 [${targetPhase}] Attempting to resolve import ID ${providedId} to flow ID`);

          try {
            const headers: Record<string, string> = {};
            if (client?.account_id) {
              headers['X-Client-Account-ID'] = client.account_id;
            }
            if (engagement?.id) {
              headers['X-Engagement-ID'] = engagement.id;
            }

            const response = await apiCall(`/api/v1/data-import/import/${providedId}`, {
              method: 'GET',
              headers
            });

            if (response && response.master_flow_id) {
              console.log(`✅ [${targetPhase}] Resolved import ID ${providedId} to flow ID ${response.master_flow_id}`);
              setResolvedFlowId(response.master_flow_id);
              setImportData(response);
              setResolutionMethod('import-resolved');
              setIsResolving(false);
              return;
            }
          } catch (err) {
            // If we get a 404, this might be an invalid ID
            if (err && typeof err === 'object' && 'status' in err && err.status === 404) {
              console.log(`⚠️ [${targetPhase}] ${providedId} not found as import ID`);
            } else {
              console.error(`❌ [${targetPhase}] Error resolving import ID ${providedId}:`, err);
            }
            // Fall through to find recent flow
          }
        }

        // Case 2: No ID provided or resolution failed - find most appropriate flow for target phase
        console.log(`🔍 [${targetPhase}] Finding most appropriate discovery flow`);

        const activeFlows = await masterFlowServiceExtended.getActiveDiscoveryFlows(
          client.id,
          engagement.id
        );

        if (!activeFlows || activeFlows.length === 0) {
          console.log(`📭 [${targetPhase}] No active discovery flows found`);
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

        // Per ADR-027: Get target phase order from dynamic configuration
        const targetPhaseOrder = getPhaseOrder(discoveryPhases, targetPhase);

        // Filter flows that are at the target phase or eligible for it
        const eligibleFlows = sortedFlows.filter(flow => {
          const currentPhase = flow.currentPhase as DiscoveryPhase;
          // Per ADR-027: Use dynamic phase ordering
          const currentPhaseOrder = getPhaseOrder(discoveryPhases, currentPhase);

          // Flow is eligible if:
          // 1. It's exactly at the target phase
          // 2. It's at the phase just before target phase (ready to transition)
          // 3. For data_cleansing specifically, accept field_mapping_approval phase
          if (targetPhase === 'data_cleansing') {
            return currentPhase === 'data_cleansing' ||
                   currentPhase === 'field_mapping_approval' ||
                   currentPhase === 'field_mapping' ||
                   currentPhase === 'attribute_mapping';
          }

          return currentPhaseOrder === targetPhaseOrder ||
                 currentPhaseOrder === targetPhaseOrder - 1;
        });

        // Find the best flow from eligible flows
        let targetFlow = null;

        // Priority 1: Flow exactly at target phase
        targetFlow = eligibleFlows.find(flow =>
          flow.currentPhase === targetPhase
        );

        // Priority 2: Flow at phase just before (ready to transition)
        if (!targetFlow && discoveryPhases) {
          // Per ADR-027: Find previous phases using dynamic phase configuration
          const previousPhases = discoveryPhases.phase_details
            .filter(phase => getPhaseOrder(discoveryPhases, phase.name) === targetPhaseOrder - 1)
            .map(phase => phase.name);

          targetFlow = eligibleFlows.find(flow =>
            previousPhases.includes(flow.currentPhase)
          );
        }

        // Priority 3: Any eligible flow with good status
        if (!targetFlow) {
          targetFlow = eligibleFlows.find(flow =>
            flow.status === 'running' ||
            flow.status === 'active' ||
            flow.status === 'processing' ||
            flow.status === 'waiting_for_approval' ||
            flow.status === 'waiting_for_user_approval' ||
            flow.status === 'paused'
          );
        }

        // Priority 4: Most recent eligible flow
        if (!targetFlow && eligibleFlows.length > 0) {
          targetFlow = eligibleFlows[0];
        }

        // Priority 5: If no eligible flows, take the most recent flow overall
        if (!targetFlow && sortedFlows.length > 0) {
          targetFlow = sortedFlows[0];
          console.log(`⚠️ [${targetPhase}] No phase-appropriate flows found, using most recent flow`);
        }

        if (targetFlow) {
          console.log(`✅ [${targetPhase}] Found appropriate flow: ${targetFlow.flowId}`, {
            phase: targetFlow.currentPhase,
            status: targetFlow.status,
            progress: targetFlow.progress,
            resolutionMethod: targetFlow.currentPhase === targetPhase ? 'phase-matched' : 'recent-flow'
          });
          setResolvedFlowId(targetFlow.flowId);
          setResolutionMethod(targetFlow.currentPhase === targetPhase ? 'phase-matched' : 'recent-flow');
        } else {
          console.log(`⚠️ [${targetPhase}] No suitable flow found`);
          setResolvedFlowId(null);
          setResolutionMethod(null);
        }
      } catch (err) {
        console.error(`❌ [${targetPhase}] Error in phase-aware flow resolver:`, err);
        setError(err as Error);
        setResolvedFlowId(null);
        setResolutionMethod(null);
      } finally {
        setIsResolving(false);
      }
    };

    resolveFlow();
  }, [providedId, targetPhase, client?.id, engagement?.id, discoveryPhases, isPhasesLoading]);

  return {
    resolvedFlowId,
    isResolving,
    error,
    importData,
    resolutionMethod
  };
}
