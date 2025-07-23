import React from 'react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom';
import { getVersionInfo } from '../../../utils/version';
import { useAuth } from '../../../contexts/AuthContext';
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

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const versionInfo = getVersionInfo();
  const { isAuthenticated, isAdmin, user, logout, isLoading } = useAuth();
  
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

  const navigationItems: NavigationItem[] = [
    { name: 'Dashboard', path: '/', icon: Home },
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
      name: 'Discovery', 
      path: '/discovery', 
      icon: Search,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/discovery/overview', icon: LayoutDashboard },
        { name: 'Data Import', path: '/discovery/cmdb-import', icon: Upload },
        { name: 'Attribute Mapping', path: '/discovery/attribute-mapping', icon: Settings2 },
        { name: 'Data Cleansing', path: '/discovery/data-cleansing', icon: Wand2 },
        { name: 'Inventory', path: '/discovery/inventory', icon: Database },
        { name: 'Dependencies', path: '/discovery/dependencies', icon: Network },
        { name: 'Tech Debt', path: '/discovery/tech-debt', icon: ShieldAlert },
      ]
    },
    { 
      name: 'Assess', 
      path: '/assess', 
      icon: FileText,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/assess/overview', icon: FileText },
        { name: 'Treatment', path: '/assess/treatment', icon: ClipboardList },
        { name: 'Wave Planning', path: '/assess/waveplanning', icon: Calendar },
        { name: 'Roadmap', path: '/assess/roadmap', icon: Route },
        { name: 'Editor', path: '/assess/editor', icon: Edit },
        { name: 'Assessment Flow', path: '/assessment/initialize', icon: GitBranch }
      ]
    },
    { 
      name: 'Plan', 
      path: '/plan', 
      icon: Building2,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/plan/overview', icon: Building2 },
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
        { name: 'Rewrite', path: '/modernize/rewrite', icon: Zap },
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
        { name: 'Agent Dashboard', path: '/observability/agent-monitoring', icon: Brain },
        { name: 'Agent Analytics', path: '/observability/enhanced?tab=analytics', icon: BarChart3 },
        { name: 'Agent Comparison', path: '/observability/enhanced?tab=comparison', icon: TrendingUp }
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

  const handleToggleExpanded = (sectionName: string) => {
    const key = sectionName.toLowerCase() as keyof ExpandedStates;
    setExpandedStates(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleVersionClick = () => {
    console.log('🔍 Version clicked - navigating to feedback-view');
    console.log('Current location:', location.pathname);
    console.log('Version info:', versionInfo);
    navigate('/feedback-view');
  };

  const handleAuthClick = () => {
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
    <div className={`fixed left-0 top-0 h-full w-64 bg-gray-800 text-white z-40 ${className || ''}`}>
      <SidebarHeader
        onAuthClick={handleAuthClick}
        isAuthenticated={isAuthenticated}
        isLoading={isLoading}
        user={user}
        isAdmin={isAdmin}
      />
      
      <NavigationMenu
        navigationItems={navigationItems}
        currentPath={location.pathname}
        expandedStates={expandedStates}
        onToggleExpanded={handleToggleExpanded}
      />

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
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