import React from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { ExpandableMenuSectionProps } from './types';
import NavigationItem from './NavigationItem';

const ExpandableMenuSection: React.FC<ExpandableMenuSectionProps> = ({
  item,
  isExpanded,
  isParentActive,
  onToggle,
  currentPath
}) => {
  const Icon = item.icon;

  return (
    <li>
      <div
        className={`flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-200 cursor-pointer ${
          isParentActive
            ? 'bg-blue-600 text-white'
            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
        }`}
        onClick={onToggle}
      >
        <div className="flex items-center space-x-3">
          <Icon className="h-5 w-5" />
          <span className="font-medium">{item.name}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </div>
      
      {isExpanded && item.submenu && (
        <ul className="ml-6 mt-2 space-y-1">
          {item.submenu.map((subItem) => {
            const isSubActive = currentPath === subItem.path;
            
            return (
              <li key={subItem.name}>
                <NavigationItem
                  item={subItem}
                  isActive={isSubActive}
                  isSubItem={true}
                />
              </li>
            );
          })}
        </ul>
      )}
    </li>
  );
};

export default ExpandableMenuSection;