import { useState } from 'react';
import type { SixRDecision } from '@/hooks/useAssessmentFlow';
import type { FieldValues } from 'react-hook-form';

interface SixRSubmissionData extends FieldValues {
  sixrDecisions: Record<string, SixRDecision>;
}

interface UseSixRSubmissionProps {
  sixrDecisions: Record<string, SixRDecision>;
  updateSixRDecision: (appId: string, decision: Partial<SixRDecision>) => void;
  resumeFlow: (data: SixRSubmissionData) => Promise<void>;
  selectedApp: string;
  currentAppDecision: SixRDecision | null;
}

export const useSixRSubmission = ({
  sixrDecisions,
  updateSixRDecision,
  resumeFlow,
  selectedApp,
  currentAppDecision
}: UseSixRSubmissionProps): any => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);

  const handleSaveDraft = async (): void => {
    if (!selectedApp || !currentAppDecision) return;

    setIsDraft(true);
    try {
      await updateSixRDecision(selectedApp, currentAppDecision);
    } catch (error) {
      console.error('Failed to save draft:', error);
      throw error;
    } finally {
      setIsDraft(false);
    }
  };

  const handleSubmit = async (): void => {
    setIsSubmitting(true);
    try {
      // Save all application decisions
      for (const [appId, decision] of Object.entries(sixrDecisions)) {
        await updateSixRDecision(appId, decision);
      }

      await resumeFlow({
        sixrDecisions: sixrDecisions
      } as SixRSubmissionData);
    } catch (error) {
      console.error('Failed to submit 6R strategy review:', error);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    isSubmitting,
    isDraft,
    handleSaveDraft,
    handleSubmit
  };
};
