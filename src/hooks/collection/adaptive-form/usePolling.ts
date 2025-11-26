/**
 * HTTP polling logic for adaptive form flow
 * Implements Railway-compatible polling (NO WebSockets)
 *
 * PRESERVED FROM ORIGINAL: Lines 808-930 of useAdaptiveFormFlow.ts
 * CRITICAL PATTERN: HTTP polling with smart intervals - required for Railway deployment
 */

import { useRef } from "react";
import { collectionFlowApi } from "@/services/api/collection-flow";
import { isFlowTerminal } from "@/constants/flowStates";
import type { CollectionQuestionnaire } from "./types";
import type { CollectionFlowStatusResponse } from "@/services/api/collection-flow";

export interface UsePollingProps {
  timeoutMs?: number;
  activePollingInterval?: number;
  waitingPollingInterval?: number;
}

export interface UsePollingReturn {
  pollForQuestionnaires: (
    flowId: string,
    flowResponse: { id: string; status?: string }
  ) => Promise<{
    questionnaires: CollectionQuestionnaire[];
    timeoutReached: boolean;
  }>;
}

/**
 * HTTP polling hook for questionnaire generation
 * CRITICAL: NO WebSockets - uses HTTP polling for Railway compatibility
 *
 * @param timeoutMs - Maximum time to wait for questionnaires (default: 120000ms / 2 minutes)
 * @param activePollingInterval - Polling interval when flow is active (default: 2000ms)
 * @param waitingPollingInterval - Polling interval when waiting (default: 5000ms)
 */
export function usePolling({
  // Bug #28 Fix: Increased timeout from 30s to 120s to match actual generation time
  // Intelligent questionnaire generation with 6-source gap analysis takes ~90s
  // Add 30s buffer for network latency and retry handling
  timeoutMs = 120000, // 120 seconds (2 minutes) to allow full generation
  activePollingInterval = 2000, // 2s for active processing
  waitingPollingInterval = 5000, // 5s for waiting states
}: UsePollingProps = {}): UsePollingReturn {
  // CRITICAL FIX: Store polling interval ID for cleanup
  const pollingIntervalIdRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Poll for questionnaires with HTTP requests
   * PRESERVED FROM ORIGINAL: Lines 811-930
   *
   * CRITICAL PATTERNS PRESERVED:
   * 1. Ref-based interval ID storage for cleanup
   * 2. Smart polling intervals (2s active, 5s waiting)
   * 3. Timeout handling with cleanup
   * 4. Flow status monitoring during polling
   */
  const pollForQuestionnaires = async (
    flowId: string,
    flowResponse: { id: string; status?: string }
  ): Promise<{
    questionnaires: CollectionQuestionnaire[];
    timeoutReached: boolean;
  }> => {
    let agentQuestionnaires: CollectionQuestionnaire[] = [];
    let timeoutReached = false;
    let flowStatus: CollectionFlowStatusResponse;
    // Bug #25: Track consecutive errors to stop polling after too many failures
    let consecutiveErrors = 0;
    const MAX_CONSECUTIVE_ERRORS = 5;

    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const poll = async () => {
        try {
          const elapsed = Date.now() - startTime;

          // Check timeout
          if (elapsed >= timeoutMs) {
            timeoutReached = true;
            console.warn(`⚠️ HTTP polling timeout after ${elapsed}ms`);
            if (pollingIntervalIdRef.current) {
              clearInterval(pollingIntervalIdRef.current);
              pollingIntervalIdRef.current = null;
            }
            resolve({ questionnaires: agentQuestionnaires, timeoutReached });
            return;
          }

          // Check flow status to monitor phase progression
          flowStatus = await collectionFlowApi.getFlowStatus();
          // Bug #25: Reset error counter on successful status fetch
          consecutiveErrors = 0;
          console.log(`📊 Flow status check (${elapsed}ms elapsed):`, {
            status: flowStatus.status,
            current_phase: flowStatus.current_phase,
            message: flowStatus.message,
          });

          // Handle terminal flow states (completed, cancelled, failed, aborted, etc.)
          // Use isFlowTerminal helper from flowStates.ts as single source of truth
          if (
            isFlowTerminal(flowStatus.status) &&
            flowStatus.status !== "completed"
          ) {
            console.error(
              `❌ Collection flow entered terminal state '${flowStatus.status}':`,
              flowStatus.message
            );
            if (pollingIntervalIdRef.current) {
              clearInterval(pollingIntervalIdRef.current);
              pollingIntervalIdRef.current = null;
            }
            reject(
              new Error(
                `Collection flow ended with status '${flowStatus.status}': ${flowStatus.message || "Please retry or contact support"}`
              )
            );
            return;
          }

          // Try to fetch questionnaires
          try {
            agentQuestionnaires =
              await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
            if (agentQuestionnaires.length > 0) {
              // Check if this is a bootstrap questionnaire for asset selection
              const isBootstrap = agentQuestionnaires[0].id === 'bootstrap_asset_selection';

              if (isBootstrap) {
                console.log(
                  `🎯 Found bootstrap asset selection questionnaire - using immediately`,
                );
              } else {
                console.log(
                  `✅ Found ${agentQuestionnaires.length} agent-generated questionnaires after ${elapsed}ms`,
                );
              }

              if (pollingIntervalIdRef.current) {
                clearInterval(pollingIntervalIdRef.current);
                pollingIntervalIdRef.current = null;
              }
              resolve({ questionnaires: agentQuestionnaires, timeoutReached });
              return;
            }
          } catch (fetchError: unknown) {
            // For errors, continue polling
            const fetchErrorObj = fetchError as {
              message?: string;
            };
            // Only log as warning if it's an actual error, not just pending status
            if (fetchErrorObj.message?.includes('pending') || fetchErrorObj.message?.includes('generating')) {
              console.log(
                `⏳ Questionnaires still generating, continuing to poll...`,
              );
            } else {
              console.log(
                `⏳ Waiting for questionnaires, continuing to poll...`,
              );
            }
          }

          console.log(
            `⏳ Still waiting for questionnaires... (${elapsed}ms elapsed)`,
          );
        } catch (error: unknown) {
          // Re-throw flow errors, but continue polling on questionnaire fetch errors
          const errorObj = error as { message?: string };
          if (errorObj?.message?.includes("Collection flow failed")) {
            if (pollingIntervalIdRef.current) {
              clearInterval(pollingIntervalIdRef.current);
              pollingIntervalIdRef.current = null;
            }
            reject(error);
            return;
          }

          // Bug #25: Track consecutive errors and stop after too many
          consecutiveErrors++;
          const errorMessage = error instanceof Error ? error.message : String(error);
          console.log(
            `⏳ Still waiting for questionnaires... polling error (${consecutiveErrors}/${MAX_CONSECUTIVE_ERRORS}): ${errorMessage}`,
          );

          // Bug #25: Stop polling after MAX_CONSECUTIVE_ERRORS to prevent endless error loop
          if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            console.error(`❌ Stopping polling after ${MAX_CONSECUTIVE_ERRORS} consecutive errors`);
            if (pollingIntervalIdRef.current) {
              clearInterval(pollingIntervalIdRef.current);
              pollingIntervalIdRef.current = null;
            }
            reject(new Error(`Polling failed after ${MAX_CONSECUTIVE_ERRORS} consecutive errors. Last error: ${errorMessage}`));
            return;
          }
        }
      };

      // Start polling immediately
      poll();

      // Smart polling interval based on flow state
      const isActive =
        flowStatus?.status === "running" ||
        flowStatus?.current_phase === "processing";
      const pollInterval = isActive ? activePollingInterval : waitingPollingInterval;
      pollingIntervalIdRef.current = setInterval(poll, pollInterval);
    });
  };

  return {
    pollForQuestionnaires,
  };
}
