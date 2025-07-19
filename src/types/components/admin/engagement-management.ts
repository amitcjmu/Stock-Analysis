/**
 * Admin Engagement Management Component Types
 * 
 * Type definitions for engagement management components including engagement lists,
 * engagement creation workflows, and engagement filtering systems.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

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

// Supporting types for Engagement Management
export interface Engagement {
  id: string;
  name: string;
  description?: string;
  clientId: string;
  client: Client;
  status: EngagementStatus;
  type: EngagementType;
  startDate: string;
  endDate?: string;
  budget?: number;
  currency?: string;
  team: TeamMember[];
  lead: User;
  progress: number;
  phases: EngagementPhase[];
  deliverables: Deliverable[];
  milestones: Milestone[];
  risks: Risk[];
  issues: Issue[];
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface EngagementListPaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
}

export interface EngagementAction {
  id: string;
  label: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'danger' | 'warning';
  disabled?: boolean;
  visible?: boolean;
  permissions?: string[];
  onClick: (engagement: Engagement) => void;
}

export interface EngagementBulkAction {
  id: string;
  label: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'danger' | 'warning';
  disabled?: boolean;
  visible?: boolean;
  permissions?: string[];
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  onClick: (engagements: Engagement[]) => void;
}

export interface EngagementTableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  render?: (value: any, engagement: Engagement, index: number) => ReactNode;
  filterType?: 'text' | 'select' | 'date' | 'number' | 'boolean';
  filterOptions?: FilterOption[];
}

export interface EngagementFilter {
  key: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number' | 'boolean' | 'multiselect';
  options?: FilterOption[];
  value?: any;
  placeholder?: string;
  validation?: ValidationRule[];
}

export interface EngagementSortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

export interface CreateEngagementRequest {
  name: string;
  description?: string;
  clientId: string;
  type: EngagementType;
  startDate: string;
  endDate?: string;
  budget?: number;
  currency?: string;
  leadId: string;
  teamIds: string[];
  templateId?: string;
  phases?: CreateEngagementPhase[];
  deliverables?: CreateDeliverable[];
  milestones?: CreateMilestone[];
  metadata?: Record<string, any>;
}

export interface EngagementTemplate {
  id: string;
  name: string;
  description?: string;
  type: EngagementType;
  phases: EngagementPhaseTemplate[];
  deliverables: DeliverableTemplate[];
  milestones: MilestoneTemplate[];
  estimatedDuration: number;
  estimatedBudget?: number;
  skillsRequired: string[];
  tags: string[];
  createdBy: string;
  createdAt: string;
  isActive: boolean;
}

export interface EngagementCreationStep {
  id: string;
  title: string;
  description?: string;
  fields: EngagementField[];
  validation?: StepValidationRule[];
  optional?: boolean;
  order: number;
}

export interface EngagementValidationConfig {
  validateOnBlur?: boolean;
  validateOnChange?: boolean;
  showValidationSummary?: boolean;
  stopOnFirstError?: boolean;
  customValidators?: Record<string, (value: any) => boolean | string>;
}

export interface Client {
  id: string;
  name: string;
  industry: string;
  size: CompanySize;
  location: string;
  contactPerson: string;
  email: string;
  phone?: string;
  status: ClientStatus;
  createdAt: string;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  lead: User;
  members: TeamMember[];
  skills: string[];
  department: string;
  isActive: boolean;
}

export interface TeamMember {
  userId: string;
  user: User;
  role: string;
  responsibilities: string[];
  allocation: number;
  startDate: string;
  endDate?: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  title: string;
  department: string;
  skills: string[];
  availability: number;
  status: UserStatus;
}

export interface EngagementPhase {
  id: string;
  name: string;
  description?: string;
  order: number;
  startDate: string;
  endDate?: string;
  status: PhaseStatus;
  progress: number;
  dependencies: string[];
  deliverables: string[];
  budget?: number;
  team: TeamMember[];
}

export interface CreateEngagementPhase {
  name: string;
  description?: string;
  order: number;
  startDate: string;
  endDate?: string;
  dependencies?: string[];
  deliverableIds?: string[];
  budget?: number;
  teamIds?: string[];
}

export interface EngagementPhaseTemplate {
  id: string;
  name: string;
  description?: string;
  order: number;
  estimatedDuration: number;
  dependencies: string[];
  deliverables: string[];
  skillsRequired: string[];
}

export interface Deliverable {
  id: string;
  name: string;
  description?: string;
  type: DeliverableType;
  status: DeliverableStatus;
  dueDate: string;
  assigneeId: string;
  assignee: User;
  phaseId: string;
  dependencies: string[];
  artifacts: Artifact[];
  reviewers: User[];
  approvers: User[];
}

export interface CreateDeliverable {
  name: string;
  description?: string;
  type: DeliverableType;
  dueDate: string;
  assigneeId: string;
  phaseId?: string;
  dependencies?: string[];
  reviewerIds?: string[];
  approverIds?: string[];
}

export interface DeliverableTemplate {
  id: string;
  name: string;
  description?: string;
  type: DeliverableType;
  estimatedEffort: number;
  skillsRequired: string[];
  dependencies: string[];
  templates: DocumentTemplate[];
}

export interface Milestone {
  id: string;
  name: string;
  description?: string;
  dueDate: string;
  status: MilestoneStatus;
  criteria: MilestoneCriteria[];
  dependencies: string[];
  deliverables: string[];
  stakeholders: User[];
}

export interface CreateMilestone {
  name: string;
  description?: string;
  dueDate: string;
  criteria: CreateMilestoneCriteria[];
  dependencies?: string[];
  deliverableIds?: string[];
  stakeholderIds?: string[];
}

export interface MilestoneTemplate {
  id: string;
  name: string;
  description?: string;
  estimatedDuration: number;
  criteria: MilestoneCriteriaTemplate[];
  dependencies: string[];
  deliverables: string[];
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

export interface EngagementField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'currency' | 'boolean' | 'user' | 'team' | 'client';
  required?: boolean;
  options?: FieldOption[];
  validation?: ValidationRule[];
  placeholder?: string;
  helpText?: string;
  dependencies?: FieldDependency[];
}

export interface StepValidationRule {
  fields: string[];
  rule: (values: Record<string, any>) => boolean | string;
  message: string;
}

// Additional supporting types
export interface Risk {
  id: string;
  title: string;
  description: string;
  probability: number;
  impact: number;
  severity: RiskSeverity;
  status: RiskStatus;
  mitigation: string;
  owner: User;
  dueDate?: string;
}

export interface Issue {
  id: string;
  title: string;
  description: string;
  priority: IssuePriority;
  status: IssueStatus;
  assignee: User;
  reporter: User;
  dueDate?: string;
  resolution?: string;
}

export interface Artifact {
  id: string;
  name: string;
  type: string;
  url: string;
  size: number;
  version: string;
  uploadedBy: string;
  uploadedAt: string;
}

export interface MilestoneCriteria {
  id: string;
  description: string;
  met: boolean;
  evidence?: string;
  verifiedBy?: string;
  verifiedAt?: string;
}

export interface CreateMilestoneCriteria {
  description: string;
  evidence?: string;
}

export interface MilestoneCriteriaTemplate {
  id: string;
  description: string;
  required: boolean;
  order: number;
}

export interface DocumentTemplate {
  id: string;
  name: string;
  description?: string;
  url: string;
  type: string;
  category: string;
}

export interface FieldOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
}

export interface FieldDependency {
  field: string;
  value: any;
  operation: 'equals' | 'not_equals' | 'in' | 'not_in';
}

export interface ValidationRule {
  type: 'required' | 'email' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface FilterOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
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

// Enum types
export type EngagementStatus = 'draft' | 'active' | 'on_hold' | 'completed' | 'cancelled';
export type EngagementType = 'discovery' | 'assessment' | 'migration' | 'optimization' | 'support' | 'training';
export type PhaseStatus = 'not_started' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled';
export type DeliverableType = 'document' | 'presentation' | 'code' | 'design' | 'analysis' | 'report';
export type DeliverableStatus = 'not_started' | 'in_progress' | 'review' | 'approved' | 'delivered';
export type MilestoneStatus = 'pending' | 'achieved' | 'missed' | 'cancelled';
export type CompanySize = 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
export type ClientStatus = 'prospect' | 'active' | 'inactive' | 'former';
export type UserStatus = 'active' | 'inactive' | 'pending' | 'blocked';
export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
export type RiskStatus = 'open' | 'mitigating' | 'closed' | 'accepted';
export type IssuePriority = 'low' | 'medium' | 'high' | 'urgent';
export type IssueStatus = 'open' | 'in_progress' | 'resolved' | 'closed';