/**
 * ClientAnalytics Component for AdminDashboard
 * Displays client distribution analytics using shared ProgressCard components
 */

import React from 'react';
import type { ProgressItemData } from '@/components/admin/shared/components/ProgressCard'
import { ProgressCard } from '@/components/admin/shared/components/ProgressCard'
import type { DashboardStatsData } from './DashboardStats';

export interface ClientAnalyticsProps {
  clientsData: DashboardStatsData['clients'];
  className?: string;
}

export const ClientAnalytics: React.FC<ClientAnalyticsProps> = ({
  clientsData,
  className = ''
}) => {
  // Transform industry data for ProgressCard
  const industryItems: ProgressItemData[] = clientsData.byIndustry && Object.keys(clientsData.byIndustry).length > 0
    ? Object.entries(clientsData.byIndustry).map(([industry, count]) => ({
        label: industry,
        value: count,
        total: clientsData.total
      }))
    : [];

  // Transform company size data for ProgressCard
  const sizeItems: ProgressItemData[] = clientsData.bySize && Object.keys(clientsData.bySize).length > 0
    ? Object.entries(clientsData.bySize).map(([size, count]) => ({
        label: size,
        value: count,
        total: clientsData.total
      }))
    : [];

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 ${className}`}>
      <ProgressCard
        title="Clients by Industry"
        description="Distribution of client accounts by industry sector"
        items={industryItems}
        totalItems={clientsData.total}
      />

      <ProgressCard
        title="Clients by Company Size"
        description="Distribution by organizational size"
        items={sizeItems}
        totalItems={clientsData.total}
      />
    </div>
  );
};
