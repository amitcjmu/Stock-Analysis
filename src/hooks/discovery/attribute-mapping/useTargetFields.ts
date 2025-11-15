import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import type { TargetField } from '@/contexts/FieldOptionsContext';

interface UseTargetFieldsOptions {
  flowId?: string | null;
  importCategory?: string;
}

interface UseTargetFieldsResult {
  fields: TargetField[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<TargetField[]>;
}

const buildEndpoint = (flowId?: string | null, importCategory?: string): string => {
  const params = new URLSearchParams();
  if (flowId) {
    params.append('flow_id', flowId);
  } else if (importCategory) {
    params.append('import_category', importCategory);
  }

  return params.toString()
    ? `/data-import/available-target-fields?${params.toString()}`
    : '/data-import/available-target-fields';
};

export const useTargetFields = ({
  flowId,
  importCategory,
}: UseTargetFieldsOptions): UseTargetFieldsResult => {
  const queryKey = ['target-fields', flowId || 'default', importCategory || 'default'];

  const query = useQuery<TargetField[], Error>({
    queryKey,
    queryFn: async () => {
      const endpoint = buildEndpoint(flowId, importCategory);
      const data = await apiCall(endpoint, { method: 'GET' });
      return Array.isArray(data?.fields) ? data.fields : [];
    },
    staleTime: 60 * 1000,
    keepPreviousData: true,
  });

  return {
    fields: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error ?? null,
    refetch: async () => (await query.refetch()).data ?? [],
  };
};
