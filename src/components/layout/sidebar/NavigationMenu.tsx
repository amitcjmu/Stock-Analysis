import React from 'react';
import type { NavigationMenuProps } from './types'
import type { NavigationItem as NavigationItemType } from './types'
import NavigationItem from './NavigationItem';
import ExpandableMenuSection from './ExpandableMenuSection';

const NavigationMenu: React.FC<NavigationMenuProps> = ({
  navigationItems,
  currentPath,
  expandedStates,
  onToggleExpanded
}) => {
  const checkIfParentActive = (item: NavigationItemType): boolean => {
    if (currentPath === item.path) return true;
    if (item.submenu) {
      return item.submenu.some((subItem: NavigationItemType) => currentPath === subItem.path);
    }
    return false;
  };

  const getExpandedState = (itemName: string): any => {
    const key = itemName.toLowerCase();
    return expandedStates[key] || false;
  };

  return (
    <nav className="mt-6">
      <ul className="space-y-1 px-3">
        {navigationItems.map((item) => {
          const isActive = currentPath === item.path;
          const isParentActive = checkIfParentActive(item);

          return item.hasSubmenu ? (
            <ExpandableMenuSection
              key={item.name}
              item={item}
              isExpanded={getExpandedState(item.name)}
              isParentActive={isParentActive}
              onToggle={() => onToggleExpanded(item.name)}
              currentPath={currentPath}
            />
          ) : (
            <li key={item.name}>
              <NavigationItem
                item={item}
                isActive={isActive}
                isSubItem={false}
              />
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

export default NavigationMenu;
