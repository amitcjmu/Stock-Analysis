/**
 * Navigation Component Types
 * 
 * Type definitions for navigation components including sidebar, breadcrumbs, 
 * tabs, and navigation-related interfaces.
 */

import type { ReactNode } from 'react';

// Base navigation types
export interface BaseNavigationProps {
  className?: string;
  children?: ReactNode;
}

export interface NavigationItem {
  id: string;
  label: string;
  icon?: string | ReactNode;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  badge?: string | number;
  children?: NavigationItem[];
  metadata?: Record<string, string | number | boolean | null>;
}

export interface RouteConfig {
  path: string;
  component: ReactNode;
  exact?: boolean;
  requireAuth?: boolean;
  permissions?: string[];
  roles?: string[];
  redirect?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

// Sidebar component types
export interface NavigationSidebarProps extends BaseNavigationProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  items: NavigationItem[];
  header?: ReactNode;
  footer?: ReactNode;
  variant?: 'default' | 'compact' | 'floating';
  position?: 'left' | 'right';
  overlay?: boolean;
  backdrop?: boolean;
  width?: number | string;
  collapsedWidth?: number | string;
  breakpoint?: number;
  autoCollapse?: boolean;
  persistState?: boolean;
  storageKey?: string;
  onItemClick?: (item: NavigationItem) => void;
  onItemHover?: (item: NavigationItem) => void;
  renderItem?: (item: NavigationItem) => ReactNode;
  renderIcon?: (icon: string | ReactNode) => ReactNode;
  renderBadge?: (badge: string | number) => ReactNode;
  showTooltips?: boolean;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  searchable?: boolean;
  searchPlaceholder?: string;
  onSearch?: (query: string, results: NavigationItem[]) => void;
  groupItems?: boolean;
  expandable?: boolean;
  multiSelect?: boolean;
  selectedItems?: string[];
  onSelectionChange?: (selectedItems: string[]) => void;
}

// Breadcrumb component types
export interface BreadcrumbItem {
  id: string;
  label: string;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  icon?: string | ReactNode;
  tooltip?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface FlowBreadcrumbsProps extends BaseNavigationProps {
  flowId: string;
  currentPhase: string;
  phases: PhaseDefinition[];
  onPhaseSelect?: (phase: string) => void;
  items?: BreadcrumbItem[];
  separator?: string | ReactNode;
  maxItems?: number;
  showIcons?: boolean;
  showTooltips?: boolean;
  interactive?: boolean;
  variant?: 'default' | 'compact' | 'pills';
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

export interface BreadcrumbsProps extends BaseNavigationProps {
  items: BreadcrumbItem[];
  separator?: string | ReactNode;
  maxItems?: number;
  showHome?: boolean;
  homeIcon?: string | ReactNode;
  homeHref?: string;
  onHomeClick?: () => void;
  ellipsisPosition?: 'start' | 'middle' | 'end';
  renderItem?: (item: BreadcrumbItem, index: number) => ReactNode;
  renderSeparator?: (index: number) => ReactNode;
  variant?: 'default' | 'compact' | 'pills';
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

// Tab component types
export interface TabDefinition {
  id: string;
  label: string;
  icon?: string | ReactNode;
  disabled?: boolean;
  badge?: string | number;
  content?: ReactNode;
  href?: string;
  onClick?: () => void;
  tooltip?: string;
  hidden?: boolean;
  loading?: boolean;
  error?: boolean;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface NavigationTabsProps extends BaseNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: TabDefinition[];
  disabled?: boolean;
  variant?: 'default' | 'pills' | 'underline' | 'cards';
  size?: 'sm' | 'md' | 'lg';
  orientation?: 'horizontal' | 'vertical';
  position?: 'start' | 'center' | 'end';
  fullWidth?: boolean;
  scrollable?: boolean;
  centered?: boolean;
  justified?: boolean;
  closable?: boolean;
  onTabClose?: (tab: string) => void;
  addable?: boolean;
  onTabAdd?: () => void;
  addButtonText?: string;
  addButtonIcon?: string | ReactNode;
  reorderable?: boolean;
  onTabReorder?: (tabs: TabDefinition[]) => void;
  renderTab?: (tab: TabDefinition, index: number) => ReactNode;
  renderIcon?: (icon: string | ReactNode) => ReactNode;
  renderBadge?: (badge: string | number) => ReactNode;
  renderContent?: (tab: TabDefinition) => ReactNode;
  lazy?: boolean;
  keepAlive?: boolean;
  animation?: boolean;
  animationType?: 'fade' | 'slide' | 'scale';
  animationDuration?: number;
}

export interface TabPanelProps extends BaseNavigationProps {
  tabId: string;
  activeTab: string;
  children: ReactNode;
  lazy?: boolean;
  keepAlive?: boolean;
  loading?: boolean;
  error?: string | null;
  renderLoading?: () => ReactNode;
  renderError?: (error: string) => ReactNode;
}

// Menu component types
export interface MenuItem {
  id: string;
  label: string;
  icon?: string | ReactNode;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  divider?: boolean;
  children?: MenuItem[];
  shortcut?: string;
  badge?: string | number;
  tooltip?: string;
  danger?: boolean;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface DropdownMenuProps extends BaseNavigationProps {
  trigger: ReactNode;
  items: MenuItem[];
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end' | 'left' | 'right';
  offset?: number;
  arrow?: boolean;
  closeOnClick?: boolean;
  closeOnEscape?: boolean;
  closeOnClickOutside?: boolean;
  disabled?: boolean;
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  onSearch?: (query: string, results: MenuItem[]) => void;
  onItemClick?: (item: MenuItem) => void;
  onOpen?: () => void;
  onClose?: () => void;
  renderItem?: (item: MenuItem) => ReactNode;
  renderIcon?: (icon: string | ReactNode) => ReactNode;
  renderBadge?: (badge: string | number) => ReactNode;
  renderShortcut?: (shortcut: string) => ReactNode;
  maxHeight?: number | string;
  minWidth?: number | string;
  variant?: 'default' | 'compact' | 'comfortable';
  size?: 'sm' | 'md' | 'lg';
}

export interface ContextMenuProps extends BaseNavigationProps {
  children: ReactNode;
  items: MenuItem[];
  disabled?: boolean;
  onItemClick?: (item: MenuItem) => void;
  onOpen?: (event: React.MouseEvent) => void;
  onClose?: () => void;
  renderItem?: (item: MenuItem) => ReactNode;
  renderIcon?: (icon: string | ReactNode) => ReactNode;
  renderBadge?: (badge: string | number) => ReactNode;
  renderShortcut?: (shortcut: string) => ReactNode;
  variant?: 'default' | 'compact' | 'comfortable';
  size?: 'sm' | 'md' | 'lg';
}

// Navigation state types
export interface NavigationState {
  currentRoute: string;
  previousRoute?: string;
  routeHistory: string[];
  sidebarCollapsed: boolean;
  activeTab?: string;
  openMenus: string[];
  breadcrumbs: BreadcrumbItem[];
  navigationItems: NavigationItem[];
  permissions: string[];
  roles: string[];
}

export interface NavigationActions {
  navigate: (route: string) => void;
  goBack: () => void;
  goForward: () => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setActiveTab: (tab: string) => void;
  openMenu: (menuId: string) => void;
  closeMenu: (menuId: string) => void;
  updateBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;
  updateNavigationItems: (items: NavigationItem[]) => void;
  setPermissions: (permissions: string[]) => void;
  setRoles: (roles: string[]) => void;
}

// Navigation configuration types
export interface NavigationConfig {
  sidebar: SidebarConfig;
  breadcrumbs: BreadcrumbConfig;
  tabs: TabConfig;
  menu: MenuConfig;
  routes: RouteConfig[];
  permissions: PermissionConfig;
}

export interface SidebarConfig {
  defaultCollapsed: boolean;
  persistState: boolean;
  storageKey: string;
  breakpoint: number;
  autoCollapse: boolean;
  width: number | string;
  collapsedWidth: number | string;
  variant: 'default' | 'compact' | 'floating';
  position: 'left' | 'right';
  overlay: boolean;
  backdrop: boolean;
  showTooltips: boolean;
  searchable: boolean;
  groupItems: boolean;
  expandable: boolean;
}

export interface BreadcrumbConfig {
  showHome: boolean;
  maxItems: number;
  separator: string | ReactNode;
  ellipsisPosition: 'start' | 'middle' | 'end';
  variant: 'default' | 'compact' | 'pills';
  size: 'sm' | 'md' | 'lg';
  showIcons: boolean;
  showTooltips: boolean;
  interactive: boolean;
}

export interface TabConfig {
  variant: 'default' | 'pills' | 'underline' | 'cards';
  size: 'sm' | 'md' | 'lg';
  orientation: 'horizontal' | 'vertical';
  scrollable: boolean;
  centered: boolean;
  justified: boolean;
  closable: boolean;
  addable: boolean;
  reorderable: boolean;
  lazy: boolean;
  keepAlive: boolean;
  animation: boolean;
  animationType: 'fade' | 'slide' | 'scale';
  animationDuration: number;
}

export interface MenuConfig {
  placement: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end' | 'left' | 'right';
  offset: number;
  arrow: boolean;
  closeOnClick: boolean;
  closeOnEscape: boolean;
  closeOnClickOutside: boolean;
  searchable: boolean;
  variant: 'default' | 'compact' | 'comfortable';
  size: 'sm' | 'md' | 'lg';
}

export interface PermissionConfig {
  enablePermissionChecks: boolean;
  enableRoleChecks: boolean;
  fallbackComponent: ReactNode;
  hideUnauthorized: boolean;
  showUnauthorizedMessage: boolean;
  unauthorizedMessage: string;
}

// Supporting types
export interface PhaseDefinition {
  id: string;
  name: string;
  description: string;
  order: number;
  dependencies: string[];
  estimatedDuration: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed';
  icon?: string | ReactNode;
  color?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

// Navigation hooks types
export interface UseNavigationReturn {
  state: NavigationState;
  actions: NavigationActions;
  config: NavigationConfig;
  isLoading: boolean;
  error: string | null;
}

export interface UseNavigationParams {
  initialRoute?: string;
  config?: Partial<NavigationConfig>;
  persistState?: boolean;
  storageKey?: string;
}

export interface UseSidebarReturn {
  collapsed: boolean;
  toggle: () => void;
  expand: () => void;
  collapse: () => void;
  isExpanded: boolean;
  isCollapsed: boolean;
}

export interface UseSidebarParams {
  defaultCollapsed?: boolean;
  persistState?: boolean;
  storageKey?: string;
  breakpoint?: number;
}

export interface UseTabsReturn {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  tabs: TabDefinition[];
  addTab: (tab: TabDefinition) => void;
  removeTab: (tabId: string) => void;
  updateTab: (tabId: string, updates: Partial<TabDefinition>) => void;
  reorderTabs: (tabs: TabDefinition[]) => void;
}

export interface UseTabsParams {
  initialTab?: string;
  tabs?: TabDefinition[];
  persistState?: boolean;
  storageKey?: string;
}

export interface UseBreadcrumbsReturn {
  breadcrumbs: BreadcrumbItem[];
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;
  addBreadcrumb: (breadcrumb: BreadcrumbItem) => void;
  removeBreadcrumb: (breadcrumbId: string) => void;
  clearBreadcrumbs: () => void;
  navigateTo: (breadcrumbId: string) => void;
}

export interface UseBreadcrumbsParams {
  initialBreadcrumbs?: BreadcrumbItem[];
  maxItems?: number;
  persistState?: boolean;
  storageKey?: string;
}

export interface UseMenuReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  items: MenuItem[];
  selectedItem: MenuItem | null;
  setSelectedItem: (item: MenuItem | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredItems: MenuItem[];
}

export interface UseMenuParams {
  items: MenuItem[];
  searchable?: boolean;
  closeOnClick?: boolean;
  onItemClick?: (item: MenuItem) => void;
}

// Event types
export interface NavigationEvent {
  type: 'navigate' | 'back' | 'forward' | 'sidebar_toggle' | 'tab_change' | 'menu_open' | 'menu_close';
  payload: unknown;
  timestamp: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface NavigationEventHandler {
  (event: NavigationEvent): void;
}