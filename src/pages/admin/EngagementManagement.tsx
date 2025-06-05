import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Calendar, 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Eye,
  Users,
  Building2,
  MapPin,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Download,
  Upload,
  Target,
  TrendingUp,
  AlertCircle,
  Briefcase,
  User,
  AlertTriangle
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
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

interface Engagement {
  id: string;
  engagement_name: string;
  client_account_id: string;
  client_account_name: string;
  migration_scope: string;
  target_cloud_provider: string;
  migration_phase: string;
  engagement_manager: string;
  technical_lead: string;
  start_date: string;
  end_date: string;
  budget: number;
  budget_currency: string;
  completion_percentage: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  total_sessions: number;
  active_sessions: number;
}

interface EngagementFormData {
  engagement_name: string;
  engagement_description: string;
  client_account_id: string;
  migration_scope: string;
  target_cloud_provider: string;
  migration_phase: string;
  engagement_manager: string;
  technical_lead: string;
  start_date: string;
  end_date: string;
  budget: number;
  budget_currency: string;
  team_preferences: Record<string, any>;
  stakeholder_preferences: Record<string, any>;
}

interface Client {
  id: string;
  account_name: string;
}

const MigrationScopes = [
  { value: 'full_datacenter', label: 'Full Datacenter Migration' },
  { value: 'application_portfolio', label: 'Application Portfolio' },
  { value: 'infrastructure_only', label: 'Infrastructure Only' },
  { value: 'selected_applications', label: 'Selected Applications' },
  { value: 'pilot_migration', label: 'Pilot Migration' },
  { value: 'hybrid_cloud', label: 'Hybrid Cloud Setup' }
];

const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' }
];

const MigrationPhases = [
  { value: 'planning', label: 'Planning' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'migration', label: 'Migration' },
  { value: 'optimization', label: 'Optimization' },
  { value: 'completed', label: 'Completed' }
];

const Currencies = [
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
  { value: 'CAD', label: 'Canadian Dollar (CAD)' },
  { value: 'AUD', label: 'Australian Dollar (AUD)' },
  { value: 'JPY', label: 'Japanese Yen (JPY)' },
  { value: 'INR', label: 'Indian Rupee (INR)' }
];

// Move EngagementForm component outside to prevent re-creation
interface EngagementFormProps {
  formData: EngagementFormData;
  onFormChange: (field: keyof EngagementFormData, value: any) => void;
  clients: Client[];
}

const EngagementForm: React.FC<EngagementFormProps> = React.memo(({ formData, onFormChange, clients }) => (
  <div className="space-y-6 max-h-96 overflow-y-auto">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="engagement_name">Engagement Name *</Label>
        <Input
          id="engagement_name"
          value={formData.engagement_name}
          onChange={(e) => onFormChange('engagement_name', e.target.value)}
          placeholder="Enter engagement name"
          required
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="client_account_id">Client Account *</Label>
        <Select value={formData.client_account_id} onValueChange={(value) => onFormChange('client_account_id', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select client" />
          </SelectTrigger>
          <SelectContent>
            {clients.map(client => (
              <SelectItem key={client.id} value={client.id}>{client.account_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="migration_scope">Migration Scope *</Label>
        <Select value={formData.migration_scope} onValueChange={(value) => onFormChange('migration_scope', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select scope" />
          </SelectTrigger>
          <SelectContent>
            {MigrationScopes.map(scope => (
              <SelectItem key={scope.value} value={scope.value}>{scope.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="target_cloud_provider">Target Cloud Provider *</Label>
        <Select value={formData.target_cloud_provider} onValueChange={(value) => onFormChange('target_cloud_provider', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select provider" />
          </SelectTrigger>
          <SelectContent>
            {CloudProviders.map(provider => (
              <SelectItem key={provider.value} value={provider.value}>{provider.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="migration_phase">Migration Phase *</Label>
        <Select value={formData.migration_phase} onValueChange={(value) => onFormChange('migration_phase', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select phase" />
          </SelectTrigger>
          <SelectContent>
            {MigrationPhases.map(phase => (
              <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="engagement_manager">Engagement Manager *</Label>
        <Input
          id="engagement_manager"
          value={formData.engagement_manager}
          onChange={(e) => onFormChange('engagement_manager', e.target.value)}
          placeholder="Full name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="technical_lead">Technical Lead *</Label>
        <Input
          id="technical_lead"
          value={formData.technical_lead}
          onChange={(e) => onFormChange('technical_lead', e.target.value)}
          placeholder="Full name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="start_date">Start Date *</Label>
        <Input
          id="start_date"
          type="date"
          value={formData.start_date}
          onChange={(e) => onFormChange('start_date', e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="end_date">End Date *</Label>
        <Input
          id="end_date"
          type="date"
          value={formData.end_date}
          onChange={(e) => onFormChange('end_date', e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="budget">Budget</Label>
        <Input
          id="budget"
          type="number"
          value={formData.budget}
          onChange={(e) => onFormChange('budget', parseFloat(e.target.value) || 0)}
          placeholder="0"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="budget_currency">Budget Currency</Label>
        <Select value={formData.budget_currency} onValueChange={(value) => onFormChange('budget_currency', value)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Currencies.map(currency => (
              <SelectItem key={currency.value} value={currency.value}>{currency.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>

    <div className="space-y-2">
      <Label htmlFor="engagement_description">Engagement Description *</Label>
      <Textarea
        id="engagement_description"
        value={formData.engagement_description}
        onChange={(e) => onFormChange('engagement_description', e.target.value)}
        placeholder="Brief description of the engagement scope and objectives"
        rows={3}
        required
      />
    </div>
  </div>
));

const EngagementManagement: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterClient, setFilterClient] = useState('');
  const [filterPhase, setFilterPhase] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingEngagement, setEditingEngagement] = useState<Engagement | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [formData, setFormData] = useState<EngagementFormData>({
    engagement_name: '',
    engagement_description: '',
    client_account_id: '',
    migration_scope: '',
    target_cloud_provider: '',
    migration_phase: 'planning',
    engagement_manager: '',
    technical_lead: '',
    start_date: '',
    end_date: '',
    budget: 0,
    budget_currency: 'USD',
    team_preferences: {},
    stakeholder_preferences: {}
  });

  // Use useCallback to memoize the form change handler
  const handleFormChange = useCallback((field: keyof EngagementFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  useEffect(() => {
    fetchEngagements();
    fetchClients();
  }, [currentPage, searchTerm, filterClient, filterPhase]);

  const fetchEngagements = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20'
      });

      if (searchTerm) params.append('engagement_name', searchTerm);
      if (filterClient) params.append('client_account_id', filterClient);
      if (filterPhase) params.append('migration_phase', filterPhase);

      const response = await fetch(`/api/v1/admin/engagements/?${params}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch engagements');
      }

      const data = await response.json();
      setEngagements(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching engagements:', error);
      toast({
        title: "Error",
        description: "Failed to fetch engagements. Using demo data.",
        variant: "destructive"
      });
      
      // Demo data fallback
      setEngagements([
        {
          id: '1',
          engagement_name: 'Cloud Migration 2025',
          client_account_id: '1',
          client_account_name: 'Pujyam Corp',
          migration_scope: 'application_portfolio',
          target_cloud_provider: 'aws',
          migration_phase: 'discovery',
          engagement_manager: 'John Smith',
          technical_lead: 'Sarah Wilson',
          start_date: '2025-01-15',
          end_date: '2025-12-31',
          budget: 2500000,
          budget_currency: 'USD',
          completion_percentage: 35.5,
          created_at: '2025-01-10T10:30:00Z',
          is_active: true,
          total_sessions: 8,
          active_sessions: 3
        },
        {
          id: '2',
          engagement_name: 'Azure Transformation',
          client_account_id: '2',
          client_account_name: 'TechCorp Solutions',
          migration_scope: 'full_datacenter',
          target_cloud_provider: 'azure',
          migration_phase: 'planning',
          engagement_manager: 'Mike Johnson',
          technical_lead: 'Lisa Chen',
          start_date: '2025-03-01',
          end_date: '2026-02-28',
          budget: 5000000,
          budget_currency: 'USD',
          completion_percentage: 15.0,
          created_at: '2025-02-20T14:45:00Z',
          is_active: true,
          total_sessions: 2,
          active_sessions: 1
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await fetch('/api/v1/admin/clients/?page_size=100', {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch clients');
      }

      const data = await response.json();
      setClients(data.items || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
      
      // Demo clients fallback
      setClients([
        { id: '1', account_name: 'Pujyam Corp' },
        { id: '2', account_name: 'TechCorp Solutions' }
      ]);
    }
  };

  const handleCreateEngagement = async () => {
    try {
      const response = await apiCall('/api/v1/admin/engagements/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(formData)
      });

      if (response.status === 'success') {
        const result = response;
        
        toast({
          title: "Success",
          description: `Engagement "${formData.engagement_name}" created successfully`,
        });

        setShowCreateDialog(false);
        resetForm();
        fetchEngagements();
      } else {
        throw new Error(response.message || 'Failed to create engagement');
      }
    } catch (error) {
      console.error('Error creating engagement:', error);
      toast({
        title: "Error",
        description: "Failed to create engagement. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleUpdateEngagement = async () => {
    if (!editingEngagement) return;

    try {
      const response = await apiCall(`/api/v1/admin/engagements/${editingEngagement.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(formData)
      });

      if (response.status === 'success') {
        toast({
          title: "Success",
          description: `Engagement "${formData.engagement_name}" updated successfully`,
        });

        setEditingEngagement(null);
        resetForm();
        fetchEngagements();
      } else {
        throw new Error(response.message || 'Failed to update engagement');
      }
    } catch (error) {
      console.error('Error updating engagement:', error);
      toast({
        title: "Error",
        description: "Failed to update engagement. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteEngagement = async (engagementId: string, engagementName: string) => {
    if (!confirm(`Are you sure you want to delete engagement "${engagementName}"?`)) {
      return;
    }

    try {
      const response = await apiCall(`/api/v1/admin/engagements/${engagementId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (response.status !== 'success') {
        throw new Error(response.message || 'Failed to delete engagement');
      }

      toast({
        title: "Success",
        description: `Engagement "${engagementName}" deleted successfully`,
      });

      fetchEngagements();
    } catch (error) {
      console.error('Error deleting engagement:', error);
      toast({
        title: "Error",
        description: "Failed to delete engagement. Please try again.",
        variant: "destructive"
      });
    }
  };

  const resetForm = () => {
    setFormData({
      engagement_name: '',
      engagement_description: '',
      client_account_id: '',
      migration_scope: '',
      target_cloud_provider: '',
      migration_phase: 'planning',
      engagement_manager: '',
      technical_lead: '',
      start_date: '',
      end_date: '',
      budget: 0,
      budget_currency: 'USD',
      team_preferences: {},
      stakeholder_preferences: {}
    });
  };

  const startEdit = (engagement: Engagement) => {
    setEditingEngagement(engagement);
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
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'planning': return 'bg-gray-100 text-gray-800';
      case 'discovery': return 'bg-blue-100 text-blue-800';
      case 'assessment': return 'bg-yellow-100 text-yellow-800';
      case 'migration': return 'bg-orange-100 text-orange-800';
      case 'optimization': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
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
  };

  const filteredEngagements = engagements.filter(engagement =>
    engagement.engagement_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.client_account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    engagement.engagement_manager.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Engagement Management</h1>
          <p className="text-muted-foreground">
            Manage client engagements and migration projects
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
            <Link to="/admin/engagements/create">
              <Plus className="w-4 h-4 mr-2" />
              New Engagement
            </Link>
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search engagements..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={filterClient} onValueChange={(value) => setFilterClient(value)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Client" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Clients</SelectItem>
            {clients.map(client => (
              <SelectItem key={client.id} value={client.id}>{client.account_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterPhase} onValueChange={(value) => setFilterPhase(value)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Phase" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Phases</SelectItem>
            {MigrationPhases.map(phase => (
              <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Engagements Table */}
      <Card>
        <CardHeader>
          <CardTitle>Active Engagements</CardTitle>
          <CardDescription>
            {filteredEngagements.length} engagement{filteredEngagements.length !== 1 ? 's' : ''} found
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
                  <TableHead>Engagement</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Team</TableHead>
                  <TableHead>Timeline</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEngagements.map((engagement) => (
                  <TableRow key={engagement.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{engagement.engagement_name}</div>
                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                          <Badge className={getPhaseColor(engagement.migration_phase)}>
                            {engagement.migration_phase}
                          </Badge>
                          <span>{engagement.migration_scope.replace('_', ' ')}</span>
                        </div>
                        <div className="text-sm text-muted-foreground flex items-center">
                          <Target className="w-3 h-3 mr-1" />
                          {engagement.target_cloud_provider.toUpperCase()}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{engagement.client_account_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {engagement.total_sessions} sessions
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm">
                          <span className="font-medium">EM:</span> {engagement.engagement_manager}
                        </div>
                        <div className="text-sm">
                          <span className="font-medium">TL:</span> {engagement.technical_lead}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(engagement.start_date).toLocaleDateString()}
                        </div>
                        <div className="flex items-center text-muted-foreground">
                          <Clock className="w-3 h-3 mr-1" />
                          {new Date(engagement.end_date).toLocaleDateString()}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">
                          {engagement.budget ? 
                            formatCurrency(engagement.budget, engagement.budget_currency || 'USD') :
                            'No budget set'
                          }
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${engagement.completion_percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {engagement.completion_percentage.toFixed(1)}%
                        </span>
                      </div>
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
                            <Link to={`/admin/engagements/${engagement.id}`}>
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => startEdit(engagement)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Engagement
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/discovery?engagement=${engagement.id}`}>
                              <TrendingUp className="w-4 h-4 mr-2" />
                              View Progress
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteEngagement(engagement.id, engagement.engagement_name)}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete Engagement
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

export default EngagementManagement; 