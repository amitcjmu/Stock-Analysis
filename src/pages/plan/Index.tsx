
import type React from 'react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import PlanNavigation from '@/components/plan/PlanNavigation';
import { Calendar, Users, Target, TrendingUp, Loader2, AlertCircle } from 'lucide-react';
import { Brain, ArrowRight, Rocket } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { PlanningInitializationWizard } from '@/components/plan/PlanningInitializationWizard';
import { apiCall } from '@/config/api';

// Types for plan overview data (snake_case per CLAUDE.md)
interface PlanOverviewSummary {
  totalApps: number;
  plannedApps: number;
  totalWaves: number;
  completedPhases: number;
  upcomingMilestones: number;
}

interface PlanOverviewData {
  summary: PlanOverviewSummary;
  nextMilestone?: {
    name: string;
    date: string;
    description: string;
  };
  recentActivity?: Array<{
    date: string;
    activity: string;
    description: string;
  }>;
}

const PlanIndex = (): JSX.Element => {
  // State for planning initialization wizard
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  // Get engagement_id from context (default to 1 for now)
  // TODO: Replace with actual engagement context when available
  const engagement_id = 1;

  // Fetch plan overview data from backend
  const {
    data: overviewData,
    isLoading: isLoadingOverview,
    error: overviewError
  } = useQuery<PlanOverviewData>({
    queryKey: ['plan-overview'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/plan/');
      return response;
    },
    staleTime: 30000, // Cache for 30 seconds
    refetchOnWindowFocus: false
  });

  // Derive summary cards from API data
  const summaryCards = overviewData ? [
    {
      title: 'Waves Planned',
      value: String(overviewData.summary.totalWaves),
      subtitle: 'Migration Waves',
      icon: Calendar,
      color: 'bg-blue-500'
    },
    {
      title: 'Applications',
      value: `${overviewData.summary.plannedApps}/${overviewData.summary.totalApps}`,
      subtitle: 'Planned / Total',
      icon: Users,
      color: 'bg-green-500'
    },
    {
      title: 'Completed Phases',
      value: String(overviewData.summary.completedPhases),
      subtitle: 'Planning Phases',
      icon: Target,
      color: 'bg-purple-500'
    },
    {
      title: 'Upcoming Milestones',
      value: String(overviewData.summary.upcomingMilestones),
      subtitle: 'Next 30 Days',
      icon: TrendingUp,
      color: 'bg-orange-500'
    }
  ] : [];

  const quickActions = [
    { title: 'Wave Planning', description: 'Organize applications into migration waves', path: '/plan/waveplanning' },
    { title: 'Migration Timeline', description: 'View detailed project timeline and milestones', path: '/plan/timeline' },
    { title: 'Resource Allocation', description: 'Manage team assignments and capacity', path: '/plan/resource' }
  ];

  // Use real activity data from API or show placeholder
  const recentActivity = overviewData?.recentActivity || [];
  const nextMilestone = overviewData?.nextMilestone;

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Context Breadcrumbs */}
            <ContextBreadcrumbs showContextSelector={true} />

            {/* Plan Navigation Tabs */}
            <PlanNavigation />

            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Plan Phase Overview</h1>
                  <p className="text-lg text-gray-600">
                    AI-powered migration planning and resource optimization
                  </p>
                </div>
                <button
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  onClick={() => setIsWizardOpen(true)}
                >
                  <Rocket className="h-5 w-5" />
                  <span>Start Planning</span>
                </button>
              </div>
            </div>

            {/* Loading State */}
            {isLoadingOverview && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600 mr-3" />
                <p className="text-gray-600">Loading plan overview...</p>
              </div>
            )}

            {/* Error State */}
            {overviewError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-6 w-6 text-red-600 mt-0.5" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-800 mb-1">Error Loading Overview</h3>
                    <p className="text-red-700">
                      {overviewError instanceof Error ? overviewError.message : 'Failed to load plan overview'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Summary Cards */}
            {!isLoadingOverview && !overviewError && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  {summaryCards.map((card) => {
                    const Icon = card.icon;
                    return (
                      <div key={card.title} className="bg-white rounded-lg shadow-md p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className={`${card.color} p-3 rounded-lg text-white`}>
                            <Icon className="h-6 w-6" />
                          </div>
                        </div>
                        <h3 className="text-2xl font-bold text-gray-900 mb-1">{card.value}</h3>
                        <p className="text-sm text-gray-600">{card.title}</p>
                        <p className="text-xs text-gray-500">{card.subtitle}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Next Milestone */}
                {nextMilestone && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <div className="flex items-center space-x-3 mb-4">
                      <Calendar className="h-8 w-8 text-blue-500" />
                      <h2 className="text-xl font-semibold text-gray-900">Next Milestone</h2>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h3 className="font-semibold text-blue-900 mb-1">{nextMilestone.name}</h3>
                      <p className="text-sm text-blue-700 mb-2">
                        Target Date: {new Date(nextMilestone.date).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-blue-800">{nextMilestone.description}</p>
                    </div>
                  </div>
                )}

                {/* Recent Activity */}
                {recentActivity.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
                    <div className="space-y-3">
                      {recentActivity.map((activity, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900">{activity.activity}</span>
                              <span className="text-xs text-gray-500">
                                {new Date(activity.date).toLocaleDateString()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">{activity.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Planning Areas</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {quickActions.map((action) => (
                  <Link
                    key={action.title}
                    to={action.path}
                    className="group block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
                          {action.title}
                        </h3>
                        <p className="text-sm text-gray-600">{action.description}</p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Coming Soon Notice */}
            {!isLoadingOverview && !overviewError && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Note:</strong> Additional AI-powered insights and recommendations coming soon
                </p>
              </div>
            )}
          </div>
          </main>
        </div>
      </div>

      {/* Planning Initialization Wizard */}
      <PlanningInitializationWizard
        open={isWizardOpen}
        onOpenChange={setIsWizardOpen}
        engagement_id={engagement_id}
      />
    </SidebarProvider>
  );
};

export default PlanIndex;
