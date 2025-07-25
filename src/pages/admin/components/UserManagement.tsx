/**
 * UserManagement Component for AdminDashboard
 * Displays user management statistics and actions using shared components
 */

import React from 'react';
import { Settings } from 'lucide-react'
import { Users, UserCheck, Clock } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { ActionItem } from '@/components/admin/shared/components/ActionCard';
import { ActionCard } from '@/components/admin/shared/components/ActionCard';
import type { DashboardStatsData } from './DashboardStats';

export interface UserManagementProps {
  usersData: DashboardStatsData['users'];
  className?: string;
}

export const UserManagement: React.FC<UserManagementProps> = ({
  usersData,
  className = ''
}) => {
  // User management actions
  const userActions: ActionItem[] = [
    {
      label: `Review Pending Approvals (${usersData.pending})`,
      href: "/admin/users/approvals",
      icon: Clock,
      variant: "default",
      disabled: usersData.pending === 0
    },
    {
      label: "Manage All Users",
      href: "/admin/users",
      icon: Users,
      variant: "outline"
    },
    {
      label: "Access Controls",
      href: "/admin/users/access",
      icon: Settings,
      variant: "outline"
    }
  ];

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 ${className}`}>
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
            <span className="text-lg font-bold">{usersData.total}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium">Approved Users</span>
            </div>
            <span className="text-lg font-bold">{usersData.approved}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-500" />
              <span className="text-sm font-medium">Pending Approval</span>
            </div>
            <span className="text-lg font-bold">{usersData.pending}</span>
          </div>
        </CardContent>
      </Card>

      <ActionCard
        title="User Management Actions"
        description="Common user administration tasks"
        actions={userActions}
      />
    </div>
  );
};
