import React, { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

import { EngagementFilters } from './EngagementFilters';
import { EngagementStats } from './EngagementStats';
import { EngagementList } from './EngagementList';
import { EngagementForm } from './EngagementForm';
import { Engagement, EngagementFormData, Client } from './types';

const EngagementManagementMain: React.FC = () => {
  const { toast } = useToast();
  const { user } = useAuth();

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
        params.append('limit', '10');
        
        // Use demo client ID if no specific client filter
        if (filterClient === 'all') {
          params.append('client_account_id', '11111111-1111-1111-1111-111111111111'); // Demo client ID
        }
        
        const queryString = params.toString();
        const result = await apiCall(`/admin/engagements/?${queryString}`);
        return result.items || [];
      } catch (error) {
        console.error('Error fetching engagements:', error);
        // Fallback demo data
        return [];
      }
    },
    initialData: [],
  });
  const engagements = engagementsQuery.data || [];
  const engagementsLoading = engagementsQuery.isLoading;
  const engagementsError = engagementsQuery.isError;

  const clientsQuery = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: async () => {
      try {
        const result = await apiCall('/admin/clients/?limit=100');
        return result.items || [];
      } catch (error) {
        console.error('Error fetching clients:', error);
        // Fallback demo data
        return [];
      }
    },
    initialData: [],
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
    stakeholder_preferences: {}
  });

  // Handle form changes
  const handleFormChange = useCallback((field: keyof EngagementFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Handle engagement update
  const handleUpdateEngagement = async () => {
    if (!editingEngagement) return;
    // TODO: Refactor to use React Query mutation for update (not in scope for this lint fix)
    // When implemented, use engagementsQuery.refetch() after mutation to refresh data.
    toast({
      title: "Not Implemented",
      description: "Update engagement mutation should use React Query.",
      variant: "destructive",
    });
  };

  // Handle engagement deletion
  const handleDeleteEngagement = async (engagementId: string, engagementName: string) => {
    if (!confirm(`Are you sure you want to delete "${engagementName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const result = await apiCall(`/admin/engagements/${engagementId}`, {
        method: 'DELETE'
      });
      if (result && result.message) {
        toast({
          title: "Success",
          description: result.message || "Engagement deleted successfully.",
        });
        // Refetch engagements after successful deletion
        engagementsQuery.refetch();
      } else {
        toast({
          title: "Error",
          description: "Failed to delete engagement.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error deleting engagement:', error);
      toast({
        title: "Error",
        description: "Failed to delete engagement. Please try again.",
        variant: "destructive",
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
      budget: 0,
      budget_currency: 'USD',
      team_preferences: {},
      stakeholder_preferences: {}
    });
  }, []);

  // Start editing an engagement
  const startEdit = useCallback((engagement: Engagement) => {
    setFormData({
      engagement_name: engagement.engagement_name || '',
      engagement_description: engagement.engagement_description || '',
      client_account_id: engagement.client_account_id || '',
      migration_scope: engagement.migration_scope || '',
      target_cloud_provider: engagement.target_cloud_provider || '',
      migration_phase: engagement.migration_phase || '',
      engagement_manager: engagement.engagement_manager || '',
      technical_lead: engagement.technical_lead || '',
      start_date: engagement.start_date || '',
      end_date: engagement.end_date || '',
      budget: engagement.budget || 0,
      budget_currency: engagement.budget_currency || 'USD',
      team_preferences: {},
      stakeholder_preferences: {}
    });
    setEditingEngagement(engagement);
  }, []);

  // Utility functions
  const getPhaseColor = useCallback((phase: string) => {
    const colors: Record<string, string> = {
      'planning': 'bg-yellow-100 text-yellow-800',
      'discovery': 'bg-blue-100 text-blue-800',
      'assessment': 'bg-purple-100 text-purple-800',
      'migration': 'bg-orange-100 text-orange-800',
      'optimization': 'bg-green-100 text-green-800',
      'completed': 'bg-gray-100 text-gray-800'
    };
    return colors[phase] || 'bg-gray-100 text-gray-800';
  }, []);

  const formatCurrency = useCallback((amount: number, currency: string) => {
    // Handle missing or invalid currency codes
    if (!currency || currency.trim() === '') {
      return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    }
    
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
      }).format(amount);
    } catch (error) {
      // Fallback to decimal format if currency is invalid
      return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    }
  }, []);

  // Filter engagements based on search term (already filtered by query, but keep for UI search)
  const filteredEngagements = engagements.filter(engagement =>
    engagement.engagement_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.client_account_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.engagement_manager?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
      />

      {/* Edit Engagement Dialog */}
      <Dialog open={!!editingEngagement} onOpenChange={(open) => !open && setEditingEngagement(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Edit Engagement: {editingEngagement?.engagement_name}</DialogTitle>
            <DialogDescription>
              Update engagement information and team assignments.
            </DialogDescription>
          </DialogHeader>
          <EngagementForm formData={formData} onFormChange={handleFormChange} clients={clients} />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {setEditingEngagement(null); resetForm();}}>
              Cancel
            </Button>
            <Button onClick={handleUpdateEngagement}>
              Update Engagement
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EngagementManagementMain; 