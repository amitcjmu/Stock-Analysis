/**
 * Security and Threat Types
 * 
 * Security, anomaly, and threat types for session comparison.
 */

import type {
  RiskLevel, 
  AnomalyType, 
  ViolationType, 
  ViolationResponse, 
  AlertType, 
  ThreatType 
} from './enum-types';

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