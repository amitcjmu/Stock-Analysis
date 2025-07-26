import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api';
import type { UseReadinessAssessmentOptions, GenerateSignoffPackageParams, SubmitForApprovalParams } from '../types'
import type { ReadinessAssessment,  } from '../types'

export const useReadinessAssessment = ({
  clientAccountId,
  engagementId,
}: UseReadinessAssessmentOptions): JSX.Element => {
  return useQuery<ReadinessAssessment, Error>({
    queryKey: ['readinessAssessment', { clientAccountId, engagementId }],
    queryFn: async () => {
      const response = await api.get<ReadinessAssessment>(
        `/api/v1/assessments/readiness/${clientAccountId}/${engagementId}`
      );
      return response;
    },
    enabled: !!clientAccountId && !!engagementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useGenerateSignoffPackage = (): JSX.Element => {
  const queryClient = useQueryClient();

  return useMutation<ReadinessAssessment, Error, GenerateSignoffPackageParams>({
    mutationFn: async ({ assessmentId, clientAccountId, engagementId }) => {
      const response = await api.post<ReadinessAssessment>(
        `/api/v1/assessments/readiness/${clientAccountId}/${engagementId}/generate-signoff`,
        { assessmentId }
      );
      return response;
    },
    onSuccess: (data, variables) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: ['readinessAssessment', {
          clientAccountId: variables.clientAccountId,
          engagementId: variables.engagementId
        }]
      });
    },
  });
};

export const useSubmitForApproval = (): JSX.Element => {
  const queryClient = useQueryClient();

  return useMutation<ReadinessAssessment, Error, SubmitForApprovalParams>({
    mutationFn: async ({
      assessmentId,
      signoffPackage,
      clientAccountId,
      engagementId,
    }) => {
      const response = await api.post<ReadinessAssessment>(
        `/api/v1/assessments/readiness/${clientAccountId}/${engagementId}/submit-approval`,
        { assessmentId, signoffPackage }
      );
      return response;
    },
    onSuccess: (data, variables) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: ['readinessAssessment', {
          clientAccountId: variables.clientAccountId,
          engagementId: variables.engagementId
        }]
      });
    },
  });
};

export * from './useReadinessAssessment';
