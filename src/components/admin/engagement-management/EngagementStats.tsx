import React from 'react';
import { Users, AlertTriangle } from 'lucide-react';
import { Building2, DollarSign, CheckCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Engagement } from './types';

interface EngagementStatsProps {
  engagements: Engagement[];
}

export const EngagementStats: React.FC<EngagementStatsProps> = ({ engagements }) => {
  // Calculate statistics from engagements
  const totalEngagements = engagements?.length || 0;
  const activeEngagements = engagements?.filter((e) => e.is_active !== false).length || 0; // Default to active if not specified
  const completedEngagements = engagements?.filter((e) => e.migration_phase === 'completed' || e.status === 'completed').length || 0;
  const totalBudget = engagements?.reduce((sum, e) => sum + (e.estimated_budget || e.budget || 0), 0) || 0;
  const avgProgress =
    engagements?.length > 0
      ? engagements.reduce((sum, e) => sum + (e.completion_percentage || 0), 0) / engagements.length
      : 0;

  // Phase distribution
  const phaseDistribution = engagements?.reduce(
    (acc, engagement) => {
      const phase = engagement.migration_phase || engagement.current_phase || engagement.status || 'unknown';
      acc[phase] = (acc[phase] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  ) || {};

  // Cloud provider distribution
  const cloudProviderDistribution = engagements?.reduce(
    (acc, engagement) => {
      const provider = engagement.target_cloud_provider || 'unknown';
      acc[provider] = (acc[provider] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  ) || {};

  const formatCurrency = (amount: number): unknown => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getPhaseLabel = (phase: string): JSX.Element => {
    const labels: Record<string, string> = {
      planning: 'Planning',
      discovery: 'Discovery',
      assessment: 'Assessment',
      migration: 'Migration',
      optimization: 'Optimization',
      completed: 'Completed',
    };
    return labels[phase] || phase;
  };

  const getProviderLabel = (provider: string): JSX.Element => {
    const labels: Record<string, string> = {
      aws: 'AWS',
      azure: 'Azure',
      gcp: 'GCP',
      multi_cloud: 'Multi-Cloud',
      hybrid: 'Hybrid',
      private_cloud: 'Private Cloud',
    };
    return labels[provider] || provider.toUpperCase();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total Engagements */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Engagements</CardTitle>
          <Building2 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalEngagements}</div>
          <p className="text-xs text-muted-foreground">{activeEngagements} active</p>
        </CardContent>
      </Card>

      {/* Completed Engagements */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Completed</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{completedEngagements}</div>
          <p className="text-xs text-muted-foreground">
            {totalEngagements > 0
              ? ((completedEngagements / totalEngagements) * 100).toFixed(1)
              : 0}
            % completion rate
          </p>
        </CardContent>
      </Card>

      {/* Total Budget */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Budget</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(totalBudget)}</div>
          <p className="text-xs text-muted-foreground">Across all engagements</p>
        </CardContent>
      </Card>

      {/* Average Progress */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Progress</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{avgProgress.toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground">Overall completion</p>
        </CardContent>
      </Card>

      {/* Phase Distribution */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Migration Phases</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(phaseDistribution).map(([phase, count]) => (
              <div key={phase} className="flex items-center justify-between">
                <span className="text-sm">{getPhaseLabel(phase)}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(count / totalEngagements) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cloud Provider Distribution */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Cloud Providers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(cloudProviderDistribution).map(([provider, count]) => (
              <div key={provider} className="flex items-center justify-between">
                <span className="text-sm">{getProviderLabel(provider)}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${(count / totalEngagements) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
