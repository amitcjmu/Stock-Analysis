/**
 * EngagementAnalytics Component for AdminDashboard
 * Displays engagement analytics using shared components
 */

import React from 'react';
import { 
  Plus, 
  BarChart3, 
  Activity 
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ProgressCard, ProgressItemData } from '@/components/admin/shared/components/ProgressCard';
import { ActionCard, ActionItem } from '@/components/admin/shared/components/ActionCard';
import { DashboardStatsData } from './DashboardStats';
import { getPhaseLabel } from '@/components/admin/shared/utils/adminFormatters';

export interface EngagementAnalyticsProps {
  engagementsData: DashboardStatsData['engagements'];
  className?: string;
}

export const EngagementAnalytics: React.FC<EngagementAnalyticsProps> = ({ 
  engagementsData, 
  className = '' 
}) => {
  // Transform phase data for ProgressCard
  const phaseItems: ProgressItemData[] = engagementsData.byPhase && Object.keys(engagementsData.byPhase).length > 0
    ? Object.entries(engagementsData.byPhase).map(([phase, count]) => ({
        label: getPhaseLabel(phase),
        value: count,
        total: engagementsData.total
      }))
    : [];

  // Transform scope data for ProgressCard
  const scopeItems: ProgressItemData[] = engagementsData.byScope && Object.keys(engagementsData.byScope).length > 0
    ? Object.entries(engagementsData.byScope).map(([scope, count]) => ({
        label: scope.replace('_', ' ').split(' ').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' '),
        value: count,
        total: engagementsData.total
      }))
    : [];

  // Quick actions for engagement management
  const engagementActions: ActionItem[] = [
    {
      label: "Create New Engagement",
      href: "/admin/engagements/new",
      icon: Plus,
      variant: "default"
    },
    {
      label: "View All Engagements", 
      href: "/admin/engagements",
      icon: BarChart3,
      variant: "outline"
    },
    {
      label: "Generate Reports",
      href: "/admin/reports",
      icon: Activity,
      variant: "outline"
    }
  ];

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Phase and Scope Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProgressCard
          title="Engagements by Phase"
          description="Current phase distribution across all engagements"
          items={phaseItems}
          totalItems={engagementsData.total}
        />

        <ProgressCard
          title="Migration Scope Analysis"
          description="Types of migration scopes being executed"
          items={scopeItems}
          totalItems={engagementsData.total}
        />
      </div>

      {/* Performance Metrics and Quick Actions */}
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
                <Progress value={engagementsData.completionRate || 0} className="w-24 h-2" />
                <span className="text-sm font-bold">{(engagementsData.completionRate || 0).toFixed(1)}%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Budget Utilization</span>
              <div className="flex items-center gap-2">
                <Progress value={engagementsData.budgetUtilization || 0} className="w-24 h-2" />
                <span className="text-sm font-bold">{(engagementsData.budgetUtilization || 0).toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <ActionCard
          title="Quick Actions"
          description="Common engagement management tasks"
          actions={engagementActions}
        />
      </div>
    </div>
  );
};