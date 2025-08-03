import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAttributeMappingFlowDetection } from '../useDiscoveryFlowAutoDetection';

export interface FlowDetectionResult {
  urlFlowId: string | null;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  emergencyFlowId: string | null;
  finalFlowId: string | null;
  hasEffectiveFlow: boolean;
  flowList: unknown[];
  isFlowListLoading: boolean;
  flowListError: unknown;
  pathname: string;
  navigate: (path: string) => void;
}

/**
 * Hook for flow detection and routing logic
 * Handles URL parsing, auto-detection, and emergency fallback mechanisms
 */
export const useFlowDetection = (): FlowDetectionResult => {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    flowListError,
    hasEffectiveFlow
  } = useAttributeMappingFlowDetection();

  // Emergency fallback: try to extract flow ID from tenant-scoped context only
  const emergencyFlowId = useMemo(() => {
    if (effectiveFlowId) return effectiveFlowId;

    // Check if there's a flow ID in the current path (still tenant-scoped by backend)
    const currentPath = pathname;
    const flowIdMatch = currentPath.match(/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})/i);
    if (flowIdMatch) {
      console.log('🆘 Emergency flow ID from path (will be tenant-validated):', flowIdMatch[0]);
      return flowIdMatch[0];
    }

    // Check localStorage for recent flow context (still tenant-scoped by backend)
    if (typeof window !== 'undefined') {
      const storedFlowId = localStorage.getItem('lastActiveFlowId');
      if (storedFlowId) {
        console.log('🆘 Emergency flow ID from localStorage (will be tenant-validated):', storedFlowId);
        return storedFlowId;
      }
    }

    // SECURITY: No hardcoded flow IDs - let the system gracefully handle no flow
    // All flow access must go through proper tenant-scoped APIs
    console.log('🔒 No emergency flow ID available - relying on tenant-scoped flow detection only');
    return null;
  }, [effectiveFlowId, pathname]);

  // Optimized debugging for flow detection (only log when values change)
  useEffect(() => {
    // Only log in development mode or when specifically debugging
    if (process.env.NODE_ENV === 'development' && flowList && !isFlowListLoading) {
      console.log('🎯 Flow Detection Debug:', {
        urlFlowId,
        autoDetectedFlowId,
        effectiveFlowId,
        hasEffectiveFlow,
        flowListLength: flowList?.length,
        pathname
      });

      if (flowList.length > 0) {
        console.log('📋 Available flows for attribute mapping:', flowList.map(f => ({
          flow_id: f.id,
          status: f.status,
          current_phase: f.current_phase,
          next_phase: f.next_phase,
          data_import_completed: f.data_import_completed,
          attribute_mapping_completed: f.attribute_mapping_completed
        })));
      }
    }
  }, [effectiveFlowId, hasEffectiveFlow, flowList?.length, isFlowListLoading]); // Reduced dependencies to prevent excessive re-renders

  // Use unified discovery flow with effective flow ID or emergency fallback
  const finalFlowId = effectiveFlowId || emergencyFlowId;

  // Only log final flow resolution when it changes (prevent spam)
  const finalFlowIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (finalFlowIdRef.current !== finalFlowId && process.env.NODE_ENV === 'development') {
      console.log('🎯 Final Flow ID Resolution:', {
        effectiveFlowId,
        emergencyFlowId,
        finalFlowId,
        urlFlowId,
        autoDetectedFlowId
      });
      finalFlowIdRef.current = finalFlowId;
    }
  }, [finalFlowId, effectiveFlowId, emergencyFlowId, urlFlowId, autoDetectedFlowId]);

  return {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    emergencyFlowId,
    finalFlowId,
    hasEffectiveFlow,
    flowList,
    isFlowListLoading,
    flowListError,
    pathname,
    navigate
  };
};
