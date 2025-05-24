
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
  Activity
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();
  const [discoveryExpanded, setDiscoveryExpanded] = useState(
    location.pathname.startsWith('/discovery')
  );

  const navigationItems = [
    { name: 'Dashboard', path: '/', icon: Home },
    { 
      name: 'Discovery', 
      path: '/discovery', 
      icon: Search,
      hasSubmenu: true,
      submenu: [
        { name: 'Overview', path: '/discovery/overview', icon: Search },
        { name: 'Inventory', path: '/discovery/inventory', icon: Database },
        { name: 'Dependencies', path: '/discovery/dependencies', icon: Network },
        { name: 'Scan', path: '/discovery/scan', icon: Activity }
      ]
    },
    { name: 'Assess', path: '/assess', icon: FileText },
    { name: 'Plan', path: '/plan', icon: Building2 },
    { name: 'Execute', path: '/execute', icon: Wrench },
    { name: 'Modernize', path: '/modernize', icon: Sparkles },
    { name: 'Decommission', path: '/decommission', icon: Archive },
    { name: 'FinOps', path: '/finops', icon: BarChart3 },
    { name: 'Observability', path: '/observability', icon: Eye },
  ];

  const handleDiscoveryToggle = () => {
    setDiscoveryExpanded(!discoveryExpanded);
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
            
            return (
              <li key={item.name}>
                {item.hasSubmenu ? (
                  <>
                    <div
                      className={`flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-200 cursor-pointer ${
                        isDiscoveryParent
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                      onClick={handleDiscoveryToggle}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="h-5 w-5" />
                        <span className="font-medium">{item.name}</span>
                      </div>
                      {discoveryExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </div>
                    {discoveryExpanded && (
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
