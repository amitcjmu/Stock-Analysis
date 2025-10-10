/**
 * Flow Details Card Component
 *
 * Displays detailed information and controls for a selected collection flow.
 * Extracted from Progress.tsx to create a focused, reusable component.
 */

import React, { useState } from "react";
import {
  Play,
  Pause,
  Square,
  ArrowRight,
  AlertCircle,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Trash2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useNavigate } from "react-router-dom";
import { collectionFlowApi } from "@/services/api/collection-flow";
import { useToast } from "@/hooks/use-toast";
import { FLOW_PHASE_ROUTES } from "@/config/flowRoutes";

export interface CollectionFlow {
  id: string;
  name: string;
  type: "adaptive" | "bulk" | "integration";
  status: "running" | "paused" | "completed" | "failed";
  progress: number;
  started_at: string;
  completed_at?: string;
  estimated_completion?: string;
  application_count: number;
  completed_applications: number;
}

export interface FlowDetailsCardProps {
  flow: CollectionFlow;
  onFlowAction: (
    flowId: string,
    action: "pause" | "resume" | "stop",
  ) => Promise<void>;
  className?: string;
  readiness?: {
    apps_ready_for_assessment: number;
    phase_scores: { collection: number; discovery: number };
    quality: { collection_quality_score: number; confidence_score: number };
  } | null;
}

export const FlowDetailsCard: React.FC<FlowDetailsCardProps> = ({
  flow,
  onFlowAction,
  className = "",
  readiness,
}) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isCheckingReadiness, setIsCheckingReadiness] = useState(false);
  const [showAppSelection, setShowAppSelection] = useState(false);
  const [isPollingForQuestionnaires, setIsPollingForQuestionnaires] =
    useState(false);
  const [pollingMessage, setPollingMessage] = useState(
    "Preparing questionnaire...",
  );
  const [pollStartTime, setPollStartTime] = useState<number>(0);

  const handleAction = async (action: "pause" | "resume" | "stop"): void => {
    await onFlowAction(flow.id, action);
  };

  const handleDelete = async (): Promise<void> => {
    if (
      !confirm(
        "Are you sure you want to delete this collection flow? This action cannot be undone.",
      )
    ) {
      return;
    }

    try {
      await collectionFlowApi.deleteFlow(flow.id, true); // force delete
      toast({
        title: "Flow Deleted",
        description: "Collection flow has been deleted successfully.",
        variant: "default",
      });

      // Navigate back to collection overview
      navigate("/collection");
    } catch (error) {
      console.error("Error deleting flow:", error);
      toast({
        title: "Delete Failed",
        description: "Failed to delete the collection flow. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleContinue = async (): Promise<void> => {
    setIsCheckingReadiness(true);
    setShowAppSelection(false);

    try {
      // Check if flow is completed (100% progress or completed status)
      if (flow.status === "completed" || flow.progress === 100) {
        try {
          // Check readiness for assessment transition
          const readinessData = await collectionFlowApi.getFlowReadiness(
            flow.id,
          );

          // Check if we have enough data for assessment
          const isReadyForAssessment =
            readinessData.apps_ready_for_assessment > 0 &&
            readinessData.quality.collection_quality_score >= 60 &&
            readinessData.quality.confidence_score >= 50;

          if (isReadyForAssessment) {
            // Transition to assessment
            const transitionResult =
              await collectionFlowApi.transitionToAssessment(flow.id);

            toast({
              title: "Transitioning to Assessment",
              description: "Collection complete. Moving to assessment phase...",
              variant: "default",
            });

            // Navigate to assessment flow
            setTimeout(() => {
              navigate(
                `/assessment/${transitionResult.assessment_flow_id}/overview`,
              );
            }, 1000);

            return;
          }
        } catch (error) {
          console.error("Error checking readiness or transitioning:", error);
        }

        // If not ready for assessment or error, go to overview
        toast({
          title: "Collection Complete",
          description:
            "Review your collection data before proceeding to assessment.",
          variant: "default",
        });
        navigate(`/collection/overview?flowId=${flow.id}`);
        return;
      }

      // CRITICAL FIX: For incomplete flows, route to CURRENT phase page to show progress
      // DO NOT call continueFlow() which advances the phase - user needs to see current results first
      try {
        console.log("🧭 Routing to current phase for flow:", flow.id);
        const flowDetails = await collectionFlowApi.getFlow(flow.id);

        const currentPhase = flowDetails.current_phase || 'asset_selection';
        console.log(`📍 Current phase: ${currentPhase}`);

        // Per ADR-012: status determines lifecycle, current_phase determines operational state
        // Route to the CURRENT phase page so user can see progress/results
        const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

        if (phaseRoute) {
          const targetRoute = phaseRoute(flow.id);
          console.log(`🧭 Navigating to ${currentPhase} phase: ${targetRoute}`);
          toast({
            title: "Continuing Flow",
            description: `Opening ${currentPhase.replace('_', ' ')} page...`,
            variant: "default",
          });
          navigate(targetRoute);
          return;
        } else {
          console.warn(`⚠️ No route found for phase: ${currentPhase}`);
          // Fallback: try to get questionnaires
          const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flow.id);
          if (questionnaires.length > 0) {
            console.log(`📋 Found ${questionnaires.length} questionnaires, routing to adaptive-forms`);
            navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
            return;
          }
        }
      } catch (error: unknown) {
        // Handle 422 'no_applications_selected' error
        if (
          error &&
          typeof error === "object" &&
          "status" in error &&
          "code" in error &&
          (error as { status: number; code: string }).status === 422 &&
          (error as { status: number; code: string }).code === "no_applications_selected"
        ) {
          console.log("⚠️ No applications selected for flow, showing app selection UI");
          setShowAppSelection(true);
          return;
        }

        console.warn("⚠️ Error routing to phase, trying questionnaire check:", error);
      }

      // If no phase route found, start polling for questionnaires as fallback
      console.log("⏳ No phase route available, starting polling for questionnaires...");
      await pollForQuestionnaires();
    } catch (error: any) {
      console.error("Error in handleContinue:", error);

      // Extract user-friendly error message from backend response
      let errorTitle = "Error Continuing Flow";
      let errorDescription = "Failed to continue flow. Please try again.";

      if (error && typeof error === "object") {
        // Check if it's an API error response with detail
        if (error.detail) {
          if (typeof error.detail === "object") {
            errorTitle = error.detail.message || errorTitle;
            errorDescription = error.detail.required_action || error.detail.mfo_error || errorDescription;
          } else if (typeof error.detail === "string") {
            errorDescription = error.detail;
          }
        }
        // Check if it's a standard Error object
        else if (error.message) {
          errorDescription = error.message;
        }
      }

      toast({
        title: errorTitle,
        description: errorDescription,
        variant: "destructive",
        duration: 10000, // Show error for 10 seconds instead of default
      });
    } finally {
      setIsCheckingReadiness(false);
    }
  };

  const pollForQuestionnaires = async (): Promise<void> => {
    setIsPollingForQuestionnaires(true);
    setPollStartTime(Date.now());
    setPollingMessage("Preparing questionnaire...");

    const POLL_TIMEOUT = 90 * 1000; // 90 seconds total
    const INITIAL_POLL_PERIOD = 30 * 1000; // First 30 seconds
    const INITIAL_POLL_INTERVAL = 2 * 1000; // 2 seconds
    const EXTENDED_POLL_INTERVAL = 5 * 1000; // 5 seconds

    const startTime = Date.now();
    let currentInterval = INITIAL_POLL_INTERVAL;

    const poll = async () => {
      const elapsed = Date.now() - startTime;

      // Update message after 30 seconds
      if (
        elapsed > INITIAL_POLL_PERIOD &&
        pollingMessage === "Preparing questionnaire..."
      ) {
        setPollingMessage(
          "Still preparing... This is taking longer than expected.",
        );
        currentInterval = EXTENDED_POLL_INTERVAL;
      }

      // Check for timeout
      if (elapsed >= POLL_TIMEOUT) {
        setIsPollingForQuestionnaires(false);
        toast({
          title: "Timeout",
          description:
            "Questionnaire preparation took too long. Please try again.",
          variant: "destructive",
        });
        return;
      }

      try {
        const questionnaires = await collectionFlowApi.getFlowQuestionnaires(
          flow.id,
        );

        if (questionnaires.length > 0) {
          setIsPollingForQuestionnaires(false);
          console.log(
            "✅ Questionnaires ready after polling, checking flow phase for navigation",
          );

          // Get flow details to determine current phase for proper routing
          try {
            const flowDetails = await collectionFlowApi.getFlow(flow.id);

            // Per ADR-012: status determines lifecycle, current_phase determines operational state
            // If flow is completed, always route to summary page
            if (flowDetails.status === 'completed') {
              console.log(`🧭 Flow is completed, navigating to summary page`);
              navigate(`/collection/summary/${flow.id}`);
              return;
            }

            const currentPhase = flowDetails.current_phase || 'asset_selection';
            const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

            if (phaseRoute) {
              const targetRoute = phaseRoute(flow.id);
              console.log(`🧭 Navigating to ${currentPhase} phase: ${targetRoute}`);
              navigate(targetRoute);
            } else {
              console.warn(`⚠️ No route found for phase: ${currentPhase}, falling back to adaptive-forms`);
              navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
            }
          } catch (error) {
            console.warn('⚠️ Failed to get flow details for phase routing, using fallback:', error);
            navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
          }
          return;
        }
      } catch (error: unknown) {
        // Handle 422 'no_applications_selected' error during polling
        if (
          error &&
          typeof error === "object" &&
          "status" in error &&
          "code" in error &&
          (error as { status: number; code: string }).status === 422 &&
          (error as { status: number; code: string }).code ===
            "no_applications_selected"
        ) {
          setIsPollingForQuestionnaires(false);
          setShowAppSelection(true);
          return;
        }
      }

      // Continue polling
      setTimeout(poll, currentInterval);
    };

    // Start polling
    setTimeout(poll, currentInterval);
  };

  const handleCancelPolling = (): void => {
    setIsPollingForQuestionnaires(false);
    setPollingMessage("Preparing questionnaire...");
  };

  const handleSelectApplications = (): void => {
    navigate(`/collection/select-applications?flowId=${flow.id}`);
  };

  const handleCloseAppSelection = (): void => {
    setShowAppSelection(false);
  };

  // Check if flow is stuck (running but with 0% progress)
  const isFlowStuck = flow.status === "running" && flow.progress === 0;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="line-clamp-2">{flow.name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Started: {new Date(flow.started_at).toLocaleString()}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {/* Continue button for stuck or completed flows */}
            {(isFlowStuck ||
              flow.status === "completed" ||
              flow.progress === 100) && (
              <Button
                variant="default"
                size="sm"
                onClick={handleContinue}
                disabled={isCheckingReadiness}
                title={
                  flow.status === "completed"
                    ? "Continue to Assessment"
                    : "Continue Flow"
                }
              >
                {isCheckingReadiness ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Checking...
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-4 w-4 mr-1" />
                    Continue
                  </>
                )}
              </Button>
            )}

            {flow.status === "running" && !isFlowStuck && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction("pause")}
                title="Pause Flow"
              >
                <Pause className="h-4 w-4" />
              </Button>
            )}

            {flow.status === "paused" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction("resume")}
                title="Resume Flow"
              >
                <Play className="h-4 w-4" />
              </Button>
            )}

            {(flow.status === "running" || flow.status === "paused") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction("stop")}
                title="Stop Flow"
              >
                <Square className="h-4 w-4" />
              </Button>
            )}

            {/* Delete button for failed flows or any flow that needs to be removed */}
            {(flow.status === "failed" ||
              flow.status === "completed" ||
              flow.status === "paused") && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                title="Delete Flow"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Progress</span>
              <span className="text-muted-foreground">
                {Math.round(flow.progress)}%
              </span>
            </div>
            <Progress value={flow.progress} className="h-3" />
          </div>

          {/* Flow Details Grid */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">Applications:</span>
                <div className="font-medium">
                  {flow.completed_applications} / {flow.application_count}
                  <span className="text-xs text-muted-foreground ml-1">
                    (
                    {Math.round(
                      (flow.completed_applications / flow.application_count) *
                        100,
                    )}
                    %)
                  </span>
                </div>
              </div>

              <div>
                <span className="text-muted-foreground">Type:</span>
                <div className="font-medium capitalize">{flow.type}</div>
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">Status:</span>
                <div
                  className={`font-medium capitalize ${
                    flow.status === "running"
                      ? "text-blue-600"
                      : flow.status === "completed"
                        ? "text-green-600"
                        : flow.status === "failed"
                          ? "text-red-600"
                          : "text-yellow-600"
                  }`}
                >
                  {flow.status}
                </div>
              </div>

              {flow.estimated_completion && flow.status === "running" && (
                <div>
                  <span className="text-muted-foreground">ETA:</span>
                  <div className="font-medium text-xs">
                    {new Date(flow.estimated_completion).toLocaleString()}
                  </div>
                </div>
              )}

              {flow.completed_at && (
                <div>
                  <span className="text-muted-foreground">Completed:</span>
                  <div className="font-medium text-xs">
                    {new Date(flow.completed_at).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Additional Status Information */}
          {readiness && (
            <div className="mt-2 p-3 bg-muted/30 border rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Apps Ready</span>
                  <div className="font-medium">
                    {readiness.apps_ready_for_assessment}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">
                    Collection Score
                  </span>
                  <div className="font-medium">
                    {Math.round(readiness.phase_scores.collection * 100)}%
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Discovery Score</span>
                  <div className="font-medium">
                    {Math.round(readiness.phase_scores.discovery * 100)}%
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">
                    Quality / Confidence
                  </span>
                  <div className="font-medium">
                    {readiness.quality.collection_quality_score || 0} /{" "}
                    {readiness.quality.confidence_score || 0}
                  </div>
                </div>
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                Intelligent gap analysis in progress. AI is enriching your data
                automatically; manual inputs will be requested only when needed.
              </div>
            </div>
          )}
          {/* Assessment Readiness Indicator for Completed Flows */}
          {(flow.status === "completed" || flow.progress === 100) &&
            readiness && (
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <AlertDescription>
                  <p className="font-medium text-green-800">
                    Collection Complete
                  </p>
                  <p className="text-sm text-green-700 mt-1">
                    {readiness.apps_ready_for_assessment > 0 &&
                    readiness.quality.collection_quality_score >= 60 &&
                    readiness.quality.confidence_score >= 50
                      ? 'Ready for assessment phase. Click "Continue" to transition.'
                      : `More data needed for assessment. Quality: ${readiness.quality.collection_quality_score}%, Confidence: ${readiness.quality.confidence_score}%`}
                  </p>
                </AlertDescription>
              </Alert>
            )}

          {isFlowStuck && (
            <Alert className="bg-amber-50 border-amber-200">
              <AlertCircle className="h-5 w-5 text-amber-600" />
              <AlertDescription>
                <p className="font-medium text-amber-800">
                  Flow appears to be stuck
                </p>
                <p className="text-sm text-amber-700 mt-1">
                  The flow is not making progress. Click "Continue" to proceed
                  with the data collection process.
                </p>
              </AlertDescription>
            </Alert>
          )}

          {flow.status === "failed" && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                Flow execution failed. Check logs for detailed error
                information.
              </p>
            </div>
          )}

          {flow.status === "paused" && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Flow is currently paused. Resume to continue processing.
              </p>
            </div>
          )}

          {/* Polling for questionnaires feedback */}
          {isPollingForQuestionnaires && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                  <div>
                    <p className="font-medium text-blue-900">
                      {pollingMessage}
                    </p>
                    <p className="text-sm text-blue-700 mt-1">
                      Elapsed: {Math.floor((Date.now() - pollStartTime) / 1000)}
                      s
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancelPolling}
                  className="text-blue-600 border-blue-300"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Application selection UI */}
          {showAppSelection && (
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-amber-900 mb-2">
                    Applications Required
                  </h4>
                  <p className="text-sm text-amber-800 mb-4">
                    This flow needs applications selected before questionnaires
                    can be generated. Please select the applications you want to
                    collect data for.
                  </p>
                  <div className="flex space-x-2">
                    <Button
                      onClick={handleSelectApplications}
                      variant="default"
                      size="sm"
                      className="bg-amber-600 hover:bg-amber-700"
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Select Applications
                    </Button>
                    <Button
                      onClick={handleCloseAppSelection}
                      variant="outline"
                      size="sm"
                      className="text-amber-600 border-amber-300"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default FlowDetailsCard;
