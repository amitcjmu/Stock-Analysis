/**
 * DashboardStats Component for AdminDashboard
 * Displays key metrics overview using shared StatCard components
 */

import React from 'react';
import { 
  Building2, 
  Calendar, 
  Clock, 
  TrendingUp 
} from 'lucide-react';
import { StatCard } from '@/components/admin/shared/components/StatCard';

export interface DashboardStatsData {
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

export interface DashboardStatsProps {
  stats: DashboardStatsData;
  className?: string;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ 
  stats, 
  className = '' 
}) => {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
      <StatCard
        title="Total Clients"
        value={stats.clients.total}
        description={`${stats.clients.active} active organizations`}
        icon={Building2}
      />

      <StatCard
        title="Active Engagements"
        value={stats.engagements.active}
        description={`of ${stats.engagements.total} total engagements`}
        icon={Calendar}
      />

      <StatCard
        title="Pending Approvals"
        value={stats.users.pending}
        description="users awaiting approval"
        icon={Clock}
      />

      <StatCard
        title="Avg Completion"
        value={`${(stats.engagements.completionRate || 0).toFixed(1)}%`}
        description="across all engagements"
        icon={TrendingUp}
      />
    </div>
  );
};