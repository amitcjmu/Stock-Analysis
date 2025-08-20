import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext';
import * as dataCleansingService from '@/services/dataCleansingService';
import type {
  DataCleansingStats,
  DataCleansingAnalysis,
  DataQualityIssue,
  DataCleansingRecommendation,
  AssetData,
  QualityFixData,
  TriggerDataCleansingRequest
} from '@/services/dataCleansingService';

// Query keys
const queryKeys = {
  latestImport: ['dataCleansing', 'latestImport'],
  assets: (page: number, pageSize: number) => ['dataCleansing', 'assets', page, pageSize],
  agentAnalysis: (dataHash: string) => ['dataCleansing', 'agentAnalysis', dataHash],
  dataCleansingStats: (flowId: string) => ['dataCleansing', 'stats', flowId],
  dataCleansingAnalysis: (flowId: string) => ['dataCleansing', 'analysis', flowId],
};

// Custom hook to fetch data cleansing statistics for a flow
export const useDataCleansingStats = (flowId: string | undefined): UseQueryResult<DataCleansingStats, Error> => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.dataCleansingStats(flowId || ''),
    queryFn: () => dataCleansingService.fetchDataCleansingStats(flowId!),
    enabled: isAuthenticated && !!flowId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });
};

// Custom hook to fetch data cleansing analysis for a flow
export const useDataCleansingAnalysis = (flowId: string | undefined, includeDetails = true): UseQueryResult<DataCleansingAnalysis, Error> => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.dataCleansingAnalysis(flowId || ''),
    queryFn: () => dataCleansingService.fetchDataCleansingAnalysis(flowId!, includeDetails),
    enabled: isAuthenticated && !!flowId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

// Custom hook to trigger data cleansing analysis
export const useTriggerDataCleansingAnalysis = (): UseMutationResult<DataCleansingAnalysis, Error, TriggerDataCleansingRequest & { flowId: string }> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ flowId, force_refresh = false, include_agent_analysis = true }: TriggerDataCleansingRequest & { flowId: string }) =>
      dataCleansingService.triggerDataCleansingAnalysis(flowId, force_refresh, include_agent_analysis),
    onSuccess: (result, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.dataCleansingStats(variables.flowId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.dataCleansingAnalysis(variables.flowId) });
      return result;
    },
  });
};

// Custom hook to fetch the latest import data (legacy)
export const useLatestImport = (): UseQueryResult<AssetData[], Error> => {
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
export const useAssets = (page = 1, pageSize = 1000): UseQueryResult<AssetData[], Error> => {
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
export const useAgentAnalysis = (data: AssetData[] | null): UseMutationResult<{
  success: boolean;
  data: {
    issues: Array<{
      id: string;
      type: string;
      severity: string;
      description: string;
      affected_assets: string[];
    }>;
    summary: {
      total_issues: number;
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
}, Error, AssetData[]> => {
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
export const useApplyFix = (): UseMutationResult<{
  success: boolean;
  data: {
    fixed: boolean;
    message: string;
    updated_assets: string[];
  };
}, Error, { issueId: string; fixData: QualityFixData }> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ issueId, fixData }: { issueId: string; fixData: QualityFixData }) =>
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
export const useCachedAgentAnalysis = (data: AssetData[] | null): { analysis: any; isLoading: boolean } => {
  const dataHash = data ? JSON.stringify(data) : '';
  const { data: analysis, isLoading } = useQuery({
    queryKey: queryKeys.agentAnalysis(dataHash),
    queryFn: () => (data ? dataCleansingService.performAgentAnalysis(data) : null),
    enabled: !!data && data.length > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  return { analysis, isLoading };
};
