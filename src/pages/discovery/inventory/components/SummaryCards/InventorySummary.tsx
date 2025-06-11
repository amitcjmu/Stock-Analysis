import React from 'react';
import { Database, Server, HardDrive, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { InventorySummary as Summary } from '../../types';

interface InventorySummaryProps {
  summary: Summary;
  isLoading?: boolean;
  lastUpdated?: string | null;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  loading?: boolean;
}> = ({ title, value, icon, trend, trendValue, loading = false }) => (
  <Card className="flex-1">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
      <div className="h-4 w-4 text-muted-foreground">
        {loading ? <div className="h-4 w-4 animate-pulse bg-gray-200 rounded" /> : icon}
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">
        {loading ? (
          <div className="h-8 w-3/4 bg-gray-200 animate-pulse rounded" />
        ) : (
          value
        )}
      </div>
      {trend && trendValue && (
        <p className="text-xs text-muted-foreground mt-1 flex items-center">
          {trend === 'up' ? (
            <span className="text-green-500 mr-1">↑ {trendValue}%</span>
          ) : trend === 'down' ? (
            <span className="text-red-500 mr-1">↓ {trendValue}%</span>
          ) : (
            <span className="text-gray-500 mr-1">→ {trendValue}%</span>
          )}
          vs last scan
        </p>
      )}
    </CardContent>
  </Card>
);

export const InventorySummary: React.FC<InventorySummaryProps> = ({
  summary,
  isLoading = false,
  lastUpdated
}) => {
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Assets"
          value={summary.total.toLocaleString()}
          icon={<Database className="h-4 w-4" />}
          trend="up"
          trendValue="12"
          loading={isLoading}
        />
        <StatCard
          title="Servers"
          value={summary.servers.toLocaleString()}
          icon={<Server className="h-4 w-4" />}
          trend="up"
          trendValue="8"
          loading={isLoading}
        />
        <StatCard
          title="Databases"
          value={summary.databases.toLocaleString()}
          icon={<Database className="h-4 w-4" />}
          trend="down"
          trendValue="3"
          loading={isLoading}
        />
        <StatCard
          title="Other Devices"
          value={summary.devices.toLocaleString()}
          icon={<HardDrive className="h-4 w-4" />}
          trend="up"
          trendValue="15"
          loading={isLoading}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Discovered"
          value={summary.discovered.toLocaleString()}
          icon={<CheckCircle className="h-4 w-4 text-green-500" />}
          loading={isLoading}
        />
        <StatCard
          title="Pending Review"
          value={summary.pending.toLocaleString()}
          icon={<AlertCircle className="h-4 w-4 text-yellow-500" />}
          loading={isLoading}
        />
        <StatCard
          title="Network Devices"
          value={summary.device_breakdown?.network?.toLocaleString() || '0'}
          icon={<HardDrive className="h-4 w-4 text-blue-500" />}
          loading={isLoading}
        />
        <StatCard
          title="Storage"
          value={summary.device_breakdown?.storage?.toLocaleString() || '0'}
          icon={<HardDrive className="h-4 w-4 text-purple-500" />}
          loading={isLoading}
        />
      </div>

      {lastUpdated && (
        <div className="text-xs text-gray-500 text-right">
          Last updated: {formatDate(lastUpdated)}
        </div>
      )}
    </div>
  );
};
