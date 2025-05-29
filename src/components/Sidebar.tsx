import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
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
  Cloud,
  ChevronDown,
  ChevronRight,
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
  Shield,
  CheckCircle,
  Settings,
  Code,
  Layers,
  Zap,
  TrendingUp,
  Calculator,
  DollarSign,
  AlertTriangle,
  Upload,
  LayoutDashboard
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();
  const [discoveryExpanded, setDiscoveryExpanded] = useState(
    location.pathname.startsWith('/discovery')
  );
  const [assessExpanded, setAssessExpanded] = useState(
    location.pathname.startsWith('/assess')
  );
  const [planExpanded, setPlanExpanded] = useState(
    location.pathname.startsWith('/plan')
  );
  const [modernizeExpanded, setModernizeExpanded] = useState(
    location.pathname.startsWith('/modernize')
  );
  const [decommissionExpanded, setDecommissionExpanded] = useState(
    location.pathname.startsWith('/decommission')
  );
  const [executeExpanded, setExecuteExpanded] = useState(
    location.pathname.startsWith('/execute')
  );
  const [finopsExpanded, setFinopsExpanded] = useState(
    location.pathname.startsWith('/finops')
  );

  const navigationItems = [
    { name: 'Dashboard', path: '/', icon: Home },
    { 
      name: 'Discovery', 
      path: '/discovery', 
      icon: Search,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/discovery/overview', icon: LayoutDashboard },
        { name: 'Data Import', path: '/discovery/data-import', icon: Upload },
        { name: 'Data Cleansing', path: '/discovery/data-cleansing', icon: Sparkles },
        { name: 'Attribute Mapping', path: '/discovery/attribute-mapping', icon: Settings },
        { name: 'Tech Debt', path: '/discovery/tech-debt-analysis', icon: BarChart3 },
        { name: 'Inventory', path: '/discovery/inventory', icon: Database },
        { name: 'Dependencies', path: '/discovery/dependencies', icon: Network }
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
        { name: 'Editor', path: '/assess/editor', icon: Edit }
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
        { name: 'Data Retention', path: '/decommission/dataretention', icon: Database },
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
        { name: 'Wave Breakdown', path: '/finops/wave-breakdown', icon: BarChart3 },
        { name: 'Cost Trends', path: '/finops/cost-trends', icon: TrendingUp },
        { name: 'Budget Alerts', path: '/finops/budget-alerts', icon: AlertTriangle }
      ]
    },
    { name: 'Observability', path: '/observability', icon: Eye },
  ];

  const handleDiscoveryToggle = () => {
    setDiscoveryExpanded(!discoveryExpanded);
  };

  const handleAssessToggle = () => {
    setAssessExpanded(!assessExpanded);
  };

  const handlePlanToggle = () => {
    setPlanExpanded(!planExpanded);
  };

  const handleModernizeToggle = () => {
    setModernizeExpanded(!modernizeExpanded);
  };

  const handleDecommissionToggle = () => {
    setDecommissionExpanded(!decommissionExpanded);
  };

  const handleExecuteToggle = () => {
    setExecuteExpanded(!executeExpanded);
  };

  const handleFinopsToggle = () => {
    setFinopsExpanded(!finopsExpanded);
  };

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-gray-800 text-white z-50">
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <Cloud className="h-8 w-8 text-blue-400" />
          <div>
            <h1 className="text-lg font-semibold">AI Force</h1>
            <p className="text-xs text-gray-400">Migration Platform</p>
          </div>
        </div>
      </div>
      
      <nav className="mt-6">
        <ul className="space-y-1 px-3">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            const isDiscoveryParent = item.name === 'Discovery' && location.pathname.startsWith('/discovery');
            const isAssessParent = item.name === 'Assess' && location.pathname.startsWith('/assess');
            const isPlanParent = item.name === 'Plan' && location.pathname.startsWith('/plan');
            const isExecuteParent = item.name === 'Execute' && location.pathname.startsWith('/execute');
            const isModernizeParent = item.name === 'Modernize' && location.pathname.startsWith('/modernize');
            const isDecommissionParent = item.name === 'Decommission' && location.pathname.startsWith('/decommission');
            const isFinopsParent = item.name === 'FinOps' && location.pathname.startsWith('/finops');
            
            return (
              <li key={item.name}>
                {item.hasSubmenu ? (
                  <>
                    <div
                      className={`flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-200 cursor-pointer ${
                        isDiscoveryParent || isAssessParent || isPlanParent || isExecuteParent || isModernizeParent || isDecommissionParent || isFinopsParent
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                      onClick={
                        item.name === 'Discovery' ? handleDiscoveryToggle :
                        item.name === 'Assess' ? handleAssessToggle :
                        item.name === 'Plan' ? handlePlanToggle :
                        item.name === 'Execute' ? handleExecuteToggle :
                        item.name === 'Modernize' ? handleModernizeToggle :
                        item.name === 'Decommission' ? handleDecommissionToggle :
                        item.name === 'FinOps' ? handleFinopsToggle :
                        undefined
                      }
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="h-5 w-5" />
                        <span className="font-medium">{item.name}</span>
                      </div>
                      {(
                        (item.name === 'Discovery' && discoveryExpanded) ||
                        (item.name === 'Assess' && assessExpanded) ||
                        (item.name === 'Plan' && planExpanded) ||
                        (item.name === 'Execute' && executeExpanded) ||
                        (item.name === 'Modernize' && modernizeExpanded) ||
                        (item.name === 'Decommission' && decommissionExpanded) ||
                        (item.name === 'FinOps' && finopsExpanded)
                      ) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </div>
                    {((item.name === 'Discovery' && discoveryExpanded) || 
                      (item.name === 'Assess' && assessExpanded) ||
                      (item.name === 'Plan' && planExpanded) ||
                      (item.name === 'Execute' && executeExpanded) ||
                      (item.name === 'Modernize' && modernizeExpanded) ||
                      (item.name === 'Decommission' && decommissionExpanded) ||
                      (item.name === 'FinOps' && finopsExpanded)) && (
                      <ul className="ml-6 mt-2 space-y-1">
                        {item.submenu?.map((subItem) => {
                          const SubIcon = subItem.icon;
                          const isSubActive = location.pathname === subItem.path;
                          
                          return (
                            <li key={subItem.name}>
                              <Link
                                to={subItem.path}
                                className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors duration-200 ${
                                  isSubActive
                                    ? 'bg-blue-500 text-white'
                                    : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                                }`}
                              >
                                <SubIcon className="h-4 w-4" />
                                <span className="text-sm">{subItem.name}</span>
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </>
                ) : (
                  <Link
                    to={item.path}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors duration-200 ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          AI Force v2.1.0
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
