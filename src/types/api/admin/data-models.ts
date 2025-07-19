/**
 * Admin Data Models and Entities
 * 
 * Shared data types, entities, and supporting models used across
 * admin API modules. Contains common structures and domain models.
 * 
 * Generated with CC for modular admin type organization.
 */

// Core Entity Types that are referenced across multiple modules
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy?: string;
  version: number;
  metadata: Record<string, any>;
}

export interface AuditableEntity extends BaseEntity {
  auditTrail: AuditTrailEntry[];
  lastAuditedAt?: string;
  complianceStatus: ComplianceStatus;
}

export interface SoftDeletableEntity extends BaseEntity {
  deletedAt?: string;
  deletedBy?: string;
  deletionReason?: string;
  isDeleted: boolean;
}

// Shared Supporting Data Types
export interface Address {
  street: string;
  street2?: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  formatted?: string;
  coordinates?: GeographicCoordinates;
}

export interface ContactInfo {
  primaryEmail: string;
  secondaryEmail?: string;
  primaryPhone?: string;
  secondaryPhone?: string;
  website?: string;
  socialMedia?: SocialMediaContact[];
  preferredContactMethod?: ContactMethod;
  address?: Address;
}

export interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  source?: CoordinateSource;
}

export interface SocialMediaContact {
  platform: SocialMediaPlatform;
  handle: string;
  url: string;
  verified: boolean;
}

export interface PersonalInfo {
  firstName: string;
  lastName: string;
  middleName?: string;
  displayName?: string;
  preferredName?: string;
  title?: string;
  suffix?: string;
  dateOfBirth?: string;
  profileImage?: string;
  bio?: string;
  pronouns?: string;
}

export interface ProfessionalInfo {
  title?: string;
  department?: string;
  division?: string;
  manager?: string;
  reports?: string[];
  startDate?: string;
  endDate?: string;
  employeeId?: string;
  location?: string;
  workLocation?: WorkLocationType;
  skills?: Skill[];
  certifications?: Certification[];
  experience?: WorkExperience[];
}

export interface UserPreferences {
  theme: ThemeType;
  language: string;
  locale: string;
  timezone: string;
  dateFormat: DateFormatType;
  timeFormat: TimeFormatType;
  currency: string;
  numberFormat: NumberFormatType;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  accessibility: AccessibilityPreferences;
  dashboard: DashboardPreferences;
}

export interface UserSettings {
  security: UserSecuritySettings;
  communication: CommunicationSettings;
  workflow: WorkflowSettings;
  integration: UserIntegrationSettings;
  data: DataSettings;
  billing: UserBillingSettings;
}

export interface SecuritySettings {
  twoFactorEnabled: boolean;
  twoFactorMethod?: TwoFactorMethod;
  backupCodes?: string[];
  trustedDevices: TrustedDevice[];
  sessionTimeout: number;
  loginAttempts: number;
  lockedUntil?: string;
  lastPasswordChange: string;
  passwordHistory: PasswordHistoryEntry[];
  ipWhitelist?: string[];
  locationTracking: boolean;
  deviceTracking: boolean;
}

export interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  inApp: boolean;
  categories: Record<NotificationCategory, boolean>;
  frequency: NotificationFrequency;
  quietHours?: QuietHours;
  digest: DigestSettings;
}

export interface PrivacyPreferences {
  profileVisibility: VisibilityLevel;
  activityTracking: boolean;
  analyticsOptOut: boolean;
  marketingEmails: boolean;
  dataSharing: DataSharingPreference[];
  cookieConsent: CookieConsentStatus;
  thirdPartyIntegrations: boolean;
}

export interface AccessibilityPreferences {
  screenReader: boolean;
  highContrast: boolean;
  largeText: boolean;
  colorBlindSupport: boolean;
  keyboardNavigation: boolean;
  motionReduced: boolean;
  audioDescriptions: boolean;
  closedCaptions: boolean;
}

export interface DashboardPreferences {
  defaultView: string;
  layout: DashboardLayout;
  widgets: WidgetConfiguration[];
  refreshInterval: number;
  autoRefresh: boolean;
  pinned: string[];
  hidden: string[];
}

// Account and Subscription Related Types
export interface SubscriptionInfo {
  planId: string;
  planName: string;
  tier: AccountTier;
  status: SubscriptionStatus;
  startDate: string;
  endDate?: string;
  renewalDate?: string;
  autoRenew: boolean;
  features: SubscriptionFeature[];
  limits: SubscriptionLimits;
  usage: SubscriptionUsage;
  billing: BillingInfo;
}

export interface SubscriptionFeature {
  featureId: string;
  name: string;
  enabled: boolean;
  limit?: number;
  usage?: number;
  overageAllowed: boolean;
  overageRate?: number;
}

export interface SubscriptionLimits {
  users: LimitConfiguration;
  engagements: LimitConfiguration;
  dataStorage: LimitConfiguration;
  apiCalls: LimitConfiguration;
  integrations: LimitConfiguration;
  customRoles: LimitConfiguration;
  reports: LimitConfiguration;
  workspaces: LimitConfiguration;
}

export interface SubscriptionUsage {
  period: UsagePeriod;
  users: UsageMetric;
  engagements: UsageMetric;
  dataStorage: UsageMetric;
  apiCalls: UsageMetric;
  integrations: UsageMetric;
  reports: UsageMetric;
  lastUpdated: string;
}

export interface BillingInfo {
  customerId: string;
  paymentMethods: PaymentMethod[];
  defaultPaymentMethod?: string;
  billingAddress: Address;
  taxInfo: TaxInformation;
  invoices: Invoice[];
  credits: BillingCredit[];
  discounts: BillingDiscount[];
}

export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  isDefault: boolean;
  details: PaymentMethodDetails;
  expiresAt?: string;
  status: PaymentMethodStatus;
  addedAt: string;
  lastUsed?: string;
}

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

// Audit and Compliance Types
export interface AuditTrailEntry {
  id: string;
  timestamp: string;
  userId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  changes: FieldChange[];
  metadata: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
}

export interface FieldChange {
  field: string;
  oldValue: any;
  newValue: any;
  changeType: ChangeType;
  sensitive: boolean;
  encrypted: boolean;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  requirements: ComplianceRequirement[];
  controls: ComplianceControl[];
  assessments: ComplianceAssessment[];
  status: ComplianceFrameworkStatus;
}

export interface ComplianceRequirement {
  id: string;
  framework: string;
  section: string;
  title: string;
  description: string;
  mandatory: boolean;
  controls: string[];
  evidence: ComplianceEvidence[];
  status: ComplianceRequirementStatus;
}

// System and Configuration Types
export interface SystemConfiguration {
  category: ConfigurationCategory;
  settings: ConfigurationSetting[];
  environment: Environment;
  version: string;
  lastModified: string;
  modifiedBy: string;
  validation: ConfigurationValidation;
}

export interface ConfigurationSetting {
  key: string;
  value: any;
  type: SettingType;
  required: boolean;
  sensitive: boolean;
  description: string;
  validation: SettingValidation;
  dependencies: string[];
  scope: SettingScope;
}

export interface IntegrationConfiguration {
  integrationId: string;
  name: string;
  type: IntegrationType;
  provider: string;
  status: IntegrationStatus;
  configuration: Record<string, any>;
  credentials: IntegrationCredentials;
  endpoints: IntegrationEndpoint[];
  healthCheck: HealthCheckConfiguration;
  monitoring: IntegrationMonitoring;
}

// Enums and Supporting Types
export type ComplianceStatus = 'compliant' | 'non_compliant' | 'pending' | 'not_applicable';
export type ContactMethod = 'email' | 'phone' | 'sms' | 'chat' | 'video' | 'in_person';
export type CoordinateSource = 'gps' | 'ip_lookup' | 'manual' | 'geocoded';
export type SocialMediaPlatform = 'linkedin' | 'twitter' | 'facebook' | 'instagram' | 'github' | 'youtube';
export type WorkLocationType = 'office' | 'remote' | 'hybrid' | 'field' | 'client_site';
export type ThemeType = 'light' | 'dark' | 'auto' | 'high_contrast';
export type DateFormatType = 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD' | 'DD MMM YYYY';
export type TimeFormatType = '12h' | '24h';
export type NumberFormatType = 'US' | 'EU' | 'UK' | 'IN' | 'custom';
export type TwoFactorMethod = 'totp' | 'sms' | 'email' | 'hardware_key' | 'biometric';
export type NotificationCategory = 'security' | 'billing' | 'engagement' | 'system' | 'marketing' | 'support';
export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'monthly';
export type VisibilityLevel = 'public' | 'internal' | 'team' | 'private';
export type CookieConsentStatus = 'necessary' | 'functional' | 'analytics' | 'marketing' | 'all' | 'none';
export type DashboardLayout = 'grid' | 'list' | 'kanban' | 'timeline' | 'custom';
export type AccountTier = 'free' | 'basic' | 'professional' | 'enterprise' | 'custom';
export type SubscriptionStatus = 'active' | 'trial' | 'past_due' | 'cancelled' | 'paused' | 'expired';
export type PaymentMethodType = 'credit_card' | 'debit_card' | 'bank_transfer' | 'paypal' | 'cryptocurrency';
export type PaymentMethodStatus = 'active' | 'expired' | 'suspended' | 'invalid';
export type StakeholderRole = 'sponsor' | 'champion' | 'user' | 'decision_maker' | 'influencer' | 'sme';
export type InfluenceLevel = 'high' | 'medium' | 'low';
export type InterestLevel = 'high' | 'medium' | 'low';
export type ChangeType = 'create' | 'update' | 'delete' | 'restore' | 'archive' | 'merge';
export type ComplianceFrameworkStatus = 'active' | 'deprecated' | 'draft' | 'archived';
export type ComplianceRequirementStatus = 'met' | 'not_met' | 'partial' | 'not_applicable' | 'pending';
export type ConfigurationCategory = 'security' | 'performance' | 'integration' | 'ui' | 'business' | 'compliance';
export type SettingType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'secret';
export type SettingScope = 'global' | 'tenant' | 'user' | 'session';
export type IntegrationType = 'api' | 'webhook' | 'sso' | 'data_sync' | 'notification' | 'analytics';
export type IntegrationStatus = 'active' | 'inactive' | 'error' | 'pending' | 'suspended';
export type Environment = 'production' | 'staging' | 'development' | 'testing' | 'sandbox';

// Complex Supporting Interfaces
export interface TrustedDevice {
  deviceId: string;
  name: string;
  type: DeviceType;
  fingerprint: string;
  firstSeen: string;
  lastSeen: string;
  trusted: boolean;
  location?: GeographicCoordinates;
  userAgent: string;
}

export interface PasswordHistoryEntry {
  hashedPassword: string;
  changedAt: string;
  strength: PasswordStrength;
  method: PasswordChangeMethod;
}

export interface QuietHours {
  enabled: boolean;
  startTime: string;
  endTime: string;
  timezone: string;
  days: DayOfWeek[];
  exceptions: QuietHoursException[];
}

export interface DigestSettings {
  enabled: boolean;
  frequency: DigestFrequency;
  time: string;
  timezone: string;
  categories: NotificationCategory[];
  maxItems: number;
}

export interface DataSharingPreference {
  partner: string;
  dataTypes: string[];
  purpose: string;
  consent: boolean;
  consentDate: string;
  expiryDate?: string;
}

export interface WidgetConfiguration {
  widgetId: string;
  type: WidgetType;
  position: WidgetPosition;
  size: WidgetSize;
  configuration: Record<string, any>;
  visible: boolean;
  minimized: boolean;
}

export interface LimitConfiguration {
  limit: number;
  soft_limit?: number;
  unit: string;
  period?: string;
  overageAllowed: boolean;
  overageRate?: number;
}

export interface UsageMetric {
  current: number;
  limit: number;
  unit: string;
  percentage: number;
  trend: TrendDirection;
  projectedExhaustion?: string;
}

export interface UsagePeriod {
  start: string;
  end: string;
  type: PeriodType;
  current: boolean;
}

export interface PaymentMethodDetails {
  // Credit Card Details
  lastFour?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  fingerprint?: string;
  
  // Bank Account Details
  bankName?: string;
  accountType?: string;
  routingNumber?: string;
  
  // Digital Wallet Details
  walletType?: string;
  walletEmail?: string;
  
  // Common Details
  billingAddress?: Address;
  metadata?: Record<string, any>;
}

export interface TaxInformation {
  taxId?: string;
  vatNumber?: string;
  taxExempt: boolean;
  taxType: TaxType;
  jurisdiction: string;
  rates: TaxRate[];
}

export interface Invoice {
  id: string;
  number: string;
  status: InvoiceStatus;
  amount: number;
  currency: string;
  issuedAt: string;
  dueAt: string;
  paidAt?: string;
  items: InvoiceItem[];
  taxes: InvoiceTax[];
  discounts: InvoiceDiscount[];
  payments: InvoicePayment[];
  downloadUrl?: string;
}

export interface BillingCredit {
  id: string;
  amount: number;
  currency: string;
  source: CreditSource;
  reason: string;
  appliedAt?: string;
  expiresAt?: string;
  metadata: Record<string, any>;
}

export interface BillingDiscount {
  id: string;
  code?: string;
  type: DiscountType;
  amount: number;
  percentage?: number;
  appliedAt: string;
  expiresAt?: string;
  restrictions?: DiscountRestriction[];
}

export interface Skill {
  name: string;
  category: SkillCategory;
  level: SkillLevel;
  verified: boolean;
  endorsements: SkillEndorsement[];
  certifications: string[];
  lastUsed?: string;
}

export interface Certification {
  name: string;
  issuer: string;
  issuedDate: string;
  expiryDate?: string;
  credentialId?: string;
  verificationUrl?: string;
  status: CertificationStatus;
}

export interface WorkExperience {
  company: string;
  title: string;
  startDate: string;
  endDate?: string;
  current: boolean;
  description?: string;
  skills: string[];
  achievements: string[];
}

export interface UserSecuritySettings {
  twoFactor: TwoFactorSettings;
  sessions: SessionSettings;
  privacy: SecurityPrivacySettings;
  access: AccessSettings;
}

export interface CommunicationSettings {
  channels: CommunicationChannelSettings[];
  preferences: CommunicationPreferences;
  boundaries: CommunicationBoundaries;
}

export interface WorkflowSettings {
  automation: AutomationSettings;
  approvals: ApprovalSettings;
  notifications: WorkflowNotificationSettings;
  integrations: WorkflowIntegrationSettings;
}

// Additional enums and supporting types
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'smartwatch' | 'tv' | 'other';
export type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong' | 'very_strong';
export type PasswordChangeMethod = 'user_initiated' | 'admin_reset' | 'forced_expiry' | 'security_incident';
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
export type DigestFrequency = 'daily' | 'weekly' | 'monthly';
export type WidgetType = 'chart' | 'metric' | 'list' | 'table' | 'calendar' | 'map' | 'feed' | 'custom';
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile';
export type PeriodType = 'monthly' | 'quarterly' | 'yearly' | 'billing_cycle';
export type TaxType = 'vat' | 'gst' | 'sales_tax' | 'withholding' | 'other';
export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
export type CreditSource = 'refund' | 'promotional' | 'error_correction' | 'goodwill' | 'migration';
export type DiscountType = 'percentage' | 'fixed_amount' | 'buy_x_get_y' | 'shipping' | 'trial_extension';
export type SkillCategory = 'technical' | 'business' | 'creative' | 'communication' | 'leadership' | 'analytical';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert' | 'master';
export type CertificationStatus = 'active' | 'expired' | 'suspended' | 'revoked' | 'pending';

// Additional complex supporting interfaces would continue here...
// These provide the foundation for the shared data models across all admin modules

export interface WidgetPosition {
  x: number;
  y: number;
  row?: number;
  column?: number;
}

export interface WidgetSize {
  width: number;
  height: number;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
}

export interface TaxRate {
  type: TaxType;
  rate: number;
  jurisdiction: string;
  effective_date: string;
  expiry_date?: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  taxable: boolean;
  periodStart?: string;
  periodEnd?: string;
}

export interface InvoiceTax {
  type: TaxType;
  rate: number;
  amount: number;
  jurisdiction: string;
}

export interface InvoiceDiscount {
  code?: string;
  description: string;
  amount: number;
  type: DiscountType;
}

export interface InvoicePayment {
  id: string;
  amount: number;
  method: PaymentMethodType;
  paidAt: string;
  reference?: string;
  status: PaymentStatus;
}

export interface SkillEndorsement {
  endorserId: string;
  endorserName: string;
  endorsedAt: string;
  relationship: EndorsementRelationship;
  verified: boolean;
}

export interface QuietHoursException {
  date: string;
  reason: string;
  override: boolean;
}

export interface DiscountRestriction {
  type: RestrictionType;
  value: any;
  message: string;
}

export interface TwoFactorSettings {
  enabled: boolean;
  method: TwoFactorMethod;
  backupCodes: BackupCodeSettings;
  trustedDevices: TrustedDeviceSettings;
}

export interface SessionSettings {
  timeout: number;
  maxConcurrent: number;
  rememberDevice: boolean;
  logoutOnClose: boolean;
}

export interface SecurityPrivacySettings {
  profileVisibility: VisibilityLevel;
  activityLogging: boolean;
  dataSharing: boolean;
  locationTracking: boolean;
}

export interface AccessSettings {
  ipRestrictions: IpRestriction[];
  timeRestrictions: TimeRestriction[];
  locationRestrictions: LocationRestriction[];
}

export interface CommunicationChannelSettings {
  channel: ContactMethod;
  enabled: boolean;
  priority: number;
  address: string;
  verified: boolean;
}

export interface CommunicationPreferences {
  defaultChannel: ContactMethod;
  urgentChannel: ContactMethod;
  language: string;
  tone: CommunicationTone;
}

export interface CommunicationBoundaries {
  quietHours: QuietHours;
  doNotDisturb: boolean;
  emergency_override: boolean;
  vacation_mode: boolean;
}

// Additional enums
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded' | 'disputed';
export type EndorsementRelationship = 'colleague' | 'manager' | 'client' | 'subordinate' | 'peer' | 'other';
export type RestrictionType = 'user_tier' | 'usage_limit' | 'time_limit' | 'geographic' | 'feature_access';
export type CommunicationTone = 'formal' | 'casual' | 'friendly' | 'professional' | 'concise';

// Complex settings interfaces (would be fully implemented)
export interface BackupCodeSettings {
  generated: boolean;
  count: number;
  used: number;
  lastRegenerated?: string;
}

export interface TrustedDeviceSettings {
  enabled: boolean;
  maxDevices: number;
  trustDuration: number;
  requireReauth: boolean;
}

export interface IpRestriction {
  cidr: string;
  description?: string;
  whitelist: boolean;
}

export interface TimeRestriction {
  startTime: string;
  endTime: string;
  days: DayOfWeek[];
  timezone: string;
}

export interface LocationRestriction {
  countries: string[];
  regions?: string[];
  whitelist: boolean;
}

// Placeholder interfaces for complex workflow settings
export interface AutomationSettings { /* automation configuration */ }
export interface ApprovalSettings { /* approval workflow settings */ }
export interface WorkflowNotificationSettings { /* workflow notification configuration */ }
export interface WorkflowIntegrationSettings { /* workflow integration settings */ }
export interface UserIntegrationSettings { /* user integration preferences */ }
export interface DataSettings { /* data management settings */ }
export interface UserBillingSettings { /* user billing preferences */ }

// Engagement-specific supporting types
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

// System configuration supporting types
export interface SettingValidation {
  required: boolean;
  type: SettingType;
  min?: number;
  max?: number;
  pattern?: string;
  allowed_values?: any[];
  custom_validator?: string;
}

export interface ConfigurationValidation {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  dependencies_satisfied: boolean;
}

export interface IntegrationCredentials {
  type: CredentialType;
  encrypted: boolean;
  fields: CredentialField[];
  expires_at?: string;
  last_rotated?: string;
}

export interface IntegrationEndpoint {
  name: string;
  url: string;
  method: HttpMethod;
  authentication: EndpointAuthentication;
  rate_limit?: RateLimit;
  timeout: number;
  retry_policy: RetryPolicy;
}

export interface HealthCheckConfiguration {
  enabled: boolean;
  interval: number;
  timeout: number;
  retry_count: number;
  endpoint: string;
  expected_status: number[];
  failure_threshold: number;
}

export interface IntegrationMonitoring {
  metrics: MonitoringMetric[];
  alerts: MonitoringAlert[];
  logs: LogConfiguration;
  tracing: TracingConfiguration;
}

export interface ComplianceEvidence {
  type: EvidenceType;
  description: string;
  location: string;
  collected_at: string;
  collected_by: string;
  hash?: string;
  verified: boolean;
}

export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  type: ControlType;
  frequency: ControlFrequency;
  owner: string;
  automated: boolean;
  evidence_required: EvidenceType[];
  last_tested?: string;
  status: ControlStatus;
}

export interface ComplianceAssessment {
  id: string;
  framework: string;
  assessor: string;
  assessment_date: string;
  scope: string[];
  findings: AssessmentFinding[];
  recommendations: AssessmentRecommendation[];
  score: number;
  status: AssessmentStatus;
}

// Additional enums for complex types
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
export type CredentialType = 'api_key' | 'oauth' | 'basic_auth' | 'certificate' | 'token' | 'custom';
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
export type EvidenceType = 'document' | 'screenshot' | 'log_file' | 'video' | 'testimony' | 'system_output';
export type ControlType = 'preventive' | 'detective' | 'corrective' | 'compensating';
export type ControlFrequency = 'continuous' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annually';
export type ControlStatus = 'effective' | 'ineffective' | 'not_tested' | 'exception' | 'remediation_required';
export type AssessmentStatus = 'planned' | 'in_progress' | 'completed' | 'approved' | 'rejected';

// Additional complex supporting interfaces would be defined here for completeness...
// These provide comprehensive data models for all admin functionality