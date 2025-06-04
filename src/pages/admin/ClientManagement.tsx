import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  Building2, 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Eye,
  Users,
  Mail,
  Phone,
  MapPin,
  Calendar,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Download,
  Upload
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';

interface Client {
  id: string;
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone?: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  total_engagements: number;
  active_engagements: number;
}

interface ClientFormData {
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines: Record<string, any>;
  decision_criteria: Record<string, any>;
  agent_preferences: Record<string, any>;
}

const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' }
];

const BusinessPriorities = [
  { value: 'cost_reduction', label: 'Cost Reduction' },
  { value: 'agility_speed', label: 'Agility & Speed' },
  { value: 'security_compliance', label: 'Security & Compliance' },
  { value: 'innovation', label: 'Innovation' },
  { value: 'scalability', label: 'Scalability' },
  { value: 'reliability', label: 'Reliability' }
];

const Industries = [
  'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
  'Education', 'Government', 'Energy', 'Transportation', 'Other'
];

const CompanySizes = [
  'Small (1-100)', 'Medium (101-1000)', 'Large (1001-5000)', 'Enterprise (5000+)'
];

const ClientManagement: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [filterSize, setFilterSize] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { toast } = useToast();

  const [formData, setFormData] = useState<ClientFormData>({
    account_name: '',
    industry: '',
    company_size: '',
    headquarters_location: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    business_objectives: [],
    target_cloud_providers: [],
    business_priorities: [],
    compliance_requirements: [],
    it_guidelines: {},
    decision_criteria: {},
    agent_preferences: {}
  });

  // Simple direct form handlers - no useCallback to prevent re-renders
  const handleFormChange = (field: keyof ClientFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  useEffect(() => {
    fetchClients();
  }, [currentPage, searchTerm, filterIndustry, filterSize]);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20'
      });

      if (searchTerm) params.append('account_name', searchTerm);
      if (filterIndustry) params.append('industry', filterIndustry);
      if (filterSize) params.append('company_size', filterSize);

      const response = await fetch(`/api/v1/admin/clients/?${params}`, {
        headers: {
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch clients');
      }

      const data = await response.json();
      setClients(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching clients:', error);
      toast({
        title: "Error",
        description: "Failed to fetch clients. Using demo data.",
        variant: "destructive"
      });
      
      // Demo data fallback
      setClients([
        {
          id: '1',
          account_name: 'Pujyam Corp',
          industry: 'Technology',
          company_size: 'Enterprise (5000+)',
          headquarters_location: 'San Francisco, CA',
          primary_contact_name: 'John Smith',
          primary_contact_email: 'john.smith@pujyam.com',
          primary_contact_phone: '+1-555-0123',
          business_objectives: ['Cost Reduction', 'Modernization'],
          target_cloud_providers: ['aws', 'azure'],
          business_priorities: ['cost_reduction', 'agility_speed'],
          compliance_requirements: ['SOC2', 'GDPR'],
          created_at: '2024-01-15T10:30:00Z',
          is_active: true,
          total_engagements: 3,
          active_engagements: 2
        },
        {
          id: '2',
          account_name: 'TechCorp Solutions',
          industry: 'Technology',
          company_size: 'Large (1001-5000)',
          headquarters_location: 'Austin, TX',
          primary_contact_name: 'Sarah Johnson',
          primary_contact_email: 'sarah.johnson@techcorp.com',
          business_objectives: ['Innovation', 'Scalability'],
          target_cloud_providers: ['gcp'],
          business_priorities: ['innovation', 'scalability'],
          compliance_requirements: ['HIPAA'],
          created_at: '2024-02-20T14:45:00Z',
          is_active: true,
          total_engagements: 1,
          active_engagements: 1
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async () => {
    try {
      const response = await fetch('/api/v1/admin/clients/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create client');
      }

      const result = await response.json();
      
      toast({
        title: "Success",
        description: `Client "${formData.account_name}" created successfully`,
      });

      setShowCreateDialog(false);
      resetForm();
      fetchClients();
    } catch (error) {
      console.error('Error creating client:', error);
      toast({
        title: "Error",
        description: "Failed to create client. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleUpdateClient = async () => {
    if (!editingClient) return;

    try {
      const response = await fetch(`/api/v1/admin/clients/${editingClient.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to update client');
      }

      toast({
        title: "Success",
        description: `Client "${formData.account_name}" updated successfully`,
      });

      setEditingClient(null);
      resetForm();
      fetchClients();
    } catch (error) {
      console.error('Error updating client:', error);
      toast({
        title: "Error",
        description: "Failed to update client. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (!confirm(`Are you sure you want to delete client "${clientName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/clients/${clientId}`, {
        method: 'DELETE',
        headers: {
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete client');
      }

      toast({
        title: "Success",
        description: `Client "${clientName}" deleted successfully`,
      });

      fetchClients();
    } catch (error) {
      console.error('Error deleting client:', error);
      toast({
        title: "Error",
        description: "Failed to delete client. Please try again.",
        variant: "destructive"
      });
    }
  };

  const resetForm = () => {
    setFormData({
      account_name: '',
      industry: '',
      company_size: '',
      headquarters_location: '',
      primary_contact_name: '',
      primary_contact_email: '',
      primary_contact_phone: '',
      business_objectives: [],
      target_cloud_providers: [],
      business_priorities: [],
      compliance_requirements: [],
      it_guidelines: {},
      decision_criteria: {},
      agent_preferences: {}
    });
  };

  const startEdit = (client: Client) => {
    setEditingClient(client);
    setFormData({
      account_name: client.account_name,
      industry: client.industry,
      company_size: client.company_size,
      headquarters_location: client.headquarters_location,
      primary_contact_name: client.primary_contact_name,
      primary_contact_email: client.primary_contact_email,
      primary_contact_phone: client.primary_contact_phone || '',
      business_objectives: client.business_objectives,
      target_cloud_providers: client.target_cloud_providers,
      business_priorities: client.business_priorities,
      compliance_requirements: client.compliance_requirements,
      it_guidelines: {},
      decision_criteria: {},
      agent_preferences: {}
    });
  };

  const filteredClients = clients.filter(client =>
    client.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.primary_contact_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.industry.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const ClientForm = () => (
    <div className="space-y-6 max-h-96 overflow-y-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account_name">Account Name *</Label>
          <Input
            id="account_name"
            value={formData.account_name}
            onChange={(e) => handleFormChange('account_name', e.target.value)}
            placeholder="Enter company name"
            required
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="industry">Industry *</Label>
          <Select value={formData.industry} onValueChange={(value) => handleFormChange('industry', value)}>
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
          <Select value={formData.company_size} onValueChange={(value) => handleFormChange('company_size', value)}>
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
            onChange={(e) => handleFormChange('headquarters_location', e.target.value)}
            placeholder="City, State/Country"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="primary_contact_name">Primary Contact Name *</Label>
          <Input
            id="primary_contact_name"
            value={formData.primary_contact_name}
            onChange={(e) => handleFormChange('primary_contact_name', e.target.value)}
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
            onChange={(e) => handleFormChange('primary_contact_email', e.target.value)}
            placeholder="email@company.com"
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
        <Input
          id="primary_contact_phone"
          value={formData.primary_contact_phone}
          onChange={(e) => handleFormChange('primary_contact_phone', e.target.value)}
          placeholder="+1-555-0123"
        />
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Business Context</h4>
        
        <div className="space-y-2">
          <Label>Target Cloud Providers</Label>
          <div className="grid grid-cols-2 gap-2">
            {CloudProviders.map(provider => (
              <label key={provider.value} className="flex items-center space-x-2">
                <Checkbox
                  checked={formData.target_cloud_providers.includes(provider.value)}
                  onCheckedChange={(checked) => {
                    const currentArray = formData.target_cloud_providers;
                    if (checked) {
                      handleFormChange('target_cloud_providers', [...currentArray, provider.value]);
                    } else {
                      handleFormChange('target_cloud_providers', currentArray.filter(item => item !== provider.value));
                    }
                  }}
                />
                <span className="text-sm">{provider.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label>Business Priorities</Label>
          <div className="grid grid-cols-2 gap-2">
            {BusinessPriorities.map(priority => (
              <label key={priority.value} className="flex items-center space-x-2">
                <Checkbox
                  checked={formData.business_priorities.includes(priority.value)}
                  onCheckedChange={(checked) => {
                    const currentArray = formData.business_priorities;
                    if (checked) {
                      handleFormChange('business_priorities', [...currentArray, priority.value]);
                    } else {
                      handleFormChange('business_priorities', currentArray.filter(item => item !== priority.value));
                    }
                  }}
                />
                <span className="text-sm">{priority.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="business_objectives">Business Objectives</Label>
          <Textarea
            id="business_objectives"
            placeholder="Enter business objectives (one per line)"
            value={formData.business_objectives.join('\n')}
            onChange={(e) => {
              const newArray = e.target.value.split('\n').filter(item => item.trim());
              handleFormChange('business_objectives', newArray);
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="compliance_requirements">Compliance Requirements</Label>
          <Textarea
            id="compliance_requirements"
            placeholder="Enter compliance requirements (one per line)"
            value={formData.compliance_requirements.join('\n')}
            onChange={(e) => {
              const newArray = e.target.value.split('\n').filter(item => item.trim());
              handleFormChange('compliance_requirements', newArray);
            }}
          />
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Client Management</h1>
          <p className="text-muted-foreground">
            Manage client accounts and business relationships
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <Button asChild>
            <Link to="/admin/clients/create">
              <Plus className="w-4 h-4 mr-2" />
              New Client
            </Link>
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
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
        <Select value={filterIndustry} onValueChange={setFilterIndustry}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Industry" />
          </SelectTrigger>
          <SelectContent>
                            <SelectItem value="all">All Industries</SelectItem>
            {Industries.map(industry => (
              <SelectItem key={industry} value={industry}>{industry}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterSize} onValueChange={setFilterSize}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Company Size" />
          </SelectTrigger>
          <SelectContent>
                            <SelectItem value="all">All Sizes</SelectItem>
            {CompanySizes.map(size => (
              <SelectItem key={size} value={size}>{size}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Clients Table */}
      <Card>
        <CardHeader>
          <CardTitle>Client Accounts</CardTitle>
          <CardDescription>
            {filteredClients.length} client{filteredClients.length !== 1 ? 's' : ''} found
          </CardDescription>
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
                  <TableHead>Industry</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Engagements</TableHead>
                  <TableHead>Cloud Strategy</TableHead>
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
                        <div className="text-sm text-muted-foreground flex items-center">
                          <MapPin className="w-3 h-3 mr-1" />
                          {client.headquarters_location}
                        </div>
                        <div className="text-sm text-muted-foreground">{client.company_size}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{client.industry}</Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{client.primary_contact_name}</div>
                        <div className="text-sm text-muted-foreground flex items-center">
                          <Mail className="w-3 h-3 mr-1" />
                          {client.primary_contact_email}
                        </div>
                        {client.primary_contact_phone && (
                          <div className="text-sm text-muted-foreground flex items-center">
                            <Phone className="w-3 h-3 mr-1" />
                            {client.primary_contact_phone}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">{client.active_engagements} active</div>
                        <div className="text-muted-foreground">{client.total_engagements} total</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {client.target_cloud_providers.slice(0, 2).map(provider => (
                          <Badge key={provider} variant="outline" className="text-xs">
                            {provider.toUpperCase()}
                          </Badge>
                        ))}
                        {client.target_cloud_providers.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{client.target_cloud_providers.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {client.is_active ? (
                        <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <XCircle className="w-3 h-3 mr-1" />
                          Inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/clients/${client.id}`}>
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => startEdit(client)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Client
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/engagements?client=${client.id}`}>
                              <Users className="w-4 h-4 mr-2" />
                              View Engagements
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteClient(client.id, client.account_name)}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete Client
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

      {/* Edit Client Dialog */}
      <Dialog open={!!editingClient} onOpenChange={(open) => !open && setEditingClient(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Edit Client: {editingClient?.account_name}</DialogTitle>
            <DialogDescription>
              Update client account information and business context.
            </DialogDescription>
          </DialogHeader>
          <ClientForm />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {setEditingClient(null); resetForm();}}>
              Cancel
            </Button>
            <Button onClick={handleUpdateClient}>
              Update Client
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button 
            variant="outline" 
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="flex items-center px-4 text-sm">
            Page {currentPage} of {totalPages}
          </span>
          <Button 
            variant="outline" 
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};

export default ClientManagement; 