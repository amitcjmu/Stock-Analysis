/**
 * Shared Admin Data Hook
 * Provides common data fetching patterns for admin components
 */

import { useState } from 'react';
import { useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import { useAdminToasts } from './useAdminToasts';

export interface UseAdminDataOptions {
  staleTime?: number;
  retryOnError?: boolean;
  showDemoWarning?: boolean;
}

export const useAdminData = <T>(
  endpoint: string,
  demoData: T,
  options: UseAdminDataOptions = {}
): {
  data: T;
  loading: boolean;
  error: string | null;
  isUsingDemoData: boolean;
  refetch: () => Promise<void>;
} => {
  const { isAuthenticated, user, getAuthHeaders } = useAuth();
  const { showDemoDataWarningToast } = useAdminToasts();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUsingDemoData, setIsUsingDemoData] = useState(false);

  const fetchData = useCallback(async (): Promise<T> => {
    if (!isAuthenticated || !user) {
      throw new Error('User is not authenticated');
    }

    try {
      setLoading(true);
      setError(null);

      // Admin calls don't need tenant context - use false as third parameter
      const response = await apiCall(
        endpoint,
        {
          method: 'GET',
          headers: getAuthHeaders?.() || {},
        },
        false
      );

      if (response.status === 'success') {
        setIsUsingDemoData(false);
        return response;
      } else {
        throw new Error(response.message || 'API call failed');
      }
    } catch (apiError) {
      console.warn(`API endpoint ${endpoint} not available, using demo data:`, apiError);

      if (options.showDemoWarning) {
        showDemoDataWarningToast(apiError instanceof Error ? apiError.message : 'Unknown error');
      }

      setIsUsingDemoData(true);
      return demoData;
    }
  }, [
    endpoint,
    isAuthenticated,
    user,
    getAuthHeaders,
    demoData,
    options.showDemoWarning,
    showDemoDataWarningToast,
  ]);

  const refetch = useCallback(async () => {
    try {
      const result = await fetchData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setData(demoData);
    } finally {
      setLoading(false);
    }
  }, [fetchData, demoData]);

  return {
    data: data || demoData,
    loading,
    error,
    isUsingDemoData,
    refetch,
    fetchData,
  };
};

/**
 * Specific hooks for common admin data patterns
 */

// Dashboard stats hook
export const useAdminDashboardStats = (): unknown => {
  const demoStats = {
    clients: {
      total: 12,
      active: 10,
      byIndustry: { Technology: 4, Healthcare: 3, Finance: 3, Manufacturing: 2 },
      bySize: { Enterprise: 6, Large: 4, Medium: 2 },
      recentRegistrations: [],
    },
    engagements: {
      total: 25,
      active: 18,
      byPhase: { Discovery: 8, Assessment: 5, Planning: 3, Migration: 2 },
      byScope: { 'Full Datacenter': 5, 'Application Portfolio': 12, 'Selected Apps': 8 },
      completionRate: 72.5,
      budgetUtilization: 65.8,
      recentActivity: [],
    },
    users: {
      total: 45,
      pending: 8,
      approved: 37,
      recentRequests: [],
    },
  };

  return useAdminData('/admin/dashboard/stats', demoStats, {
    showDemoWarning: true,
  });
};

// Pending purge items hook
export const usePendingPurgeItems = (): unknown => {
  const demoItems = [
    {
      id: 'item_001',
      item_type: 'client_account',
      item_id: 'client_001',
      item_name: 'Legacy Systems Corp',
      client_account_name: 'Legacy Systems Corp',
      engagement_name: null,
      deleted_by_name: 'John Admin',
      deleted_by_email: 'john.admin@company.com',
      deleted_at: '2025-01-05T14:30:00Z',
      delete_reason: 'Client requested account closure after migration completion',
      status: 'pending_review',
    },
  ];

  return useAdminData('admin/platform/platform-admin/pending-purge-items', {
    pending_items: demoItems,
  });
};
