import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  Building2, Plus, Search, Edit, Trash2, Eye, Users, Mail, Phone, MapPin, 
  MoreHorizontal, Download, Upload
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';
import { apiCall } from '@/config/api';
import { Client, ClientFormData, Industries, CompanySizes, SubscriptionTiers } from './types';

// ClientForm component
interface ClientFormProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: any) => void;
}

const ClientForm: React.FC<ClientFormProps> = React.memo(({ formData, onFormChange }) => (
  <div className="space-y-6 max-h-96 overflow-y-auto">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="account_name">Account Name *</Label>
        <Input
          id="account_name"
          value={formData.account_name}
          onChange={(e) => onFormChange('account_name', e.target.value)}
          placeholder="Enter company name"
          required
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="industry">Industry *</Label>
        <Select value={formData.industry} onValueChange={(value) => onFormChange('industry', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select industry" />
          </SelectTrigger>
          <SelectContent>
            {Industries.map(industry => (
              <SelectItem key={industry} value={industry}>{industry}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="company_size">Company Size *</Label>
        <Select value={formData.company_size} onValueChange={(value) => onFormChange('company_size', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select company size" />
          </SelectTrigger>
          <SelectContent>
            {CompanySizes.map(size => (
              <SelectItem key={size} value={size}>{size}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="headquarters_location">Headquarters Location *</Label>
        <Input
          id="headquarters_location"
          value={formData.headquarters_location}
          onChange={(e) => onFormChange('headquarters_location', e.target.value)}
          placeholder="City, State/Country"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="primary_contact_name">Primary Contact Name *</Label>
        <Input
          id="primary_contact_name"
          value={formData.primary_contact_name}
          onChange={(e) => onFormChange('primary_contact_name', e.target.value)}
          placeholder="Full name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="primary_contact_email">Primary Contact Email *</Label>
        <Input
          id="primary_contact_email"
          type="email"
          value={formData.primary_contact_email}
          onChange={(e) => onFormChange('primary_contact_email', e.target.value)}
          placeholder="email@company.com"
          required
        />
      </div>
    </div>

    <div className="space-y-2">
      <Label htmlFor="description">Description</Label>
      <Textarea
        id="description"
        value={formData.description}
        onChange={(e) => onFormChange('description', e.target.value)}
        placeholder="Brief description of the client..."
        rows={3}
      />
    </div>
  </div>
));

const ClientManagementMain: React.FC = () => {
  const { toast } = useToast();

  // State management
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);

  // Form data state
  const [formData, setFormData] = useState<ClientFormData>({
    account_name: '',
    industry: '',
    company_size: '',
    headquarters_location: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    description: '',
    subscription_tier: 'basic',
    billing_contact_email: '',
    settings: {},
    branding: {},
    business_objectives: [],
    target_cloud_providers: [],
    business_priorities: [],
    compliance_requirements: [],
    it_guidelines: {},
    decision_criteria: {},
    agent_preferences: {},
    budget_constraints: {},
    timeline_constraints: {}
  });

  // Handle form changes
  const handleFormChange = useCallback((field: keyof ClientFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Fetch clients from API
  const fetchClients = useCallback(async () => {
    try {
      setLoading(true);
      
      // Build query parameters
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

  // Handle client operations
  const handleCreateClient = async () => {
    const newClient: Client = {
      id: Date.now().toString(),
      ...formData,
      created_at: new Date().toISOString(),
      is_active: true,
      total_engagements: 0,
      active_engagements: 0
    };

    setClients(prev => [newClient, ...prev]);
    toast({ title: "Success", description: "Client created successfully" });
    setShowCreateDialog(false);
    resetForm();
  };

  const handleUpdateClient = async () => {
    if (!editingClient) return;

    const updatedClient: Client = {
      ...editingClient,
      ...formData,
      updated_at: new Date().toISOString()
    };

    setClients(prev => prev.map(client => 
      client.id === editingClient.id ? updatedClient : client
    ));

    toast({ title: "Success", description: "Client updated successfully" });
    setEditingClient(null);
    resetForm();
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (!confirm(`Delete client "${clientName}"?`)) return;

    setClients(prev => prev.filter(client => client.id !== clientId));
    toast({ title: "Success", description: "Client deleted successfully" });
  };

  const resetForm = useCallback(() => {
    setFormData({
      account_name: '',
      industry: '',
      company_size: '',
      headquarters_location: '',
      primary_contact_name: '',
      primary_contact_email: '',
      primary_contact_phone: '',
      description: '',
      subscription_tier: 'basic',
      billing_contact_email: '',
      settings: {},
      branding: {},
      business_objectives: [],
      target_cloud_providers: [],
      business_priorities: [],
      compliance_requirements: [],
      it_guidelines: {},
      decision_criteria: {},
      agent_preferences: {},
      budget_constraints: {},
      timeline_constraints: {}
    });
  }, []);

  const startEdit = useCallback((client: Client) => {
    setFormData({
      account_name: client.account_name,
      industry: client.industry,
      company_size: client.company_size,
      headquarters_location: client.headquarters_location,
      primary_contact_name: client.primary_contact_name,
      primary_contact_email: client.primary_contact_email,
      primary_contact_phone: client.primary_contact_phone || '',
      description: client.description || '',
      subscription_tier: client.subscription_tier || 'basic',
      billing_contact_email: client.billing_contact_email || '',
      settings: client.settings || {},
      branding: client.branding || {},
      business_objectives: client.business_objectives,
      target_cloud_providers: client.target_cloud_providers,
      business_priorities: client.business_priorities,
      compliance_requirements: client.compliance_requirements,
      it_guidelines: client.it_guidelines || {},
      decision_criteria: client.decision_criteria || {},
      agent_preferences: client.agent_preferences || {},
      budget_constraints: client.budget_constraints || {},
      timeline_constraints: client.timeline_constraints || {}
    });
    setEditingClient(client);
  }, []);

  const filteredClients = clients.filter(client =>
    client.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.primary_contact_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Client Management</h1>
          <p className="text-muted-foreground">Manage client accounts and settings</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="w-4 h-4 mr-2" />Export</Button>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />New Client
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search clients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {/* Clients Table */}
      <Card>
        <CardHeader>
          <CardTitle>Client Accounts</CardTitle>
          <CardDescription>{filteredClients.length} clients found</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredClients.map((client) => (
                  <TableRow key={client.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{client.account_name}</div>
                        <div className="text-sm text-muted-foreground">{client.headquarters_location}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{client.primary_contact_name}</div>
                        <div className="text-sm text-muted-foreground">{client.primary_contact_email}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{client.industry}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={client.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                        {client.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => startEdit(client)}>
                            <Edit className="w-4 h-4 mr-2" />Edit Client
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteClient(client.id, client.account_name)}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />Delete Client
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Create New Client</DialogTitle>
            <DialogDescription>Add a new client account to the system.</DialogDescription>
          </DialogHeader>
          <ClientForm formData={formData} onFormChange={handleFormChange} />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {setShowCreateDialog(false); resetForm();}}>Cancel</Button>
            <Button onClick={handleCreateClient}>Create Client</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editingClient} onOpenChange={(open) => !open && setEditingClient(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Edit Client: {editingClient?.account_name}</DialogTitle>
            <DialogDescription>Update client account information.</DialogDescription>
          </DialogHeader>
          <ClientForm formData={formData} onFormChange={handleFormChange} />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {setEditingClient(null); resetForm();}}>Cancel</Button>
            <Button onClick={handleUpdateClient}>Update Client</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientManagementMain; 