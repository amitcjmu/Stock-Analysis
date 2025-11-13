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
}: UseSixRSubmissionProps): unknown => {
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

      // Trigger backend agent to start processing
      const response = await resumeFlow({
        sixrDecisions: sixrDecisions
      } as SixRSubmissionData);

      console.log('✅ 6R submission complete, agent triggered:', response);
      console.log('⏳ Complexity analysis agent is now processing in background...');
      console.log('💡 Click "Check Status" button to check if agent has completed');

      // The agent is now processing in the background
      // The UI will show status === "processing" with a "Check Status" button
      // User can click the button to manually check if agent completed and navigate
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
