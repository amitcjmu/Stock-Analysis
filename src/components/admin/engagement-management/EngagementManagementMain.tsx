import React, { useState, useEffect, useCallback } from 'react';
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

  // State management
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterClient, setFilterClient] = useState('all');
  const [filterPhase, setFilterPhase] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [editingEngagement, setEditingEngagement] = useState<Engagement | null>(null);

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

  // Fetch engagements from API
  const fetchEngagements = useCallback(async () => {
    try {
      setLoading(true);
      
      // Build query parameters
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterClient !== 'all') params.append('client_id', filterClient);
      if (filterPhase !== 'all') params.append('phase', filterPhase);
      params.append('page', currentPage.toString());
      params.append('limit', '10');

      const queryString = params.toString();
      const url = `/admin/engagements${queryString ? `?${queryString}` : ''}`;

      const result = await apiCall(url);
      
      if (result.success) {
        setEngagements(result.data.engagements || []);
        setTotalPages(Math.ceil((result.data.total || 0) / 10));
      } else {
        console.error('Failed to fetch engagements:', result.error);
        toast({
          title: "Error",
          description: "Failed to fetch engagements. Please try again.",
          variant: "destructive",
        });
        setEngagements([]);
      }
    } catch (error) {
      console.error('Error fetching engagements:', error);
      toast({
        title: "Error",
        description: "Failed to fetch engagements. Please try again.",
        variant: "destructive",
      });
      setEngagements([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterClient, filterPhase, currentPage, toast]);

  // Fetch clients for dropdown
  const fetchClients = useCallback(async () => {
    try {
      const result = await apiCall('/admin/clients?limit=100');
      if (result.success) {
        setClients(result.data.clients || []);
      } else {
        console.error('Failed to fetch clients:', result.error);
        setClients([]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    }
  }, []);

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

    try {
      const result = await apiCall(`/admin/engagements/${editingEngagement.id}`, {
        method: 'PUT',
        body: JSON.stringify(formData)
      });

      if (result.success) {
        toast({
          title: "Success",
          description: "Engagement updated successfully.",
        });
        setEditingEngagement(null);
        resetForm();
        await fetchEngagements();
      } else {
        toast({
          title: "Error", 
          description: result.error || "Failed to update engagement.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error updating engagement:', error);
      toast({
        title: "Error",
        description: "Failed to update engagement. Please try again.",
        variant: "destructive",
      });
    }
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

      if (result.success) {
        toast({
          title: "Success",
          description: "Engagement deleted successfully.",
        });
        await fetchEngagements();
      } else {
        toast({
          title: "Error",
          description: result.error || "Failed to delete engagement.",
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
      engagement_name: engagement.engagement_name,
      engagement_description: '',
      client_account_id: engagement.client_account_id,
      migration_scope: engagement.migration_scope,
      target_cloud_provider: engagement.target_cloud_provider,
      migration_phase: engagement.migration_phase,
      engagement_manager: engagement.engagement_manager,
      technical_lead: engagement.technical_lead,
      start_date: engagement.start_date,
      end_date: engagement.end_date,
      budget: engagement.budget,
      budget_currency: engagement.budget_currency,
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

  // Filter engagements based on search term
  const filteredEngagements = engagements.filter(engagement =>
    engagement.engagement_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.client_account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.engagement_manager.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Effects
  useEffect(() => {
    fetchEngagements();
  }, [fetchEngagements]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

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
        loading={loading}
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