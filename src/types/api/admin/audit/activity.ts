/**
 * User Activity Types
 * 
 * Types for tracking and analyzing user activity patterns.
 * 
 * Generated with CC for modular admin type organization.
 */

import { ActivityLocation, ActivityDevice, ConfidenceLevel } from '../common';
import { PatternType, AnomalyType, AnomalySeverity } from './enums';

// User activity summary
export interface UserActivitySummary {
  user_id: string;
  email: string;
  display_name: string;
  total_actions: number;
  unique_resources: number;
  risk_score: number;
  last_activity: string;
  locations: ActivityLocation[];
  devices: ActivityDevice[];
  patterns: ActivityPattern[];
  anomalies: ActivityAnomaly[];
}

// Activity pattern
export interface ActivityPattern {
  pattern_type: PatternType;
  description: string;
  frequency: number;
  confidence: ConfidenceLevel;
  baseline_deviation: number;
}

// Activity anomaly
export interface ActivityAnomaly {
  anomaly_type: AnomalyType;
  description: string;
  severity: AnomalySeverity;
  confidence: ConfidenceLevel;
  detected_at: string;
  investigated: boolean;
}