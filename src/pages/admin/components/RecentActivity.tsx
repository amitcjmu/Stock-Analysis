/**
 * RecentActivity Component for AdminDashboard
 * Displays recent platform administration events from audit log
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, UserCheck, UserX, Shield, AlertCircle, CheckCircle } from 'lucide-react';
import { Activity } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiCall } from '@/config/api';
import { AdminLoadingState } from '@/components/admin/shared';

export interface ActivityItem {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  message: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning';
}

export interface RecentActivityProps {
  className?: string;
}

interface ApiActivityItem {
  id: string;
  user_name: string;
  action_type: string;
  resource_type: string;
  resource_id: string;
  result: string;
  reason: string;
  created_at: string;
}

// Helper function to format timestamp to relative time
const formatRelativeTime = (isoString: string): string => {
  const now = new Date();
  const past = new Date(isoString);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return past.toLocaleDateString();
};

// Helper function to get icon based on action type
const getIconForAction = (actionType: string): React.ComponentType<{ className?: string }> => {
  const actionLower = actionType.toLowerCase();
  if (actionLower.includes('approve') || actionLower.includes('grant')) return UserCheck;
  if (actionLower.includes('reject') || actionLower.includes('revoke')) return UserX;
  if (actionLower.includes('access') || actionLower.includes('permission')) return Shield;
  return Activity;
};

// Helper function to get activity type based on result
const getActivityType = (result: string): 'info' | 'success' | 'warning' => {
  const resultLower = result.toLowerCase();
  if (resultLower === 'success') return 'success';
  if (resultLower === 'denied' || resultLower === 'error') return 'warning';
  return 'info';
};

// Helper function to format action into readable message
const formatActivityMessage = (activity: ApiActivityItem): string => {
  const { user_name, action_type, resource_type, result } = activity;

  // Format action type: "approve_user" -> "approved user"
  const action = action_type.replace(/_/g, ' ').toLowerCase();
  const resource = resource_type ? resource_type.replace(/_/g, ' ').toLowerCase() : 'resource';

  return `${user_name} ${action} ${resource} - ${result}`;
};

export const RecentActivity: React.FC<RecentActivityProps> = ({
  className = ''
}) => {
  // Fetch recent activities from API
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'recent-activities'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/admin/user-access/recent-activities?limit=6', {}, false);
      return response;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest platform administration events</CardDescription>
        </CardHeader>
        <CardContent>
          <AdminLoadingState message="Loading activities..." />
        </CardContent>
      </Card>
    );
  }

  if (isError || !data || data.status !== 'success') {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest platform administration events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AlertCircle className="w-4 h-4" />
            <span>Unable to load recent activities</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const activities: ApiActivityItem[] = data.activities || [];

  // Transform API activities to display format
  const activityList: ActivityItem[] = activities.map((activity) => ({
    id: activity.id,
    icon: getIconForAction(activity.action_type),
    message: formatActivityMessage(activity),
    timestamp: formatRelativeTime(activity.created_at),
    type: getActivityType(activity.result),
  }));

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest platform administration events</CardDescription>
      </CardHeader>
      <CardContent>
        {activityList.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity className="w-4 h-4" />
            <span>No recent activities to display</span>
          </div>
        ) : (
          <div className="space-y-4">
            {activityList.map((activity) => {
              const IconComponent = activity.icon;
              return (
                <div key={activity.id} className="flex items-center gap-4 text-sm">
                  <IconComponent className="w-4 h-4 text-muted-foreground" />
                  <span className="flex-1">{activity.message}</span>
                  <Badge variant="secondary">{activity.timestamp}</Badge>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
