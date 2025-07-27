import React from 'react';
import { Cloud } from 'lucide-react';
import type { SidebarHeaderProps } from './types';

const SidebarHeader: React.FC<SidebarHeaderProps> = ({
  onAuthClick,
  isAuthenticated,
  isLoading,
  user,
  isAdmin
}) => {
  // Determine cloud icon color based on authentication status
  const getCloudIconColor = (): unknown => {
    console.log('🌤️ Cloud Icon Color Check:', {
      isAuthenticated,
      isAdmin,
      userRole: user?.role,
      userEmail: user?.email
    });

    if (!isAuthenticated) {
      return 'text-gray-400'; // White/gray for anonymous
    } else if (isAdmin) {
      return 'text-red-400'; // Red for admin
    } else {
      return 'text-blue-400'; // Blue for regular user
    }
  };

  // Debug log on every render
  console.log('🎨 SidebarHeader Render:', {
    isAuthenticated,
    isAdmin,
    userRole: user?.role,
    cloudColor: getCloudIconColor()
  });

  return (
    <div className="p-6 border-b border-gray-700">
      <div
        className="flex items-center space-x-3 cursor-pointer hover:bg-gray-700 rounded-lg p-2 -m-2 transition-colors duration-200 group"
        onClick={onAuthClick}
        title={
          isLoading ? 'Loading...' :
          isAuthenticated ? `Signed in as ${user?.full_name || user?.email || 'User'} - Click to logout` :
          'Click to login'
        }
      >
        <Cloud className={`h-8 w-8 ${getCloudIconColor()} group-hover:scale-110 transition-transform duration-200`} />
        <div className="flex-1">
          <h1 className="text-lg font-semibold group-hover:text-white transition-colors">AI Modernize</h1>
          <p className="text-xs text-gray-400 group-hover:text-gray-300 transition-colors">
            Migration Platform
          </p>
        </div>
      </div>
    </div>
  );
};

export default SidebarHeader;
