import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import type { NavigationItemProps } from './types';

const NavigationItem: React.FC<NavigationItemProps> = ({
  item,
  isActive,
  isSubItem = false
}) => {
  const Icon = item.icon;
  const location = useLocation();

  // Preserve query parameters when navigating between flow pages
  const pathWithParams = `${item.path}${location.search}`;

  const baseClasses = "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors duration-200";
  const activeClasses = isSubItem
    ? "bg-blue-500 text-white"
    : "bg-blue-600 text-white";
  const inactiveClasses = isSubItem
    ? "text-gray-400 hover:bg-gray-700 hover:text-white"
    : "text-gray-300 hover:bg-gray-700 hover:text-white";

  const iconSize = isSubItem ? "h-4 w-4" : "h-5 w-5";
  const textSize = isSubItem ? "text-sm" : "font-medium";

  return (
    <Link
      to={pathWithParams}
      className={`${baseClasses} ${isActive ? activeClasses : inactiveClasses}`}
    >
      <Icon className={iconSize} />
      <span className={textSize}>{item.name}</span>
    </Link>
  );
};

export default NavigationItem;
