
import type React from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { Calendar, Users, Target, TrendingUp } from 'lucide-react'
import { Brain, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';

const PlanIndex = () => {
  const summaryCards = [
    { title: 'Waves Planned', value: '3', subtitle: 'Migration Waves', icon: Calendar, color: 'bg-blue-500' },
    { title: 'Resource Utilization', value: '75%', subtitle: 'Team Capacity', icon: Users, color: 'bg-green-500' },
    { title: 'Target Designs', value: '2', subtitle: 'Architecture Plans', icon: Target, color: 'bg-purple-500' },
    { title: 'Planning Progress', value: '60%', subtitle: 'Complete', icon: TrendingUp, color: 'bg-orange-500' }
  ];

  const quickActions = [
    { title: 'Migration Timeline', description: 'View detailed project timeline and milestones', path: '/plan/timeline' },
    { title: 'Resource Allocation', description: 'Manage team assignments and capacity', path: '/plan/resource' },
    { title: 'Target Architecture', description: 'Design cloud-native architecture', path: '/plan/target' }
  ];

  const aiInsights = [
    'Migration Goals Assistant recommends light modernization for Wave 1',
    'AI suggests 2-week buffer for critical applications in Wave 2',
    'Resource optimization shows 15% efficiency gain possible'
  ];

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Context Breadcrumbs */}
            <ContextBreadcrumbs showContextSelector={true} />

            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Plan Phase Overview</h1>
                  <p className="text-lg text-gray-600">
                    AI-powered migration planning and resource optimization
                  </p>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>AI Analysis</span>
                </button>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> Enhanced planning powered by CloudBridge AI (September 2025)
                </p>
              </div>
            </div>

            {/* Summary Cards */}
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

            {/* AI Assistant Panel */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Brain className="h-8 w-8 text-blue-500" />
                <h2 className="text-xl font-semibold text-gray-900">AI Assistant Insights</h2>
              </div>
              <div className="space-y-3">
                {aiInsights.map((insight, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-blue-800">{insight}</span>
                  </div>
                ))}
              </div>
            </div>

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

            {/* Planning Summary */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Planning Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">85</p>
                  <p className="text-gray-600">Days Estimated</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">16</p>
                  <p className="text-gray-600">Team Members</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">35</p>
                  <p className="text-gray-600">Applications</p>
                </div>
              </div>
            </div>
          </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default PlanIndex;
