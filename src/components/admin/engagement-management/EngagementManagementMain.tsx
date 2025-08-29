import React from 'react';
import { useState } from 'react';
import { useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { useDialog } from '@/hooks/useDialog';
import { apiCall } from '@/config/api';

import { EngagementFilters } from './EngagementFilters';
import { EngagementStats } from './EngagementStats';
import { EngagementList } from './EngagementList';
import { EngagementForm } from './EngagementForm';
import type { EngagementFormData } from './types';
import type { Engagement, Client } from './types';

const EngagementManagementMain: React.FC = () => {
  const { toast } = useToast();
  const { user } = useAuth();
  const dialog = useDialog();
  const queryClient = useQueryClient();

  // UI state must be declared before useQuery hooks
  const [searchTerm, setSearchTerm] = useState('');
  const [filterClient, setFilterClient] = useState('all');
  const [filterPhase, setFilterPhase] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [editingEngagement, setEditingEngagement] = useState<Engagement | null>(null);

  // Server state: useQuery for API data
  const engagementsQuery = useQuery<Engagement[]>({
    queryKey: ['engagements', searchTerm, filterClient, filterPhase, currentPage],
    queryFn: async () => {
      try {
        // Build query parameters
        const params = new URLSearchParams();
        if (searchTerm) params.append('search', searchTerm);
        if (filterClient !== 'all') params.append('client_account_id', filterClient);
        if (filterPhase !== 'all') params.append('phase', filterPhase);
        params.append('page', currentPage.toString());
        params.append('page_size', '20'); // Changed from 'limit' to 'page_size' to match backend

        const queryString = params.toString();
        console.log('🔍 Fetching engagements with query:', queryString);

        const result = await apiCall(
          `/api/v1/admin/engagements/${queryString ? '?' + queryString : ''}`
        );
        console.log('🔍 Engagements API result:', result);
        console.log('🔍 Engagements API result type:', typeof result);
        console.log('🔍 Engagements API result keys:', result ? Object.keys(result) : 'null');

        // Handle different response formats
        if (result && Array.isArray(result)) {
          console.log('✅ Using direct array format, length:', result.length);
          return result;
        } else if (result && result.items && Array.isArray(result.items)) {
          console.log('✅ Using items array format, length:', result.items.length);
          // Also update pagination if available
          if (result.total_pages) {
            setTotalPages(result.total_pages);
          }
          return result.items;
        } else if (result && result.engagements && Array.isArray(result.engagements)) {
          console.log('✅ Using engagements array format, length:', result.engagements.length);
          return result.engagements;
        } else if (result && result.data && Array.isArray(result.data)) {
          console.log('✅ Using data array format, length:', result.data.length);
          return result.data;
        } else {
          console.warn('⚠️ Unexpected engagements API response format:', result);
          return [];
        }
      } catch (error: unknown) {
        console.error('❌ Error fetching engagements:', {
          error: error.message || error,
          status: error.status,
          endpoint: `/api/v1/admin/engagements/${queryString ? '?' + queryString : ''}`,
        });

        // If 404 or other error, still try to return empty array but log the issue
        return [];
      }
    },
    retry: (failureCount, error: unknown) => {
      // Only retry on network errors, not on 404/403 which are expected
      if (error?.status === 404 || error?.status === 403) {
        return false;
      }
      return failureCount < 2;
    },
    enabled: true, // Force query to be enabled
    refetchOnMount: 'always', // Force refetch on mount
    refetchOnWindowFocus: false, // Prevent excessive refetches
    staleTime: 0, // Always consider data stale
    gcTime: 0, // Don't keep in cache (replacement for deprecated cacheTime)
  });
  const engagements = engagementsQuery.data || [];
  const engagementsLoading = engagementsQuery.isLoading;
  const engagementsError = engagementsQuery.isError;

  // Debug logging to understand component state
  React.useEffect(() => {
    console.log('🔍 EngagementManagementMain component state:', {
      engagementsLoading,
      engagementsError,
      engagementsCount: engagements.length,
      queryStatus: engagementsQuery.status,
      queryFetchStatus: engagementsQuery.fetchStatus,
      queryIsStale: engagementsQuery.isStale,
      queryIsEnabled: engagementsQuery.isEnabled,
      queryKey: engagementsQuery.queryKey,
    });
  }, [
    engagementsLoading,
    engagementsError,
    engagements.length,
    engagementsQuery.status,
    engagementsQuery.fetchStatus,
    engagementsQuery.isStale,
    engagementsQuery.isEnabled,
    engagementsQuery.queryKey,
  ]);

  const clientsQuery = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: async () => {
      console.log('🔍 Fetching clients for engagement management...');
      const result = await apiCall('/api/v1/admin/clients/?limit=100');
      console.log('🔍 Clients API result:', result);

      // Handle different response formats
      if (result && Array.isArray(result)) {
        console.log('✅ Using direct array format for clients');
        return result;
      } else if (result && result.items && Array.isArray(result.items)) {
        console.log('✅ Using items array format for clients');
        return result.items;
      } else if (result && result.clients && Array.isArray(result.clients)) {
        console.log('✅ Using clients array format for clients');
        return result.clients;
      } else {
        console.warn('⚠️ Unexpected clients API response format:', result);
        return [];
      }
    },
    retry: 2,
    enabled: true,
    refetchOnMount: 'always',
    staleTime: 0, // Always consider data stale
    gcTime: 0, // Don't keep in cache (replacement for deprecated cacheTime)
  });
  const clients = clientsQuery.data || [];
  const clientsLoading = clientsQuery.isLoading;
  const clientsError = clientsQuery.isError;

  // Form data state
  const [formData, setFormData] = useState<EngagementFormData>({
    engagement_name: '',
    engagement_description: '',
    client_account_id: '',
    migration_scope: '',
    target_cloud_provider: '',
    migration_phase: '',
    engagement_manager: '',
    technical_lead: '',
    start_date: '',
    end_date: '',
    budget: 0,
    budget_currency: 'USD',
    team_preferences: {},
    stakeholder_preferences: {},
  });

  // Handle form changes
  const handleFormChange = useCallback(
    (field: keyof EngagementFormData, value: EngagementFormData[keyof EngagementFormData]) => {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    },
    []
  );

  // Handle engagement update
  const handleUpdateEngagement = async (): void => {
    if (!editingEngagement) return;

    try {
      // Map frontend fields to backend field names
      const submissionData = {
        engagement_name: formData.engagement_name,
        engagement_description: formData.engagement_description,
        // Don't include client_account_id in updates - it shouldn't be changeable
        migration_scope: formData.migration_scope,
        target_cloud_provider: formData.target_cloud_provider,
        current_phase: formData.migration_phase, // Map migration_phase to current_phase
        engagement_manager: formData.engagement_manager,
        technical_lead: formData.technical_lead,
        planned_start_date: formData.start_date
          ? new Date(formData.start_date).toISOString()
          : null,
        planned_end_date: formData.end_date ? new Date(formData.end_date).toISOString() : null,
        estimated_budget: formData.budget || null,
        team_preferences: formData.team_preferences || {},
        agent_configuration: {},
        discovery_preferences: {},
        assessment_criteria: {},
      };

      console.log('Updating engagement with data:', JSON.stringify(submissionData, null, 2));

      const result = await apiCall(`/api/v1/admin/engagements/${editingEngagement.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      if (result && result.message) {
        toast({
          title: 'Success',
          description: result.message || 'Engagement updated successfully.',
        });
        // Refetch engagements after successful update
        engagementsQuery.refetch();
        setEditingEngagement(null);
        resetForm();
      } else {
        toast({
          title: 'Error',
          description: 'Failed to update engagement.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error updating engagement:', error);
      toast({
        title: 'Error',
        description: 'Failed to update engagement. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Handle engagement deletion
  const handleDeleteEngagement = async (engagementId: string, engagementName: string): void => {
    const confirmed = await dialog.confirm({
      title: 'Delete Engagement',
      description: `Are you sure you want to delete "${engagementName}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      variant: 'destructive',
      icon: 'warning',
    });

    if (!confirmed) {
      return;
    }

    try {
      const result = await apiCall(`/api/v1/admin/engagements/${engagementId}`, {
        method: 'DELETE',
      });
      if (result && result.message) {
        toast({
          title: 'Success',
          description: result.message || 'Engagement deleted successfully.',
        });
        // Refetch engagements after successful deletion
        engagementsQuery.refetch();
      } else {
        toast({
          title: 'Error',
          description: 'Failed to delete engagement.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error deleting engagement:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete engagement. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Reset form data
  const resetForm = useCallback(() => {
    setFormData({
      engagement_name: '',
      engagement_description: '',
      client_account_id: '',
      migration_scope: '',
      target_cloud_provider: '',
      migration_phase: '',
      engagement_manager: '',
      technical_lead: '',
      start_date: '',
      end_date: '',
      actual_start_date: '',
      actual_end_date: '',
      budget: 0,
      budget_currency: 'USD',
      actual_budget: 0,
      estimated_asset_count: 0,
      completion_percentage: 0,
      team_preferences: {},
      stakeholder_preferences: {},
    });
  }, []);

  // Start editing an engagement
  const startEdit = useCallback((engagement: Engagement) => {
    // Map backend fields to frontend form fields
    const plannedStartDate = engagement.planned_start_date || engagement.start_date;
    const plannedEndDate = engagement.planned_end_date || engagement.end_date;
    const currentPhase = engagement.current_phase || engagement.migration_phase;

    setFormData({
      engagement_name: engagement.engagement_name || '',
      engagement_description: engagement.engagement_description || '',
      client_account_id: engagement.client_account_id || '',
      migration_scope: engagement.migration_scope || '',
      target_cloud_provider: engagement.target_cloud_provider || '',
      migration_phase: currentPhase || '',
      engagement_manager: engagement.engagement_manager || '',
      technical_lead: engagement.technical_lead || '',
      start_date: plannedStartDate ? new Date(plannedStartDate).toISOString().split('T')[0] : '',
      end_date: plannedEndDate ? new Date(plannedEndDate).toISOString().split('T')[0] : '',
      budget: engagement.estimated_budget || engagement.budget || 0,
      budget_currency: engagement.budget_currency || 'USD',
      team_preferences: engagement.team_preferences || {},
      stakeholder_preferences: {},
    });
    setEditingEngagement(engagement);
  }, []);

  // Utility functions
  const getPhaseColor = useCallback((phase: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-yellow-100 text-yellow-800',
      discovery: 'bg-blue-100 text-blue-800',
      assessment: 'bg-purple-100 text-purple-800',
      migration: 'bg-orange-100 text-orange-800',
      optimization: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
    };
    return colors[phase] || 'bg-gray-100 text-gray-800';
  }, []);

  const formatCurrency = useCallback((amount: number, currency: string) => {
    // Handle missing or invalid currency codes
    if (!currency || currency.trim() === '') {
      return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount);
    }

    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
      }).format(amount);
    } catch (error) {
      // Fallback to decimal format if currency is invalid
      return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount);
    }
  }, []);

  // Filter engagements based on search term (already filtered by query, but keep for UI search)
  const filteredEngagements = engagements.filter(
    (engagement) =>
      engagement.engagement_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      engagement.client_account_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      engagement.engagement_manager?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Debug Panel */}
      <div className="bg-gray-100 p-4 rounded-lg border">
        <h3 className="font-semibold mb-2">Debug Information</h3>
        <div className="text-sm space-y-1">
          <p>Loading: {engagementsLoading ? 'true' : 'false'}</p>
          <p>Error: {engagementsError ? 'true' : 'false'}</p>
          <p>Engagements Count: {engagements.length}</p>
          <p>Query Status: {engagementsQuery.status}</p>
          <p>Fetch Status: {engagementsQuery.fetchStatus}</p>
          <p>Clients Loading: {clientsLoading ? 'true' : 'false'}</p>
          <p>Clients Error: {clientsError ? 'true' : 'false'}</p>
          <p>Clients Count: {clients.length}</p>
          <p>
            Clients: {clients.length > 0 ? clients.map((c) => c.account_name).join(', ') : 'None'}
          </p>
        </div>
        <div className="flex gap-2 mt-2">
          <Button onClick={() => engagementsQuery.refetch()} disabled={engagementsQuery.isFetching}>
            {engagementsQuery.isFetching ? 'Fetching...' : 'Manual Refetch'}
          </Button>
          <Button
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['engagements'] });
              queryClient.refetchQueries({ queryKey: ['engagements'] });
            }}
            variant="outline"
          >
            Clear Cache & Refetch
          </Button>
          <Button
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['clients'] });
              queryClient.refetchQueries({ queryKey: ['clients'] });
            }}
            variant="outline"
          >
            Refetch Clients
          </Button>
        </div>
      </div>

      <EngagementFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        filterClient={filterClient}
        onClientFilterChange={setFilterClient}
        filterPhase={filterPhase}
        onPhaseFilterChange={setFilterPhase}
        clients={clients}
      />

      <EngagementStats engagements={filteredEngagements} />

      <EngagementList
        engagements={filteredEngagements}
        loading={engagementsLoading}
        onEditEngagement={startEdit}
        onDeleteEngagement={handleDeleteEngagement}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        getPhaseColor={getPhaseColor}
        formatCurrency={formatCurrency}
      />

      {/* Edit Engagement Dialog */}
      <Dialog
        open={!!editingEngagement}
        onOpenChange={(open) => !open && setEditingEngagement(null)}
      >
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Edit Engagement: {editingEngagement?.engagement_name}</DialogTitle>
            <DialogDescription>
              Update engagement information and team assignments.
            </DialogDescription>
          </DialogHeader>
          <EngagementForm formData={formData} onFormChange={handleFormChange} clients={clients} />
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setEditingEngagement(null);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdateEngagement}>Update Engagement</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EngagementManagementMain;
