/**
 * Assessment Flow Hook
 *
 * Main React hook for managing assessment flow state and operations.
 */

import { useState, useRef } from "react";
import { useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { assessmentFlowAPI } from "./api";
import type {
  AssessmentFlowState,
  AssessmentFlowStatus,
  AssessmentPhase,
  UseAssessmentFlowReturn,
  ArchitectureStandard,
  ApplicationComponent,
  TechDebtItem,
  SixRDecision,
  UserInput,
  AssessmentApplication,
} from "./types";

export const useAssessmentFlow = (
  initialFlowId?: string,
): UseAssessmentFlowReturn => {
  const navigate = useNavigate();
  const { user, client, engagement, getAuthHeaders } = useAuth();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Get client account and engagement from auth context
  const clientAccountId = client?.id;
  const engagementId = engagement?.id;

  // Initial state
  const [state, setState] = useState<AssessmentFlowState>({
    flowId: initialFlowId || null,
    status: "initialized",
    progress: 0,
    currentPhase: "architecture_minimums",
    nextPhase: null,
    pausePoints: [],
    selectedApplicationIds: [],
    selectedApplications: [], // Add application details
    applicationCount: 0, // Add application count
    engagementStandards: [],
    applicationOverrides: {},
    applicationComponents: {},
    techDebtAnalysis: {},
    sixrDecisions: {},
    isLoading: false,
    error: null,
    lastUserInteraction: null,
    appsReadyForPlanning: [],
    agentUpdates: [],
  });

  // Load phase-specific data - DEFINED EARLY to avoid initialization errors
  const loadPhaseData = useCallback(
    async (phase: AssessmentPhase): Promise<void> => {
      if (!state.flowId) return;

      try {
        switch (phase) {
          case "asset_application_resolution": {
            // Asset resolution data is fetched directly in the page component
            // No additional loading needed here
            break;
          }

          case "architecture_minimums": {
            const archData = await assessmentFlowAPI.getArchitectureStandards(
              state.flowId,
            );
            setState((prev) => ({
              ...prev,
              engagementStandards: archData.engagement_standards,
              applicationOverrides: archData.application_overrides,
            }));
            break;
          }

          case "tech_debt_analysis": {
            const techDebtData = await assessmentFlowAPI.getTechDebtAnalysis(
              state.flowId,
            );
            const componentsData =
              await assessmentFlowAPI.getApplicationComponents(state.flowId);
            setState((prev) => ({
              ...prev,
              techDebtAnalysis: techDebtData.applications,
              applicationComponents: componentsData.applications,
            }));
            break;
          }

          case "component_sixr_strategies":
          case "app_on_page_generation": {
            const decisionsData = await assessmentFlowAPI.getSixRDecisions(
              state.flowId,
            );
            setState((prev) => ({
              ...prev,
              sixrDecisions: decisionsData.decisions.reduce(
                (acc: Record<string, SixRDecision>, decision: SixRDecision) => {
                  acc[decision.application_id] = decision;
                  return acc;
                },
                {},
              ),
            }));
            break;
          }
        }
      } catch (error) {
        console.error(`Failed to load ${phase} data:`, error);
      }
    },
    [state.flowId],
  );

  // Start HTTP/2 polling for status updates
  const startPolling = useCallback(() => {
    if (!state.flowId || !clientAccountId || pollingIntervalRef.current) return;

    const pollStatus = async () => {
      try {
        const status = await assessmentFlowAPI.getStatus(
          state.flowId,
          clientAccountId,
          engagementId,
        );

        setState((prev) => {
          const nextProgress =
            typeof status.progress === "number"
              ? Math.max(prev.progress ?? 0, status.progress)
              : prev.progress;

          // Detect phase change to trigger data reload (Bug #664 fix)
          const phaseChanged = prev.currentPhase !== status.current_phase;

          // Schedule phase data reload if phase changed
          if (phaseChanged && status.current_phase) {
            // Use setTimeout to avoid blocking the setState
            setTimeout(() => {
              loadPhaseData(status.current_phase as AssessmentPhase);
            }, 0);
          }

          return {
            ...prev,
            status: status.status as AssessmentFlowStatus,
            progress: nextProgress,
            currentPhase: status.current_phase as AssessmentPhase,
            applicationCount: status.application_count,
            error: null, // Clear error on successful poll
          };
        });
      } catch (error) {
        console.error("Assessment flow polling error:", error);
        // Don't set error state - allow retries
      }
    };

    // Poll immediately, then every 5 seconds
    pollStatus();
    pollingIntervalRef.current = setInterval(pollStatus, 5000);
  }, [state.flowId, clientAccountId, engagementId, loadPhaseData]);

  // Initialize assessment flow
  const initializeFlow = useCallback(
    async (selectedAppIds: string[]) => {
      if (!clientAccountId || !engagementId) {
        throw new Error("Client account and engagement context required");
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const headers = getAuthHeaders?.() || {};
        const response = await assessmentFlowAPI.initialize(
          {
            selected_application_ids: selectedAppIds,
          },
          headers,
        );

        setState((prev) => ({
          ...prev,
          flowId: response.flow_id,
          status: response.status as AssessmentFlowStatus,
          currentPhase: response.current_phase as AssessmentPhase,
          nextPhase: response.next_phase as AssessmentPhase,
          selectedApplicationIds: selectedAppIds,
          progress: 10,
          isLoading: false,
        }));

        // Start HTTP/2 polling
        startPolling();

        // Navigate to first phase
        if (navigate) {
          navigate(`/assessment/${response.flow_id}/architecture`);
        }
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to initialize assessment",
          isLoading: false,
        }));
        throw error;
      }
    },
    [
      clientAccountId,
      engagementId,
      navigate,
      getAuthHeaders,
      startPolling,
    ],
  );

  // Resume flow from current phase
  const resumeFlow = useCallback(
    async (userInput: UserInput) => {
      if (!state.flowId) {
        throw new Error("No active flow to resume");
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await assessmentFlowAPI.resume(state.flowId, {
          user_input: userInput,
          save_progress: true,
        });

        // Update state with new phase from backend response (ADR-027)
        setState((prev) => ({
          ...prev,
          status: "processing",
          currentPhase: response.current_phase as AssessmentPhase,
          progress: response.progress || prev.progress,
          lastUserInteraction: new Date(),
          isLoading: false,
        }));

        return response; // Return response for navigation
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error ? error.message : "Failed to resume flow",
          isLoading: false,
        }));
        throw error;
      }
    },
    [state.flowId],
  );

  // Utility function to check if navigation to phase is allowed
  const canNavigateToPhase = useCallback(
    (phase: AssessmentPhase): boolean => {
      const phaseOrder: AssessmentPhase[] = [
        "initialization",
        "asset_application_resolution",
        "architecture_minimums",
        "tech_debt_analysis",
        "component_sixr_strategies",
        "app_on_page_generation",
        "finalization",
      ];

      const currentIndex = phaseOrder.indexOf(state.currentPhase);
      const targetIndex = phaseOrder.indexOf(phase);

      // Can navigate to current phase or any previous completed phase
      return targetIndex <= currentIndex || state.pausePoints.includes(phase);
    },
    [state.currentPhase, state.pausePoints],
  );

  // Navigate to specific phase
  const navigateToPhase = useCallback(
    async (phase: AssessmentPhase) => {
      if (!state.flowId) {
        throw new Error("No active flow for navigation");
      }

      if (!canNavigateToPhase(phase)) {
        throw new Error(`Cannot navigate to phase: ${phase}`);
      }

      try {
        await assessmentFlowAPI.navigateToPhase(state.flowId, phase);

        setState((prev) => ({
          ...prev,
          currentPhase: phase,
          nextPhase: getNextPhaseForNavigation(phase),
        }));

        // Update URL
        const phaseRoutes: Record<AssessmentPhase, string> = {
          initialization: "initialize",
          asset_application_resolution: "asset-resolution",
          architecture_minimums: "architecture",
          tech_debt_analysis: "tech-debt",
          component_sixr_strategies: "sixr-review",
          app_on_page_generation: "app-on-page",
          finalization: "summary",
        };

        if (navigate) {
          navigate(`/assessment/${state.flowId}/${phaseRoutes[phase]}`);
        }
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error: error instanceof Error ? error.message : "Navigation failed",
        }));
        throw error;
      }
    },
    [state.flowId, navigate, canNavigateToPhase],
  );

  // Update architecture standards
  const updateArchitectureStandards = useCallback(
    async (
      standards: ArchitectureStandard[],
      overrides: Record<string, ArchitectureStandard>,
    ) => {
      if (!state.flowId) {
        throw new Error("No active flow");
      }

      try {
        await assessmentFlowAPI.updateArchitectureStandards(state.flowId, {
          engagement_standards: standards,
          application_overrides: overrides,
        });

        setState((prev) => ({
          ...prev,
          engagementStandards: standards,
          applicationOverrides: overrides,
          lastUserInteraction: new Date(),
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to update standards",
        }));
        throw error;
      }
    },
    [state.flowId],
  );

  // Update application components
  const updateApplicationComponents = useCallback(
    async (appId: string, components: ApplicationComponent[]) => {
      if (!state.flowId) {
        throw new Error("No active flow");
      }

      try {
        await assessmentFlowAPI.updateApplicationComponents(
          state.flowId,
          appId,
          components,
        );

        setState((prev) => ({
          ...prev,
          applicationComponents: {
            ...prev.applicationComponents,
            [appId]: components,
          },
          lastUserInteraction: new Date(),
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to update components",
        }));
        throw error;
      }
    },
    [state.flowId],
  );

  // Update tech debt analysis
  const updateTechDebtAnalysis = useCallback(
    async (appId: string, techDebt: TechDebtItem[]) => {
      if (!state.flowId) {
        throw new Error("No active flow");
      }

      try {
        // Note: API endpoint would need to be implemented for tech debt updates
        setState((prev) => ({
          ...prev,
          techDebtAnalysis: {
            ...prev.techDebtAnalysis,
            [appId]: techDebt,
          },
          lastUserInteraction: new Date(),
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to update tech debt analysis",
        }));
        throw error;
      }
    },
    [state.flowId],
  );

  // Update 6R decision
  const updateSixRDecision = useCallback(
    async (appId: string, decision: Partial<SixRDecision>) => {
      if (!state.flowId) {
        throw new Error("No active flow");
      }

      try {
        await assessmentFlowAPI.updateSixRDecision(
          state.flowId,
          appId,
          decision,
        );

        setState((prev) => ({
          ...prev,
          sixrDecisions: {
            ...prev.sixrDecisions,
            [appId]: {
              ...prev.sixrDecisions[appId],
              ...decision,
            } as SixRDecision,
          },
          lastUserInteraction: new Date(),
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to update decision",
        }));
        throw error;
      }
    },
    [state.flowId],
  );

  // Stop HTTP/2 polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Utility functions
  const getPhaseProgress = useCallback((phase: AssessmentPhase): number => {
    const progressMap: Record<AssessmentPhase, number> = {
      initialization: 5,
      asset_application_resolution: 15,
      architecture_minimums: 25,
      tech_debt_analysis: 50,
      component_sixr_strategies: 75,
      app_on_page_generation: 90,
      finalization: 100,
    };
    return progressMap[phase] || 0;
  }, []);

  const getApplicationsNeedingReview = useCallback((): string[] => {
    return Object.entries(state.sixrDecisions)
      .filter(([_, decision]) => decision.confidence_score < 0.8)
      .map(([appId, _]) => appId);
  }, [state.sixrDecisions]);

  const isPhaseComplete = useCallback(
    (phase: AssessmentPhase): boolean => {
      return state.pausePoints.includes(phase);
    },
    [state.pausePoints],
  );

  // loadPhaseData is now defined earlier in the file (line 60) to avoid initialization errors

  // Load application data
  const loadApplicationData = useCallback(async (): Promise<void> => {
    console.log('[useAssessmentFlow] loadApplicationData called', {
      flowId: state.flowId,
      clientAccountId,
      engagementId,
    });

    if (!state.flowId || !clientAccountId) {
      console.log('[useAssessmentFlow] Early return - missing flowId or clientAccountId', {
        flowId: state.flowId,
        clientAccountId,
      });
      return;
    }

    try {
      console.log('[useAssessmentFlow] Fetching application data...');
      // Load both status with count and full application details
      const [statusResponse, applicationsResponse] = await Promise.all([
        assessmentFlowAPI.getAssessmentStatus(
          state.flowId,
          clientAccountId,
          engagementId,
        ),
        assessmentFlowAPI.getAssessmentApplications(
          state.flowId,
          clientAccountId,
          engagementId,
        ),
      ]);

      console.log('[useAssessmentFlow] Application data loaded successfully', {
        applicationCount: statusResponse.application_count,
        applications: applicationsResponse.applications.length,
      });

      setState((prev) => ({
        ...prev,
        applicationCount: statusResponse.application_count,
        selectedApplications: applicationsResponse.applications,
        selectedApplicationIds: applicationsResponse.applications.map(
          (app) => app.application_id,
        ),
      }));
    } catch (error) {
      console.error("[useAssessmentFlow] Failed to load application data:", error);
      // Don't throw here - this is supplementary data
    }
  }, [state.flowId, clientAccountId, engagementId]);

  // Load current flow state
  const loadFlowState = useCallback(async (): Promise<void> => {
    if (!state.flowId || !clientAccountId) return;

    try {
      setState((prev) => ({ ...prev, isLoading: true }));

      // Call getStatus with required multi-tenant parameters
      const flowStatus = await assessmentFlowAPI.getStatus(
        state.flowId,
        clientAccountId,
        engagementId,
      );

      setState((prev) => ({
        ...prev,
        status: flowStatus.status as AssessmentFlowStatus,
        progress: flowStatus.progress,
        currentPhase: flowStatus.current_phase as AssessmentPhase,
        applicationCount: flowStatus.application_count,
        // Note: Backend doesn't return these fields, keep previous values
        // nextPhase: populated by phase logic
        // pausePoints: populated by phase completion
        // appsReadyForPlanning: populated by phase logic
        // Keep isLoading=true until ALL data loads (Bug #640 fix)
      }));

      // Load phase-specific data
      await loadPhaseData(flowStatus.current_phase as AssessmentPhase);

      // Load application data (full details)
      await loadApplicationData();

      // Only set isLoading=false after ALL data loading completes (Bug #640 fix)
      setState((prev) => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error ? error.message : "Failed to load flow state",
        isLoading: false,
      }));
    }
  }, [state.flowId, clientAccountId, engagementId, loadPhaseData, loadApplicationData]);

  // Load flow state on mount or flowId change
  useEffect(() => {
    if (state.flowId && clientAccountId) {
      loadFlowState();
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [
    state.flowId,
    clientAccountId,
    loadFlowState,
    startPolling,
    stopPolling,
  ]);

  // Expose loadApplicationData for manual refresh
  const refreshApplicationData = useCallback(() => {
    return loadApplicationData();
  }, [loadApplicationData]);

  // Helper function for navigation
  const getNextPhaseForNavigation = (
    currentPhase: AssessmentPhase,
  ): AssessmentPhase | null => {
    const phaseOrder: AssessmentPhase[] = [
      "initialization",
      "asset_application_resolution",
      "architecture_minimums",
      "tech_debt_analysis",
      "component_sixr_strategies",
      "app_on_page_generation",
      "finalization",
    ];

    const currentIndex = phaseOrder.indexOf(currentPhase);
    return currentIndex < phaseOrder.length - 1
      ? phaseOrder[currentIndex + 1]
      : null;
  };

  return {
    state,
    initializeFlow,
    resumeFlow,
    navigateToPhase,
    finalizeAssessment: async () => {
      if (!state.flowId) return;
      await assessmentFlowAPI.finalize(state.flowId);
    },
    updateArchitectureStandards,
    updateApplicationComponents,
    updateTechDebtAnalysis,
    updateSixRDecision,
    startPolling,
    stopPolling,
    getPhaseProgress,
    canNavigateToPhase,
    getApplicationsNeedingReview,
    isPhaseComplete,
    refreshApplicationData, // Add method to refresh application data
  };
};
