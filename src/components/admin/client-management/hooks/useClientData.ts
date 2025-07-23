import { useState } from 'react'
import { useCallback, useEffect } from 'react'
import { apiCall } from '@/config/api';
import type { Client } from '../types';

interface UseClientDataProps {
  searchTerm?: string;
  filterIndustry?: string;
}

export const useClientData = ({ searchTerm = '', filterIndustry = 'all' }: UseClientDataProps = {}) => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchClients = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (searchTerm) params.append('account_name', searchTerm);
      if (filterIndustry && filterIndustry !== 'all') params.append('industry', filterIndustry);
      params.append('page', '1');
      params.append('page_size', '50');

      const queryString = params.toString();
      const url = `/api/v1/admin/clients/${queryString ? `?${queryString}` : ''}`;

      const result = await apiCall(url);
      
      if (result && result.items) {
        setClients(result.items || []);
      } else {
        console.error('Invalid API response format:', result);
        setClients([]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterIndustry]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  return {
    clients,
    setClients,
    loading,
    refetch: fetchClients
  };
};