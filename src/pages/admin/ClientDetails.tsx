import React, { useState, useEffect } from 'react';
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

const ClientDetails: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (clientId) {
      fetchClientDetails(clientId);
    }
  }, [clientId]);

  const fetchClientDetails = async (id: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/admin/clients/${id}`, {
        headers: {
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch client details');
      }

      const data = await response.json();
      setClient(data);
    } catch (error) {
      console.error('Error fetching client details:', error);
      toast({
        title: "Error",
        description: "Failed to fetch client details. Using demo data.",
        variant: "destructive"
      });
      
      // Demo data fallback
      setClient({
        id: id,
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
      });
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
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
          <Button variant="outline">
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
                  {client.business_objectives && client.business_objectives.length > 0 ? (
                    client.business_objectives.map((objective, index) => (
                      <Badge key={index} variant="secondary">
                        {objective}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No business objectives specified</p>
                  )}
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
    </div>
  );
};

export default ClientDetails; 