/**
 * useApprovalForm Hook
 * Manages approval request form state and submission
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/ui/use-toast';
import type { ApprovalFormData, ApprovalRequest } from '../types';
import { validateApprovalForm } from '../utils/validationHelpers';

const defaultFormData: ApprovalFormData = {
  title: '',
  description: '',
  request_type: 'policy_exception',
  scope: 'application',
  scope_id: '',
  business_justification: '',
  risk_assessment: '',
  mitigation_measures: '',
  priority: 'medium'
};

interface UseApprovalFormReturn {
  formData: ApprovalFormData;
  setFormData: React.Dispatch<React.SetStateAction<ApprovalFormData>>;
  isDialogOpen: boolean;
  setIsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isSubmitting: boolean;
  handleSubmit: () => void;
  resetForm: () => void;
}

export function useApprovalForm(): UseApprovalFormReturn {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<ApprovalFormData>(defaultFormData);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Create approval request mutation
  const createMutation = useMutation({
    mutationFn: async (data: ApprovalFormData): Promise<ApprovalRequest> => {
      // TODO: Replace with actual API call: apiCall('/api/v1/collection/governance/approval-requests', { method: 'POST', body: JSON.stringify(data) })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        id: Date.now().toString(),
        ...data,
        requested_by: 'Current User',
        status: 'pending',
        created_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-requests'] });
      setIsDialogOpen(false);
      resetForm();
      toast({
        title: 'Approval Request Submitted',
        description: 'Your approval request has been submitted for review.'
      });
    },
    onError: (error) => {
      console.error('Failed to create approval request:', error);
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit approval request. Please try again.',
        variant: 'destructive'
      });
    }
  });

  const resetForm = (): void => {
    setFormData(defaultFormData);
  };

  const handleSubmit = (): void => {
    const validation = validateApprovalForm(formData);

    if (!validation.isValid) {
      toast({
        title: 'Validation Error',
        description: validation.errors.join(', '),
        variant: 'destructive'
      });
      return;
    }

    createMutation.mutate(formData);
  };

  return {
    formData,
    setFormData,
    isDialogOpen,
    setIsDialogOpen,
    isSubmitting: createMutation.isPending,
    handleSubmit,
    resetForm
  };
}
