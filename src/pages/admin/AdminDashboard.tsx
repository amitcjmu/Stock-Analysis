import React from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Link } from 'react-router-dom';
import type { Plus, Clock } from 'lucide-react'
import { Settings } from 'lucide-react'
import type { Button } from '@/components/ui/button';
import type { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { apiCall } from '@/config/api'; 
import { useAuth } from '@/contexts/AuthContext';
import type { AdminLoadingState, AdminErrorState } from '@/components/admin/shared/components'
import { AdminHeader } from '@/components/admin/shared/components'
import type { formatDate } from '@/components/admin/shared'
import { useAdminToasts } from '@/components/admin/shared'
import type { DashboardStatsData } from './components/DashboardStats'
import { DashboardStats } from './components/DashboardStats'
import { ClientAnalytics } from './components/ClientAnalytics';
import { EngagementAnalytics } from './components/EngagementAnalytics';
import { UserManagement } from './components/UserManagement';
import { RecentActivity } from './components/RecentActivity';

// Interface moved to components/DashboardStats.tsx

// Fallback demo data if API fails
const demoStats: DashboardStatsData = {
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
  const { isAuthenticated, user } = useAuth();
  const { showDemoDataWarningToast } = useAdminToasts();
  
  const fetchDashboardStats = async (): Promise<DashboardStatsData> => {
    try {
      // Get token from localStorage to verify it exists
      const token = localStorage.getItem('auth_token');
      console.log('📊 Admin Dashboard - Token available:', !!token);
      console.log('📊 Admin Dashboard - User:', user);
      console.log('📊 Admin Dashboard - isAuthenticated:', isAuthenticated);
      
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      if (!isAuthenticated) {
        throw new Error('User is not authenticated');
      }
      
      console.log('📊 Admin Dashboard - Making API calls...');
      
      // Test fixed apiCall function - admin calls don't need tenant context
      const [clientsData, engagementsData, usersData] = await Promise.all([
        apiCall('/admin/clients/dashboard/stats', { method: 'GET' }, false),
        apiCall('/admin/engagements/dashboard/stats', { method: 'GET' }, false),
        apiCall('/auth/admin/dashboard-stats', { method: 'GET' }, false)
      ]);
      
      console.log('📊 Admin Dashboard - Raw API responses:', {
        clientsData,
        engagementsData, 
        usersData
      });
      
      // The API responses don't wrap data in dashboard_stats, use the data directly
      const transformedClients = clientsData;
      const transformedEngagements = engagementsData;
      const transformedUsers = usersData;
      
      const result = {
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
          byPhase: transformedEngagements.engagements_by_type || {}, // Use engagements_by_type as phase
          byScope: transformedEngagements.engagements_by_status || {}, // Use status as scope
          completionRate: transformedEngagements.completion_rate_average || 0,
          budgetUtilization: transformedEngagements.budget_utilization_average || 0,
          recentActivity: transformedEngagements.recent_engagements || []
        },
        users: {
          total: transformedUsers.total_users || 0,
          pending: transformedUsers.pending_users || 0, // This field doesn't exist in the API response
          approved: transformedUsers.active_users || 0,
          recentRequests: transformedUsers.recent_requests || []
        }
      };
      
      console.log('📊 Admin Dashboard - Transformed result:', result);
      return result;
    } catch (apiError) {
      console.warn('API endpoints not available, using demo data:', apiError);
      showDemoDataWarningToast(apiError instanceof Error ? apiError.message : 'Unknown error');
      return demoStats;
    }
  };

  const { data, isLoading, isError, error, refetch } = useQuery<DashboardStatsData>({
    queryKey: ['adminDashboardStats'], 
    queryFn: fetchDashboardStats,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: isAuthenticated && !!user, // Only run query when authenticated
  });

  // Debug the query state
  console.log('📊 Admin Dashboard Query State:', {
    isLoading,
    isError,
    hasData: !!data,
    error: error?.message,
    isAuthenticated,
    hasUser: !!user
  });

  const stats = data || demoStats;

  if (isLoading && !stats) {
    return <AdminLoadingState message="Loading Dashboard..." />;
  }

  if (!stats) {
    return (
      <AdminErrorState 
        message="Failed to load dashboard data. Please try again later."
        onRetry={() => refetch()}
      />
    );
  }
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <AdminHeader
        title="Admin Dashboard"
        description="Manage clients, engagements, and user access for AI Modernize Migration Platform"
        onRefresh={() => refetch()}
        refreshLoading={isLoading}
        actions={[
          {
            label: "New Client",
            href: "/admin/clients/new",
            icon: Plus,
            variant: "default"
          },
          {
            label: "User Approvals",
            href: "/admin/users/approvals",
            icon: Clock,
            variant: "outline",
            badge: stats.users.pending > 0 ? {
              text: stats.users.pending,
              variant: "destructive"
            } : undefined
          }
        ]}
      />

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
      <DashboardStats stats={stats} />

      {/* Detailed Analytics */}
      <Tabs defaultValue="clients" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="clients">Client Analytics</TabsTrigger>
          <TabsTrigger value="engagements">Engagement Analytics</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
        </TabsList>

        <TabsContent value="clients" className="space-y-4">
          <ClientAnalytics clientsData={stats.clients} />
        </TabsContent>

        <TabsContent value="engagements" className="space-y-4">
          <EngagementAnalytics engagementsData={stats.engagements} />
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <UserManagement usersData={stats.users} />
        </TabsContent>
      </Tabs>

      {/* Recent Activity */}
      <RecentActivity />
    </div>
  );
};

export default AdminDashboard; 