/**
 * Layout Component Types
 * 
 * Type definitions for layout components including containers, grids,
 * responsive layouts, and structural components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, ContainerComponentProps } from './shared';

// Main layout component types
export interface MainLayoutProps extends BaseComponentProps {
  header?: ReactNode;
  sidebar?: ReactNode;
  footer?: ReactNode;
  content?: ReactNode;
  children?: ReactNode;
  sidebarWidth?: number | string;
  sidebarCollapsed?: boolean;
  sidebarPosition?: 'left' | 'right';
  headerHeight?: number | string;
  footerHeight?: number | string;
  stickyHeader?: boolean;
  stickyFooter?: boolean;
  stickysidebar?: boolean;
  overlay?: boolean;
  backdrop?: boolean;
  responsive?: boolean;
  breakpoint?: number;
  onSidebarToggle?: () => void;
  onBreakpointChange?: (breakpoint: string) => void;
  theme?: 'light' | 'dark' | 'auto';
  variant?: 'default' | 'boxed' | 'fluid' | 'compact';
  gap?: number | string;
  padding?: number | string;
  minHeight?: number | string;
  maxWidth?: number | string;
  centered?: boolean;
  scrollable?: boolean;
  lockScroll?: boolean;
  className?: string;
  headerClassName?: string;
  sidebarClassName?: string;
  contentClassName?: string;
  footerClassName?: string;
  layoutClassName?: string;
}

export interface AdminLayoutProps extends BaseComponentProps {
  user?: UserInfo;
  navigation?: NavigationItem[];
  breadcrumbs?: BreadcrumbItem[];
  notifications?: NotificationItem[];
  userMenu?: UserMenuItem[];
  quickActions?: QuickAction[];
  searchEnabled?: boolean;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  onNotificationClick?: (notification: NotificationItem) => void;
  onUserMenuClick?: (item: UserMenuItem) => void;
  onQuickActionClick?: (action: QuickAction) => void;
  logo?: ReactNode;
  brand?: string;
  version?: string;
  headerActions?: ReactNode;
  sidebarActions?: ReactNode;
  footerContent?: ReactNode;
  helpUrl?: string;
  feedbackUrl?: string;
  supportUrl?: string;
  settingsUrl?: string;
  profileUrl?: string;
  logoutUrl?: string;
  onLogout?: () => void;
  theme?: 'light' | 'dark' | 'auto';
  colorScheme?: string;
  compact?: boolean;
  fullWidth?: boolean;
  bordered?: boolean;
  showBreadcrumbs?: boolean;
  showNotifications?: boolean;
  showUserMenu?: boolean;
  showQuickActions?: boolean;
  showSearch?: boolean;
  showHelp?: boolean;
  showFeedback?: boolean;
  showSettings?: boolean;
  loading?: boolean;
  error?: string | null;
  children?: ReactNode;
}

// Container component types
export interface ContainerProps extends ContainerComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'full';
  fluid?: boolean;
  centered?: boolean;
  disableGutters?: boolean;
  fixed?: boolean;
  breakpoint?: string;
  as?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
}

export interface SectionProps extends ContainerComponentProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  actions?: ReactNode;
  collapsible?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  bordered?: boolean;
  divided?: boolean;
  elevated?: boolean;
  rounded?: boolean;
  variant?: 'default' | 'outlined' | 'filled' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullHeight?: boolean;
  scrollable?: boolean;
  stickyHeader?: boolean;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  headerClassName?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  actionsClassName?: string;
  contentClassName?: string;
  footerClassName?: string;
}

export interface PanelProps extends ContainerComponentProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
  collapsible?: boolean;
  collapsed?: boolean;
  defaultCollapsed?: boolean;
  onToggleCollapse?: (collapsed: boolean) => void;
  closable?: boolean;
  onClose?: () => void;
  resizable?: boolean;
  onResize?: (size: { width: number; height: number }) => void;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
  bordered?: boolean;
  elevated?: boolean;
  rounded?: boolean;
  variant?: 'default' | 'outlined' | 'filled' | 'ghost' | 'card';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  headerSize?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  headerSpacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  contentSpacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  scrollable?: boolean;
  stickyHeader?: boolean;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  headerClassName?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  iconClassName?: string;
  badgeClassName?: string;
  actionsClassName?: string;
  contentClassName?: string;
  footerClassName?: string;
}

// Grid system component types
export interface GridContainerProps extends ContainerComponentProps {
  columns?: number | string;
  rows?: number | string;
  gap?: number | string;
  columnGap?: number | string;
  rowGap?: number | string;
  templateColumns?: string;
  templateRows?: string;
  templateAreas?: string;
  autoColumns?: string;
  autoRows?: string;
  autoFlow?: 'row' | 'column' | 'row dense' | 'column dense';
  alignItems?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  alignContent?: 'start' | 'center' | 'end' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly';
  justifyItems?: 'start' | 'center' | 'end' | 'stretch';
  justifyContent?: 'start' | 'center' | 'end' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly';
  placeItems?: string;
  placeContent?: string;
  responsive?: boolean;
  breakpoints?: GridBreakpoints;
  minColumnWidth?: number | string;
  maxColumnWidth?: number | string;
  equalHeights?: boolean;
  masonry?: boolean;
  masonryColumnWidth?: number | string;
  virtualized?: boolean;
  virtualizedHeight?: number;
  virtualizedItemHeight?: number;
  virtualizedOverscan?: number;
  onLayoutChange?: (layout: GridLayout[]) => void;
}

export interface GridItemProps extends BaseComponentProps {
  column?: number | string;
  row?: number | string;
  columnSpan?: number | string;
  rowSpan?: number | string;
  columnStart?: number | string;
  columnEnd?: number | string;
  rowStart?: number | string;
  rowEnd?: number | string;
  area?: string;
  alignSelf?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justifySelf?: 'start' | 'center' | 'end' | 'stretch';
  placeSelf?: string;
  order?: number;
  responsive?: boolean;
  breakpoints?: GridItemBreakpoints;
  minWidth?: number | string;
  maxWidth?: number | string;
  minHeight?: number | string;
  maxHeight?: number | string;
  aspectRatio?: number | string;
  resizable?: boolean;
  draggable?: boolean;
  onResize?: (size: { width: number; height: number }) => void;
  onDrag?: (position: { x: number; y: number }) => void;
  onDragStart?: () => void;
  onDragEnd?: () => void;
}

// Flex layout component types
export interface FlexProps extends ContainerComponentProps {
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
  wrap?: boolean | 'wrap' | 'nowrap' | 'wrap-reverse';
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  gap?: number | string;
  rowGap?: number | string;
  columnGap?: number | string;
  flex?: number | string;
  grow?: number;
  shrink?: number;
  basis?: number | string;
  inline?: boolean;
  responsive?: boolean;
  breakpoints?: FlexBreakpoints;
  equalWidths?: boolean;
  equalHeights?: boolean;
  reverse?: boolean;
  vertical?: boolean;
  horizontal?: boolean;
}

export interface FlexItemProps extends BaseComponentProps {
  flex?: number | string;
  grow?: number;
  shrink?: number;
  basis?: number | string;
  alignSelf?: 'auto' | 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  order?: number;
  responsive?: boolean;
  breakpoints?: FlexItemBreakpoints;
  minWidth?: number | string;
  maxWidth?: number | string;
  minHeight?: number | string;
  maxHeight?: number | string;
}

// Stack layout component types
export interface StackProps extends ContainerComponentProps {
  direction?: 'vertical' | 'horizontal';
  spacing?: number | string;
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
  reverse?: boolean;
  responsive?: boolean;
  breakpoints?: StackBreakpoints;
  divider?: ReactNode;
  dividerStyle?: React.CSSProperties;
  dividerClassName?: string;
}

export interface VStackProps extends Omit<StackProps, 'direction'> {
  direction?: never;
}

export interface HStackProps extends Omit<StackProps, 'direction'> {
  direction?: never;
}

// Masonry layout component types
export interface MasonryProps extends BaseComponentProps {
  columns?: number;
  spacing?: number | string;
  responsive?: boolean;
  breakpoints?: MasonryBreakpoints;
  minColumnWidth?: number;
  maxColumnWidth?: number;
  children: ReactNode[];
  itemComponent?: React.ComponentType<MasonryItemProps>;
  onLayoutChange?: (layout: MasonryLayout[]) => void;
  virtualized?: boolean;
  virtualizedHeight?: number;
  virtualizedOverscan?: number;
  sequential?: boolean;
}

export interface MasonryItemProps extends BaseComponentProps {
  index: number;
  column: number;
  height?: number;
  children: ReactNode;
}

// Responsive component types
export interface ResponsiveProps extends BaseComponentProps {
  breakpoint?: string | number;
  minBreakpoint?: string | number;
  maxBreakpoint?: string | number;
  hideBelow?: string | number;
  hideAbove?: string | number;
  showOnly?: string | number | (string | number)[];
  children: ReactNode | ((breakpoint: string, width: number) => ReactNode);
}

export interface MediaQueryProps extends BaseComponentProps {
  query: string;
  children: ReactNode | ((matches: boolean) => ReactNode);
  fallback?: ReactNode;
  serverFallback?: boolean;
}

// Supporting types
export interface UserInfo {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  permissions: string[];
  lastLogin?: string;
  status: 'online' | 'offline' | 'away' | 'busy';
}

export interface NavigationItem {
  id: string;
  label: string;
  icon?: ReactNode;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  badge?: string | number;
  children?: NavigationItem[];
  metadata?: Record<string, any>;
}

export interface BreadcrumbItem {
  id: string;
  label: string;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  metadata?: Record<string, any>;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  timestamp: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  metadata?: Record<string, any>;
}

export interface UserMenuItem {
  id: string;
  label: string;
  icon?: ReactNode;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  divider?: boolean;
  metadata?: Record<string, any>;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  tooltip?: string;
  shortcut?: string;
  metadata?: Record<string, any>;
}

export interface GridBreakpoints {
  xs?: GridContainerConfig;
  sm?: GridContainerConfig;
  md?: GridContainerConfig;
  lg?: GridContainerConfig;
  xl?: GridContainerConfig;
  xxl?: GridContainerConfig;
}

export interface GridContainerConfig {
  columns?: number | string;
  gap?: number | string;
  templateColumns?: string;
  templateRows?: string;
  autoColumns?: string;
  autoRows?: string;
  alignItems?: string;
  alignContent?: string;
  justifyItems?: string;
  justifyContent?: string;
}

export interface GridItemBreakpoints {
  xs?: GridItemConfig;
  sm?: GridItemConfig;
  md?: GridItemConfig;
  lg?: GridItemConfig;
  xl?: GridItemConfig;
  xxl?: GridItemConfig;
}

export interface GridItemConfig {
  column?: number | string;
  row?: number | string;
  columnSpan?: number | string;
  rowSpan?: number | string;
  columnStart?: number | string;
  columnEnd?: number | string;
  rowStart?: number | string;
  rowEnd?: number | string;
  area?: string;
  alignSelf?: string;
  justifySelf?: string;
  order?: number;
}

export interface FlexBreakpoints {
  xs?: FlexConfig;
  sm?: FlexConfig;
  md?: FlexConfig;
  lg?: FlexConfig;
  xl?: FlexConfig;
  xxl?: FlexConfig;
}

export interface FlexConfig {
  direction?: string;
  wrap?: boolean | string;
  align?: string;
  justify?: string;
  gap?: number | string;
  flex?: number | string;
  grow?: number;
  shrink?: number;
  basis?: number | string;
}

export interface FlexItemBreakpoints {
  xs?: FlexItemConfig;
  sm?: FlexItemConfig;
  md?: FlexItemConfig;
  lg?: FlexItemConfig;
  xl?: FlexItemConfig;
  xxl?: FlexItemConfig;
}

export interface FlexItemConfig {
  flex?: number | string;
  grow?: number;
  shrink?: number;
  basis?: number | string;
  alignSelf?: string;
  order?: number;
}

export interface StackBreakpoints {
  xs?: StackConfig;
  sm?: StackConfig;
  md?: StackConfig;
  lg?: StackConfig;
  xl?: StackConfig;
  xxl?: StackConfig;
}

export interface StackConfig {
  direction?: 'vertical' | 'horizontal';
  spacing?: number | string;
  align?: string;
  justify?: string;
  wrap?: boolean;
  reverse?: boolean;
}

export interface MasonryBreakpoints {
  xs?: MasonryConfig;
  sm?: MasonryConfig;
  md?: MasonryConfig;
  lg?: MasonryConfig;
  xl?: MasonryConfig;
  xxl?: MasonryConfig;
}

export interface MasonryConfig {
  columns?: number;
  spacing?: number | string;
  minColumnWidth?: number;
  maxColumnWidth?: number;
}

export interface GridLayout {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  maxW?: number;
  minH?: number;
  maxH?: number;
  static?: boolean;
  isDraggable?: boolean;
  isResizable?: boolean;
  resizeHandles?: string[];
  isBounded?: boolean;
}

export interface MasonryLayout {
  index: number;
  column: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

// Layout hooks types
export interface UseLayoutReturn {
  breakpoint: string;
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  orientation: 'portrait' | 'landscape';
}

export interface UseResponsiveReturn {
  matches: boolean;
  breakpoint: string;
  width: number;
  height: number;
}

export interface UseGridReturn {
  layout: GridLayout[];
  setLayout: (layout: GridLayout[]) => void;
  addItem: (item: Omit<GridLayout, 'x' | 'y'>) => void;
  removeItem: (itemId: string) => void;
  updateItem: (itemId: string, updates: Partial<GridLayout>) => void;
  resetLayout: () => void;
  compactLayout: () => void;
}

export interface UseMasonryReturn {
  layout: MasonryLayout[];
  columns: number;
  heights: number[];
  addItem: (height: number) => void;
  removeItem: (index: number) => void;
  resetLayout: () => void;
  recalculateLayout: () => void;
}

// Layout context types
export interface LayoutContext {
  breakpoint: string;
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
  theme: 'light' | 'dark' | 'auto';
  colorScheme: string;
  direction: 'ltr' | 'rtl';
  compact: boolean;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

export interface AdminLayoutContext extends LayoutContext {
  user: UserInfo | null;
  notifications: NotificationItem[];
  unreadNotifications: number;
  markNotificationAsRead: (id: string) => void;
  markAllNotificationsAsRead: () => void;
  addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
}