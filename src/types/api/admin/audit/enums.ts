/**
 * Audit and Security Enums
 *
 * Enumeration types specific to audit logging and security events.
 *
 * Generated with CC for modular admin type organization.
 */

// Audit severity levels
export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

// Audit actions
export type AuditAction =
  | 'login' | 'logout' | 'password_change' | 'password_reset'
  | 'user_create' | 'user_update' | 'user_delete' | 'user_deactivate'
  | 'role_assign' | 'role_revoke' | 'permission_grant' | 'permission_deny'
  | 'account_create' | 'account_update' | 'account_delete' | 'account_suspend'
  | 'engagement_create' | 'engagement_update' | 'engagement_delete'
  | 'data_access' | 'data_export' | 'data_import' | 'data_delete'
  | 'settings_change' | 'integration_add' | 'integration_remove'
  | 'report_generate' | 'report_download' | 'backup_create' | 'backup_restore'
  | 'api_call' | 'webhook_trigger' | 'notification_send'
  | 'security_violation' | 'compliance_check' | 'system_error';

// Audit resources
export type AuditResource =
  | 'user' | 'role' | 'permission' | 'client_account' | 'engagement'
  | 'flow' | 'data' | 'report' | 'setting' | 'integration' | 'notification'
  | 'session' | 'api' | 'webhook' | 'audit_log' | 'system';

// Audit outcomes
export type AuditOutcome = 'success' | 'failure' | 'partial' | 'blocked' | 'error';

// Audit sources
export type AuditSource = 'user' | 'system' | 'api' | 'webhook' | 'scheduled' | 'automated';

// Security event types
export type SecurityEventType =
  | 'login' | 'logout' | 'permission_change' | 'data_access' | 'configuration_change'
  | 'security_violation' | 'brute_force' | 'suspicious_activity' | 'unauthorized_access'
  | 'data_breach' | 'malware_detection' | 'phishing_attempt' | 'privilege_escalation'
  | 'account_takeover' | 'insider_threat' | 'compliance_violation';

// Security severity levels
export type SecuritySeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

// Threat levels
export type ThreatLevel = 'minimal' | 'low' | 'moderate' | 'high' | 'severe';

// Security event sources
export type SecurityEventSource =
  | 'waf' | 'ids' | 'antivirus' | 'firewall' | 'application' | 'user_report' | 'automated_scan';

// Indicator types
export type IndicatorType = 'ip' | 'domain' | 'url' | 'hash' | 'email' | 'user_agent' | 'certificate';

// Effectiveness levels
export type EffectivenessLevel = 'ineffective' | 'partially_effective' | 'effective' | 'highly_effective';

// Investigation status
export type InvestigationStatus = 'open' | 'in_progress' | 'pending' | 'closed' | 'escalated';

// Threat actor types
export type ThreatActorType = 'nation_state' | 'cybercriminal' | 'hacktivist' | 'insider' | 'unknown';

// Sophistication levels
export type SophisticationLevel = 'low' | 'medium' | 'high' | 'advanced';

// Evidence types
export type EvidenceType = 'log' | 'network_capture' | 'file' | 'memory_dump' | 'screenshot' | 'metadata';

// Recommendation types
export type RecommendationType =
  | 'security_policy' | 'access_control' | 'monitoring' | 'training' | 'technical' | 'process';

// Recommendation priority
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';

// Pattern types
export type PatternType = 'temporal' | 'behavioral' | 'access' | 'network' | 'resource_usage';

// Anomaly types
export type AnomalyType = 'statistical' | 'behavioral' | 'temporal' | 'geographical' | 'access_pattern';

// Anomaly severity
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';
