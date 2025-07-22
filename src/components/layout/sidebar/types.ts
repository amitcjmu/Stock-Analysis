import { LucideIcon } from 'lucide-react';

export interface NavigationItem {
  name: string;
  path: string;
  icon: LucideIcon;
  hasSubmenu?: boolean;
  submenu?: NavigationItem[];
}

export interface SidebarHeaderProps {
  onAuthClick: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  user: unknown;
  isAdmin: boolean;
}

export interface NavigationMenuProps {
  navigationItems: NavigationItem[];
  currentPath: string;
  expandedStates: Record<string, boolean>;
  onToggleExpanded: (sectionName: string) => void;
}

export interface ExpandableMenuSectionProps {
  item: NavigationItem;
  isExpanded: boolean;
  isParentActive: boolean;
  onToggle: () => void;
  currentPath: string;
}

export interface NavigationItemProps {
  item: NavigationItem;
  isActive: boolean;
  isSubItem?: boolean;
}

export interface AuthenticationIndicatorProps {
  isAuthenticated: boolean;
  user: unknown;
}

export interface VersionDisplayProps {
  versionInfo: {
    fullVersion: string;
  };
  onVersionClick: () => void;
}

export interface SidebarProps {
  // All props are optional as the component manages its own state
  className?: string;
}

export interface ExpandedStates {
  discovery: boolean;
  collection: boolean;
  assess: boolean;
  plan: boolean;
  execute: boolean;
  modernize: boolean;
  decommission: boolean;
  finops: boolean;
  observability: boolean;
  admin: boolean;
}