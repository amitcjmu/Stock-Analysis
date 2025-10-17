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
  Cloud
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
    collection: location.pathname.startsWith('/collection'),
    discovery: location.pathname.startsWith('/discovery'),
    assess: location.pathname.startsWith('/assess'),
    plan: location.pathname.startsWith('/plan'),
    execute: location.pathname.startsWith('/execute'),
    modernize: location.pathname.startsWith('/modernize'),
    decommission: location.pathname.startsWith('/decommission'),
    finops: location.pathname.startsWith('/finops'),
    observability: location.pathname.startsWith('/observability'),
    admin: location.pathname.startsWith('/admin')
  });

  /**
   * Build dynamic Discovery submenu from API-driven phases
   * Per ADR-027: Use FlowTypeConfig as single source of truth
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
    const phases = allFlowPhases.discovery.phase_details.map(phase => ({
      name: phase.ui_short_name || phase.display_name,
      path: phase.ui_route,
      icon: getIconForPhase(phase.name)
    }));

    // Always include Overview at the top
    return [
      { name: 'Overview', path: '/discovery/overview', icon: LayoutDashboard },
      ...phases
    ];
  }, [allFlowPhases]);

  /**
   * Build dynamic Assessment submenu from API-driven phases
   * Per ADR-027: Use FlowTypeConfig as single source of truth
   */
  const assessmentSubmenu = React.useMemo(() => {
    // Fallback while loading or if API fails
    if (!allFlowPhases?.assessment) {
      return [
        { name: 'Overview', path: '/assess/overview', icon: FileText }
      ];
    }

    // Map API phases to NavigationItem format
    // Use ui_short_name for compact sidebar labels, fallback to display_name
    const phases = allFlowPhases.assessment.phase_details.map(phase => ({
      name: phase.ui_short_name || phase.display_name,
      path: phase.ui_route,
      icon: getIconForPhase(phase.name)
    }));

    // Custom menu structure: Overview → Treatment → Phases → Editor
    return [
      { name: 'Overview', path: '/assess/overview', icon: FileText },
      { name: 'Treatment', path: '/assess/treatment', icon: ClipboardList },
      ...phases,
      { name: 'Editor', path: '/assess/editor', icon: Edit }
    ];
  }, [allFlowPhases]);

  const navigationItems: NavigationItem[] = [
    { name: 'Dashboard', path: '/', icon: Home },
    {
      name: 'Discovery',
      path: '/discovery',
      icon: Search,
      hasSubmenu: true,
      submenu: discoverySubmenu // ✅ API-driven submenu
    },
    {
      name: 'Collection',
      path: '/collection',
      icon: Database,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/collection/overview', icon: LayoutDashboard },
        { name: 'Adaptive Forms', path: '/collection/adaptive-forms', icon: FileText },
        { name: 'Bulk Upload', path: '/collection/bulk-upload', icon: Upload },
        { name: 'Data Integration', path: '/collection/data-integration', icon: Network },
        { name: 'Progress', path: '/collection/progress', icon: Activity }
      ]
    },
    {
      name: 'Assess',
      path: '/assess',
      icon: FileText,
      hasSubmenu: true,
      submenu: assessmentSubmenu // ✅ API-driven submenu
    },
    {
      name: 'Plan',
      path: '/plan',
      icon: Building2,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/plan/overview', icon: Building2 },
        { name: '6R Analysis', path: '/plan/6r-analysis', icon: BarChart3 },
        { name: 'Wave Planning', path: '/plan/waveplanning', icon: Calendar },
        { name: 'Roadmap', path: '/plan/roadmap', icon: Route },
        { name: 'Timeline', path: '/plan/timeline', icon: Clock },
        { name: 'Resource', path: '/plan/resource', icon: Users },
        { name: 'Target', path: '/plan/target', icon: Target }
      ]
    },
    {
      name: 'Execute',
      path: '/execute',
      icon: Wrench,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/execute/overview', icon: Wrench },
        { name: 'Rehost', path: '/execute/rehost', icon: Settings },
        { name: 'Replatform', path: '/execute/replatform', icon: Cloud },
        { name: 'Cutovers', path: '/execute/cutovers', icon: Calendar },
        { name: 'Reports', path: '/execute/reports', icon: Activity }
      ]
    },
    {
      name: 'Modernize',
      path: '/modernize',
      icon: Sparkles,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/modernize/overview', icon: Sparkles },
        { name: 'Refactor', path: '/modernize/refactor', icon: Code },
        { name: 'Rearchitect', path: '/modernize/rearchitect', icon: Layers },
        { name: 'Replace', path: '/modernize/replace', icon: Zap },
        { name: 'Progress', path: '/modernize/progress', icon: Activity }
      ]
    },
    {
      name: 'Decommission',
      path: '/decommission',
      icon: Archive,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/decommission/overview', icon: Archive },
        { name: 'Planning', path: '/decommission/planning', icon: FileText },
        { name: 'Data Retention', path: '/decommission/data-retention', icon: Database },
        { name: 'Execution', path: '/decommission/execution', icon: Trash2 },
        { name: 'Validation', path: '/decommission/validation', icon: CheckCircle }
      ]
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
