/**
 * PlatformStats Component for Platform Admin Dashboard
 * Displays platform administration statistics using shared StatCard components
 */

import React from 'react';
import { 
  Clock, 
  AlertTriangle, 
  Calendar 
} from 'lucide-react';
import { StatCard } from '@/components/admin/shared/components/StatCard';

export interface SoftDeletedItem {
  id: string;
  item_type: string;
  item_id: string;
  item_name: string;
  client_account_name?: string;
  engagement_name?: string;
  deleted_by_name: string;
  deleted_by_email: string;
  deleted_at: string;
  delete_reason?: string;
  status: string;
}

export interface PlatformStatsProps {
  pendingItems: SoftDeletedItem[];
  className?: string;
}

export const PlatformStats: React.FC<PlatformStatsProps> = ({ 
  pendingItems, 
  className = '' 
}) => {
  const highPriorityItems = pendingItems.filter(item => item.item_type === 'client_account').length;
  
  const recentItems = pendingItems.filter(item => {
    const deletedDate = new Date(item.deleted_at);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return deletedDate > yesterday;
  }).length;

  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 ${className}`}>
      <StatCard
        title="Pending Reviews"
        value={pendingItems.length}
        description="awaiting your approval"
        icon={Clock}
      />
      
      <StatCard
        title="High Priority"
        value={highPriorityItems}
        description="client account deletions"
        icon={AlertTriangle}
      />
      
      <StatCard
        title="Recent Activity"
        value={recentItems}
        description="deleted in last 24h"
        icon={Calendar}
      />
    </div>
  );
};