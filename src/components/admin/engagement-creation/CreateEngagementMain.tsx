import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

import { CreateEngagementData, ClientAccount } from './types';
import { EngagementBasicInfo } from './EngagementBasicInfo';
import { EngagementTimeline } from './EngagementTimeline';
import { EngagementScope } from './EngagementScope';
import { EngagementSummary } from './EngagementSummary';

export const CreateEngagementMain: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();
  const { user } = useAuth();

  // Fetch client accounts with React Query
  const clientAccountsQuery = useQuery<ClientAccount[]>({
    queryKey: ['client-accounts'],
    queryFn: async () => {
      try {
        const result = await apiCall('/admin/clients/');
        if (result.items && Array.isArray(result.items)) {
          return result.items.map((client: any) => ({
            id: client.id,
            account_name: client.account_name,
            industry: client.industry
          }));
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error('Error fetching client accounts:', error);
        // Enhanced fallback to demo data including the real backend clients
        return [
          { id: 'd838573d-f461-44e4-81b5-5af510ef83b7', account_name: 'Acme Corporation', industry: 'Technology' },
          { id: '73dee5f1-6a01-43e3-b1b8-dbe6c66f2990', account_name: 'Marathon Petroleum', industry: 'Energy' },
          { id: 'bafd5b46-aaaf-4c95-8142-573699d93171', account_name: 'Complete Test Client', industry: 'Technology' },
          { id: '11111111-1111-1111-1111-111111111111', account_name: 'Democorp', industry: 'Technology' }
        ];
      }
    },
    initialData: [],
  });
  const clientAccounts = clientAccountsQuery.data || [];
  const accountsLoading = clientAccountsQuery.isLoading;
  const accountsError = clientAccountsQuery.isError;

  // Server state: useMutation for API interaction
  const createEngagementMutation = useMutation({
    mutationFn: async (submissionData: any) => {
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
    onError: (error: any) => {
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
  const handleFormChange = (field: keyof CreateEngagementData, value: any) => {
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