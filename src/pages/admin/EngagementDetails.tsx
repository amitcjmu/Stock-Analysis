import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Calendar, 
  DollarSign, 
  Users, 
  MapPin, 
  Cloud,
  ArrowLeft,
  Edit,
  Archive,
  CheckCircle,
  XCircle,
  Building2,
  User,
  Clock,
  Target
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
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
  progress_percentage: number;
  total_applications: number;
  migrated_applications: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

const EngagementDetails: React.FC = () => {
  const { engagementId } = useParams<{ engagementId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (engagementId) {
      fetchEngagementDetails(engagementId);
    }
  }, [engagementId]);

  const fetchEngagementDetails = async (id: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/admin/engagements/${id}`, {
        headers: {
          'X-Demo-Mode': 'true',
          'X-User-ID': 'demo-admin-user',
          'Authorization': 'Bearer demo-admin-token'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch engagement details');
      }

      const data = await response.json();
      setEngagement(data);
    } catch (error) {
      console.error('Error fetching engagement details:', error);
      toast({
        title: "Error",
        description: "Failed to fetch engagement details. Using demo data.",
        variant: "destructive"
      });
      
      // Demo data fallback
      setEngagement({
        id: id,
        engagement_name: 'Cloud Migration Initiative 2024',
        client_account_id: 'client-123',
        client_account_name: 'Pujyam Corp',
        migration_scope: 'full_datacenter',
        target_cloud_provider: 'aws',
        migration_phase: 'execution',
        engagement_manager: 'Sarah Johnson',
        technical_lead: 'Mike Chen',
        start_date: '2024-01-15T00:00:00Z',
        end_date: '2024-12-31T00:00:00Z',
        budget: 850000,
        budget_currency: 'USD',
        progress_percentage: 65,
        total_applications: 45,
        migrated_applications: 29,
        created_at: '2024-01-10T10:30:00Z',
        is_active: true
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateDurationMonths = (startDate: string, endDate: string) => {
    if (!startDate || !endDate) return 'Not calculated';
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return 'Invalid dates';
    }
    
    const diffTime = end.getTime() - start.getTime();
    const diffMonths = Math.ceil(diffTime / (1000 * 60 * 60 * 24 * 30));
    
    return diffMonths > 0 ? `${diffMonths} months` : 'Invalid duration';
  };

  const formatCurrency = (amount: number, currency: string) => {
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
      return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    }
  };

  const getPhaseColor = (phase: string) => {
    if (!phase) return 'bg-gray-100 text-gray-800';
    
    switch (phase) {
      case 'planning': return 'bg-yellow-100 text-yellow-800';
      case 'discovery': return 'bg-blue-100 text-blue-800';
      case 'assessment': return 'bg-purple-100 text-purple-800';
      case 'execution': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getProviderLabel = (provider: string) => {
    const providerMap: Record<string, string> = {
      'aws': 'Amazon Web Services (AWS)',
      'azure': 'Microsoft Azure',
      'gcp': 'Google Cloud Platform (GCP)',
      'multi_cloud': 'Multi-Cloud Strategy',
      'hybrid': 'Hybrid Cloud'
    };
    return providerMap[provider] || provider;
  };

  const getScopeLabel = (scope: string) => {
    const scopeMap: Record<string, string> = {
      'single_application': 'Single Application',
      'application_group': 'Application Group',
      'partial_datacenter': 'Partial Datacenter',
      'full_datacenter': 'Full Datacenter Migration',
      'multi_datacenter': 'Multi-Datacenter'
    };
    return scopeMap[scope] || scope;
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

  if (!engagement) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">
          <h2 className="text-2xl font-bold mb-4">Engagement Not Found</h2>
          <p className="text-muted-foreground mb-4">The requested engagement could not be found.</p>
          <Button onClick={() => navigate('/admin/engagements')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Engagements
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
            onClick={() => navigate('/admin/engagements')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Engagements
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Cloud className="w-8 h-8" />
              {engagement.engagement_name}
              {engagement.is_active ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
            </h1>
            <p className="text-muted-foreground flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              {engagement.client_account_name}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Edit className="w-4 h-4 mr-2" />
            Edit Engagement
          </Button>
          <Button variant="outline">
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </Button>
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Migration Progress</CardTitle>
          <CardDescription>Current status of the migration engagement</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-2xl font-bold text-green-600">{engagement.progress_percentage}%</span>
            </div>
            <Progress value={engagement.progress_percentage} className="h-3" />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{engagement.total_applications}</div>
                <div className="text-sm text-muted-foreground">Total Applications</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{engagement.migrated_applications}</div>
                <div className="text-sm text-muted-foreground">Migrated</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{engagement.total_applications - engagement.migrated_applications}</div>
                <div className="text-sm text-muted-foreground">Remaining</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Engagement Details */}
          <Card>
            <CardHeader>
              <CardTitle>Engagement Details</CardTitle>
              <CardDescription>Migration scope and technical specifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Target className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Migration Scope</p>
                    <p className="text-sm text-muted-foreground">{getScopeLabel(engagement.migration_scope)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Cloud className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Target Cloud</p>
                    <p className="text-sm text-muted-foreground">{getProviderLabel(engagement.target_cloud_provider)}</p>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-3">Current Phase</h4>
                <Badge className={getPhaseColor(engagement.migration_phase)}>
                  {engagement.migration_phase ? 
                    engagement.migration_phase.charAt(0).toUpperCase() + engagement.migration_phase.slice(1) :
                    'Unknown'
                  }
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Team Information */}
          <Card>
            <CardHeader>
              <CardTitle>Team</CardTitle>
              <CardDescription>Key personnel assigned to this engagement</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Engagement Manager</p>
                  <p className="text-sm text-muted-foreground">{engagement.engagement_manager}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Technical Lead</p>
                  <p className="text-sm text-muted-foreground">{engagement.technical_lead}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Start Date</p>
                  <p className="font-medium">{formatDate(engagement.start_date)}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">End Date</p>
                  <p className="font-medium">{formatDate(engagement.end_date)}</p>
                </div>
              </div>
              <Separator />
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="font-medium">
                    {calculateDurationMonths(engagement.start_date, engagement.end_date)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Budget */}
          <Card>
            <CardHeader>
              <CardTitle>Budget</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Total Budget</p>
                  <p className="text-2xl font-bold text-green-600">
                    {engagement.budget ? 
                      formatCurrency(engagement.budget, engagement.budget_currency || 'USD') :
                      'No budget set'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full" variant="outline">
                <Users className="w-4 h-4 mr-2" />
                View Team Members
              </Button>
              <Button className="w-full" variant="outline">
                <Target className="w-4 h-4 mr-2" />
                View Applications
              </Button>
              <Button className="w-full" variant="outline">
                <Calendar className="w-4 h-4 mr-2" />
                View Timeline
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default EngagementDetails; 