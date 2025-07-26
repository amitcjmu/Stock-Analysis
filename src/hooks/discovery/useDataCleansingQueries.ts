import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext';
import * as dataCleansingService from '@/services/dataCleansingService';
import type { QualityMetrics, QualityIssue, AgentRecommendation, AgentAnalysisResult } from '@/types/discovery';

// Query keys
const queryKeys = {
  latestImport: ['dataCleansing', 'latestImport'],
  assets: (page: number, pageSize: number) => ['dataCleansing', 'assets', page, pageSize],
  agentAnalysis: (dataHash: string) => ['dataCleansing', 'agentAnalysis', dataHash],
};

// Custom hook to fetch the latest import data
export const useLatestImport = (): any => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.latestImport,
    queryFn: dataCleansingService.fetchLatestImport,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};

// Custom hook to fetch paginated assets
export const useAssets = (page = 1, pageSize = 1000): any => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.assets(page, pageSize),
    queryFn: () => dataCleansingService.fetchAssets(page, pageSize),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};

// Custom hook to perform agent analysis
export const useAgentAnalysis = (data: unknown[] | null): any => {
  const queryClient = useQueryClient();
  const dataHash = data ? JSON.stringify(data) : '';

  return useMutation({
    mutationFn: () => dataCleansingService.performAgentAnalysis(data || []),
    onSuccess: (result) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: queryKeys.agentAnalysis(dataHash) });
      return result;
    },
  });
};

// Custom hook to apply a fix
export const useApplyFix = (): any => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ issueId, fixData }: { issueId: string; fixData: unknown }) =>
      dataCleansingService.applyFix(issueId, fixData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: queryKeys.latestImport });
    },
  });
};

// Custom hook to get agent analysis result
// This would be used to cache the analysis result
// and avoid re-running the analysis unnecessarily
export const useCachedAgentAnalysis = (data: unknown[] | null): any => {
  const dataHash = data ? JSON.stringify(data) : '';
  const { data: analysis, isLoading } = useQuery({
    queryKey: queryKeys.agentAnalysis(dataHash),
    queryFn: () => (data ? dataCleansingService.performAgentAnalysis(data) : null),
    enabled: !!data && data.length > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  return { analysis, isLoading };
};
