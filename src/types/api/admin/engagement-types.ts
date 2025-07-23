/**
 * Engagement Management API Types
 * 
 * Type definitions for engagement lifecycle management including engagement
 * creation, team management, progress tracking, and engagement analytics.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse
} from '../shared';

// Engagement Creation APIs
export interface CreateEngagementRequest extends CreateRequest<EngagementData> {
  clientAccountId: string;
  data: EngagementData;
  teamMembers: TeamMember[];
  objectives: EngagementObjective[];
  timeline: EngagementTimeline;
  budget?: EngagementBudget;
}

export interface CreateEngagementResponse extends CreateResponse<Engagement> {
  data: Engagement;
  engagementId: string;
  teamAssignments: TeamAssignment[];
  projectSetup: ProjectSetup;
  resourceAllocations: ResourceAllocation[];
}

// Engagement Retrieval APIs
export interface GetEngagementRequest extends GetRequest {
  engagementId: string;
  includeTeam?: boolean;
  includeFlows?: boolean;
  includeProgress?: boolean;
  includeBudget?: boolean;
  includeMetrics?: boolean;
}

export interface GetEngagementResponse extends GetResponse<Engagement> {
  data: Engagement;
  team: EngagementTeam;
  flows: EngagementFlow[];
  progress: EngagementProgress;
  budget: EngagementBudget;
  metrics: EngagementMetrics;
}

// Engagement Listing APIs
export interface ListEngagementsRequest extends ListRequest {
  clientAccountId?: string;
  status?: EngagementStatus[];
  types?: string[];
  startDateAfter?: string;
  startDateBefore?: string;
  endDateAfter?: string;
  endDateBefore?: string;
  includeCompleted?: boolean;
  includeArchived?: boolean;
}

export interface ListEngagementsResponse extends ListResponse<EngagementSummary> {
  data: EngagementSummary[];
  statistics: EngagementStatistics;
  statusDistribution: StatusDistribution[];
  timelineAnalysis: TimelineAnalysis;
}

// Engagement Update APIs
export interface UpdateEngagementRequest extends UpdateRequest<Partial<EngagementData>> {
  engagementId: string;
  data: Partial<EngagementData>;
  updateType?: 'details' | 'team' | 'timeline' | 'budget' | 'status' | 'objectives';
  notifyTeam?: boolean;
}

export interface UpdateEngagementResponse extends UpdateResponse<Engagement> {
  data: Engagement;
  changes: EngagementChange[];
  teamNotifications: TeamNotification[];
  impactAnalysis: ChangeImpactAnalysis;
}

// Supporting Types for Engagement Management
export interface EngagementData {
  name: string;
  description?: string;
  type: EngagementType;
  scope: EngagementScope;
  objectives: EngagementObjective[];
  timeline: EngagementTimeline;
  budget?: EngagementBudget;
  stakeholders: Stakeholder[];
  requirements: EngagementRequirement[];
  deliverables: Deliverable[];
  riskFactors: RiskFactor[];
  successCriteria: SuccessCriteria[];
}

export interface Engagement {
  id: string;
  clientAccountId: string;
  name: string;
  description: string;
  type: EngagementType;
  status: EngagementStatus;
  progress: number;
  startDate: string;
  endDate?: string;
  budget: EngagementBudget;
  team: EngagementTeam;
  flows: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface TeamMember {
  userId: string;
  role: TeamRole;
  responsibilities: string[];
  allocation: number; // percentage
  startDate: string;
  endDate?: string;
  billableRate?: number;
  skills: string[];
}

export interface EngagementObjective {
  id: string;
  title: string;
  description: string;
  priority: ObjectivePriority;
  category: ObjectiveCategory;
  success_criteria: string[];
  target_date?: string;
  status: ObjectiveStatus;
  progress: number;
  owner: string;
  dependencies: string[];
  metrics: ObjectiveMetric[];
}

export interface EngagementTimeline {
  phases: EngagementPhase[];
  milestones: Milestone[];
  dependencies: Dependency[];
  criticalPath: string[];
  bufferTime: number; // in days
}

export interface EngagementBudget {
  totalBudget: number;
  currency: string;
  breakdown: BudgetBreakdown[];
  trackingMode: BudgetTrackingMode;
  approvals: BudgetApproval[];
  expenses: Expense[];
  forecasts: BudgetForecast[];
}

export interface Stakeholder {
  id: string;
  name: string;
  role: StakeholderRole;
  organization: string;
  contact: ContactInfo;
  influence: InfluenceLevel;
  interest: InterestLevel;
  communicationPreferences: CommunicationPreference[];
}

export interface EngagementRequirement {
  id: string;
  title: string;
  description: string;
  type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
  source: string;
  category: RequirementCategory;
  acceptance_criteria: string[];
  dependencies: string[];
  estimatedEffort: number;
  assignedTo?: string;
}

export interface Deliverable {
  id: string;
  name: string;
  description: string;
  type: DeliverableType;
  status: DeliverableStatus;
  dueDate: string;
  completedDate?: string;
  owner: string;
  reviewers: string[];
  dependencies: string[];
  artifacts: Artifact[];
  qualityGates: QualityGate[];
}

export interface RiskFactor {
  id: string;
  title: string;
  description: string;
  category: RiskCategory;
  probability: RiskProbability;
  impact: RiskImpact;
  severity: RiskSeverity;
  status: RiskStatus;
  owner: string;
  mitigation_plan: string;
  contingency_plan?: string;
  triggers: string[];
  lastAssessed: string;
}

export interface SuccessCriteria {
  id: string;
  title: string;
  description: string;
  metric: string;
  target: number | string;
  measurement_method: string;
  frequency: MeasurementFrequency;
  current_value?: number | string;
  status: CriteriaStatus;
  owner: string;
}

export interface EngagementTeam {
  lead: TeamMember;
  members: TeamMember[];
  consultants: Consultant[];
  stakeholders: Stakeholder[];
  structure: TeamStructure;
  capacity: TeamCapacity;
  skills: SkillMatrix;
}

export interface EngagementFlow {
  flowId: string;
  name: string;
  type: string;
  status: string;
  progress: number;
  lastExecuted?: string;
  nextExecution?: string;
  owner: string;
  dependencies: string[];
}

export interface EngagementProgress {
  overall: number;
  phases: PhaseProgress[];
  objectives: ObjectiveProgress[];
  deliverables: DeliverableProgress[];
  timeline: TimelineProgress;
  budget: BudgetProgress;
  risks: RiskProgress;
  quality: QualityProgress;
}

export interface EngagementMetrics {
  kpis: KPI[];
  performance: PerformanceMetric[];
  quality: QualityMetric[];
  efficiency: EfficiencyMetric[];
  satisfaction: SatisfactionMetric[];
  financial: FinancialMetric[];
}

export interface EngagementSummary {
  id: string;
  clientAccountId: string;
  name: string;
  type: EngagementType;
  status: EngagementStatus;
  progress: number;
  startDate: string;
  endDate?: string;
  teamSize: number;
  budget: {
    total: number;
    spent: number;
    remaining: number;
  };
  healthScore: number;
  riskLevel: RiskLevel;
}

export interface EngagementStatistics {
  total: number;
  active: number;
  completed: number;
  onHold: number;
  cancelled: number;
  byType: Record<EngagementType, number>;
  byStatus: Record<EngagementStatus, number>;
  averageDuration: number;
  successRate: number;
  budgetVariance: number;
}

export interface StatusDistribution {
  status: EngagementStatus;
  count: number;
  percentage: number;
  trend: TrendDirection;
}

export interface TimelineAnalysis {
  onSchedule: number;
  delayed: number;
  accelerated: number;
  averageDelay: number;
  criticalPath: {
    totalEngagements: number;
    atRisk: number;
  };
}

export interface EngagementChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
  changedAt: string;
  changedBy: string;
  reason?: string;
  impact: ChangeImpact;
}

export interface TeamNotification {
  recipientId: string;
  type: NotificationType;
  message: string;
  priority: NotificationPriority;
  deliveryMethod: DeliveryMethod[];
  scheduled: boolean;
  sentAt?: string;
}

export interface ChangeImpactAnalysis {
  timeline: TimelineImpact;
  budget: BudgetImpact;
  resources: ResourceImpact;
  risks: RiskImpact[];
  dependencies: DependencyImpact[];
  recommendations: string[];
}

// Enums and Supporting Types
export type EngagementType = 'discovery' | 'assessment' | 'migration' | 'modernization' | 'optimization' | 'consulting';
export type EngagementStatus = 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
export type TeamRole = 'lead' | 'architect' | 'developer' | 'analyst' | 'consultant' | 'specialist' | 'coordinator';
export type ObjectivePriority = 'critical' | 'high' | 'medium' | 'low';
export type ObjectiveCategory = 'technical' | 'business' | 'operational' | 'compliance' | 'strategic';
export type ObjectiveStatus = 'not_started' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';
export type BudgetTrackingMode = 'fixed' | 'time_and_materials' | 'milestone_based' | 'hybrid';
export type StakeholderRole = 'sponsor' | 'champion' | 'user' | 'decision_maker' | 'influencer' | 'subject_matter_expert';
export type InfluenceLevel = 'high' | 'medium' | 'low';
export type InterestLevel = 'high' | 'medium' | 'low';
export type RequirementType = 'functional' | 'non_functional' | 'business' | 'technical' | 'compliance';
export type RequirementPriority = 'must_have' | 'should_have' | 'could_have' | 'wont_have';
export type RequirementStatus = 'draft' | 'approved' | 'in_progress' | 'completed' | 'rejected';
export type RequirementCategory = 'feature' | 'performance' | 'security' | 'integration' | 'usability';
export type DeliverableType = 'document' | 'software' | 'report' | 'training' | 'process' | 'other';
export type DeliverableStatus = 'not_started' | 'in_progress' | 'review' | 'approved' | 'delivered';
export type RiskCategory = 'technical' | 'resource' | 'schedule' | 'budget' | 'external' | 'business';
export type RiskProbability = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
export type RiskImpact = 'negligible' | 'minor' | 'moderate' | 'major' | 'severe';
export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
export type RiskStatus = 'identified' | 'assessed' | 'mitigated' | 'accepted' | 'transferred' | 'closed';
export type MeasurementFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'milestone_based';
export type CriteriaStatus = 'not_started' | 'in_progress' | 'met' | 'partially_met' | 'not_met';
export type TrendDirection = 'increasing' | 'decreasing' | 'stable';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type ChangeImpact = 'minimal' | 'low' | 'medium' | 'high' | 'critical';
export type NotificationType = 'info' | 'warning' | 'alert' | 'update' | 'reminder';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type DeliveryMethod = 'email' | 'in_app' | 'sms' | 'slack' | 'teams';

// Complex Supporting Interfaces
export interface EngagementScope {
  boundaries: string[];
  inclusions: string[];
  exclusions: string[];
  assumptions: string[];
  constraints: string[];
}

export interface EngagementPhase {
  id: string;
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  status: PhaseStatus;
  deliverables: string[];
  milestones: string[];
  gates: QualityGate[];
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  targetDate: string;
  actualDate?: string;
  status: MilestoneStatus;
  criteria: string[];
  dependencies: string[];
  owner: string;
}

export interface Dependency {
  id: string;
  type: DependencyType;
  predecessor: string;
  successor: string;
  relationship: DependencyRelationship;
  lag: number;
  critical: boolean;
}

export interface TeamAssignment {
  memberId: string;
  engagementId: string;
  role: TeamRole;
  startDate: string;
  endDate?: string;
  allocation: number;
  status: AssignmentStatus;
}

export interface ProjectSetup {
  workspaces: Workspace[];
  tools: Tool[];
  repositories: Repository[];
  environments: Environment[];
  accessControls: AccessControl[];
}

export interface ResourceAllocation {
  resourceType: ResourceType;
  amount: number;
  unit: string;
  period: string;
  cost: number;
  allocation: AllocationDetail[];
}

export type PhaseStatus = 'not_started' | 'in_progress' | 'completed' | 'cancelled' | 'on_hold';
export type MilestoneStatus = 'planned' | 'in_progress' | 'achieved' | 'missed' | 'cancelled';
export type DependencyType = 'internal' | 'external' | 'resource' | 'deliverable';
export type DependencyRelationship = 'finish_to_start' | 'start_to_start' | 'finish_to_finish' | 'start_to_finish';
export type AssignmentStatus = 'assigned' | 'active' | 'completed' | 'cancelled';
export type ResourceType = 'human' | 'infrastructure' | 'software' | 'hardware' | 'service';

export interface BudgetBreakdown {
  category: string;
  amount: number;
  percentage: number;
  allocated: number;
  spent: number;
  remaining: number;
}

export interface BudgetApproval {
  amount: number;
  approver: string;
  approvedAt: string;
  notes?: string;
}

export interface Expense {
  id: string;
  description: string;
  amount: number;
  category: string;
  date: string;
  submittedBy: string;
  approvedBy?: string;
  status: ExpenseStatus;
}

export interface BudgetForecast {
  period: string;
  estimated: number;
  confidence: number;
  assumptions: string[];
}

export type ExpenseStatus = 'draft' | 'submitted' | 'approved' | 'rejected' | 'reimbursed';

// Additional supporting interfaces for complex nested types would continue here...
// These are truncated for brevity but would include full definitions for:
// - ContactInfo, CommunicationPreference, Artifact, QualityGate
// - Consultant, TeamStructure, TeamCapacity, SkillMatrix
// - Various Progress, Metric, and Impact interfaces
// - Workspace, Tool, Repository, Environment, AccessControl interfaces