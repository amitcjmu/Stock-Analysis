import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export interface SupportTimeline {
  id: string;
  name: string;
  description: string;
  endOfLife: string;
  endOfSupport: string;
  status: 'active' | 'deprecated' | 'upcoming' | 'end_of_life';
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  category: TechDebtCategory;
  impact: string;
  remediation: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  technology?: string;
  currentVersion?: string;
  supportStatus?: 'active' | 'maintenance' | 'security' | 'end_of_life' | 'end_of_support';
  recommendedAction?: string;
  documentationUrl?: string;
  updateAvailable?: boolean;
  updateUrl?: string;
  extendedSupportEnd?: string;
  daysUntilEOL?: number;
  isExtendedSupport?: boolean;
  version?: string;
  component?: string;
  assetName?: string;
  latestVersion?: string;
}

export type TechDebtCategory = 'infrastructure' | 'dependencies' | 'security' | 'performance' | 'code-quality' | 'documentation' | 'all';

export interface TechDebtItem {
  id: string;
  name: string;
  description: string;
  category: TechDebtCategory;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  securityRisk: 'low' | 'medium' | 'high' | 'critical';
  status: 'identified' | 'in-progress' | 'resolved' | 'deferred' | 'active' | 'mitigated' | 'planned';
  supportStatus: 'active' | 'maintenance' | 'security' | 'end_of_life' | 'end_of_support';
  impact: string;
  remediation: string;
  timeline: SupportTimeline[];
  dependencies: string[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
  technology?: string;
  currentVersion?: string;
  component?: string;
  assetName?: string;
  latestVersion?: string;
  endOfLifeDate?: string;
  isDeprecated?: boolean;
  recommendedAction?: string;
  documentationUrl?: string;
  updateAvailable?: boolean;
  updateUrl?: string;
  extendedSupportEnd?: string;
  daysUntilEOL?: number;
  isExtendedSupport?: boolean;
}

export interface TechDebtSummary {
  totalItems: number;
  byCategory: Record<TechDebtCategory, number>;
  byRisk: Record<'low' | 'medium' | 'high' | 'critical', number>;
  byStatus: Record<'identified' | 'in-progress' | 'resolved' | 'deferred' | 'active' | 'mitigated' | 'planned', number>;
  lastUpdated: string;
  criticalRisk: number;
  highRisk: number;
  endOfLife: number;
  deprecated: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface TechDebtFilters {
  category?: TechDebtCategory;
  risk?: string;
  status?: string;
  search?: string;
}

export const useTechDebtData = (filters: TechDebtFilters = {}) => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  const fetchTechDebtData = async () => {
    const headers = getAuthHeaders();
    const params = new URLSearchParams();
    if (filters.category && filters.category !== 'all') params.append('category', filters.category);
    if (filters.risk && filters.risk !== 'all') params.append('risk', filters.risk);
    if (filters.status && filters.status !== 'all') params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);

    const response = await apiCall(`/api/v1/discovery/tech-debt?${params.toString()}`, { headers });
    return response.data;
  };

  return useQuery<{ items: TechDebtItem[]; summary: TechDebtSummary }>({
    queryKey: ['tech-debt', filters],
    queryFn: fetchTechDebtData,
  });
};

export const useSupportTimelines = () => {
  const { getAuthHeaders } = useAuth();

  const fetchSupportTimelines = async () => {
    const headers = getAuthHeaders();
    const response = await apiCall('discovery/support-timelines', { headers });
    return response.data;
  };

  return useQuery<SupportTimeline[]>({
    queryKey: ['support-timelines'],
    queryFn: fetchSupportTimelines,
  });
};

export const useUpdateTechDebtItem = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<TechDebtItem> & { id: string }) => {
      const headers = getAuthHeaders();
      const response = await apiCall(`/api/v1/discovery/tech-debt/${data.id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tech-debt'] });
    },
  });
};

export const useDeleteTechDebtItem = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const headers = getAuthHeaders();
      await apiCall(`/api/v1/discovery/tech-debt/${id}`, {
        method: 'DELETE',
        headers,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tech-debt'] });
    },
  });
};

export const useMigrationPlan = () => {
  const { clientAccountId, engagementId } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (items: string[]) => {
      if (!clientAccountId || !engagementId) {
        throw new Error('Client account and engagement are required');
      }
      return generateMigrationPlan(clientAccountId, engagementId, items);
    },
    onSuccess: () => {
      toast.success('Migration plan generated successfully');
      queryClient.invalidateQueries({ queryKey: ['techDebtAnalysis'] });
    },
    onError: (error: Error) => {
      console.error('Error generating migration plan:', error);
      toast.error('Failed to generate migration plan');
    },
  });
};

export const useFilteredTechDebtItems = (
  items: TechDebtItem[], 
  category: string, 
  risk: string
) => {
  return items.filter(item => {
    const matchesCategory = category === 'all' || item.component === category;
    const matchesRisk = risk === 'all' || item.securityRisk === risk;
    return matchesCategory && matchesRisk;
  });
};

export const useTechDebtSummary = (items: TechDebtItem[]): TechDebtSummary => {
  return items.reduce(
    (summary, item) => ({
      totalItems: summary.totalItems + 1,
      highRisk: item.securityRisk === 'high' ? summary.highRisk + 1 : summary.highRisk,
      mediumRisk: item.securityRisk === 'medium' ? summary.mediumRisk + 1 : summary.mediumRisk,
      lowRisk: item.securityRisk === 'low' ? summary.lowRisk + 1 : summary.lowRisk,
      criticalRisk: item.securityRisk === 'critical' ? summary.criticalRisk + 1 : summary.criticalRisk,
      endOfLife: item.supportStatus === 'end_of_life' ? summary.endOfLife + 1 : summary.endOfLife,
      extendedSupport: item.supportStatus === 'extended' ? summary.extendedSupport + 1 : summary.extendedSupport,
      deprecated: item.supportStatus === 'deprecated' ? summary.deprecated + 1 : summary.deprecated,
    }),
    {
      totalItems: 0,
      highRisk: 0,
      mediumRisk: 0,
      lowRisk: 0,
      criticalRisk: 0,
      endOfLife: 0,
      extendedSupport: 0,
      deprecated: 0,
    }
  );
};
