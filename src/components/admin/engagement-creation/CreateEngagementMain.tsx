import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

import { CreateEngagementData, ClientAccount } from './types';

// CC: API response interfaces for type safety
interface ClientApiResponse {
  id: string;
  account_name: string;
  industry: string;
  [key: string]: unknown;
}

interface EngagementSubmissionData extends CreateEngagementData {
  user_id?: string;
  [key: string]: unknown;
}
import { EngagementBasicInfo } from './EngagementBasicInfo';
import { EngagementTimeline } from './EngagementTimeline';
import { EngagementScope } from './EngagementScope';
import { EngagementSummary } from './EngagementSummary';

export const CreateEngagementMain: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Fetch client accounts with React Query
  const clientAccountsQuery = useQuery<ClientAccount[]>({
    queryKey: ['client-accounts'],
    queryFn: async () => {
      console.log('🔍 Fetching client accounts for engagement creation...');
      const result = await apiCall('/api/v1/admin/clients/');
      console.log('🔍 Client accounts API result:', result);
      
      // Handle different response formats
      if (result && Array.isArray(result)) {
        console.log('✅ Using direct array format for clients');
        return result.map((client: ClientApiResponse) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry
        }));
      } else if (result && result.items && Array.isArray(result.items)) {
        console.log('✅ Using items array format for clients');
        return result.items.map((client: ClientApiResponse) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry
        }));
      } else if (result && result.clients && Array.isArray(result.clients)) {
        console.log('✅ Using clients array format for clients');
        return result.clients.map((client: ClientApiResponse) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry
        }));
      } else if (result && result.data && Array.isArray(result.data)) {
        console.log('✅ Using data array format for clients');
        return result.data.map((client: ClientApiResponse) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry
        }));
      } else {
        console.warn('⚠️ Unexpected client accounts API response format:', result);
        return [];
      }
    },
    initialData: [],
    retry: 2,
    enabled: true,
    refetchOnMount: true,
    staleTime: 0,  // Always consider data stale
    cacheTime: 0   // Don't cache the data
  });
  const clientAccounts = clientAccountsQuery.data || [];
  const accountsLoading = clientAccountsQuery.isLoading;
  const accountsError = clientAccountsQuery.isError;

  // Server state: useMutation for API interaction
  const createEngagementMutation = useMutation({
    mutationFn: async (submissionData: EngagementSubmissionData) => {
      return await apiCall('/admin/engagements/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData)
      });
    },
    // Pass engagement name via context for toast
    onSuccess: (_data, variables) => {
      toast({
        title: "Engagement Created Successfully",
        description: `Engagement ${variables.engagement_name} has been created and is now active.`,
      });
      navigate('/admin/engagements');
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error?.message || "Failed to create engagement. Please try again.",
        variant: "destructive"
      });
    }
  });

  const [formData, setFormData] = useState<CreateEngagementData>({
    engagement_name: '',
    client_account_id: '',
    project_manager: '',
    estimated_start_date: '',
    estimated_end_date: '',
    budget: '',
    budget_currency: 'USD',
    engagement_status: 'planning',
    phase: 'discovery',
    description: '',
    business_objectives: [],
    target_cloud_provider: '',
    scope_applications: true,
    scope_databases: true,
    scope_infrastructure: true,
    scope_data_migration: false,
    risk_level: 'medium',
    compliance_requirements: []
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Simple form handler - no useCallback to prevent re-renders
  const handleFormChange = (field: keyof CreateEngagementData, value: string | number | boolean | string[]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.engagement_name) newErrors.engagement_name = 'Engagement name is required';
    if (!formData.client_account_id) newErrors.client_account_id = 'Client account is required';
    if (!formData.project_manager) newErrors.project_manager = 'Project manager is required';
    if (!formData.estimated_start_date) newErrors.estimated_start_date = 'Start date is required';
    if (!formData.estimated_end_date) newErrors.estimated_end_date = 'End date is required';
    if (!formData.target_cloud_provider) newErrors.target_cloud_provider = 'Target cloud provider is required';
    if (formData.estimated_start_date && formData.estimated_end_date) {
      if (new Date(formData.estimated_start_date) >= new Date(formData.estimated_end_date)) {
        newErrors.estimated_end_date = 'End date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form",
        variant: "destructive"
      });
      return;
    }

    // Determine migration scope based on checkboxes
    let migrationScope = 'application_portfolio'; // Default
    if (formData.scope_applications && formData.scope_databases && formData.scope_infrastructure) {
      migrationScope = 'full_datacenter';
    } else if (formData.scope_applications && !formData.scope_databases && !formData.scope_infrastructure) {
      migrationScope = 'selected_applications';
    } else if (!formData.scope_applications && !formData.scope_databases && formData.scope_infrastructure) {
      migrationScope = 'infrastructure_only';
    }

    // Format data for submission - map frontend fields to backend fields
    const submissionData = {
      engagement_name: formData.engagement_name,
      client_account_id: formData.client_account_id,
      engagement_description: formData.description || `${formData.engagement_name} migration engagement`,
      migration_scope: migrationScope,
      target_cloud_provider: formData.target_cloud_provider || 'aws',
      engagement_manager: formData.project_manager,
      technical_lead: formData.project_manager, // Use same person as default
      planned_start_date: formData.estimated_start_date ? new Date(formData.estimated_start_date).toISOString() : null,
      planned_end_date: formData.estimated_end_date ? new Date(formData.estimated_end_date).toISOString() : null,
      estimated_budget: formData.budget ? parseFloat(formData.budget.toString()) : null,
      team_preferences: {},
      agent_configuration: {},
      discovery_preferences: {},
      assessment_criteria: {}
    };

    // Ensure description is at least 10 characters to meet backend validation
    if (!submissionData.engagement_description || submissionData.engagement_description.length < 10) {
      submissionData.engagement_description = `${submissionData.engagement_name} migration engagement project`;
    }

    console.log('Submitting engagement data:', JSON.stringify(submissionData, null, 2));
    createEngagementMutation.mutate(submissionData);
  };

  const handleCancel = () => {
    navigate('/admin/engagements');
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={handleCancel}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Engagement Management
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Engagement</h1>
          <p className="text-muted-foreground">
            Set up a new migration engagement with timeline, budget, and scope
          </p>
        </div>
      </div>

      {/* Debug Panel */}
      <div className="bg-gray-100 p-4 rounded-lg border mb-4">
        <h3 className="font-semibold mb-2">Debug - Client Accounts</h3>
        <div className="text-sm space-y-1">
          <p>Loading: {accountsLoading ? 'true' : 'false'}</p>
          <p>Error: {accountsError ? 'true' : 'false'}</p>
          <p>Client Accounts Count: {clientAccounts.length}</p>
          <p>Query Status: {clientAccountsQuery.status}</p>
          <p>Fetch Status: {clientAccountsQuery.fetchStatus}</p>
          <p>Clients: {clientAccounts.length > 0 ? clientAccounts.map(c => c.account_name).join(', ') : 'None'}</p>
        </div>
        <div className="flex gap-2 mt-2">
          <Button 
            onClick={() => clientAccountsQuery.refetch()} 
            disabled={clientAccountsQuery.isFetching}
            size="sm"
          >
            {clientAccountsQuery.isFetching ? 'Fetching...' : 'Manual Refetch'}
          </Button>
          <Button 
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['client-accounts'] });
              queryClient.refetchQueries({ queryKey: ['client-accounts'] });
            }}
            variant="outline"
            size="sm"
          >
            Clear Cache & Refetch
          </Button>
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <EngagementBasicInfo
              formData={formData}
              clientAccounts={clientAccounts}
              errors={errors}
              onFormChange={handleFormChange}
            />
            <EngagementTimeline
              formData={formData}
              errors={errors}
              onFormChange={handleFormChange}
            />
            <EngagementScope
              formData={formData}
              onFormChange={handleFormChange}
            />
          </div>

          <div className="space-y-6">
            <EngagementSummary
              formData={formData}
              clientAccounts={clientAccounts}
              loading={createEngagementMutation.isPending}
              onCancel={handleCancel}
              onSubmit={handleSubmit}
            />
          </div>
        </div>
      </form>
    </div>
  );
};