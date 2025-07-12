/**
 * Admin Component Types
 * 
 * Type definitions for admin-specific components including user management,
 * system settings, analytics dashboards, and administrative interfaces.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './shared';

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
  onChartClick?: (chart: UserStatsChart, data: any) => void;
  renderStat?: (stat: UserStatCard) => ReactNode;
  renderChart?: (chart: UserStatsChart) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'cards' | 'table' | 'chart' | 'mixed';
  layout?: 'grid' | 'list' | 'masonry';
  columns?: number;
  spacing?: number | string;
}

// Engagement Management component types
export interface EngagementListProps extends BaseComponentProps {
  engagements: Engagement[];
  loading?: boolean;
  error?: string | null;
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  selectable?: boolean;
  pagination?: EngagementListPaginationConfig;
  actions?: EngagementAction[];
  bulkActions?: EngagementBulkAction[];
  columns?: EngagementTableColumn[];
  filters?: EngagementFilter[];
  sorting?: EngagementSortConfig;
  onEngagementClick?: (engagement: Engagement) => void;
  onEngagementSelect?: (selectedEngagements: Engagement[]) => void;
  onEngagementAction?: (action: string, engagement: Engagement) => void;
  onBulkAction?: (action: string, engagements: Engagement[]) => void;
  onFiltersChange?: (filters: Record<string, any>) => void;
  onSortChange?: (sort: EngagementSortConfig) => void;
  onPageChange?: (page: number, pageSize: number) => void;
  onRefresh?: () => void;
  renderEngagementRow?: (engagement: Engagement, index: number) => ReactNode;
  renderEngagementActions?: (engagement: Engagement) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'table' | 'card' | 'list' | 'kanban';
  density?: 'compact' | 'normal' | 'comfortable';
  showClient?: boolean;
  showStatus?: boolean;
  showProgress?: boolean;
  showTeam?: boolean;
  showTimeline?: boolean;
  showActions?: boolean;
  enableQuickEdit?: boolean;
  enableInlineEdit?: boolean;
  enableBulkOperations?: boolean;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, engagements: Engagement[]) => void;
}

export interface EngagementCreationProps extends BaseComponentProps {
  onSubmit: (engagement: CreateEngagementRequest) => void | Promise<void>;
  onCancel?: () => void;
  clients?: Client[];
  templates?: EngagementTemplate[];
  teams?: Team[];
  users?: User[];
  loading?: boolean;
  error?: string | null;
  mode?: 'create' | 'clone' | 'template';
  sourceEngagement?: Engagement;
  sourceTemplate?: EngagementTemplate;
  steps?: EngagementCreationStep[];
  currentStep?: number;
  onStepChange?: (step: number) => void;
  validation?: EngagementValidationConfig;
  autoSave?: boolean;
  autoSaveInterval?: number;
  onAutoSave?: (data: Partial<CreateEngagementRequest>) => void;
  renderStep?: (step: EngagementCreationStep, data: Partial<CreateEngagementRequest>) => ReactNode;
  renderNavigation?: (currentStep: number, totalSteps: number) => ReactNode;
  renderActions?: (currentStep: number, totalSteps: number, canProceed: boolean) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  layout?: 'vertical' | 'horizontal' | 'wizard';
  showProgress?: boolean;
  showValidation?: boolean;
  allowSkipSteps?: boolean;
  allowBackNavigation?: boolean;
}

export interface EngagementFiltersProps extends BaseComponentProps {
  filters: EngagementFilter[];
  values: Record<string, any>;
  onFiltersChange: (filters: Record<string, any>) => void;
  onReset?: () => void;
  onSave?: (name: string, filters: Record<string, any>) => void;
  savedFilters?: SavedFilter[];
  onLoadSavedFilter?: (filter: SavedFilter) => void;
  onDeleteSavedFilter?: (filter: SavedFilter) => void;
  clients?: Client[];
  teams?: Team[];
  users?: User[];
  loading?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  showSavedFilters?: boolean;
  showFilterCount?: boolean;
  showClearAll?: boolean;
  showApplyButton?: boolean;
  autoApply?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'sidebar' | 'toolbar' | 'modal' | 'popover';
  layout?: 'vertical' | 'horizontal' | 'grid';
  spacing?: number | string;
}

// System Settings component types
export interface SystemSettingsProps extends BaseComponentProps {
  settings: SystemSettings;
  onUpdate: (updates: Partial<SystemSettings>) => void | Promise<void>;
  onReset?: (section?: string) => void | Promise<void>;
  onExport?: () => void;
  onImport?: (file: File) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
  sections?: SettingsSection[];
  activeSection?: string;
  onSectionChange?: (section: string) => void;
  validation?: SettingsValidationConfig;
  autoSave?: boolean;
  autoSaveInterval?: number;
  onAutoSave?: (updates: Partial<SystemSettings>) => void;
  showNavigation?: boolean;
  showActions?: boolean;
  showValidation?: boolean;
  showDirtyIndicator?: boolean;
  enableReset?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  enableAuditLog?: boolean;
  auditLogs?: SettingsAuditLog[];
  onAuditLogRefresh?: () => void;
  renderSection?: (section: SettingsSection, settings: SystemSettings) => ReactNode;
  renderNavigation?: (sections: SettingsSection[], activeSection: string) => ReactNode;
  renderActions?: (hasChanges: boolean) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  layout?: 'sidebar' | 'tabs' | 'accordion' | 'wizard';
  variant?: 'default' | 'compact' | 'detailed';
}

export interface SecuritySettingsProps extends BaseComponentProps {
  settings: SecuritySettings;
  onUpdate: (updates: Partial<SecuritySettings>) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
  policies?: SecurityPolicy[];
  onPolicyCreate?: (policy: SecurityPolicy) => void | Promise<void>;
  onPolicyUpdate?: (policy: SecurityPolicy) => void | Promise<void>;
  onPolicyDelete?: (policy: SecurityPolicy) => void | Promise<void>;
  auditLogs?: SecurityAuditLog[];
  onAuditLogRefresh?: () => void;
  showPasswordPolicy?: boolean;
  showSessionSettings?: boolean;
  showMFASettings?: boolean;
  showAccessControl?: boolean;
  showEncryption?: boolean;
  showAuditLog?: boolean;
  showPolicies?: boolean;
  enableTestMode?: boolean;
  onTestPolicy?: (policy: SecurityPolicy) => void | Promise<void>;
  renderPolicyForm?: (policy: SecurityPolicy | null, onSubmit: (policy: SecurityPolicy) => void) => ReactNode;
  renderAuditLog?: (logs: SecurityAuditLog[]) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'default' | 'advanced' | 'compliance';
}

// Analytics Dashboard component types
export interface AnalyticsDashboardProps extends BaseComponentProps {
  widgets: DashboardWidget[];
  layout: DashboardLayout;
  onLayoutChange?: (layout: DashboardLayout) => void;
  onWidgetAdd?: (widget: DashboardWidget) => void;
  onWidgetRemove?: (widgetId: string) => void;
  onWidgetUpdate?: (widgetId: string, updates: Partial<DashboardWidget>) => void;
  onWidgetResize?: (widgetId: string, size: { width: number; height: number }) => void;
  onWidgetMove?: (widgetId: string, position: { x: number; y: number }) => void;
  loading?: boolean;
  error?: string | null;
  editable?: boolean;
  resizable?: boolean;
  draggable?: boolean;
  responsive?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  filters?: DashboardFilter[];
  onFiltersChange?: (filters: Record<string, any>) => void;
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  templates?: DashboardTemplate[];
  onLoadTemplate?: (template: DashboardTemplate) => void;
  onSaveTemplate?: (name: string, description?: string) => void;
  onExport?: (format: ExportFormat) => void;
  renderWidget?: (widget: DashboardWidget) => ReactNode;
  renderWidgetHeader?: (widget: DashboardWidget) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'default' | 'compact' | 'detailed';
  theme?: 'light' | 'dark' | 'auto';
  gridSize?: number;
  margin?: number | [number, number];
  padding?: number | [number, number];
  containerPadding?: number | [number, number];
  rowHeight?: number;
  maxRows?: number;
  cols?: number;
  breakpoints?: Record<string, number>;
  colWidths?: Record<string, number>;
}

export interface MetricsOverviewProps extends BaseComponentProps {
  metrics: Metric[];
  loading?: boolean;
  error?: string | null;
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  comparisonEnabled?: boolean;
  comparisonPeriod?: TimeRange;
  onComparisonPeriodChange?: (timeRange: TimeRange) => void;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  filters?: MetricFilter[];
  onFiltersChange?: (filters: Record<string, any>) => void;
  onMetricClick?: (metric: Metric) => void;
  onDrillDown?: (metric: Metric, filters?: Record<string, any>) => void;
  refreshInterval?: number;
  onRefresh?: () => void;
  showTrends?: boolean;
  showTargets?: boolean;
  showAlerts?: boolean;
  showExport?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, metrics: Metric[]) => void;
  renderMetric?: (metric: Metric) => ReactNode;
  renderTrend?: (metric: Metric, trend: MetricTrend) => ReactNode;
  renderTarget?: (metric: Metric, target: MetricTarget) => ReactNode;
  renderAlert?: (metric: Metric, alert: MetricAlert) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'cards' | 'table' | 'chart' | 'tiles';
  layout?: 'grid' | 'list' | 'masonry';
  columns?: number;
  spacing?: number | string;
  showValues?: boolean;
  showPercentages?: boolean;
  showChanges?: boolean;
  showSparklines?: boolean;
}

// Session Comparison component types
export interface SessionComparisonProps extends BaseComponentProps {
  sessions: UserSession[];
  onCompare: (sessionIds: string[]) => void;
  onRefresh?: () => void;
  loading?: boolean;
  error?: string | null;
  maxComparisons?: number;
  columns?: SessionComparisonColumn[];
  filters?: SessionFilter[];
  onFiltersChange?: (filters: Record<string, any>) => void;
  showDifferences?: boolean;
  showSimilarities?: boolean;
  showMetrics?: boolean;
  showTimeline?: boolean;
  showActivities?: boolean;
  showDeviceInfo?: boolean;
  showLocationInfo?: boolean;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, sessions: UserSession[]) => void;
  renderSession?: (session: UserSession) => ReactNode;
  renderComparison?: (sessions: UserSession[]) => ReactNode;
  renderDifference?: (sessions: UserSession[], field: string) => ReactNode;
  renderMetric?: (sessions: UserSession[], metric: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'table' | 'side-by-side' | 'overlay' | 'detailed';
  layout?: 'horizontal' | 'vertical' | 'grid';
}

// Supporting types for admin components
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  roles: Role[];
  permissions: Permission[];
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  system: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  conditions?: Record<string, any>;
  system: boolean;
}

export interface Engagement {
  id: string;
  name: string;
  description?: string;
  client: Client;
  status: 'planning' | 'active' | 'on-hold' | 'completed' | 'cancelled';
  progress: number;
  startDate: string;
  endDate?: string;
  estimatedEndDate?: string;
  team: Team[];
  lead: User;
  flows: Flow[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export interface Client {
  id: string;
  name: string;
  domain: string;
  industry?: string;
  size?: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  location?: string;
  contact: Contact;
  settings: ClientSettings;
  createdAt: string;
  updatedAt: string;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  members: User[];
  lead: User;
  roles: TeamRole[];
  createdAt: string;
  updatedAt: string;
}

export interface Flow {
  id: string;
  type: string;
  name: string;
  status: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

export interface UserSession {
  id: string;
  userId: string;
  deviceInfo: DeviceInfo;
  locationInfo: LocationInfo;
  activities: UserActivity[];
  metrics: SessionMetrics;
  startTime: string;
  endTime?: string;
  duration?: number;
  ipAddress: string;
  userAgent: string;
}

export interface DeviceInfo {
  type: 'desktop' | 'mobile' | 'tablet';
  os: string;
  osVersion: string;
  browser: string;
  browserVersion: string;
  screen: { width: number; height: number };
  timezone: string;
}

export interface LocationInfo {
  country?: string;
  region?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  isp?: string;
}

export interface UserActivity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SessionMetrics {
  pageViews: number;
  actions: number;
  duration: number;
  bounceRate: number;
  conversionRate: number;
}

export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  changes?: Record<string, any>;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  metadata?: Record<string, any>;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  dateFormat: string;
  timeFormat: string;
  notifications: NotificationPreferences;
  dashboard: DashboardPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  frequency: 'immediate' | 'daily' | 'weekly';
  categories: Record<string, boolean>;
}

export interface DashboardPreferences {
  layout: string;
  widgets: string[];
  defaultTimeRange: TimeRange;
  autoRefresh: boolean;
  refreshInterval: number;
}

export interface AccessibilityPreferences {
  highContrast: boolean;
  largeText: boolean;
  reduceMotion: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
}

// Additional supporting interfaces
export interface UserAction {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick: (user: User) => void;
  disabled?: boolean | ((user: User) => boolean);
  visible?: boolean | ((user: User) => boolean);
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  tooltip?: string;
}

export interface UserBulkAction {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick: (users: User[]) => void;
  disabled?: boolean | ((users: User[]) => boolean);
  confirmationRequired?: boolean;
  confirmationMessage?: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  tooltip?: string;
}

export interface UserTableColumn {
  id: string;
  key: string;
  title: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (user: User) => ReactNode;
  align?: 'left' | 'center' | 'right';
}

export interface UserFilter {
  id: string;
  key: string;
  label: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'boolean';
  options?: { label: string; value: any }[];
  placeholder?: string;
  multiple?: boolean;
}

export interface UserSortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface UserListPaginationConfig {
  page: number;
  pageSize: number;
  total?: number;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  showQuickJumper?: boolean;
  showTotal?: boolean;
}

export interface UserDetailsTab {
  id: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
  disabled?: boolean;
  visible?: boolean;
  badge?: string | number;
}

export interface UserApprovalData {
  roles: string[];
  permissions: string[];
  welcomeMessage?: string;
  sendWelcomeEmail: boolean;
  temporaryAccess: boolean;
  accessExpiry?: string;
  metadata?: Record<string, any>;
}

export interface ApprovalFormField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  options?: { label: string; value: any }[];
  placeholder?: string;
  validation?: any;
}

export interface RejectionReason {
  value: string;
  label: string;
  description?: string;
}

export interface UserStats {
  total: number;
  active: number;
  inactive: number;
  pending: number;
  suspended: number;
  newThisMonth: number;
  loginRate: number;
  retentionRate: number;
  averageSessionDuration: number;
  topRoles: Array<{ role: string; count: number }>;
  registrationTrend: Array<{ date: string; count: number }>;
  activityTrend: Array<{ date: string; count: number }>;
}

export interface UserStatCard {
  id: string;
  title: string;
  value: number | string;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
    period: string;
  };
  comparison?: {
    value: number | string;
    period: string;
  };
  format?: 'number' | 'percentage' | 'currency' | 'duration';
  color?: string;
  icon?: ReactNode;
  onClick?: () => void;
}

export interface UserStatsChart {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  data: any[];
  config?: any;
  height?: number;
  refreshInterval?: number;
}

export interface CustomMetric {
  id: string;
  name: string;
  query: string;
  aggregation: 'sum' | 'avg' | 'min' | 'max' | 'count';
  format: 'number' | 'percentage' | 'currency' | 'duration';
  refresh: boolean;
}

export interface TimeRange {
  start: string;
  end: string;
  preset?: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'last90days' | 'thisMonth' | 'lastMonth' | 'thisYear' | 'lastYear' | 'custom';
}

export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
}

export interface Contact {
  name: string;
  email: string;
  phone?: string;
  title?: string;
}

export interface ClientSettings {
  branding: {
    logo?: string;
    primaryColor: string;
    secondaryColor: string;
  };
  features: string[];
  limits: {
    users: number;
    engagements: number;
    storage: number;
  };
  notifications: {
    email: boolean;
    sms: boolean;
    webhook?: string;
  };
}

export interface TeamRole {
  userId: string;
  role: 'lead' | 'member' | 'consultant' | 'observer';
  permissions: string[];
  joinedAt: string;
}

// Additional complex types
export interface EngagementAction {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick: (engagement: Engagement) => void;
  disabled?: boolean | ((engagement: Engagement) => boolean);
  visible?: boolean | ((engagement: Engagement) => boolean);
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  tooltip?: string;
}

export interface EngagementBulkAction {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick: (engagements: Engagement[]) => void;
  disabled?: boolean | ((engagements: Engagement[]) => boolean);
  confirmationRequired?: boolean;
  confirmationMessage?: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success';
  tooltip?: string;
}

export interface EngagementTableColumn {
  id: string;
  key: string;
  title: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (engagement: Engagement) => ReactNode;
  align?: 'left' | 'center' | 'right';
}

export interface EngagementFilter {
  id: string;
  key: string;
  label: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'boolean';
  options?: { label: string; value: any }[];
  placeholder?: string;
  multiple?: boolean;
}

export interface EngagementSortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface EngagementListPaginationConfig {
  page: number;
  pageSize: number;
  total?: number;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  showQuickJumper?: boolean;
  showTotal?: boolean;
}

export interface CreateEngagementRequest {
  name: string;
  description?: string;
  clientId: string;
  teamIds: string[];
  leadId: string;
  startDate: string;
  estimatedEndDate?: string;
  scope: EngagementScope;
  budget?: EngagementBudget;
  deliverables: Deliverable[];
  timeline: TimelinePhase[];
  risks: Risk[];
  assumptions: string[];
  dependencies: Dependency[];
  metadata?: Record<string, any>;
}

export interface EngagementTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  scope: EngagementScope;
  deliverables: Deliverable[];
  timeline: TimelinePhase[];
  risks: Risk[];
  assumptions: string[];
  dependencies: Dependency[];
  estimatedDuration: number;
  requiredRoles: string[];
  metadata?: Record<string, any>;
}

export interface EngagementCreationStep {
  id: string;
  title: string;
  description?: string;
  fields: string[];
  validation?: any;
  optional?: boolean;
  component?: ReactNode;
}

export interface EngagementValidationConfig {
  required: string[];
  rules: Record<string, any>;
  messages: Record<string, string>;
}

export interface SavedFilter {
  id: string;
  name: string;
  description?: string;
  filters: Record<string, any>;
  isDefault?: boolean;
  isShared?: boolean;
  createdBy: string;
  createdAt: string;
}

export interface SystemSettings {
  general: GeneralSettings;
  security: SecuritySettings;
  notifications: NotificationSettings;
  integrations: IntegrationSettings;
  appearance: AppearanceSettings;
  performance: PerformanceSettings;
  backup: BackupSettings;
  audit: AuditSettings;
}

export interface GeneralSettings {
  siteName: string;
  siteUrl: string;
  adminEmail: string;
  timezone: string;
  language: string;
  dateFormat: string;
  timeFormat: string;
  currency: string;
  maintenanceMode: boolean;
  maintenanceMessage?: string;
}

export interface SecuritySettings {
  passwordPolicy: PasswordPolicy;
  sessionTimeout: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
  mfaRequired: boolean;
  mfaMethods: string[];
  ipWhitelist: string[];
  encryptionEnabled: boolean;
  auditLogging: boolean;
  dataRetentionDays: number;
}

export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  maxAge: number;
  historySize: number;
  preventCommonPasswords: boolean;
}

export interface NotificationSettings {
  emailEnabled: boolean;
  smsEnabled: boolean;
  pushEnabled: boolean;
  webhookEnabled: boolean;
  defaultSender: string;
  smtpSettings: SmtpSettings;
  smsSettings: SmsSettings;
  pushSettings: PushSettings;
  webhookSettings: WebhookSettings;
}

export interface IntegrationSettings {
  apiKeyEnabled: boolean;
  webhooksEnabled: boolean;
  ssoEnabled: boolean;
  ldapEnabled: boolean;
  samlEnabled: boolean;
  oauth2Enabled: boolean;
  rateLimiting: RateLimitingSettings;
  cors: CorsSettings;
}

export interface AppearanceSettings {
  theme: 'light' | 'dark' | 'auto';
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  logo?: string;
  favicon?: string;
  customCss?: string;
  brandingEnabled: boolean;
}

export interface PerformanceSettings {
  cacheEnabled: boolean;
  cacheTtl: number;
  compressionEnabled: boolean;
  minificationEnabled: boolean;
  cdnEnabled: boolean;
  cdnUrl?: string;
  databasePoolSize: number;
  requestTimeout: number;
}

export interface BackupSettings {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly';
  retention: number;
  location: 'local' | 's3' | 'gcs' | 'azure';
  encryption: boolean;
  compression: boolean;
  excludeTables: string[];
}

export interface AuditSettings {
  enabled: boolean;
  events: string[];
  retention: number;
  encryption: boolean;
  realTimeAlerts: boolean;
  alertThresholds: Record<string, number>;
}

export interface SettingsSection {
  id: string;
  title: string;
  description?: string;
  icon?: ReactNode;
  fields: SettingsField[];
  validation?: any;
  permissions?: string[];
}

export interface SettingsField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  placeholder?: string;
  help?: string;
  options?: { label: string; value: any }[];
  validation?: any;
  dependencies?: string[];
  sensitive?: boolean;
}

export interface SettingsValidationConfig {
  rules: Record<string, any>;
  messages: Record<string, string>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

export interface SettingsAuditLog {
  id: string;
  section: string;
  field: string;
  oldValue: any;
  newValue: any;
  changedBy: string;
  timestamp: string;
  reason?: string;
}

export interface SecurityPolicy {
  id: string;
  name: string;
  description: string;
  type: 'password' | 'access' | 'data' | 'network' | 'compliance';
  rules: PolicyRule[];
  enabled: boolean;
  enforced: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface PolicyRule {
  id: string;
  condition: string;
  action: string;
  parameters: Record<string, any>;
  enabled: boolean;
}

export interface SecurityAuditLog {
  id: string;
  event: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  user?: string;
  resource: string;
  action: string;
  result: 'success' | 'failure' | 'blocked';
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  details: Record<string, any>;
}

export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  config: Record<string, any>;
  position: { x: number; y: number };
  size: { width: number; height: number };
  minSize?: { width: number; height: number };
  maxSize?: { width: number; height: number };
  resizable?: boolean;
  draggable?: boolean;
  static?: boolean;
  data?: any;
  refreshInterval?: number;
  lastRefresh?: string;
}

export interface DashboardLayout {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  responsive?: boolean;
  breakpoints?: Record<string, number>;
  cols?: Record<string, number>;
  rowHeight?: number;
  margin?: [number, number];
  containerPadding?: [number, number];
}

export interface DashboardFilter {
  id: string;
  key: string;
  label: string;
  type: string;
  options?: { label: string; value: any }[];
  defaultValue?: any;
  global?: boolean;
}

export interface DashboardTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  layout: DashboardLayout;
  preview?: string;
  tags: string[];
  popularity: number;
  createdAt: string;
}

export interface Metric {
  id: string;
  name: string;
  value: number;
  unit?: string;
  format?: 'number' | 'percentage' | 'currency' | 'duration';
  trend?: MetricTrend;
  target?: MetricTarget;
  alert?: MetricAlert;
  description?: string;
  category: string;
  tags: string[];
  lastUpdated: string;
}

export interface MetricTrend {
  direction: 'up' | 'down' | 'stable';
  percentage: number;
  period: string;
  sparkline?: number[];
}

export interface MetricTarget {
  value: number;
  type: 'minimum' | 'maximum' | 'exact';
  status: 'met' | 'not-met' | 'exceeded';
}

export interface MetricAlert {
  id: string;
  threshold: number;
  condition: 'above' | 'below' | 'equal';
  severity: 'low' | 'medium' | 'high' | 'critical';
  active: boolean;
  triggered: boolean;
  lastTriggered?: string;
}

export interface MetricFilter {
  id: string;
  key: string;
  label: string;
  type: string;
  options?: { label: string; value: any }[];
}

export interface SessionComparisonColumn {
  id: string;
  key: string;
  title: string;
  type: 'text' | 'number' | 'date' | 'duration' | 'boolean';
  format?: (value: any) => string;
  compare?: boolean;
  highlight?: boolean;
}

export interface SessionFilter {
  id: string;
  key: string;
  label: string;
  type: string;
  options?: { label: string; value: any }[];
}

// Additional utility types
export interface EngagementScope {
  objectives: string[];
  inclusions: string[];
  exclusions: string[];
  constraints: string[];
  successCriteria: string[];
}

export interface EngagementBudget {
  currency: string;
  total: number;
  allocated: Record<string, number>;
  contingency: number;
  approvedBy: string;
  approvedAt: string;
}

export interface Deliverable {
  id: string;
  name: string;
  description: string;
  type: 'document' | 'software' | 'training' | 'service' | 'other';
  status: 'planned' | 'in-progress' | 'completed' | 'cancelled';
  dueDate: string;
  assignee: string;
  dependencies: string[];
  acceptanceCriteria: string[];
}

export interface TimelinePhase {
  id: string;
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  deliverables: string[];
  milestones: Milestone[];
  dependencies: string[];
  resources: Resource[];
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  date: string;
  status: 'upcoming' | 'achieved' | 'missed' | 'cancelled';
  dependencies: string[];
}

export interface Resource {
  id: string;
  type: 'human' | 'equipment' | 'software' | 'facility' | 'other';
  name: string;
  allocation: number;
  startDate: string;
  endDate: string;
  cost?: number;
}

export interface Risk {
  id: string;
  description: string;
  category: 'technical' | 'business' | 'resource' | 'schedule' | 'external';
  probability: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'identified' | 'assessed' | 'mitigated' | 'closed' | 'realized';
  owner: string;
  mitigation: string;
  contingency?: string;
  identifiedAt: string;
  reviewDate?: string;
}

export interface Dependency {
  id: string;
  name: string;
  description: string;
  type: 'internal' | 'external' | 'technical' | 'business';
  status: 'pending' | 'in-progress' | 'resolved' | 'blocked' | 'cancelled';
  owner: string;
  deadline?: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  notes?: string;
}

export interface SmtpSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  encryption: 'none' | 'tls' | 'ssl';
  timeout: number;
}

export interface SmsSettings {
  provider: string;
  apiKey: string;
  fromNumber: string;
  webhook?: string;
}

export interface PushSettings {
  provider: string;
  apiKey: string;
  appId: string;
  webhook?: string;
}

export interface WebhookSettings {
  endpoints: WebhookEndpoint[];
  retryAttempts: number;
  timeout: number;
  authentication: 'none' | 'basic' | 'bearer' | 'apikey';
}

export interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  enabled: boolean;
  secret?: string;
  headers?: Record<string, string>;
}

export interface RateLimitingSettings {
  enabled: boolean;
  requests: number;
  window: number;
  skipSuccessfulRequests: boolean;
  skipFailedRequests: boolean;
  keyGenerator?: string;
}

export interface CorsSettings {
  enabled: boolean;
  origins: string[];
  methods: string[];
  allowedHeaders: string[];
  exposedHeaders: string[];
  credentials: boolean;
  maxAge: number;
}