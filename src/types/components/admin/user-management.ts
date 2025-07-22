/**
 * Admin User Management Component Types
 * 
 * Type definitions for user management components including user lists,
 * user details, user approval workflows, and user statistics.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// User Management component types
export interface UserListProps extends BaseComponentProps {
  users: User[];
  loading?: boolean;
  error?: string | null;
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  selectable?: boolean;
  pagination?: UserListPaginationConfig;
  actions?: UserAction[];
  bulkActions?: UserBulkAction[];
  columns?: UserTableColumn[];
  filters?: UserFilter[];
  sorting?: UserSortConfig;
  onUserClick?: (user: User) => void;
  onUserSelect?: (selectedUsers: User[]) => void;
  onUserAction?: (action: string, user: User) => void;
  onBulkAction?: (action: string, users: User[]) => void;
  onFiltersChange?: (filters: Record<string, any>) => void;
  onSortChange?: (sort: UserSortConfig) => void;
  onPageChange?: (page: number, pageSize: number) => void;
  onRefresh?: () => void;
  renderUserRow?: (user: User, index: number) => ReactNode;
  renderUserActions?: (user: User) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'table' | 'card' | 'list';
  density?: 'compact' | 'normal' | 'comfortable';
  showAvatar?: boolean;
  showStatus?: boolean;
  showRoles?: boolean;
  showLastLogin?: boolean;
  showActions?: boolean;
  enableQuickEdit?: boolean;
  enableInlineEdit?: boolean;
  enableBulkOperations?: boolean;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, users: User[]) => void;
}

export interface UserDetailsModalProps extends BaseComponentProps {
  user: User | null;
  open: boolean;
  onClose: () => void;
  onSave?: (user: User) => void | Promise<void>;
  onDelete?: (user: User) => void | Promise<void>;
  mode?: 'view' | 'edit' | 'create';
  tabs?: UserDetailsTab[];
  actions?: UserAction[];
  loading?: boolean;
  error?: string | null;
  readonly?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showHeader?: boolean;
  showFooter?: boolean;
  showTabs?: boolean;
  showActions?: boolean;
  enableEdit?: boolean;
  enableDelete?: boolean;
  enableAuditLog?: boolean;
  enablePermissions?: boolean;
  enableRoles?: boolean;
  enableSessions?: boolean;
  enableActivity?: boolean;
  enablePreferences?: boolean;
  auditLogs?: AuditLog[];
  permissions?: Permission[];
  roles?: Role[];
  sessions?: UserSession[];
  activities?: UserActivity[];
  preferences?: UserPreferences;
  onTabChange?: (tab: string) => void;
  onAuditLogRefresh?: () => void;
  onPermissionChange?: (permissions: Permission[]) => void;
  onRoleChange?: (roles: Role[]) => void;
  onSessionRevoke?: (session: UserSession) => void;
  onPreferencesUpdate?: (preferences: UserPreferences) => void;
  renderTab?: (tab: UserDetailsTab, user: User) => ReactNode;
  renderHeader?: (user: User) => ReactNode;
  renderFooter?: (user: User) => ReactNode;
  renderActions?: (user: User) => ReactNode;
}

export interface UserApprovalProps extends BaseComponentProps {
  pendingUsers: User[];
  loading?: boolean;
  error?: string | null;
  onApprove?: (user: User, approvalData?: UserApprovalData) => void | Promise<void>;
  onReject?: (user: User, rejectionReason?: string) => void | Promise<void>;
  onBulkApprove?: (users: User[]) => void | Promise<void>;
  onBulkReject?: (users: User[], rejectionReason?: string) => void | Promise<void>;
  showBulkActions?: boolean;
  showApprovalForm?: boolean;
  showRejectionForm?: boolean;
  approvalFormFields?: ApprovalFormField[];
  rejectionReasons?: RejectionReason[];
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  renderUser?: (user: User) => ReactNode;
  renderApprovalForm?: (user: User, onSubmit: (data: UserApprovalData) => void) => ReactNode;
  renderRejectionForm?: (user: User, onSubmit: (reason: string) => void) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'table' | 'card' | 'list';
  density?: 'compact' | 'normal' | 'comfortable';
}

export interface UserStatsProps extends BaseComponentProps {
  stats: UserStats;
  loading?: boolean;
  error?: string | null;
  refreshInterval?: number;
  onRefresh?: () => void;
  onDrillDown?: (stat: string, filters?: Record<string, any>) => void;
  showTrends?: boolean;
  showComparisons?: boolean;
  showBreakdowns?: boolean;
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  comparisonPeriod?: TimeRange;
  onComparisonPeriodChange?: (timeRange: TimeRange) => void;
  charts?: UserStatsChart[];
  customMetrics?: CustomMetric[];
  onChartClick?: (chart: UserStatsChart, data: unknown) => void;
  renderStat?: (stat: UserStatCard) => ReactNode;
  renderChart?: (chart: UserStatsChart) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'cards' | 'table' | 'chart' | 'mixed';
  layout?: 'grid' | 'list' | 'masonry';
  columns?: number;
  spacing?: number | string;
}

// Supporting types for User Management
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  status: UserStatus;
  roles: Role[];
  permissions: Permission[];
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export interface UserListPaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
}

export interface UserAction {
  id: string;
  label: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'danger' | 'warning';
  disabled?: boolean;
  visible?: boolean;
  permissions?: string[];
  onClick: (user: User) => void;
}

export interface UserBulkAction {
  id: string;
  label: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'danger' | 'warning';
  disabled?: boolean;
  visible?: boolean;
  permissions?: string[];
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  onClick: (users: User[]) => void;
}

export interface UserTableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  render?: (value: any, user: User, index: number) => ReactNode;
  filterType?: 'text' | 'select' | 'date' | 'number' | 'boolean';
  filterOptions?: FilterOption[];
}

export interface UserFilter {
  key: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number' | 'boolean' | 'multiselect';
  options?: FilterOption[];
  value?: unknown;
  placeholder?: string;
  validation?: ValidationRule[];
}

export interface UserSortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

export interface UserDetailsTab {
  key: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  visible?: boolean;
  permissions?: string[];
  component?: ReactNode;
}

export interface UserApprovalData {
  role?: string;
  permissions?: string[];
  notes?: string;
  metadata?: Record<string, any>;
}

export interface ApprovalFormField {
  key: string;
  label: string;
  type: 'text' | 'select' | 'textarea' | 'checkbox' | 'radio';
  required?: boolean;
  options?: FieldOption[];
  validation?: ValidationRule[];
  placeholder?: string;
  helpText?: string;
}

export interface RejectionReason {
  id: string;
  label: string;
  description?: string;
  requiresNote?: boolean;
}

export interface UserStats {
  totalUsers: number;
  activeUsers: number;
  pendingUsers: number;
  blockedUsers: number;
  newUsersToday: number;
  newUsersThisWeek: number;
  newUsersThisMonth: number;
  loginRate: number;
  averageSessionDuration: number;
  userGrowthRate: number;
  churnRate: number;
  customStats?: Record<string, number>;
}

export interface UserStatsChart {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  data: unknown[];
  config?: ChartConfig;
  loading?: boolean;
  error?: string;
}

export interface UserStatCard {
  id: string;
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  trend?: TrendData[];
  format?: 'number' | 'percentage' | 'currency' | 'duration';
  color?: string;
  icon?: string;
}

export interface TimeRange {
  start: string;
  end: string;
  preset?: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth' | 'lastMonth' | 'thisYear' | 'custom';
}

export interface CustomMetric {
  id: string;
  name: string;
  value: number;
  format?: 'number' | 'percentage' | 'currency';
  description?: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  details: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
  metadata?: Record<string, any>;
}

export interface Permission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
  granted: boolean;
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: Permission[];
  isDefault?: boolean;
  isSystem?: boolean;
}

export interface UserSession {
  id: string;
  userId: string;
  deviceInfo: string;
  ipAddress: string;
  location?: string;
  startTime: string;
  lastActivity: string;
  isActive: boolean;
}

export interface UserActivity {
  id: string;
  userId: string;
  action: string;
  details: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  notifications: NotificationPreferences;
  display: DisplayPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  types: string[];
}

export interface DisplayPreferences {
  density: 'compact' | 'normal' | 'comfortable';
  sidebarCollapsed: boolean;
  tablePageSize: number;
  showAvatars: boolean;
  showTooltips: boolean;
}

// Common supporting types
export interface FilterOption {
  label: string;
  value: unknown;
  disabled?: boolean;
  description?: string;
}

export interface FieldOption {
  label: string;
  value: unknown;
  disabled?: boolean;
}

export interface ValidationRule {
  type: 'required' | 'email' | 'min' | 'max' | 'pattern' | 'custom';
  value?: unknown;
  message: string;
  validator?: (value: unknown) => boolean | Promise<boolean>;
}

export interface ExportFormat {
  type: 'csv' | 'excel' | 'pdf' | 'json';
  label: string;
  options?: ExportOptions;
}

export interface ExportOptions {
  includeHeaders?: boolean;
  includeMetadata?: boolean;
  compression?: boolean;
  format?: string;
}

export interface ChartConfig {
  xAxis?: unknown;
  yAxis?: unknown;
  legend?: unknown;
  tooltip?: unknown;
  colors?: string[];
  responsive?: boolean;
}

export interface TrendData {
  timestamp: string;
  value: number;
}

export type UserStatus = 'active' | 'inactive' | 'pending' | 'blocked' | 'suspended';