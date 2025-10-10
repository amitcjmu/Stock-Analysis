/**
 * useExceptionForm Hook
 * Manages migration exception form state and submission
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/ui/use-toast';
import type { ExceptionFormData, MigrationException, GovernanceRequirement } from '../types';
import { validateExceptionForm } from '../utils/validationHelpers';

const defaultFormData: ExceptionFormData = {
  requirement_id: '',
  title: '',
  justification: '',
  business_impact: '',
  mitigation_plan: '',
  scope: 'application',
  scope_id: '',
  priority: 'medium'
};

interface UseExceptionFormReturn {
  formData: ExceptionFormData;
  setFormData: React.Dispatch<React.SetStateAction<ExceptionFormData>>;
  isDialogOpen: boolean;
  setIsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  selectedRequirement: GovernanceRequirement | null;
  isSubmitting: boolean;
  handleSubmit: () => void;
  handleRequestException: (requirement: GovernanceRequirement) => void;
  resetForm: () => void;
}

export function useExceptionForm(): UseExceptionFormReturn {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<ExceptionFormData>(defaultFormData);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState<GovernanceRequirement | null>(null);

  // Create exception mutation
  const createMutation = useMutation({
    mutationFn: async (data: ExceptionFormData): Promise<MigrationException> => {
      // TODO: Replace with actual API call: apiCall('/api/v1/collection/governance/exceptions', { method: 'POST', body: JSON.stringify(data) })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        id: Date.now().toString(),
        ...data,
        requested_by: 'Current User',
        status: 'pending',
        approval_history: [],
        created_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['migration-exceptions'] });
      setIsDialogOpen(false);
      resetForm();
      toast({
        title: 'Exception Request Submitted',
        description: 'Your migration exception request has been submitted for approval.'
      });
    },
    onError: (error) => {
      console.error('Failed to create exception:', error);
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit exception request. Please try again.',
        variant: 'destructive'
      });
    }
  });

  const resetForm = (): void => {
    setFormData(defaultFormData);
    setSelectedRequirement(null);
  };

  const handleSubmit = (): void => {
    const validation = validateExceptionForm(formData);

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

  const handleRequestException = (requirement: GovernanceRequirement): void => {
    setSelectedRequirement(requirement);
    setFormData({
      ...formData,
      requirement_id: requirement.id,
      title: `Exception for: ${requirement.title}`
    });
    setIsDialogOpen(true);
  };

  return {
    formData,
    setFormData,
    isDialogOpen,
    setIsDialogOpen,
    selectedRequirement,
    isSubmitting: createMutation.isPending,
    handleSubmit,
    handleRequestException,
    resetForm
  };
}
