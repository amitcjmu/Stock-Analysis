/**
 * Session Core Types
 * 
 * Core session and user type definitions for session comparison.
 */

import { ReactNode } from 'react';
import { 
  DeviceType, 
  AuthMethod, 
  ActivityType, 
  ActivityStatus, 
  RiskLevel 
} from './enum-types';
import { 
  DeviceInfo, 
  LocationInfo, 
  NetworkInfo, 
  BrowserInfo 
} from './device-types';
import { 
  SessionSecurity 
} from './security-types';
import { 
  SessionMetrics 
} from './metric-types';

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
  metadata?: Record<string, string | number | boolean | null>;
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
  data?: Record<string, string | number | boolean | null>;
  ipAddress: string;
  userAgent: string;
  status: ActivityStatus;
  risk: RiskLevel;
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