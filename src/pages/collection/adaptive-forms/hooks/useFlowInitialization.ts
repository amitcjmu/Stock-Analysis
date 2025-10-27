/**
 * useFlowInitialization Hook
 * Manages protected initialization with ref guards to prevent duplicate calls
 */

import { useRef, useCallback, useEffect } from 'react';
import { debugLog, debugWarn, debugError } from '@/utils/debug';

interface UseFlowInitializationProps {
  initializeFlow: () => Promise<void>;
  activeFlowId: string | null;
  flowId: string | null;
}

interface UseFlowInitializationReturn {
  initializationAttempts: React.MutableRefObject<Set<string>>;
  isInitializingRef: React.MutableRefObject<boolean>;
  protectedInitializeFlow: () => Promise<void>;
}

/**
 * Hook for managing protected flow initialization with duplicate call prevention
 */
export const useFlowInitialization = ({
  initializeFlow,
  activeFlowId,
  flowId,
}: UseFlowInitializationProps): UseFlowInitializationReturn => {
  // CRITICAL FIX: Ref guard to prevent duplicate initialization calls per flowId
  const initializationAttempts = useRef<Set<string>>(new Set());
  const isInitializingRef = useRef<boolean>(false);

  // CRITICAL FIX: Protected initialization function with ref guard
  const protectedInitializeFlow = useCallback(async () => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';

    // Prevent duplicate initializations for the same flow
    if (isInitializingRef.current) {
      debugLog('⚠️ Initialization already in progress, skipping duplicate call');
      return;
    }

    if (initializationAttempts.current.has(currentFlowKey)) {
      debugLog('⚠️ Already attempted initialization for flow:', currentFlowKey);
      return;
    }

    debugLog('🔐 Protected initialization starting for flow:', currentFlowKey);
    isInitializingRef.current = true;
    initializationAttempts.current.add(currentFlowKey);

    try {
      await initializeFlow();
      debugLog('✅ Protected initialization completed for flow:', currentFlowKey);
    } catch (error) {
      debugError('❌ Protected initialization failed for flow:', currentFlowKey, error);
      // Remove from attempts on error to allow retry
      initializationAttempts.current.delete(currentFlowKey);
      throw error;
    } finally {
      isInitializingRef.current = false;
    }
  }, [initializeFlow, activeFlowId, flowId]);

  // Reset initialization attempts when flowId changes
  useEffect(() => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';
    // Clear attempts for different flows, but keep current one
    const newAttempts = new Set<string>();
    if (initializationAttempts.current.has(currentFlowKey)) {
      newAttempts.add(currentFlowKey);
    }
    initializationAttempts.current = newAttempts;
  }, [activeFlowId, flowId]);

  return {
    initializationAttempts,
    isInitializingRef,
    protectedInitializeFlow,
  };
};
