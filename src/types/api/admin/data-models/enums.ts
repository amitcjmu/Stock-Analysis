/**
 * Shared Enums and Type Literals
 * 
 * Centralized enumeration definitions and type literals used across
 * admin data models to ensure consistency and type safety.
 * 
 * Generated with CC for modular admin type organization.
 */

// Core enum types used across multiple modules
export type ComplianceStatus = 'compliant' | 'non_compliant' | 'pending' | 'not_applicable';
export type ContactMethod = 'email' | 'phone' | 'sms' | 'chat' | 'video' | 'in_person';
export type CoordinateSource = 'gps' | 'ip_lookup' | 'manual' | 'geocoded';
export type SocialMediaPlatform = 'linkedin' | 'twitter' | 'facebook' | 'instagram' | 'github' | 'youtube';
export type WorkLocationType = 'office' | 'remote' | 'hybrid' | 'field' | 'client_site';
export type ChangeType = 'create' | 'update' | 'delete' | 'restore' | 'archive' | 'merge';

// User and profile related enums
export type ThemeType = 'light' | 'dark' | 'auto' | 'high_contrast';
export type DateFormatType = 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD' | 'DD MMM YYYY';
export type TimeFormatType = '12h' | '24h';
export type NumberFormatType = 'US' | 'EU' | 'UK' | 'IN' | 'custom';
export type VisibilityLevel = 'public' | 'internal' | 'team' | 'private';
export type DashboardLayout = 'grid' | 'list' | 'kanban' | 'timeline' | 'custom';

// Security and authentication enums
export type TwoFactorMethod = 'totp' | 'sms' | 'email' | 'hardware_key' | 'biometric';
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'smartwatch' | 'tv' | 'other';
export type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong' | 'very_strong';
export type PasswordChangeMethod = 'user_initiated' | 'admin_reset' | 'forced_expiry' | 'security_incident';

// Notification and communication enums
export type NotificationCategory = 'security' | 'billing' | 'engagement' | 'system' | 'marketing' | 'support';
export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'monthly';
export type CookieConsentStatus = 'necessary' | 'functional' | 'analytics' | 'marketing' | 'all' | 'none';
export type DigestFrequency = 'daily' | 'weekly' | 'monthly';
export type CommunicationTone = 'formal' | 'casual' | 'friendly' | 'professional' | 'concise';

// Time and calendar enums
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

// Widget and dashboard enums
export type WidgetType = 'chart' | 'metric' | 'list' | 'table' | 'calendar' | 'map' | 'feed' | 'custom';

// Account and subscription enums
export type AccountTier = 'free' | 'basic' | 'professional' | 'enterprise' | 'custom';
export type SubscriptionStatus = 'active' | 'trial' | 'past_due' | 'cancelled' | 'paused' | 'expired';
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile';
export type PeriodType = 'monthly' | 'quarterly' | 'yearly' | 'billing_cycle';

// Payment and billing enums
export type PaymentMethodType = 'credit_card' | 'debit_card' | 'bank_transfer' | 'paypal' | 'cryptocurrency';
export type PaymentMethodStatus = 'active' | 'expired' | 'suspended' | 'invalid';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded' | 'disputed';
export type TaxType = 'vat' | 'gst' | 'sales_tax' | 'withholding' | 'other';
export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
export type CreditSource = 'refund' | 'promotional' | 'error_correction' | 'goodwill' | 'migration';
export type DiscountType = 'percentage' | 'fixed_amount' | 'buy_x_get_y' | 'shipping' | 'trial_extension';
export type RestrictionType = 'user_tier' | 'usage_limit' | 'time_limit' | 'geographic' | 'feature_access';

// Skills and professional enums
export type SkillCategory = 'technical' | 'business' | 'creative' | 'communication' | 'leadership' | 'analytical';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert' | 'master';
export type CertificationStatus = 'active' | 'expired' | 'suspended' | 'revoked' | 'pending';
export type EndorsementRelationship = 'colleague' | 'manager' | 'client' | 'subordinate' | 'peer' | 'other';

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

// Compliance and security enums
export type ComplianceFrameworkStatus = 'active' | 'deprecated' | 'draft' | 'archived';
export type ComplianceRequirementStatus = 'met' | 'not_met' | 'partial' | 'not_applicable' | 'pending';
export type ControlType = 'preventive' | 'detective' | 'corrective' | 'compensating';
export type ControlFrequency = 'continuous' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annually';
export type ControlStatus = 'effective' | 'ineffective' | 'not_tested' | 'exception' | 'remediation_required';
export type AssessmentStatus = 'planned' | 'in_progress' | 'completed' | 'approved' | 'rejected';
export type EvidenceType = 'document' | 'screenshot' | 'log_file' | 'video' | 'testimony' | 'system_output';
export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type FindingStatus = 'open' | 'in_progress' | 'resolved' | 'accepted_risk' | 'false_positive';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low';
export type RecommendationStatus = 'pending' | 'in_progress' | 'implemented' | 'deferred' | 'rejected';

// System configuration enums
export type ConfigurationCategory = 'security' | 'performance' | 'integration' | 'ui' | 'business' | 'compliance';
export type SettingType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'secret';
export type SettingScope = 'global' | 'tenant' | 'user' | 'session';
export type IntegrationType = 'api' | 'webhook' | 'sso' | 'data_sync' | 'notification' | 'analytics';
export type IntegrationStatus = 'active' | 'inactive' | 'error' | 'pending' | 'suspended';
export type Environment = 'production' | 'staging' | 'development' | 'testing' | 'sandbox';
export type CredentialType = 'api_key' | 'oauth' | 'basic_auth' | 'certificate' | 'token' | 'custom';
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
export type ValidationSeverity = 'error' | 'warning' | 'info';
export type CredentialFieldType = 'text' | 'password' | 'email' | 'url' | 'number' | 'boolean' | 'file';
export type AuthenticationType = 'none' | 'basic' | 'bearer' | 'oauth2' | 'api_key' | 'custom';
export type BackoffStrategy = 'fixed' | 'exponential' | 'linear' | 'custom';
export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary';
export type AggregationMethod = 'sum' | 'average' | 'min' | 'max' | 'count' | 'percentile';
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type LogFormat = 'json' | 'text' | 'structured' | 'custom';
export type ComparisonOperator = 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'ne';
export type ChannelType = 'email' | 'slack' | 'webhook' | 'sms' | 'pagerduty' | 'teams';
export type LogDestinationType = 'file' | 'console' | 'syslog' | 'elasticsearch' | 'cloudwatch' | 'custom';
export type TracingExporterType = 'jaeger' | 'zipkin' | 'otlp' | 'console' | 'custom';

// Additional enums that may be missing
export type BudgetCategory = 'personnel' | 'infrastructure' | 'software' | 'training' | 'travel' | 'other';
export type ResourceType = 'human' | 'equipment' | 'software' | 'facility' | 'service' | 'material';