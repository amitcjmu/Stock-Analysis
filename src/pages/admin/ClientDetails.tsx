import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar,
  Users,
  ArrowLeft,
  Edit,
  Archive,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { apiCallWithFallback } from '@/lib/api';

interface Client {
  id: string;
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone?: string;
  description?: string;
  subscription_tier?: string;
  billing_contact_email?: string;
  settings?: Record<string, any>;
  branding?: Record<string, any>;
  slug?: string;
  created_by?: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
  it_guidelines?: Record<string, any>;
  decision_criteria?: Record<string, any>;
  agent_preferences?: Record<string, any>;
  budget_constraints?: Record<string, any>;
  timeline_constraints?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  total_engagements: number;
  active_engagements: number;
}

const ClientDetails: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getAuthHeaders } = useAuth();

  const demoClient: Client = {
    id: clientId || 'demo-id',
    account_name: 'Pujyam Corp',
    industry: 'Technology',
    company_size: 'Enterprise (5000+)',
    headquarters_location: 'San Francisco, CA',
    primary_contact_name: 'John Smith',
    primary_contact_email: 'john.smith@pujyam.com',
    primary_contact_phone: '+1-555-0123',
    business_objectives: ['Cost Reduction', 'Modernization', 'Cloud Migration'],
    target_cloud_providers: ['aws', 'azure'],
    business_priorities: ['cost_reduction', 'agility_speed', 'security_compliance'],
    compliance_requirements: ['SOC2', 'GDPR', 'HIPAA'],
    created_at: '2024-01-15T10:30:00Z',
    is_active: true,
    total_engagements: 3,
    active_engagements: 2
  };

  const { data, isLoading, isError } = useQuery<Client>({
    queryKey: ['client', clientId],
    queryFn: async () => {
      const response = await apiCallWithFallback(`/admin/clients/${clientId}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch client details');
      }

      return response.json();
    },
    onError: (error) => {
      console.error('Error fetching client details:', error);
      toast({
        title: "Error",
        description: "Failed to fetch client details. Using demo data.",
        variant: "destructive"
      });
    }
  });

  const client: Client = !isLoading && (isError || !data) ? demoClient : (data as Client);

  const [showEditDialog, setShowEditDialog] = useState(false);
  const [formData, setFormData] = useState({
    account_name: '',
    industry: '',
    company_size: '',
    headquarters_location: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    description: '',
    subscription_tier: '',
    billing_contact_email: '',
    business_objectives: [] as string[],
    target_cloud_providers: [] as string[],
    business_priorities: [] as string[],
    compliance_requirements: [] as string[]
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getProviderLabel = (provider: string) => {
    const providerMap: Record<string, string> = {
      'aws': 'Amazon Web Services (AWS)',
      'azure': 'Microsoft Azure',
      'gcp': 'Google Cloud Platform (GCP)',
      'multi_cloud': 'Multi-Cloud Strategy',
      'hybrid': 'Hybrid Cloud',
      'private_cloud': 'Private Cloud'
    };
    return providerMap[provider] || provider;
  };

  const getPriorityLabel = (priority: string) => {
    const priorityMap: Record<string, string> = {
      'cost_reduction': 'Cost Reduction',
      'agility_speed': 'Agility & Speed',
      'security_compliance': 'Security & Compliance',
      'innovation': 'Innovation',
      'scalability': 'Scalability',
      'reliability': 'Reliability'
    };
    return priorityMap[priority] || priority;
  };

  const handleEdit = () => {
    if (client) {
      setFormData({
        account_name: client.account_name,
        industry: client.industry,
        company_size: client.company_size,
        headquarters_location: client.headquarters_location || '',
        primary_contact_name: client.primary_contact_name || '',
        primary_contact_email: client.primary_contact_email || '',
        primary_contact_phone: client.primary_contact_phone || '',
        description: client.description || '',
        subscription_tier: client.subscription_tier || '',
        billing_contact_email: client.billing_contact_email || '',
        business_objectives: client.business_objectives || [],
        target_cloud_providers: client.target_cloud_providers || [],
        business_priorities: client.business_priorities || [],
        compliance_requirements: client.compliance_requirements || []
      });
      setShowEditDialog(true);
    }
  };

  const handleUpdate = async () => {
    try {
      const response = await apiCallWithFallback(`/admin/clients/${clientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(formData)
      });

      if (response.status !== 'success') {
        throw new Error(response.message || 'Failed to update client');
      }

      toast({
        title: "Success",
        description: `Client "${formData.account_name}" updated successfully`,
      });

      setShowEditDialog(false);
      if (clientId) {
        // Assuming fetchClientDetails is called elsewhere in the component
        // fetchClientDetails(clientId);
      }
    } catch (error) {
      console.error('Error updating client:', error);
      toast({
        title: "Error",
        description: "Failed to update client. Please try again.",
        variant: "destructive"
      });
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">
          <h2 className="text-2xl font-bold mb-4">Client Not Found</h2>
          <p className="text-muted-foreground mb-4">The requested client could not be found.</p>
          <Button onClick={() => navigate('/admin/clients')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Clients
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            onClick={() => navigate('/admin/clients')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Clients
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Building2 className="w-8 h-8" />
              {client.account_name}
              {client.is_active ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
            </h1>
            <p className="text-muted-foreground">
              {client.industry} • {client.company_size}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleEdit}>
            <Edit className="w-4 h-4 mr-2" />
            Edit Client
          </Button>
          <Button variant="outline">
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
              <CardDescription>Primary contact details for this client</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">{client.primary_contact_name}</p>
                  <p className="text-sm text-muted-foreground">{client.primary_contact_email}</p>
                </div>
              </div>
              {client.primary_contact_phone && (
                <div className="flex items-center gap-3">
                  <Phone className="w-5 h-5 text-muted-foreground" />
                  <p className="text-sm">{client.primary_contact_phone}</p>
                </div>
              )}
              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-muted-foreground" />
                <p className="text-sm">{client.headquarters_location}</p>
              </div>
              {client.billing_contact_email && (
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Billing Contact</p>
                    <p className="text-sm">{client.billing_contact_email}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Business Context */}
          <Card>
            <CardHeader>
              <CardTitle>Business Context</CardTitle>
              <CardDescription>Strategic objectives and migration priorities</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-3">Business Objectives</h4>
                <div className="flex flex-wrap gap-2">
                  {(() => {
                    // Handle different data structures from API
                    let objectives = [];
                    if (Array.isArray(client.business_objectives)) {
                      objectives = client.business_objectives;
                    } else if (client.business_objectives && typeof client.business_objectives === 'object' && client.business_objectives.primary_goals) {
                      objectives = client.business_objectives.primary_goals;
                    }
                    
                    return objectives && objectives.length > 0 ? (
                      objectives.map((objective, index) => (
                        <Badge key={index} variant="secondary">
                          {objective}
                        </Badge>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No business objectives specified</p>
                    );
                  })()}
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-3">Target Cloud Providers</h4>
                <div className="flex flex-wrap gap-2">
                  {client.target_cloud_providers && client.target_cloud_providers.length > 0 ? (
                    client.target_cloud_providers.map((provider, index) => (
                      <Badge key={index} variant="outline">
                        {getProviderLabel(provider)}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No cloud providers specified</p>
                  )}
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-3">Business Priorities</h4>
                <div className="flex flex-wrap gap-2">
                  {client.business_priorities && client.business_priorities.length > 0 ? (
                    client.business_priorities.map((priority, index) => (
                      <Badge key={index} className="bg-blue-100 text-blue-800">
                        {getPriorityLabel(priority)}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No business priorities specified</p>
                  )}
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-3">Compliance Requirements</h4>
                <div className="flex flex-wrap gap-2">
                  {client.compliance_requirements && client.compliance_requirements.length > 0 ? (
                    client.compliance_requirements.map((requirement, index) => (
                      <Badge key={index} className="bg-purple-100 text-purple-800">
                        {requirement}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No compliance requirements specified</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Account Information */}
          {(client.description || client.subscription_tier) && (
            <Card>
              <CardHeader>
                <CardTitle>Account Information</CardTitle>
                <CardDescription>Additional client account details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {client.description && (
                  <div>
                    <h4 className="font-medium mb-2">Description</h4>
                    <p className="text-sm text-muted-foreground">{client.description}</p>
                  </div>
                )}
                {client.subscription_tier && (
                  <div>
                    <h4 className="font-medium mb-2">Subscription Tier</h4>
                    <Badge variant="outline" className="capitalize">
                      {client.subscription_tier}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Engagement Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Engagements</span>
                <span className="font-medium">{client.total_engagements}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Active Engagements</span>
                <span className="font-medium text-green-600">{client.active_engagements}</span>
              </div>
              <Separator />
              <Button className="w-full">
                <Users className="w-4 h-4 mr-2" />
                View Engagements
              </Button>
            </CardContent>
          </Card>

          {/* Account Details */}
          <Card>
            <CardHeader>
              <CardTitle>Account Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p className="text-sm font-medium">{formatDate(client.created_at)}</p>
              </div>
              {client.updated_at && (
                <div>
                  <p className="text-sm text-muted-foreground">Last Updated</p>
                  <p className="text-sm font-medium">{formatDate(client.updated_at)}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant={client.is_active ? "default" : "secondary"}>
                  {client.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Client: {client?.account_name}</DialogTitle>
            <DialogDescription>
              Update client account information and business context.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="account_name">Account Name *</Label>
                <Input
                  id="account_name"
                  value={formData.account_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, account_name: e.target.value }))}
                  placeholder="Enter company name"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="industry">Industry *</Label>
                <Select value={formData.industry} onValueChange={(value) => setFormData(prev => ({ ...prev, industry: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    {['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 'Education', 'Government', 'Energy', 'Transportation', 'Other'].map(industry => (
                      <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_size">Company Size *</Label>
                <Select value={formData.company_size} onValueChange={(value) => setFormData(prev => ({ ...prev, company_size: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select company size" />
                  </SelectTrigger>
                  <SelectContent>
                    {['Small (1-100)', 'Medium (101-1000)', 'Large (1001-5000)', 'Enterprise (5000+)'].map(size => (
                      <SelectItem key={size} value={size}>{size}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="headquarters_location">Headquarters Location</Label>
                <Input
                  id="headquarters_location"
                  value={formData.headquarters_location}
                  onChange={(e) => setFormData(prev => ({ ...prev, headquarters_location: e.target.value }))}
                  placeholder="City, State/Country"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primary_contact_name">Primary Contact Name</Label>
                <Input
                  id="primary_contact_name"
                  value={formData.primary_contact_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_name: e.target.value }))}
                  placeholder="Full name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primary_contact_email">Primary Contact Email</Label>
                <Input
                  id="primary_contact_email"
                  type="email"
                  value={formData.primary_contact_email}
                  onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_email: e.target.value }))}
                  placeholder="email@company.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
                <Input
                  id="primary_contact_phone"
                  value={formData.primary_contact_phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_phone: e.target.value }))}
                  placeholder="+1-555-0123"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="billing_contact_email">Billing Contact Email</Label>
                <Input
                  id="billing_contact_email"
                  type="email"
                  value={formData.billing_contact_email}
                  onChange={(e) => setFormData(prev => ({ ...prev, billing_contact_email: e.target.value }))}
                  placeholder="billing@company.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="subscription_tier">Subscription Tier</Label>
                <Select value={formData.subscription_tier} onValueChange={(value) => setFormData(prev => ({ ...prev, subscription_tier: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select subscription tier" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="pro">Pro</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of the client and their business"
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleUpdate}>
                Update Client
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientDetails; 