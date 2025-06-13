import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface NavigationItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  roles?: string[];
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: '📊' },
  { name: 'Discovery', path: '/discovery', icon: '🔍' },
  { name: 'Planning', path: '/planning', icon: '📋' },
  { name: 'Migration', path: '/migration', icon: '🚀' },
  { name: 'Reports', path: '/reports', icon: '📈' },
  { name: 'Admin', path: '/admin', icon: '⚙️', roles: ['admin'] },
];

const NavigationSidebar: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [isOpen, setIsOpen] = React.useState(true);

  const filteredNavigation = navigation.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <div className={`h-screen bg-gray-800 text-white flex flex-col ${isOpen ? 'w-64' : 'w-20'} transition-all duration-300 ease-in-out`}>
      <div className="p-4 flex items-center justify-between">
        {isOpen && <h1 className="text-xl font-bold">Migration Portal</h1>}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-md hover:bg-gray-700 focus:outline-none"
          aria-label={isOpen ? 'Collapse menu' : 'Expand menu'}
        >
          {isOpen ? '«' : '»'}
        </button>
      </div>
      
      <nav className="flex-1 px-2 space-y-1">
        {filteredNavigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                isActive ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`
            }
          >
            <span className="mr-3 text-xl">{item.icon}</span>
            {isOpen && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>
      
      {isOpen && (
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 rounded-full bg-gray-600 flex items-center justify-center">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">{user?.name || 'User'}</p>
              <p className="text-xs font-medium text-gray-400">{user?.email || ''}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export { NavigationSidebar };
