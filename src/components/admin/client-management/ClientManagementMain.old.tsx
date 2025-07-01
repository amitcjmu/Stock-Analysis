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
import { Client, ClientFormData, Industries, CompanySizes, SubscriptionTiers, CloudProviders, BusinessPriorities } from './types';

// ClientForm component
interface ClientFormProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: any) => void;
}

const ClientForm: React.FC<ClientFormProps> = React.memo(({ formData, onFormChange }) => {
  const [activeTab, setActiveTab] = useState<'basic' | 'business' | 'technical' | 'advanced'>('basic');

  const handleMultiSelect = (field: keyof ClientFormData, value: string, checked: boolean) => {
    const currentValues = (formData[field] as string[]) || [];
    if (checked) {
      onFormChange(field, [...currentValues, value]);
    } else {
      onFormChange(field, currentValues.filter(v => v !== value));
    }
  };

  return (
    <div className="space-y-6 max-h-[600px] overflow-y-auto">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'basic', label: 'Basic Information' },
            { id: 'business', label: 'Business Context' },
            { id: 'technical', label: 'Technical Preferences' },
            { id: 'advanced', label: 'Advanced Settings' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Basic Information Tab */}
      {activeTab === 'basic' && (
        <div className="space-y-6">
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

            <div className="space-y-2">
              <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
              <Input
                id="primary_contact_phone"
                value={formData.primary_contact_phone}
                onChange={(e) => onFormChange('primary_contact_phone', e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="billing_contact_email">Billing Contact Email</Label>
              <Input
                id="billing_contact_email"
                type="email"
                value={formData.billing_contact_email}
                onChange={(e) => onFormChange('billing_contact_email', e.target.value)}
                placeholder="billing@company.com"
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

          <div className="space-y-2">
            <Label htmlFor="subscription_tier">Subscription Tier</Label>
            <Select value={formData.subscription_tier} onValueChange={(value) => onFormChange('subscription_tier', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select subscription tier" />
              </SelectTrigger>
              <SelectContent>
                {SubscriptionTiers.map(tier => (
                  <SelectItem key={tier.value} value={tier.value}>{tier.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Business Context Tab */}
      {activeTab === 'business' && (
        <div className="space-y-6">
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">Business Objectives</Label>
              <p className="text-sm text-gray-600 mb-3">Select primary business objectives for this migration</p>
              <div className="space-y-2">
                {['Cost Reduction', 'Increased Agility', 'Enhanced Security', 'Scalability', 'Innovation', 'Compliance', 'Digital Transformation'].map((objective) => (
                  <div key={objective} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`objective-${objective}`}
                      checked={formData.business_objectives.includes(objective)}
                      onChange={(e) => handleMultiSelect('business_objectives', objective, e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`objective-${objective}`} className="text-sm">{objective}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-base font-medium">Target Cloud Providers</Label>
              <p className="text-sm text-gray-600 mb-3">Select preferred cloud platforms</p>
              <div className="space-y-2">
                {CloudProviders.map((provider) => (
                  <div key={provider.value} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`provider-${provider.value}`}
                      checked={formData.target_cloud_providers.includes(provider.value)}
                      onChange={(e) => handleMultiSelect('target_cloud_providers', provider.value, e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`provider-${provider.value}`} className="text-sm">{provider.label}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-base font-medium">Business Priorities</Label>
              <p className="text-sm text-gray-600 mb-3">Rank key business priorities</p>
              <div className="space-y-2">
                {BusinessPriorities.map((priority) => (
                  <div key={priority.value} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`priority-${priority.value}`}
                      checked={formData.business_priorities.includes(priority.value)}
                      onChange={(e) => handleMultiSelect('business_priorities', priority.value, e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`priority-${priority.value}`} className="text-sm">{priority.label}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-base font-medium">Compliance Requirements</Label>
              <p className="text-sm text-gray-600 mb-3">Select applicable compliance standards</p>
              <div className="space-y-2">
                {['SOC 2', 'HIPAA', 'PCI DSS', 'GDPR', 'ISO 27001', 'FedRAMP', 'FISMA', 'SOX'].map((compliance) => (
                  <div key={compliance} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`compliance-${compliance}`}
                      checked={formData.compliance_requirements.includes(compliance)}
                      onChange={(e) => handleMultiSelect('compliance_requirements', compliance, e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`compliance-${compliance}`} className="text-sm">{compliance}</Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Technical Preferences Tab */}
      {activeTab === 'technical' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">IT Guidelines</h3>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="architecture_patterns">Architecture Patterns</Label>
                  <Input
                    id="architecture_patterns"
                    value={formData.it_guidelines?.architecture_patterns?.join(', ') || ''}
                    onChange={(e) => onFormChange('it_guidelines', { 
                      ...formData.it_guidelines, 
                      architecture_patterns: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                    })}
                    placeholder="Microservices, Containerization, Serverless"
                  />
                </div>
                <div>
                  <Label htmlFor="security_requirements">Security Requirements</Label>
                  <Textarea
                    id="security_requirements"
                    value={formData.it_guidelines?.security_requirements?.join('\n') || ''}
                    onChange={(e) => onFormChange('it_guidelines', { 
                      ...formData.it_guidelines, 
                      security_requirements: e.target.value.split('\n').filter(Boolean)
                    })}
                    placeholder="Zero Trust Architecture&#10;End-to-end encryption&#10;Multi-factor authentication"
                    rows={3}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium">Decision Criteria</h3>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="risk_tolerance">Risk Tolerance</Label>
                  <Select 
                    value={formData.decision_criteria?.risk_tolerance || 'medium'} 
                    onValueChange={(value) => onFormChange('decision_criteria', { 
                      ...formData.decision_criteria, 
                      risk_tolerance: value 
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low Risk</SelectItem>
                      <SelectItem value="medium">Medium Risk</SelectItem>
                      <SelectItem value="high">High Risk</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="cost_sensitivity">Cost Sensitivity</Label>
                  <Select 
                    value={formData.decision_criteria?.cost_sensitivity || 'medium'} 
                    onValueChange={(value) => onFormChange('decision_criteria', { 
                      ...formData.decision_criteria, 
                      cost_sensitivity: value 
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low Sensitivity</SelectItem>
                      <SelectItem value="medium">Medium Sensitivity</SelectItem>
                      <SelectItem value="high">High Sensitivity</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="timeline_pressure">Timeline Pressure</Label>
                  <Select 
                    value={formData.decision_criteria?.timeline_pressure || 'medium'} 
                    onValueChange={(value) => onFormChange('decision_criteria', { 
                      ...formData.decision_criteria, 
                      timeline_pressure: value 
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Flexible Timeline</SelectItem>
                      <SelectItem value="medium">Moderate Urgency</SelectItem>
                      <SelectItem value="high">Urgent Timeline</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Settings Tab */}
      {activeTab === 'advanced' && (
        <div className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Agent Preferences</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="confidence_threshold">Field Mapping Confidence</Label>
                <Select 
                  value={formData.agent_preferences?.confidence_thresholds?.field_mapping?.toString() || '0.8'} 
                  onValueChange={(value) => onFormChange('agent_preferences', { 
                    ...formData.agent_preferences, 
                    confidence_thresholds: {
                      ...formData.agent_preferences?.confidence_thresholds,
                      field_mapping: parseFloat(value)
                    }
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.7">70% - Permissive</SelectItem>
                    <SelectItem value="0.8">80% - Balanced</SelectItem>
                    <SelectItem value="0.9">90% - Conservative</SelectItem>
                    <SelectItem value="0.95">95% - Very Conservative</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="learning_style">Learning Style</Label>
                <Select 
                  value={formData.agent_preferences?.learning_preferences?.[0] || 'conservative'} 
                  onValueChange={(value) => onFormChange('agent_preferences', { 
                    ...formData.agent_preferences, 
                    learning_preferences: [value]
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conservative">Conservative</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="aggressive">Aggressive</SelectItem>
                    <SelectItem value="accuracy_focused">Accuracy Focused</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium">Budget & Timeline Constraints</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="budget_range">Budget Range</Label>
                  <Input
                    id="budget_range"
                    value={formData.budget_constraints?.range || ''}
                    onChange={(e) => onFormChange('budget_constraints', { 
                      ...formData.budget_constraints, 
                      range: e.target.value 
                    })}
                    placeholder="$100K - $500K"
                  />
                </div>
                <div>
                  <Label htmlFor="timeline_expectation">Timeline Expectation</Label>
                  <Input
                    id="timeline_expectation"
                    value={formData.timeline_constraints?.expectation || ''}
                    onChange={(e) => onFormChange('timeline_constraints', { 
                      ...formData.timeline_constraints, 
                      expectation: e.target.value 
                    })}
                    placeholder="6-12 months"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

const ClientManagementMain: React.FC = () => {
  const { toast } = useToast();

  // State management
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
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
      const url = `/admin/clients/${queryString ? `?${queryString}` : ''}`;

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
    try {
      setActionLoading('create');
      
      // Clean up form data - convert empty strings to null for optional fields
      const cleanedFormData = {
        ...formData,
        primary_contact_phone: formData.primary_contact_phone?.trim() || null,
        billing_contact_email: formData.billing_contact_email?.trim() || null,
        description: formData.description?.trim() || null,
      };
      
      // Make API call to create client
      const response = await apiCall('/admin/clients/', {
        method: 'POST',
        body: JSON.stringify(cleanedFormData)
      });

      if (response.status === 'success') {
        // Add the new client to local state with server response
        const newClient: Client = {
          id: response.data.id,
          ...formData,
          created_at: response.data.created_at,
          updated_at: response.data.updated_at,
          is_active: true,
          total_engagements: 0,
          active_engagements: 0
        };

        setClients(prev => [newClient, ...prev]);
        toast({ 
          title: "Success", 
          description: `Client "${formData.account_name}" created successfully` 
        });
        setShowCreateDialog(false);
        resetForm();
      } else {
        throw new Error(response.message || 'Failed to create client');
      }
    } catch (error: any) {
      console.error('Error creating client:', error);
      
      // Enhanced error handling for validation errors
      let errorMessage = error.message || "Failed to create client. Please try again.";
      if (error.response && error.response.detail) {
        if (Array.isArray(error.response.detail)) {
          // Format validation errors nicely
          const validationErrors = error.response.detail.map((d: any) => {
            if (d.loc && d.msg) {
              const field = d.loc[d.loc.length - 1]; // Get the field name
              return `${field}: ${d.msg}`;
            }
            return d.msg || d.message || JSON.stringify(d);
          });
          errorMessage = validationErrors.join(', ');
        } else {
          errorMessage = error.response.detail;
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateClient = async () => {
    if (!editingClient) return;

    try {
      setActionLoading(editingClient.id);
      
      // Debug logging to see what data is being sent
      console.log('🔍 Updating client with data:', formData);
      console.log('🔍 Client ID:', editingClient.id);
      
      // Clean up form data - convert empty strings to null for optional fields
      const cleanedFormData = {
        ...formData,
        primary_contact_phone: formData.primary_contact_phone?.trim() || null,
        billing_contact_email: formData.billing_contact_email?.trim() || null,
        description: formData.description?.trim() || null,
      };
      
      // Make API call to update client
      const response = await apiCall(`/admin/clients/${editingClient.id}`, {
        method: 'PUT',
        body: JSON.stringify(cleanedFormData)
      });

      if (response.status === 'success') {
        const updatedClient: Client = {
          ...editingClient,
          ...formData,
          updated_at: response.data.updated_at || new Date().toISOString()
        };

        setClients(prev => prev.map(client => 
          client.id === editingClient.id ? updatedClient : client
        ));

        toast({ 
          title: "Success", 
          description: `Client "${formData.account_name}" updated successfully` 
        });
        setEditingClient(null);
        resetForm();
      } else {
        throw new Error(response.message || 'Failed to update client');
      }
    } catch (error: any) {
      console.error('❌ Error updating client:', error);
      console.error('❌ Error details:', {
        message: error.message,
        status: error.status,
        response: error.response,
        requestId: error.requestId
      });
      
      // Show detailed error message if available
      let errorMessage = error.message || "Failed to update client. Please try again.";
      if (error.response && error.response.detail) {
        if (Array.isArray(error.response.detail)) {
          errorMessage = error.response.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = error.response.detail;
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (!confirm(`Delete client "${clientName}"? This action cannot be undone.`)) return;

    try {
      setActionLoading(clientId);
      
      // Make API call to delete client
      const response = await apiCall(`/admin/clients/${clientId}`, {
        method: 'DELETE'
      });

      if (response.status === 'success') {
        setClients(prev => prev.filter(client => client.id !== clientId));
        toast({ 
          title: "Success", 
          description: `Client "${clientName}" deleted successfully` 
        });
      } else {
        throw new Error(response.message || 'Failed to delete client');
      }
    } catch (error: any) {
      console.error('Error deleting client:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to delete client. Please try again.",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
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
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/clients/${client.id}`}>
                              <Eye className="w-4 h-4 mr-2" />View Details
                            </Link>
                          </DropdownMenuItem>
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
            <Button variant="outline" onClick={() => {setShowCreateDialog(false); resetForm();}} disabled={actionLoading === 'create'}>Cancel</Button>
            <Button onClick={handleCreateClient} disabled={actionLoading === 'create'}>
              {actionLoading === 'create' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </>
              ) : (
                'Create Client'
              )}
            </Button>
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
            <Button variant="outline" onClick={() => {setEditingClient(null); resetForm();}} disabled={actionLoading === editingClient?.id}>Cancel</Button>
            <Button onClick={handleUpdateClient} disabled={actionLoading === editingClient?.id}>
              {actionLoading === editingClient?.id ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Updating...
                </>
              ) : (
                'Update Client'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientManagementMain; 