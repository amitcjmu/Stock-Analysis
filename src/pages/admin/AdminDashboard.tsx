import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Users, 
  Building2, 
  UserCheck, 
  User, 
  Calendar,
  TrendingUp,
  Settings,
  Plus,
  BarChart3,
  Activity,
  DollarSign,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { apiCall } from '@/lib/api'; 
import { useAuth } from '@/contexts/AuthContext';

interface DashboardStats {
  clients: {
    total: number;
    active: number;
    byIndustry: Record<string, number>;
    bySize: Record<string, number>;
    recentRegistrations: any[];
  };
  engagements: {
    total: number;
    active: number;
    byPhase: Record<string, number>;
    byScope: Record<string, number>;
    completionRate: number;
    budgetUtilization: number;
    recentActivity: any[];
  };
  users: {
    total: number;
    pending: number;
    approved: number;
    recentRequests: any[];
  };
}

// Fallback demo data if API fails
const demoStats: DashboardStats = {
  clients: {
    total: 12,
    active: 10,
    byIndustry: { "Technology": 4, "Healthcare": 3, "Finance": 3, "Manufacturing": 2 },
    bySize: { "Enterprise": 6, "Large": 4, "Medium": 2 },
    recentRegistrations: []
  },
  engagements: {
    total: 25,
    active: 18,
    byPhase: { "Discovery": 8, "Assessment": 5, "Planning": 3, "Migration": 2 },
    byScope: { "Full Datacenter": 5, "Application Portfolio": 12, "Selected Apps": 8 },
    completionRate: 72.5,
    budgetUtilization: 65.8,
    recentActivity: []
  },
  users: {
    total: 45,
    pending: 8,
    approved: 37,
    recentRequests: []
  }
};

const AdminDashboard: React.FC = () => {
  const { getAuthHeaders } = useAuth();

  const fetchDashboardStats = async (): Promise<DashboardStats> => {
    const headers = getAuthHeaders();
    try {
      const [clientsData, engagementsData, usersData] = await Promise.all([
        apiCall('/admin/clients/dashboard/stats', { headers }),
        apiCall('/admin/engagements/dashboard/stats', { headers }),
        apiCall('/auth/admin/dashboard-stats', { headers })
      ]);
      
      const transformedClients = clientsData.dashboard_stats || clientsData;
      const transformedEngagements = engagementsData.dashboard_stats || engagementsData;
      
      return {
        clients: {
          total: transformedClients.total_clients || 0,
          active: transformedClients.active_clients || 0,
          byIndustry: transformedClients.clients_by_industry || {},
          bySize: transformedClients.clients_by_company_size || {},
          recentRegistrations: transformedClients.recent_client_registrations || []
        },
        engagements: {
          total: transformedEngagements.total_engagements || 0,
          active: transformedEngagements.active_engagements || 0,
          byPhase: transformedEngagements.engagements_by_phase || {},
          byScope: transformedEngagements.engagements_by_scope || {},
          completionRate: transformedEngagements.completion_rate_average || 0,
          budgetUtilization: transformedEngagements.budget_utilization_average || 0,
          recentActivity: transformedEngagements.recent_engagement_activity || []
        },
        users: usersData.dashboard_stats || usersData
      };
    } catch (apiError) {
      console.warn('API endpoints not available, using demo data:', apiError);
      throw apiError; // Rethrow to let useQuery handle the error state
    }
  };

  const { data, isLoading, isError, error } = useQuery<DashboardStats>(
    ['adminDashboardStats'], 
    fetchDashboardStats,
    {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const stats = isError ? demoStats : data;

  if (isLoading && !stats) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="ml-4 text-muted-foreground">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          <p className="text-red-500">Failed to load dashboard data. Please try again later.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            Manage clients, engagements, and user access for AI Force Migration Platform
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link to="/admin/clients/new">
              <Plus className="w-4 h-4 mr-2" />
              New Client
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/admin/users/approvals">
              <Clock className="w-4 h-4 mr-2" />
              User Approvals {stats.users.pending > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {stats.users.pending}
                </Badge>
              )}
            </Link>
          </Button>
        </div>
      </div>

      {isError && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-orange-800">
              <Settings className="w-4 h-4" />
              <span className="text-sm">
                There was an issue fetching live data. Showing demo statistics. Error: {error instanceof Error ? error.message : 'Unknown Error'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Clients</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.clients.total}</div>
            <p className="text-xs text-muted-foreground">
              {stats.clients.active} active organizations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Engagements</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.engagements.active}</div>
            <p className="text-xs text-muted-foreground">
              of {stats.engagements.total} total engagements
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.users.pending}</div>
            <p className="text-xs text-muted-foreground">
              users awaiting approval
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Completion</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(stats.engagements.completionRate || 0).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              across all engagements
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="clients" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="clients">Client Analytics</TabsTrigger>
          <TabsTrigger value="engagements">Engagement Analytics</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
        </TabsList>

        <TabsContent value="clients" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Clients by Industry</CardTitle>
                <CardDescription>Distribution of client accounts by industry sector</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.clients.byIndustry && Object.entries(stats.clients.byIndustry).length > 0 ? (
                  Object.entries(stats.clients.byIndustry).map(([industry, count]) => (
                    <div key={industry} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{industry}</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={(count / Math.max(stats.clients.total, 1)) * 100} 
                          className="w-20 h-2"
                        />
                        <span className="text-sm text-muted-foreground w-8">{count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No industry data available
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Clients by Company Size</CardTitle>
                <CardDescription>Distribution by organizational size</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.clients.bySize && Object.entries(stats.clients.bySize).length > 0 ? (
                  Object.entries(stats.clients.bySize).map(([size, count]) => (
                    <div key={size} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{size}</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={(count / Math.max(stats.clients.total, 1)) * 100} 
                          className="w-20 h-2"
                        />
                        <span className="text-sm text-muted-foreground w-8">{count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No company size data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="engagements" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Engagements by Phase</CardTitle>
                <CardDescription>Current phase distribution across all engagements</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.engagements.byPhase && Object.entries(stats.engagements.byPhase).length > 0 ? (
                  Object.entries(stats.engagements.byPhase).map(([phase, count]) => (
                    <div key={phase} className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">{phase}</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={(count / Math.max(stats.engagements.total, 1)) * 100} 
                          className="w-20 h-2"
                        />
                        <span className="text-sm text-muted-foreground w-8">{count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No engagement phase data available
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Migration Scope Analysis</CardTitle>
                <CardDescription>Types of migration scopes being executed</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.engagements.byScope && Object.entries(stats.engagements.byScope).length > 0 ? (
                  Object.entries(stats.engagements.byScope).map(([scope, count]) => (
                    <div key={scope} className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {scope.replace('_', ' ').split(' ').map(word => 
                          word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ')}
                      </span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={(count / Math.max(stats.engagements.total, 1)) * 100} 
                          className="w-20 h-2"
                        />
                        <span className="text-sm text-muted-foreground w-8">{count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No engagement scope data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Overall engagement performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Average Completion Rate</span>
                  <div className="flex items-center gap-2">
                    <Progress value={stats.engagements.completionRate || 0} className="w-24 h-2" />
                    <span className="text-sm font-bold">{(stats.engagements.completionRate || 0).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Budget Utilization</span>
                  <div className="flex items-center gap-2">
                    <Progress value={stats.engagements.budgetUtilization || 0} className="w-24 h-2" />
                    <span className="text-sm font-bold">{(stats.engagements.budgetUtilization || 0).toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common engagement management tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button asChild className="w-full justify-start">
                  <Link to="/admin/engagements/new">
                    <Plus className="w-4 h-4 mr-2" />
                    Create New Engagement
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link to="/admin/engagements">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    View All Engagements
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link to="/admin/reports">
                    <Activity className="w-4 h-4 mr-2" />
                    Generate Reports
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Statistics</CardTitle>
                <CardDescription>Platform user management overview</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-blue-500" />
                    <span className="text-sm font-medium">Total Users</span>
                  </div>
                  <span className="text-lg font-bold">{stats.users.total}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-medium">Approved Users</span>
                  </div>
                  <span className="text-lg font-bold">{stats.users.approved}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-orange-500" />
                    <span className="text-sm font-medium">Pending Approval</span>
                  </div>
                  <span className="text-lg font-bold">{stats.users.pending}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Management Actions</CardTitle>
                <CardDescription>Common user administration tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button asChild className="w-full justify-start" disabled={stats.users.pending === 0}>
                  <Link to="/admin/users/approvals">
                    <Clock className="w-4 h-4 mr-2" />
                    Review Pending Approvals ({stats.users.pending})
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link to="/admin/users">
                    <Users className="w-4 h-4 mr-2" />
                    Manage All Users
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link to="/admin/users/access">
                    <Settings className="w-4 h-4 mr-2" />
                    Access Controls
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest platform administration events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4 text-sm">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span>New client registration: "TechCorp Solutions" - pending approval</span>
              <Badge variant="secondary">2 hours ago</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <Activity className="w-4 h-4 text-muted-foreground" />
              <span>Engagement "Cloud Migration 2025" moved to execution phase</span>
              <Badge variant="secondary">5 hours ago</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <UserCheck className="w-4 h-4 text-muted-foreground" />
              <span>3 new users approved for platform access</span>
              <Badge variant="secondary">1 day ago</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard; 