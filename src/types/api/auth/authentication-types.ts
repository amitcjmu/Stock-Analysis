/**
 * Authentication Types
 * 
 * Core authentication API types including login, logout, and password management.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

import type { AuthenticationResult, LogoutResult, PasswordChangeResult, AuthenticatedUser, MFAChallenge, MFAMethod } from './core-types';

// Authentication APIs
export interface LoginRequest extends BaseApiRequest {
  email: string;
  password: string;
  remember?: boolean;
  mfaToken?: string;
  deviceId?: string;
  deviceName?: string;
  ipAddress?: string;
  userAgent?: string;
}

export interface LoginResponse extends BaseApiResponse<AuthenticationResult> {
  data: AuthenticationResult;
  sessionId: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  user: AuthenticatedUser;
  permissions: string[];
  mfaRequired?: boolean;
  mfaChallenge?: MFAChallenge;
}

export interface LogoutRequest extends BaseApiRequest {
  sessionId?: string;
  revokeAllSessions?: boolean;
  context: MultiTenantContext;
}

export interface LogoutResponse extends BaseApiResponse<LogoutResult> {
  data: LogoutResult;
  loggedOutAt: string;
  sessionsRevoked: number;
  tokensRevoked: number;
}

export interface RefreshTokenRequest extends BaseApiRequest {
  refreshToken: string;
  deviceId?: string;
  context: MultiTenantContext;
}

export interface RefreshTokenResponse extends BaseApiResponse<AuthenticationResult> {
  data: AuthenticationResult;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  sessionExtended: boolean;
}

export interface ForgotPasswordRequest extends BaseApiRequest {
  email: string;
  resetUrl?: string;
  context: MultiTenantContext;
}

export interface ForgotPasswordResponse extends BaseApiResponse<unknown> {
  data: unknown;
  emailSent: boolean;
  resetTokenGenerated: boolean;
  expiresAt: string;
}

export interface ResetPasswordRequest extends BaseApiRequest {
  resetToken: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse extends BaseApiResponse<PasswordChangeResult> {
  data: PasswordChangeResult;
  passwordReset: boolean;
  strengthScore: number;
  loginRequired: boolean;
}

export interface ChangePasswordRequest extends BaseApiRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  logoutOtherSessions?: boolean;
  context: MultiTenantContext;
}

export interface ChangePasswordResponse extends BaseApiResponse<PasswordChangeResult> {
  data: PasswordChangeResult;
  passwordChanged: boolean;
  strengthScore: number;
  sessionsInvalidated: number;
}