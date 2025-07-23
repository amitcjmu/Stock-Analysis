/**
 * Multi-Factor Authentication Types
 * 
 * MFA setup, verification, and management API types.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

import type { MFASetupResult, MFAVerificationResult, MFADisableResult, BackupCodesResult } from './core-types'
import type { MFAMethod } from './core-types'

// Multi-Factor Authentication APIs
export interface SetupMFARequest extends BaseApiRequest {
  method: MFAMethod;
  phoneNumber?: string;
  backupCodes?: boolean;
  context: MultiTenantContext;
}

export interface SetupMFAResponse extends BaseApiResponse<MFASetupResult> {
  data: MFASetupResult;
  setupId: string;
  qrCode?: string;
  secret?: string;
  backupCodes?: string[];
  verificationRequired: boolean;
}

export interface VerifyMFASetupRequest extends BaseApiRequest {
  setupId: string;
  verificationCode: string;
  context: MultiTenantContext;
}

export interface VerifyMFASetupResponse extends BaseApiResponse<MFAVerificationResult> {
  data: MFAVerificationResult;
  verified: boolean;
  mfaEnabled: boolean;
  backupCodes: string[];
  recoveryCodes: string[];
}

export interface DisableMFARequest extends BaseApiRequest {
  password: string;
  verificationCode?: string;
  reason?: string;
  context: MultiTenantContext;
}

export interface DisableMFAResponse extends BaseApiResponse<MFADisableResult> {
  data: MFADisableResult;
  disabled: boolean;
  disabledAt: string;
  backupMethodsRevoked: boolean;
}

export interface VerifyMFARequest extends BaseApiRequest {
  sessionId: string;
  verificationCode: string;
  method: MFAMethod;
  trustDevice?: boolean;
}

export interface VerifyMFAResponse extends BaseApiResponse<MFAVerificationResult> {
  data: MFAVerificationResult;
  verified: boolean;
  accessToken?: string;
  sessionUpdated: boolean;
  deviceTrusted: boolean;
}

export interface GenerateBackupCodesRequest extends BaseApiRequest {
  password: string;
  invalidateExisting?: boolean;
  context: MultiTenantContext;
}

export interface GenerateBackupCodesResponse extends BaseApiResponse<BackupCodesResult> {
  data: BackupCodesResult;
  backupCodes: string[];
  generatedAt: string;
  expiresAt?: string;
  previousCodesInvalidated: boolean;
}

export interface GetMFAMethodsRequest extends BaseApiRequest {
  context: MultiTenantContext;
}

export interface GetMFAMethodsResponse extends BaseApiResponse<MFAMethod[]> {
  data: MFAMethod[];
  enabledMethods: MFAMethod[];
  availableMethods: MFAMethod[];
  recommendedMethod?: MFAMethod;
}