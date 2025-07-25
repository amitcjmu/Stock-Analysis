/**
 * RecentActivity Component for AdminDashboard
 * Displays recent platform administration events
 */

import React from 'react';
import { Clock, UserCheck } from 'lucide-react'
import { Activity } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface ActivityItem {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  message: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning';
}

export interface RecentActivityProps {
  activities?: ActivityItem[];
  className?: string;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({
  activities,
  className = ''
}) => {
  // Default demo activities if none provided
  const defaultActivities: ActivityItem[] = [
    {
      id: '1',
      icon: Clock,
      message: 'New client registration: "TechCorp Solutions" - pending approval',
      timestamp: '2 hours ago',
      type: 'info'
    },
    {
      id: '2',
      icon: Activity,
      message: 'Engagement "Cloud Migration 2025" moved to execution phase',
      timestamp: '5 hours ago',
      type: 'success'
    },
    {
      id: '3',
      icon: UserCheck,
      message: '3 new users approved for platform access',
      timestamp: '1 day ago',
      type: 'success'
    }
  ];

  const activityList = activities || defaultActivities;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest platform administration events</CardDescription>
      </CardHeader>
      <CardContent>
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
      </CardContent>
    </Card>
  );
};
