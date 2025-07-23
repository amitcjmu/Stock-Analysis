import type { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext';

// Types
export type CostTrend = 'Increasing' | 'Decreasing' | 'Stable';
export type ResourceType = 'Compute' | 'Storage' | 'Network' | 'Database' | 'Other';

export interface CostMetrics {
  totalCost: number;
  monthOverMonth: number;
  projectedAnnual: number;
  savingsIdentified: number;
  resourceUtilization: number;
  wastedSpend: number;
  optimizationScore: number;
}

export interface ResourceCost {
  id: string;
  name: string;
  type: ResourceType;
  currentCost: number;
  previousCost: number;
  trend: CostTrend;
  utilizationRate: number;
  recommendations: string[];
}

export interface SavingsOpportunity {
  id: string;
  title: string;
  description: string;
  potentialSavings: number;
  effort: 'Low' | 'Medium' | 'High';
  impact: 'Low' | 'Medium' | 'High';
  status: 'New' | 'In Progress' | 'Implemented';
}

export interface BudgetAlert {
  id: string;
  resourceGroup: string;
  threshold: number;
  currentSpend: number;
  status: 'Warning' | 'Critical' | 'OK';
  lastUpdated: string;
}

// Hooks
export const useCostMetrics = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['costMetrics'],
    queryFn: async () => {
      const response = await fetch('/api/v1/finops/metrics', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch cost metrics');
      return response.json();
    }
  });
};

export const useResourceCosts = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['resourceCosts'],
    queryFn: async () => {
      const response = await fetch('/api/v1/finops/resources', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch resource costs');
      return response.json();
    }
  });
};

export const useSavingsOpportunities = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['savingsOpportunities'],
    queryFn: async () => {
      const response = await fetch('/api/v1/finops/opportunities', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch savings opportunities');
      return response.json();
    }
  });
};

export const useBudgetAlerts = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['budgetAlerts'],
    queryFn: async () => {
      const response = await fetch('/api/v1/finops/alerts', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch budget alerts');
      return response.json();
    }
  });
};

// Mutations
export const useUpdateSavingsOpportunity = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (opportunity: Partial<SavingsOpportunity> & { id: string }) => {
      const response = await fetch(`/api/v1/finops/opportunities/${opportunity.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify(opportunity)
      });
      if (!response.ok) throw new Error('Failed to update savings opportunity');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savingsOpportunities'] });
    }
  });
};

export const useUpdateBudgetAlert = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (alert: Partial<BudgetAlert> & { id: string }) => {
      const response = await fetch(`/api/v1/finops/alerts/${alert.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify(alert)
      });
      if (!response.ok) throw new Error('Failed to update budget alert');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetAlerts'] });
    }
  });
}; 