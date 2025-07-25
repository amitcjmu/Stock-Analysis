/**
 * Custom hooks for ClientDetails component
 * Generated with CC for UI modularization
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiCallWithFallback } from '@/config/api';
import type { ClientFormData } from './types'
import type { Client } from './types'

export const useClient = (clientId: string | undefined) => {
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();

  const demoClient: Client = {
    id: clientId || 'demo-id',
    account_name: 'Pujyam Corp',
    industry: 'Technology',
    company_size: 'Enterprise (5000+)',
    headquarters_location: 'San Francisco, CA',
    primary_contact_name: 'John Smith',
    primary_contact_email: 'john.smith@pujyam.com',
    primary_contact_phone: '+1-555-0123',
    business_objectives: ['Cost Reduction', 'Modernization', 'Cloud Migration'],
    target_cloud_providers: ['aws', 'azure'],
    business_priorities: ['cost_reduction', 'agility_speed', 'security_compliance'],
    compliance_requirements: ['SOC2', 'GDPR', 'HIPAA'],
    created_at: '2024-01-15T10:30:00Z',
    is_active: true,
    total_engagements: 3,
    active_engagements: 2
  };

  const { data, isLoading, isError, refetch } = useQuery<Client>({
    queryKey: ['client', clientId],
    queryFn: async () => {
      const response = await apiCallWithFallback(`/admin/clients/${clientId}`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to fetch client details');
      }

      return response.json();
    },
    onError: (error) => {
      console.error('Error fetching client details:', error);
      toast({
        title: "Error",
        description: "Failed to fetch client details. Using demo data.",
        variant: "destructive"
      });
    }
  });

  const client: Client = !isLoading && (isError || !data) ? demoClient : (data as Client);

  return {
    client,
    isLoading,
    isError,
    refetch
  };
};

export const useClientForm = (client: Client | null, clientId: string | undefined) => {
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [formData, setFormData] = useState<ClientFormData>({
    account_name: '',
    industry: '',
    company_size: '',
    headquarters_location: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    description: '',
    subscription_tier: '',
    billing_contact_email: '',
    business_objectives: [],
    target_cloud_providers: [],
    business_priorities: [],
    compliance_requirements: []
  });

  const handleEdit = () => {
    if (client) {
      setFormData({
        account_name: client.account_name,
        industry: client.industry,
        company_size: client.company_size,
        headquarters_location: client.headquarters_location || '',
        primary_contact_name: client.primary_contact_name || '',
        primary_contact_email: client.primary_contact_email || '',
        primary_contact_phone: client.primary_contact_phone || '',
        description: client.description || '',
        subscription_tier: client.subscription_tier || '',
        billing_contact_email: client.billing_contact_email || '',
        business_objectives: client.business_objectives || [],
        target_cloud_providers: client.target_cloud_providers || [],
        business_priorities: client.business_priorities || [],
        compliance_requirements: client.compliance_requirements || []
      });
      setShowEditDialog(true);
    }
  };

  const handleUpdate = async () => {
    try {
      const response = await apiCallWithFallback(`/admin/clients/${clientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(formData)
      });

      if (response.status !== 'success') {
        throw new Error(response.message || 'Failed to update client');
      }

      toast({
        title: "Success",
        description: `Client "${formData.account_name}" updated successfully`,
      });

      setShowEditDialog(false);
    } catch (error) {
      console.error('Error updating client:', error);
      toast({
        title: "Error",
        description: "Failed to update client. Please try again.",
        variant: "destructive"
      });
    }
  };

  return {
    showEditDialog,
    setShowEditDialog,
    formData,
    setFormData,
    handleEdit,
    handleUpdate
  };
};
