/**
 * Engagement and Project Management Types
 * 
 * Project scope, timeline, budget, stakeholder management,
 * and engagement-specific data structures.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { ContactInfo, Address } from './base-entities';
import type { ContactMethod, DayOfWeek } from './enums';

// Engagement and Project Related Types
export interface EngagementScope {
  boundaries: string[];
  inclusions: string[];
  exclusions: string[];
  assumptions: string[];
  constraints: string[];
  dependencies: ScopeDependency[];
  risks: ScopeRisk[];
}

export interface EngagementTimeline {
  phases: EngagementPhase[];
  milestones: Milestone[];
  dependencies: TaskDependency[];
  criticalPath: string[];
  bufferTime: number;
  workingCalendar: WorkingCalendar;
}

export interface EngagementBudget {
  totalBudget: number;
  currency: string;
  allocations: BudgetAllocation[];
  tracking: BudgetTracking;
  approvals: BudgetApproval[];
  expenses: Expense[];
  forecasts: BudgetForecast[];
  variance: BudgetVariance;
}

export interface Stakeholder {
  id: string;
  name: string;
  role: StakeholderRole;
  organization: string;
  contact: ContactInfo;
  influence: InfluenceLevel;
  interest: InterestLevel;
  expectations: string[];
  communicationPlan: CommunicationPlan;
  escalationPath: EscalationPath[];
}

// Scope and dependency management
export interface ScopeDependency {
  type: DependencyType;
  description: string;
  impact: ImpactLevel;
  mitigation: string;
}

export interface ScopeRisk {
  description: string;
  probability: RiskProbability;
  impact: RiskImpact;
  mitigation: string;
}

// Project phases and milestones
export interface EngagementPhase {
  id: string;
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  status: PhaseStatus;
  deliverables: string[];
  milestones: string[];
  dependencies: string[];
  resources: ResourceRequirement[];
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  targetDate: string;
  actualDate?: string;
  status: MilestoneStatus;
  criteria: MilestoneCriteria[];
  dependencies: string[];
  owner: string;
}

export interface TaskDependency {
  id: string;
  type: DependencyType;
  predecessor: string;
  successor: string;
  relationship: DependencyRelationship;
  lag: number;
  critical: boolean;
}

export interface WorkingCalendar {
  workingDays: DayOfWeek[];
  workingHours: WorkingHours;
  holidays: Holiday[];
  exceptions: CalendarException[];
  timezone: string;
}

// Budget management
export interface BudgetAllocation {
  category: BudgetCategory;
  amount: number;
  percentage: number;
  description: string;
  owner: string;
}

export interface BudgetTracking {
  method: BudgetTrackingMethod;
  frequency: TrackingFrequency;
  variance_threshold: number;
  approval_required: boolean;
}

export interface BudgetApproval {
  amount: number;
  approver: string;
  level: ApprovalLevel;
  approvedAt: string;
  notes?: string;
  conditions?: string[];
}

export interface Expense {
  id: string;
  description: string;
  amount: number;
  category: BudgetCategory;
  date: string;
  submittedBy: string;
  approvedBy?: string;
  status: ExpenseStatus;
  receipts: ExpenseReceipt[];
  metadata: Record<string, any>;
}

export interface BudgetForecast {
  period: string;
  categories: BudgetCategoryForecast[];
  total_estimated: number;
  confidence: ConfidenceLevel;
  assumptions: string[];
  risks: ForecastRisk[];
}

export interface BudgetVariance {
  planned: number;
  actual: number;
  variance: number;
  variance_percentage: number;
  explanation?: string;
  corrective_actions?: string[];
}

// Stakeholder communication
export interface CommunicationPlan {
  frequency: CommunicationFrequency;
  methods: ContactMethod[];
  templates: string[];
  escalation_triggers: string[];
  reporting_schedule: ReportingSchedule[];
}

export interface EscalationPath {
  level: number;
  contact: string;
  trigger_conditions: string[];
  timeframe: string;
  notification_method: ContactMethod;
}

// Supporting interfaces
// Supporting interfaces moved to supporting-types.ts to avoid duplicates

// Engagement and project enums
export type StakeholderRole = 'sponsor' | 'champion' | 'user' | 'decision_maker' | 'influencer' | 'sme';
export type InfluenceLevel = 'high' | 'medium' | 'low';
export type InterestLevel = 'high' | 'medium' | 'low';
export type DependencyType = 'finish_to_start' | 'start_to_start' | 'finish_to_finish' | 'start_to_finish';
export type ImpactLevel = 'low' | 'medium' | 'high' | 'critical';
export type RiskProbability = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
export type RiskImpact = 'negligible' | 'minor' | 'moderate' | 'major' | 'severe';
export type PhaseStatus = 'not_started' | 'in_progress' | 'completed' | 'on_hold' | 'cancelled';
export type MilestoneStatus = 'planned' | 'in_progress' | 'achieved' | 'missed' | 'cancelled';
export type DependencyRelationship = 'blocks' | 'enables' | 'informs' | 'requires';
export type BudgetCategory = 'personnel' | 'infrastructure' | 'software' | 'training' | 'travel' | 'other';
export type BudgetTrackingMethod = 'time_based' | 'milestone_based' | 'deliverable_based' | 'hybrid';
export type TrackingFrequency = 'daily' | 'weekly' | 'monthly' | 'per_milestone';
export type ApprovalLevel = 'team_lead' | 'project_manager' | 'department_head' | 'executive' | 'board';
export type ExpenseStatus = 'draft' | 'submitted' | 'approved' | 'rejected' | 'reimbursed';
export type ConfidenceLevel = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
export type CommunicationFrequency = 'daily' | 'weekly' | 'bi_weekly' | 'monthly' | 'quarterly' | 'as_needed';
export type ResourceType = 'human' | 'equipment' | 'software' | 'facility' | 'service' | 'material';
export type HolidayType = 'public' | 'company' | 'personal' | 'religious' | 'cultural';
export type ExceptionType = 'holiday' | 'overtime' | 'half_day' | 'closure' | 'special_hours';
export type ReportFormat = 'pdf' | 'excel' | 'powerpoint' | 'html' | 'json' | 'csv';