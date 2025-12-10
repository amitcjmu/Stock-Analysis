import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useDialog } from '@/hooks/useDialog';
import { apiCall } from '@/config/api';

import { EngagementFilters } from './EngagementFilters';
import { EngagementStats } from './EngagementStats';
import { EngagementList } from './EngagementList';
import { EngagementForm } from './EngagementForm';
import type { EngagementFormData } from './types';
import type { Engagement, Client } from './types';

const EngagementManagementMain = () => {
  const { toast } = useToast();
  const dialog = useDialog();

  // UI state must be declared before useQuery hooks
  const [searchTerm, setSearchTerm] = useState('');
  const [filterClient, setFilterClient] = useState('all');
  const [filterPhase, setFilterPhase] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [editingEngagement, setEditingEngagement] = useState<Engagement | null>(null);
  const [selectedEngagements, setSelectedEngagements] = useState<string[]>([]);
  const [bulkDeleteLoading, setBulkDeleteLoading] = useState(false);

  // Server state: useQuery for API data
  const engagementsQuery = useQuery<Engagement[]>({
    queryKey: ['engagements', filterClient, filterPhase, currentPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterClient !== 'all') params.append('client_account_id', filterClient);
      if (filterPhase !== 'all') params.append('phase', filterPhase);
      params.append('page', currentPage.toString());
      params.append('page_size', '20');

      const queryString = params.toString();
      const result = await apiCall(
        `/api/v1/admin/engagements/${queryString ? '?' + queryString : ''}`
      );

      // Handle paginated response
      if (result && typeof result === 'object' && 'items' in result) {
        if (result.total_pages) {
          setTotalPages(result.total_pages);
        }
        return result.items || [];
      }

      // Handle direct array response
      if (Array.isArray(result)) {
        return result;
      }

      return [];
    },
    refetchOnWindowFocus: false,
  });
  const engagements = engagementsQuery.data || [];
  const engagementsLoading = engagementsQuery.isLoading;

  const clientsQuery = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: async () => {
      const result = await apiCall('/api/v1/admin/clients/?page_size=100');

      // Handle paginated response
      if (result && typeof result === 'object' && 'items' in result) {
        return result.items || [];
      }

      // Handle direct array
      if (Array.isArray(result)) {
        return result;
      }

      return [];
    },
    refetchOnWindowFocus: false,
  });
  const clients = clientsQuery.data || [];
  const clientsLoading = clientsQuery.isLoading;

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

  // Filter engagements based on search term (already filtered by query, but keep for UI search)
  // NOTE: This must be defined BEFORE handleSelectAll which depends on it
  const filteredEngagements = Array.isArray(engagements)
    ? engagements.filter((engagement) => {
        // Handle case where engagement might be null or have missing properties
        if (!engagement) {
          return false;
        }

        // If no search term, include all valid engagements
        if (!searchTerm) {
          return true;
        }

        // Safe property access with optional chaining
        const name = engagement.engagement_name || engagement.name || '';
        const clientName = engagement.client_account_name || '';
        const manager = engagement.engagement_manager || '';

        const matchesSearch =
          name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          clientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          manager.toLowerCase().includes(searchTerm.toLowerCase());

        return matchesSearch;
      })
    : [];

  // Handle toggle selection for a single engagement
  const handleToggleSelection = useCallback((engagementId: string) => {
    setSelectedEngagements((prev) =>
      prev.includes(engagementId)
        ? prev.filter((id) => id !== engagementId)
        : [...prev, engagementId]
    );
  }, []);

  // Handle select all engagements
  const handleSelectAll = useCallback(
    (selected: boolean) => {
      setSelectedEngagements(
        selected ? filteredEngagements.map((engagement) => engagement.id) : []
      );
    },
    [filteredEngagements]
  );

  // Handle bulk delete engagements
  const handleBulkDelete = async (): Promise<void> => {
    if (selectedEngagements.length === 0) return;

    const confirmed = await dialog.confirm({
      title: 'Bulk Delete Engagements',
      description: `Delete ${selectedEngagements.length} selected engagements? This action cannot be undone.`,
      confirmText: 'Delete All',
      cancelText: 'Cancel',
      variant: 'destructive',
      icon: 'warning',
    });

    if (!confirmed) return;

    try {
      setBulkDeleteLoading(true);

      const result = await apiCall('/api/v1/admin/engagements/bulk-delete', {
        method: 'POST',
        body: JSON.stringify(selectedEngagements),
      });

      if (result && (result.status === 'success' || result.message)) {
        toast({
          title: 'Success',
          description: `Deleted ${result.data?.deleted_count || selectedEngagements.length} engagements`,
        });
        // Refetch engagements and clear selection
        engagementsQuery.refetch();
        setSelectedEngagements([]);
      } else {
        throw new Error(result?.message || 'Failed to bulk delete engagements');
      }
    } catch (error) {
      console.error('Error bulk deleting engagements:', error);
      const errorObj = error as { message?: string };
      toast({
        title: 'Error',
        description: errorObj.message || 'Failed to bulk delete engagements',
        variant: 'destructive',
      });
    } finally {
      setBulkDeleteLoading(false);
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

  return (
    <div className="container mx-auto p-6 space-y-6">
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
        selectedEngagements={selectedEngagements}
        onToggleSelection={handleToggleSelection}
        onSelectAll={handleSelectAll}
        onBulkDelete={handleBulkDelete}
        bulkDeleteLoading={bulkDeleteLoading}
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
