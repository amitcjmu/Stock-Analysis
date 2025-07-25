import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { Upload } from 'lucide-react'
import { Building2, Plus, Search, Download } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ClientForm } from './components/ClientForm';
import { ClientTable } from './components/ClientTable';
import { useClientData } from './hooks/useClientData';
import { useClientOperations } from './hooks/useClientOperations';
import type { ClientFormData , Client} from './types'
import { Industries } from './types'

const initialFormData: ClientFormData = {
  account_name: '',
  industry: '',
  company_size: '',
  primary_contact_name: '',
  primary_contact_email: '',
  primary_contact_phone: '',
  billing_contact_email: '',
  headquarters_location: '',
  time_zone: '',
  subscription_tier: 'Standard',
  description: '',
  business_objectives: [],
  target_cloud_providers: [],
  business_priorities: [],
  compliance_requirements: [],
  migration_timeline: '',
  it_guidelines: {
    architecture_patterns: [],
    security_requirements: [],
    data_residency_requirements: [],
    integration_standards: []
  },
  decision_criteria: {
    risk_tolerance: 'medium',
    cost_sensitivity: 'medium',
    timeline_pressure: 'medium',
    technical_debt_tolerance: 'medium'
  },
  agent_preferences: {
    confidence_thresholds: {
      field_mapping: 0.8,
      dependency_detection: 0.75,
      risk_assessment: 0.85
    },
    escalation_mode: 'balanced'
  },
  platform_settings: {
    enable_notifications: true,
    enable_auto_discovery: true,
    enable_cost_optimization: true,
    data_retention_days: 90,
    backup_frequency: 'daily'
  }
};

const ClientManagementMain: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [formData, setFormData] = useState<ClientFormData>(initialFormData);

  const { clients, setClients, loading } = useClientData({ searchTerm, filterIndustry });
  const { actionLoading, createClient, updateClient, deleteClient } = useClientOperations();

  // Form handlers
  const handleFormChange = useCallback((field: keyof ClientFormData, value: string | string[]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData(initialFormData);
  }, []);

  // Client operations
  const handleCreateClient = async () => {
    const newClient = await createClient(formData);
    if (newClient) {
      setClients(prev => [newClient, ...prev]);
      setShowCreateDialog(false);
      resetForm();
    }
  };

  const handleUpdateClient = async () => {
    if (!editingClient) return;

    const updatedClient = await updateClient(editingClient, formData);
    if (updatedClient) {
      setClients(prev => prev.map(client =>
        client.id === editingClient.id ? updatedClient : client
      ));
      setEditingClient(null);
      resetForm();
    }
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    const success = await deleteClient(clientId, clientName);
    if (success) {
      setClients(prev => prev.filter(client => client.id !== clientId));
    }
  };

  const handleEditClient = (client: Client) => {
    setEditingClient(client);
    setFormData({
      account_name: client.account_name,
      industry: client.industry,
      company_size: client.company_size,
      primary_contact_name: client.primary_contact_name,
      primary_contact_email: client.primary_contact_email,
      primary_contact_phone: client.primary_contact_phone || '',
      billing_contact_email: client.billing_contact_email || '',
      headquarters_location: client.headquarters_location || '',
      time_zone: client.time_zone || '',
      subscription_tier: client.subscription_tier,
      description: client.description || '',
      business_objectives: client.business_objectives || [],
      target_cloud_providers: client.target_cloud_providers || [],
      business_priorities: client.business_priorities || [],
      compliance_requirements: client.compliance_requirements || [],
      migration_timeline: client.migration_timeline || '',
      it_guidelines: client.it_guidelines || initialFormData.it_guidelines,
      decision_criteria: client.decision_criteria || initialFormData.decision_criteria,
      agent_preferences: client.agent_preferences || initialFormData.agent_preferences,
      platform_settings: client.platform_settings || initialFormData.platform_settings
    });
  };

  const exportClients = () => {
    const dataStr = JSON.stringify(clients, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    const exportFileDefaultName = `clients_export_${new Date().toISOString().split('T')[0]}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-6 w-6" />
                Client Management
              </CardTitle>
              <CardDescription>
                Manage client accounts, engagements, and platform settings
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="icon" onClick={exportClients}>
                <Download className="h-4 w-4" />
              </Button>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Client
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search by account name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterIndustry} onValueChange={setFilterIndustry}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by industry" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Industries</SelectItem>
                {Industries.map(industry => (
                  <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Client Table */}
          <ClientTable
            clients={clients}
            loading={loading}
            actionLoading={actionLoading}
            onEditClient={handleEditClient}
            onDeleteClient={handleDeleteClient}
          />
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Create New Client</DialogTitle>
            <DialogDescription>
              Enter the client details below. Fields marked with * are required.
            </DialogDescription>
          </DialogHeader>
          <ClientForm formData={formData} onFormChange={handleFormChange} />
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false);
              resetForm();
            }}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateClient}
              disabled={actionLoading === 'create'}
            >
              {actionLoading === 'create' ? 'Creating...' : 'Create Client'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editingClient} onOpenChange={(open) => {
        if (!open) {
          setEditingClient(null);
          resetForm();
        }
      }}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Edit Client</DialogTitle>
            <DialogDescription>
              Update the client details below. Fields marked with * are required.
            </DialogDescription>
          </DialogHeader>
          <ClientForm formData={formData} onFormChange={handleFormChange} />
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => {
              setEditingClient(null);
              resetForm();
            }}>
              Cancel
            </Button>
            <Button
              onClick={handleUpdateClient}
              disabled={actionLoading === editingClient?.id}
            >
              {actionLoading === editingClient?.id ? 'Updating...' : 'Update Client'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ClientManagementMain;
