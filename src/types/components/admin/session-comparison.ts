/**
 * Admin Session Comparison Component Types
 * 
 * Type definitions for session comparison components including session analysis,
 * comparison views, and session metrics.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

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

// Supporting types for Session Comparison
export interface UserSession {
  id: string;
  userId: string;
  user: SessionUser;
  startTime: string;
  endTime?: string;
  duration?: number;
  isActive: boolean;
  device: DeviceInfo;
  location: LocationInfo;
  authentication: AuthenticationInfo;
  activities: SessionActivity[];
  metrics: SessionMetrics;
  security: SessionSecurity;
  network: NetworkInfo;
  browser: BrowserInfo;
  flags: SessionFlags;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface SessionUser {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  roles: string[];
  department?: string;
  title?: string;
}

export interface DeviceInfo {
  type: DeviceType;
  os: OperatingSystem;
  brand?: string;
  model?: string;
  fingerprint: string;
  trusted: boolean;
  registeredAt?: string;
  lastSeen: string;
}

export interface OperatingSystem {
  name: string;
  version: string;
  platform: string;
  architecture?: string;
}

export interface LocationInfo {
  ip: string;
  country?: string;
  region?: string;
  city?: string;
  timezone?: string;
  coordinates?: [number, number];
  isp?: string;
  organization?: string;
  asn?: string;
  vpn: boolean;
  proxy: boolean;
  tor: boolean;
}

export interface AuthenticationInfo {
  method: AuthMethod;
  mfaUsed: boolean;
  mfaMethods?: string[];
  loginAttempts: number;
  failedAttempts: number;
  lastFailedAttempt?: string;
  passwordAge?: number;
  accountLocked: boolean;
  rememberMe: boolean;
}

export interface SessionActivity {
  id: string;
  timestamp: string;
  type: ActivityType;
  action: string;
  resource?: string;
  details?: string;
  data?: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  status: ActivityStatus;
  risk: RiskLevel;
}

export interface SessionMetrics {
  pageViews: number;
  uniquePages: number;
  totalClicks: number;
  totalKeystrokes: number;
  idleTime: number;
  activeTime: number;
  bounceRate: number;
  engagementScore: number;
  performanceMetrics: PerformanceMetrics;
  errorCount: number;
  warningCount: number;
}

export interface PerformanceMetrics {
  averagePageLoadTime: number;
  averageResponseTime: number;
  networkLatency: number;
  renderTime: number;
  resourceLoadTime: number;
  jsExecutionTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
}

export interface SessionSecurity {
  riskScore: number;
  anomalies: SecurityAnomaly[];
  violations: SecurityViolation[];
  alerts: SecurityAlert[];
  permissions: SessionPermission[];
  accessPatterns: AccessPattern[];
  threatIndicators: ThreatIndicator[];
}

export interface SecurityAnomaly {
  id: string;
  type: AnomalyType;
  description: string;
  severity: RiskLevel;
  confidence: number;
  detectedAt: string;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
}

export interface SecurityViolation {
  id: string;
  type: ViolationType;
  rule: string;
  description: string;
  severity: RiskLevel;
  timestamp: string;
  action: string;
  response: ViolationResponse;
}

export interface SecurityAlert {
  id: string;
  type: AlertType;
  message: string;
  severity: RiskLevel;
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  falsePositive: boolean;
}

export interface SessionPermission {
  resource: string;
  action: string;
  granted: boolean;
  reason?: string;
  timestamp: string;
}

export interface AccessPattern {
  pattern: string;
  frequency: number;
  risk: RiskLevel;
  firstSeen: string;
  lastSeen: string;
}

export interface ThreatIndicator {
  type: ThreatType;
  value: string;
  source: string;
  confidence: number;
  severity: RiskLevel;
  detectedAt: string;
}

export interface NetworkInfo {
  connectionType: ConnectionType;
  bandwidth?: number;
  latency?: number;
  protocol: string;
  encryption: EncryptionInfo;
  proxy?: ProxyInfo;
  cdn?: CdnInfo;
  requestsCount: number;
  bytesTransferred: number;
  bytesReceived: number;
}

export interface EncryptionInfo {
  protocol: string;
  cipher: string;
  keySize: number;
  version: string;
  certificateValid: boolean;
}

export interface ProxyInfo {
  type: ProxyType;
  address: string;
  port: number;
  authentication: boolean;
  trusted: boolean;
}

export interface CdnInfo {
  provider: string;
  edge: string;
  cacheHit: boolean;
  responseTime: number;
}

export interface BrowserInfo {
  name: string;
  version: string;
  engine: string;
  userAgent: string;
  language: string;
  languages: string[];
  cookiesEnabled: boolean;
  javaScriptEnabled: boolean;
  adBlocker: boolean;
  plugins: BrowserPlugin[];
  extensions: BrowserExtension[];
  viewport: Viewport;
  screen: ScreenInfo;
}

export interface BrowserPlugin {
  name: string;
  version: string;
  enabled: boolean;
  filename?: string;
}

export interface BrowserExtension {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
  permissions: string[];
}

export interface Viewport {
  width: number;
  height: number;
  devicePixelRatio: number;
  orientation: 'portrait' | 'landscape';
}

export interface ScreenInfo {
  width: number;
  height: number;
  colorDepth: number;
  pixelDepth: number;
  availWidth: number;
  availHeight: number;
}

export interface SessionFlags {
  suspicious: boolean;
  highRisk: boolean;
  newDevice: boolean;
  newLocation: boolean;
  concurrentSession: boolean;
  apiAccess: boolean;
  adminAccess: boolean;
  dataExport: boolean;
  privilegedAction: boolean;
  offHours: boolean;
}

export interface SessionComparisonColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, sessions: UserSession[], index: number) => ReactNode;
  compareRender?: (values: any[], sessions: UserSession[]) => ReactNode;
  showDifferences?: boolean;
  type: ColumnType;
}

export interface SessionFilter {
  key: string;
  label: string;
  type: FilterType;
  field: string;
  operator?: FilterOperator;
  options?: FilterOption[];
  value?: any;
  placeholder?: string;
  validation?: ValidationRule[];
}

export interface SessionComparison {
  sessions: UserSession[];
  differences: ComparisonDifference[];
  similarities: ComparisonSimilarity[];
  metrics: ComparisonMetrics;
  summary: ComparisonSummary;
  recommendations: ComparisonRecommendation[];
}

export interface ComparisonDifference {
  field: string;
  label: string;
  values: ComparisonValue[];
  significance: SignificanceLevel;
  category: DifferenceCategory;
  impact: ImpactLevel;
}

export interface ComparisonSimilarity {
  field: string;
  label: string;
  value: any;
  confidence: number;
  category: SimilarityCategory;
}

export interface ComparisonValue {
  sessionId: string;
  value: any;
  normalized?: any;
  deviation?: number;
}

export interface ComparisonMetrics {
  overallSimilarity: number;
  behavioralSimilarity: number;
  temporalSimilarity: number;
  technicalSimilarity: number;
  securitySimilarity: number;
  riskDifferential: number;
  anomalyScore: number;
}

export interface ComparisonSummary {
  totalDifferences: number;
  significantDifferences: number;
  majorDifferences: number;
  minorDifferences: number;
  totalSimilarities: number;
  strongSimilarities: number;
  weakSimilarities: number;
  overallAssessment: AssessmentLevel;
  riskAssessment: RiskLevel;
}

export interface ComparisonRecommendation {
  id: string;
  type: RecommendationType;
  priority: PriorityLevel;
  title: string;
  description: string;
  rationale: string;
  actions: RecommendedAction[];
  impact: ImpactLevel;
  effort: EffortLevel;
}

export interface RecommendedAction {
  action: string;
  description: string;
  automated: boolean;
  parameters?: Record<string, any>;
}

// Enum and union types
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

// Additional supporting interfaces
export interface FilterOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface ExportFormat {
  type: 'csv' | 'excel' | 'pdf' | 'json' | 'xml';
  label: string;
  options?: ExportOptions;
}

export interface ExportOptions {
  includeMetadata?: boolean;
  includeActivities?: boolean;
  includeMetrics?: boolean;
  includeComparison?: boolean;
  compression?: boolean;
  format?: string;
}