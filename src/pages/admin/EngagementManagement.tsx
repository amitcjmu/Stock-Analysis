import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
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

const EngagementManagement: React.FC = () => {
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
  const { toast } = useToast();

  const [formData, setFormData] = useState<EngagementFormData>({
    engagement_name: '',
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

  // Optimized form field handlers to prevent input focus loss
  const handleInputChange = useCallback((field: keyof EngagementFormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = field === 'budget' ? parseFloat(e.target.value) || 0 : e.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleSelectChange = useCallback((field: keyof EngagementFormData) => (value: string) => {
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
        headers: {
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        }
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
      const response = await fetch('/api/v1/admin/engagements/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create engagement');
      }

      const result = await response.json();
      
      toast({
        title: "Success",
        description: `Engagement "${formData.engagement_name}" created successfully`,
      });

      setShowCreateDialog(false);
      resetForm();
      fetchEngagements();
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
      const response = await fetch(`/api/v1/admin/engagements/${editingEngagement.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to update engagement');
      }

      toast({
        title: "Success",
        description: `Engagement "${formData.engagement_name}" updated successfully`,
      });

      setEditingEngagement(null);
      resetForm();
      fetchEngagements();
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
      const response = await fetch(`/api/v1/admin/engagements/${engagementId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete engagement');
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

  const EngagementForm = () => (
    <div className="space-y-6 max-h-96 overflow-y-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="engagement_name">Engagement Name *</Label>
          <Input
            id="engagement_name"
            value={formData.engagement_name}
            onChange={handleInputChange('engagement_name')}
            placeholder="Enter engagement name"
            required
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="client_account_id">Client *</Label>
          <Select value={formData.client_account_id} onValueChange={handleSelectChange('client_account_id')}>
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
          <Select value={formData.migration_scope} onValueChange={handleSelectChange('migration_scope')}>
            <SelectTrigger>
              <SelectValue placeholder="Select migration scope" />
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
          <Select value={formData.target_cloud_provider} onValueChange={handleSelectChange('target_cloud_provider')}>
            <SelectTrigger>
              <SelectValue placeholder="Select cloud provider" />
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
          <Select value={formData.migration_phase} onValueChange={handleSelectChange('migration_phase')}>
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
            onChange={handleInputChange('engagement_manager')}
            placeholder="Full name"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="technical_lead">Technical Lead *</Label>
          <Input
            id="technical_lead"
            value={formData.technical_lead}
            onChange={handleInputChange('technical_lead')}
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
            onChange={handleInputChange('start_date')}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="end_date">End Date *</Label>
          <Input
            id="end_date"
            type="date"
            value={formData.end_date}
            onChange={handleInputChange('end_date')}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="budget">Budget</Label>
          <div className="flex gap-2">
            <Input
              id="budget"
              type="number"
              value={formData.budget || ''}
              onChange={handleInputChange('budget')}
              placeholder="0"
              className="flex-1"
            />
            <Select value={formData.budget_currency} onValueChange={handleSelectChange('budget_currency')}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="USD">USD</SelectItem>
                <SelectItem value="EUR">EUR</SelectItem>
                <SelectItem value="GBP">GBP</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
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
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Engagement
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl">
              <DialogHeader>
                <DialogTitle>Create New Engagement</DialogTitle>
                <DialogDescription>
                  Set up a new migration engagement with project details and team assignments.
                </DialogDescription>
              </DialogHeader>
              <EngagementForm />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => {setShowCreateDialog(false); resetForm();}}>
                  Cancel
                </Button>
                <Button onClick={handleCreateEngagement}>
                  Create Engagement
                </Button>
              </div>
            </DialogContent>
          </Dialog>
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
        <Select value={filterClient} onValueChange={setFilterClient}>
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
        <Select value={filterPhase} onValueChange={setFilterPhase}>
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
              Update engagement details and project configuration.
            </DialogDescription>
          </DialogHeader>
          <EngagementForm />
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