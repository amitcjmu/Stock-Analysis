/**
 * Enum and Union Types
 *
 * All enum and union types for session comparison.
 */

// Device and Authentication Types
export type DeviceType =
  | 'desktop'
  | 'laptop'
  | 'tablet'
  | 'mobile'
  | 'tv'
  | 'watch'
  | 'embedded'
  | 'unknown';

export type AuthMethod =
  | 'password'
  | 'sso'
  | 'oauth'
  | 'saml'
  | 'ldap'
  | 'api_key'
  | 'certificate'
  | 'biometric';

// Activity Types
export type ActivityType =
  | 'navigation'
  | 'interaction'
  | 'api_call'
  | 'data_access'
  | 'configuration'
  | 'authentication'
  | 'security'
  | 'system';

export type ActivityStatus =
  | 'success'
  | 'failure'
  | 'partial'
  | 'timeout'
  | 'blocked'
  | 'error';

// Risk and Security Types
export type RiskLevel =
  | 'very_low'
  | 'low'
  | 'medium'
  | 'high'
  | 'very_high'
  | 'critical';

export type AnomalyType =
  | 'behavioral'
  | 'temporal'
  | 'geographical'
  | 'technical'
  | 'access_pattern'
  | 'data_pattern';

export type ViolationType =
  | 'policy'
  | 'access_control'
  | 'data_protection'
  | 'compliance'
  | 'security'
  | 'usage';

export type ViolationResponse =
  | 'blocked'
  | 'warned'
  | 'logged'
  | 'escalated'
  | 'ignored';

export type AlertType =
  | 'security'
  | 'compliance'
  | 'performance'
  | 'availability'
  | 'data_quality'
  | 'system';

export type ThreatType =
  | 'malware'
  | 'phishing'
  | 'ddos'
  | 'brute_force'
  | 'injection'
  | 'xss'
  | 'csrf'
  | 'insider_threat';

// Network and Connection Types
export type ConnectionType =
  | 'ethernet'
  | 'wifi'
  | 'cellular'
  | 'satellite'
  | 'vpn'
  | 'proxy'
  | 'unknown';

export type ProxyType =
  | 'http'
  | 'https'
  | 'socks4'
  | 'socks5'
  | 'transparent'
  | 'anonymous'
  | 'elite';

// UI and Filter Types
export type ColumnType =
  | 'text'
  | 'number'
  | 'date'
  | 'boolean'
  | 'array'
  | 'object'
  | 'custom';

export type FilterType =
  | 'text'
  | 'select'
  | 'multiselect'
  | 'date'
  | 'daterange'
  | 'number'
  | 'numberrange'
  | 'boolean';

export type FilterOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'greater_than'
  | 'less_than'
  | 'between'
  | 'in'
  | 'not_in';

// Comparison Types
export type SignificanceLevel =
  | 'not_significant'
  | 'low'
  | 'moderate'
  | 'high'
  | 'very_high';

export type DifferenceCategory =
  | 'behavioral'
  | 'temporal'
  | 'technical'
  | 'security'
  | 'geographic'
  | 'access_pattern';

export type SimilarityCategory =
  | 'behavioral'
  | 'temporal'
  | 'technical'
  | 'security'
  | 'geographic'
  | 'demographic';

export type ImpactLevel =
  | 'negligible'
  | 'minor'
  | 'moderate'
  | 'major'
  | 'critical';

export type AssessmentLevel =
  | 'very_similar'
  | 'similar'
  | 'somewhat_similar'
  | 'different'
  | 'very_different';

export type RecommendationType =
  | 'security'
  | 'performance'
  | 'user_experience'
  | 'compliance'
  | 'monitoring'
  | 'optimization';

export type PriorityLevel =
  | 'low'
  | 'medium'
  | 'high'
  | 'urgent'
  | 'critical';

export type EffortLevel =
  | 'minimal'
  | 'low'
  | 'medium'
  | 'high'
  | 'extensive';
