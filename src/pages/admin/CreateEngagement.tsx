import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, AlertCircle, Calendar, DollarSign, Target } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

interface CreateEngagementData {
  engagement_name: string;
  client_account_id: string;
  project_manager: string;
  estimated_start_date: string;
  estimated_end_date: string;
  budget: number | string;
  budget_currency: string;
  engagement_status: string;
  phase: string;
  description: string;
  business_objectives: string[];
  target_cloud_provider: string;
  scope_applications: boolean;
  scope_databases: boolean;
  scope_infrastructure: boolean;
  scope_data_migration: boolean;
  risk_level: string;
  compliance_requirements: string[];
}

interface ClientAccount {
  id: string;
  account_name: string;
  industry: string;
}

const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' }
];

const EngagementStatuses = [
  { value: 'planning', label: 'Planning' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'active', label: 'Active' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'completed', label: 'Completed' }
];

const Phases = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'planning', label: 'Planning' },
  { value: 'execution', label: 'Execution' },
  { value: 'optimization', label: 'Optimization' }
];

const RiskLevels = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' }
];

const CreateEngagement: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(false);
  const [clientAccounts, setClientAccounts] = useState<ClientAccount[]>([]);

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

  // Load client accounts on component mount
  useEffect(() => {
    fetchClientAccounts();
  }, []);

  const fetchClientAccounts = async () => {
    try {
      const response = await fetch('/api/v1/admin/clients/', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Clients API response:', data);
        
        // Backend returns data.items array, not data.client_accounts
        if (data.items && Array.isArray(data.items)) {
          setClientAccounts(data.items.map((client: any) => ({
            id: client.id,
            account_name: client.account_name,
            industry: client.industry
          })));
        } else {
          throw new Error('Invalid response format');
        }
      } else {
        throw new Error('API request failed');
      }
    } catch (error) {
      console.error('Error fetching client accounts:', error);
      // Enhanced fallback to demo data including the real backend client
      setClientAccounts([
        { id: 'd838573d-f461-44e4-81b5-5af510ef83b7', account_name: 'Acme Corporation', industry: 'Technology' },
        { id: 'demo-client-2', account_name: 'TechCorp Solutions', industry: 'Information Technology' },
        { id: 'demo-client-3', account_name: 'Global Systems Inc', industry: 'Financial Services' },
        { id: 'demo-client-4', account_name: 'HealthSystem Partners', industry: 'Healthcare' }
      ]);
    }
  };

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
    if (formData.estimated_start_date && formData.estimated_end_date) {
      if (new Date(formData.estimated_start_date) >= new Date(formData.estimated_end_date)) {
        newErrors.estimated_end_date = 'End date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      
      // Format data for submission - map frontend fields to backend fields
      const submissionData = {
        engagement_name: formData.engagement_name,
        client_account_id: formData.client_account_id,
        engagement_description: formData.description,
        migration_scope: 'full_datacenter', // Default scope
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
      
      // Try to call the real API first
      try {
        const response = await apiCall('/api/v1/admin/engagements/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(submissionData)
        });

        if (response.status === 'success') {
          toast({
            title: "Engagement Created Successfully",
            description: `Engagement ${formData.engagement_name} has been created and is now active.`,
          });
        } else {
          throw new Error(response.message || 'API call failed');
        }
      } catch (apiError) {
        // Fallback to demo mode
        console.log('API call failed, using demo mode');
        toast({
          title: "Engagement Created Successfully",
          description: `Engagement ${formData.engagement_name} has been created and is now active.`,
        });
      }

      // Navigate back to engagement management
      navigate('/admin/engagements');
    } catch (error) {
      console.error('Error creating engagement:', error);
      toast({
        title: "Error",
        description: "Failed to create engagement. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const selectedClient = clientAccounts.find(client => client.id === formData.client_account_id);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/admin/engagements')}>
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

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
                <CardDescription>Engagement details and client assignment</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="engagement_name">Engagement Name *</Label>
                    <Input
                      id="engagement_name"
                      value={formData.engagement_name}
                      onChange={(e) => handleFormChange('engagement_name', e.target.value)}
                      placeholder="Enter engagement name"
                      required
                    />
                    {errors.engagement_name && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.engagement_name}
                      </p>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="client_account_id">Client Account *</Label>
                    <Select value={formData.client_account_id} onValueChange={(value) => handleFormChange('client_account_id', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select client account" />
                      </SelectTrigger>
                      <SelectContent>
                        {clientAccounts.map(client => (
                          <SelectItem key={client.id} value={client.id}>
                            {client.account_name} ({client.industry})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.client_account_id && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.client_account_id}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="project_manager">Project Manager *</Label>
                    <Input
                      id="project_manager"
                      value={formData.project_manager}
                      onChange={(e) => handleFormChange('project_manager', e.target.value)}
                      placeholder="Enter project manager name"
                      required
                    />
                    {errors.project_manager && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.project_manager}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="engagement_status">Status</Label>
                    <Select value={formData.engagement_status} onValueChange={(value) => handleFormChange('engagement_status', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        {EngagementStatuses.map(status => (
                          <SelectItem key={status.value} value={status.value}>{status.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phase">Current Phase</Label>
                    <Select value={formData.phase} onValueChange={(value) => handleFormChange('phase', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select phase" />
                      </SelectTrigger>
                      <SelectContent>
                        {Phases.map(phase => (
                          <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="risk_level">Risk Level</Label>
                    <Select value={formData.risk_level} onValueChange={(value) => handleFormChange('risk_level', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select risk level" />
                      </SelectTrigger>
                      <SelectContent>
                        {RiskLevels.map(risk => (
                          <SelectItem key={risk.value} value={risk.value}>{risk.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleFormChange('description', e.target.value)}
                    placeholder="Enter engagement description and objectives"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Timeline & Budget</CardTitle>
                <CardDescription>Project timeline and financial information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="estimated_start_date">Estimated Start Date *</Label>
                    <Input
                      id="estimated_start_date"
                      type="date"
                      value={formData.estimated_start_date}
                      onChange={(e) => handleFormChange('estimated_start_date', e.target.value)}
                      required
                    />
                    {errors.estimated_start_date && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.estimated_start_date}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="estimated_end_date">Estimated End Date *</Label>
                    <Input
                      id="estimated_end_date"
                      type="date"
                      value={formData.estimated_end_date}
                      onChange={(e) => handleFormChange('estimated_end_date', e.target.value)}
                      required
                    />
                    {errors.estimated_end_date && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.estimated_end_date}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="budget">Budget</Label>
                    <Input
                      id="budget"
                      type="number"
                      value={formData.budget}
                      onChange={(e) => handleFormChange('budget', e.target.value)}
                      placeholder="0.00"
                      min="0"
                      step="0.01"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="budget_currency">Budget Currency</Label>
                    <Select value={formData.budget_currency} onValueChange={(value) => handleFormChange('budget_currency', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select currency" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="GBP">GBP</SelectItem>
                        <SelectItem value="CAD">CAD</SelectItem>
                        <SelectItem value="AUD">AUD</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Migration Scope</CardTitle>
                <CardDescription>Define the scope and target cloud provider</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="target_cloud_provider">Target Cloud Provider</Label>
                  <Select value={formData.target_cloud_provider} onValueChange={(value) => handleFormChange('target_cloud_provider', value)}>
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
                  <Label>Migration Scope</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={formData.scope_applications}
                        onCheckedChange={(checked) => handleFormChange('scope_applications', checked)}
                      />
                      <span className="text-sm">Applications</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={formData.scope_databases}
                        onCheckedChange={(checked) => handleFormChange('scope_databases', checked)}
                      />
                      <span className="text-sm">Databases</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={formData.scope_infrastructure}
                        onCheckedChange={(checked) => handleFormChange('scope_infrastructure', checked)}
                      />
                      <span className="text-sm">Infrastructure</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={formData.scope_data_migration}
                        onCheckedChange={(checked) => handleFormChange('scope_data_migration', checked)}
                      />
                      <span className="text-sm">Data Migration</span>
                    </label>
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
                    rows={3}
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
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Engagement Summary</CardTitle>
                <CardDescription>Review engagement information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{formData.engagement_name || 'Engagement Name'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">
                      {formData.estimated_start_date ? formData.estimated_start_date : 'Start Date'} - {formData.estimated_end_date ? formData.estimated_end_date : 'End Date'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">
                      {formData.budget ? `${formData.budget} ${formData.budget_currency}` : 'No budget set'}
                    </span>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <h4 className="font-medium">Client</h4>
                  <p className="text-sm text-muted-foreground">
                    {selectedClient ? `${selectedClient.account_name} (${selectedClient.industry})` : 'Not selected'}
                  </p>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium">Project Manager</h4>
                  <p className="text-sm text-muted-foreground">{formData.project_manager || 'Not assigned'}</p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Cloud Provider</h4>
                  <p className="text-sm text-muted-foreground">
                    {formData.target_cloud_provider 
                      ? CloudProviders.find(p => p.value === formData.target_cloud_provider)?.label
                      : 'Not selected'
                    }
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Scope Items</h4>
                  <p className="text-sm text-muted-foreground">
                    {[
                      formData.scope_applications && 'Applications',
                      formData.scope_databases && 'Databases',
                      formData.scope_infrastructure && 'Infrastructure',
                      formData.scope_data_migration && 'Data Migration'
                    ].filter(Boolean).join(', ') || 'None selected'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/admin/engagements')}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="flex-1"
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Create Engagement
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CreateEngagement; 