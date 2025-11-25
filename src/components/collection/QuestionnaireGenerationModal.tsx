/**
 * Modal component for showing questionnaire generation progress
 * Displays a progress bar that fills from 0% to 100% over 30 seconds
 * Polls the backend for questionnaire status during generation
 */

import React, { useEffect, useState, useRef } from "react";
import { Loader2, CheckCircle, AlertCircle, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { apiCall } from "@/config/api";

interface QuestionnaireData {
  questions: Array<{
    id: string;
    text: string;
    type: string;
    options?: string[];
  }>;
  metadata?: Record<string, unknown>;
}

interface QuestionnaireGenerationModalProps {
  isOpen: boolean;
  flowId: string | null;
  onComplete: (questionnaire: QuestionnaireData) => void;
  onFallback: () => void;
  onRetry?: () => void;
  onCancel?: () => void; // Bug #25: Allow user to cancel and navigate away
}

export const QuestionnaireGenerationModal: React.FC<
  QuestionnaireGenerationModalProps
> = ({ isOpen, flowId, onComplete, onFallback, onRetry, onCancel }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"generating" | "ready" | "fallback">(
    "generating"
  );
  const [message, setMessage] = useState(
    "Initializing intelligent questionnaire generation..."
  );
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Bug #893 Fix: Increased timeout from 30s to 90s to match backend agent execution time
  // Total generation time in milliseconds (90 seconds)
  const TOTAL_GENERATION_TIME = 90000;
  const POLLING_INTERVAL = 2000; // Poll every 2 seconds

  useEffect(() => {
    if (!isOpen || !flowId) {
      // Reset state when modal closes
      setProgress(0);
      setStatus("generating");
      return;
    }

    startTimeRef.current = Date.now();

    // Start progress bar animation
    progressIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      const progressPercent = Math.min(
        (elapsed / TOTAL_GENERATION_TIME) * 100,
        100
      );
      setProgress(progressPercent);

      // Update message based on progress
      if (progressPercent < 20) {
        setMessage("Analyzing your application portfolio...");
      } else if (progressPercent < 40) {
        setMessage("Identifying data gaps and requirements...");
      } else if (progressPercent < 60) {
        setMessage("Generating personalized questions...");
      } else if (progressPercent < 80) {
        setMessage("Optimizing questionnaire structure...");
      } else if (progressPercent < 100) {
        setMessage("Finalizing adaptive questionnaire...");
      } else {
        // Progress reached 100%, check final status
        if (status === "generating") {
          // If still generating after 30 seconds, fallback
          setStatus("fallback");
          setMessage("Using bootstrap questionnaire template");
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }
          setTimeout(() => onFallback(), 1000);
        }
      }
    }, 100); // Update progress every 100ms for smooth animation

    // Start polling for questionnaire status
    const pollForQuestionnaire = async () => {
      try {
        // Check if agent-generated questionnaire is ready
        const response = await apiCall(
          `/collection/flows/${flowId}/questionnaires/status`
        );

        if (response.status === "ready" && response.questionnaire) {
          // Questionnaire is ready!
          setStatus("ready");
          setMessage("Questionnaire generated successfully!");
          setProgress(100);

          // Clear intervals
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }

          // Call onComplete after a short delay
          setTimeout(() => onComplete(response.questionnaire), 1000);
        } else if (response.status === "error") {
          // Generation failed, use fallback
          console.error("Questionnaire generation failed:", response.error);
          setStatus("fallback");
          setMessage("Using fallback questionnaire template");

          // Clear intervals
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }

          setTimeout(() => onFallback(), 1000);
        }
        // If still generating, continue polling
      } catch (error) {
        console.error("Failed to poll questionnaire status:", error);
        // Continue polling despite errors
      }
    };

    // Start polling immediately
    pollForQuestionnaire();
    pollingIntervalRef.current = setInterval(pollForQuestionnaire, POLLING_INTERVAL);

    // Cleanup on unmount or when modal closes
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isOpen, flowId, onComplete, onFallback, status]);

  if (!isOpen) {
    return null;
  }

  // Bug #25: Handle cancel - cleanup intervals and call onCancel
  const handleCancel = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    onCancel?.();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleCancel()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {status === "generating" && (
              <>
                <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                Generating Adaptive Questionnaire
              </>
            )}
            {status === "ready" && (
              <>
                <CheckCircle className="h-5 w-5 text-green-600" />
                Questionnaire Ready
              </>
            )}
            {status === "fallback" && (
              <>
                <AlertCircle className="h-5 w-5 text-amber-600" />
                Using Template Questionnaire
              </>
            )}
          </DialogTitle>
          <DialogDescription className="mt-2">
            {message}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {status === "generating" && (
            <div className="space-y-3">
              <div className="text-sm text-gray-500">
                <p>
                  Our AI agents are analyzing your requirements and generating a
                  personalized questionnaire. This typically takes 30-60 seconds.
                </p>
              </div>
              {/* Bug #25: Add cancel button to allow navigation away */}
              {onCancel && (
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  size="sm"
                  className="w-full"
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel and Navigate Away
                </Button>
              )}
            </div>
          )}

          {status === "ready" && (
            <div className="text-sm text-green-600">
              <p>
                Your adaptive questionnaire has been generated successfully!
                Loading the form now...
              </p>
            </div>
          )}

          {status === "fallback" && (
            <div className="space-y-3">
              <div className="text-sm text-amber-600">
                <p>
                  The AI-generated questionnaire is taking longer than expected.
                  We're loading a comprehensive template questionnaire instead.
                </p>
              </div>
              {onRetry && (
                <Button
                  onClick={onRetry}
                  variant="outline"
                  size="sm"
                  className="w-full"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Check for AI Questionnaire
                </Button>
              )}
            </div>
          )}
        </div>

        <div className="mt-4 text-xs text-gray-400 text-center">
          Flow ID: {flowId || "Initializing..."}
        </div>
      </DialogContent>
    </Dialog>
  );
};
