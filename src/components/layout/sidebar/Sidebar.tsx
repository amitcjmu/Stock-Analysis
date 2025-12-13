import React from 'react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom';
import { getVersionInfo } from '../../../utils/version';
import { useAuth } from '../../../contexts/AuthContext';
import { useAllFlowPhases } from '../../../hooks/useFlowPhases';
import {
  Home,
  Search,
  FileText,
  Building2,
  Wrench,
  Sparkles,
  Archive,
  BarChart3,
  Eye,
  Settings,
  Database,
  Network,
  Activity,
  ClipboardList,
  Calendar,
  Route,
  Edit,
  Users,
  Target,
  Clock,
  Trash2,
  CheckCircle,
  Code,
  Layers,
  Zap,
  TrendingUp,
  Calculator,
  AlertTriangle,
  Upload,
  LayoutDashboard,
  User,
  Brain,
  Settings2,
  Wand2,
  ShieldAlert,
  GitBranch,
  Cloud,
  Power,
  Star
} from 'lucide-react';
import type { SidebarProps } from './types'
import type { NavigationItem, ExpandedStates } from './types'
import SidebarHeader from './SidebarHeader';
import NavigationMenu from './NavigationMenu';
import AuthenticationIndicator from './AuthenticationIndicator';
import VersionDisplay from './VersionDisplay';

/**
 * Icon mapping helper for phase names
 * Maps phase_name (snake_case) to appropriate Lucide icons
 */
const getIconForPhase = (phaseName: string) => {
  const iconMap: Record<string, any> = {
    data_import: Upload,
    data_validation: CheckCircle,
    field_mapping: Settings2,
    data_cleansing: Wand2,
    asset_inventory: Database,
    dependency_analysis: Network,
    tech_debt_assessment: ShieldAlert,
    readiness_assessment: FileText,
    complexity_analysis: BarChart3,
    risk_assessment: AlertTriangle,
    recommendation_generation: Target
  };

  return iconMap[phaseName] || FileText;
};

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const versionInfo = getVersionInfo();
  const { isAuthenticated, isAdmin, user, logout, isLoading } = useAuth();

  // Fetch API-driven phase configuration
  const { data: allFlowPhases, isLoading: isPhasesLoading } = useAllFlowPhases();

  const [expandedStates, setExpandedStates] = useState<ExpandedStates>({
    discovery: location.pathname.startsWith('/discovery'),
    finops: location.pathname.startsWith('/finops'),
    observability: location.pathname.startsWith('/observability'),
    admin: location.pathname.startsWith('/admin')
  });

  /**
   * Extract flowId from current URL for discovery phase navigation
   * ADR-038: Support data validation and other phases that need flowId context
   */
  const discoveryFlowId = React.useMemo(() => {
    // Match flowId from various discovery URL patterns
    const patterns = [
      /\/discovery\/data-validation\/([a-f0-9-]+)/,
      /\/discovery\/attribute-mapping\/([a-f0-9-]+)/,
      /\/discovery\/data-cleansing\/([a-f0-9-]+)/,
      /\/discovery\/inventory\/([a-f0-9-]+)/,
      /\/discovery\/dependencies\/([a-f0-9-]+)/,
      /\/discovery\/monitor\/([a-f0-9-]+)/,
    ];

    for (const pattern of patterns) {
      const match = location.pathname.match(pattern);
      if (match) return match[1];
    }

    // Also check query params for flowId
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('flow_id') || searchParams.get('flowId') || null;
  }, [location.pathname, location.search]);

  /**
   * Build dynamic Discovery submenu from API-driven phases
   * Per ADR-027: Use FlowTypeConfig as single source of truth
   * ADR-038: Replace :flowId placeholder with actual flow ID from URL
   */
  const discoverySubmenu = React.useMemo(() => {
    // Fallback while loading or if API fails
    if (!allFlowPhases?.discovery) {
      return [
        { name: 'Overview', path: '/discovery/overview', icon: LayoutDashboard }
      ];
    }

    // Map API phases to NavigationItem format
    // Use ui_short_name for compact sidebar labels, fallback to display_name
    const phases = allFlowPhases.discovery.phase_details.map(phase => {
      // Replace :flowId placeholder with actual flowId if available
      let routePath = phase.ui_route;
      if (discoveryFlowId && routePath.includes(':flowId')) {
        routePath = routePath.replace(':flowId', discoveryFlowId);
      }

      return {
        name: phase.ui_short_name || phase.display_name,
        path: routePath,
        icon: getIconForPhase(phase.name)
      };
    });

    // Always include Overview and Watchlist at the top
    return [
      { name: 'Overview', path: '/discovery/overview', icon: LayoutDashboard },
      { name: 'Watchlist', path: '/discovery/watchlist', icon: Star },
      ...phases
    ];
  }, [allFlowPhases, discoveryFlowId]);


  const navigationItems: NavigationItem[] = [
    { name: 'Dashboard', path: '/', icon: Home },
    {
      name: 'Stock Analysis',
      path: '/discovery',
      icon: Search,
      hasSubmenu: true,
      submenu: discoverySubmenu // ✅ API-driven submenu
    },
    {
      name: 'FinOps',
      path: '/finops',
      icon: BarChart3,
      hasSubmenu: true,
      submenu: [
        { name: 'Cloud Comparison', path: '/finops/cloud-comparison', icon: Cloud },
        { name: 'Savings Analysis', path: '/finops/savings-analysis', icon: TrendingUp },
        { name: 'Cost Analysis', path: '/finops/cost-analysis', icon: Calculator },
        { name: 'LLM Costs', path: '/finops/llm-costs', icon: Brain },
        { name: 'Wave Breakdown', path: '/finops/wave-breakdown', icon: BarChart3 },
        { name: 'Cost Trends', path: '/finops/cost-trends', icon: TrendingUp },
        { name: 'Budget Alerts', path: '/finops/budget-alerts', icon: AlertTriangle }
      ]
    },
    {
      name: 'Observability',
      path: '/observability',
      icon: Eye,
      hasSubmenu: true,
      submenu: [
        { name: 'System Overview', path: '/observability', icon: Eye },
        { name: 'Agent Dashboard', path: '/observability/agent-monitoring', icon: Brain }
      ]
    },
    {
      name: 'Admin',
      path: '/admin',
      icon: Settings,
      hasSubmenu: true,
      submenu: [
        { name: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
        { name: 'Client Management', path: '/admin/clients', icon: Building2 },
        { name: 'Engagement Management', path: '/admin/engagements', icon: Calendar },
        { name: 'User Approvals', path: '/admin/users/approvals', icon: User }
      ]
    },
  ];

  // Split items: keep FinOps, Observability, Admin at the bottom near the profile block
  const bottomNames = new Set(['FinOps', 'Observability', 'Admin']);
  const topNavigationItems = navigationItems.filter((i) => !bottomNames.has(i.name));
  const bottomNavigationItems = navigationItems.filter((i) => bottomNames.has(i.name));

  const handleToggleExpanded = (sectionName: string): void => {
    const key = sectionName.toLowerCase() as keyof ExpandedStates;
    setExpandedStates(prev => {
      const isCurrentlyExpanded = prev[key];

      // If the section is currently expanded, collapse it
      if (isCurrentlyExpanded) {
        return {
          ...prev,
          [key]: false
        };
      }

      // If the section is collapsed, expand it and collapse all others
      const newState: ExpandedStates = {
        collection: false,
        discovery: false,
        assess: false,
        plan: false,
        execute: false,
        modernize: false,
        decommission: false,
        decom: false,
        finops: false,
        observability: false,
        admin: false
      };

      newState[key] = true;
      return newState;
    });
  };

  const handleVersionClick = (): void => {
    console.log('🔍 Version clicked - navigating to feedback-view');
    console.log('Current location:', location.pathname);
    console.log('Version info:', versionInfo);
    navigate('/feedback-view');
  };

  const handleAuthClick = (): void => {
    if (isAuthenticated) {
      // User is logged in, show logout confirmation or logout directly
      logout();
      navigate('/');
    } else {
      // User is not logged in, navigate to login page
      navigate('/login');
    }
  };

  return (
    <div className={`fixed left-0 top-0 h-full w-64 bg-gray-800 text-white z-40 ${className || ''} flex flex-col
      lg:translate-x-0 transition-transform duration-300 ease-in-out
      -translate-x-full lg:block`}>
      <SidebarHeader
        onAuthClick={handleAuthClick}
        isAuthenticated={isAuthenticated}
        isLoading={isLoading}
        user={user}
        isAdmin={isAdmin}
      />

      <div className="flex-1 overflow-y-auto">
        <NavigationMenu
          navigationItems={topNavigationItems}
          currentPath={location.pathname}
          expandedStates={expandedStates}
          onToggleExpanded={handleToggleExpanded}
        />

        {bottomNavigationItems.length > 0 && (
          <div className="mt-20 border-t border-gray-700 pt-12">
            <NavigationMenu
              navigationItems={bottomNavigationItems}
              currentPath={location.pathname}
              expandedStates={expandedStates}
              onToggleExpanded={handleToggleExpanded}
            />
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-700 mt-auto">
        <AuthenticationIndicator
          isAuthenticated={isAuthenticated}
          user={user}
        />
        <VersionDisplay
          versionInfo={versionInfo}
          onVersionClick={handleVersionClick}
        />
      </div>
    </div>
  );
};

export default Sidebar;
