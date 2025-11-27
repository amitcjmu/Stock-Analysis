import React from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { LayoutDashboard, Calendar, Users, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PlanTab {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const planTabs: PlanTab[] = [
  { name: 'Overview', href: '/plan', icon: LayoutDashboard },
  { name: 'Timeline', href: '/plan/timeline', icon: Calendar },
  { name: 'Resources', href: '/plan/resource', icon: Users },
  { name: 'Export', href: '/plan/export', icon: Download },
];

export const PlanNavigation: React.FC = () => {
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Preserve planning_flow_id when navigating between Plan tabs
  const planningFlowId = searchParams.get('planning_flow_id');

  // Build URL with preserved query params
  const buildUrl = (href: string): string => {
    if (planningFlowId) {
      return `${href}?planning_flow_id=${planningFlowId}`;
    }
    return href;
  };

  // Determine active tab based on current path
  const isActive = (href: string): boolean => {
    if (href === '/plan') {
      // Exact match for overview page
      return location.pathname === '/plan';
    }
    // Prefix match for other pages
    return location.pathname.startsWith(href);
  };

  return (
    <nav className="border-b border-gray-200 bg-white mb-6">
      <div className="flex space-x-8">
        {planTabs.map((tab) => {
          const Icon = tab.icon;
          const active = isActive(tab.href);

          return (
            <Link
              key={tab.name}
              to={buildUrl(tab.href)}
              className={cn(
                'flex items-center space-x-2 px-1 py-4 border-b-2 text-sm font-medium transition-colors',
                active
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default PlanNavigation;
