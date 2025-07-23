/**
 * Token Management Types
 * 
 * API token creation, management, and validation types.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

import type { TokenValidationResult } from './core-types'
import { ApiToken } from './core-types'

// API Token Management APIs
export interface CreateApiTokenRequest extends BaseApiRequest {
  name: string;
  description?: string;
  scopes: string[];
  expiresAt?: string;
  ipWhitelist?: string[];
  context: MultiTenantContext;
}

export interface CreateApiTokenResponse extends BaseApiResponse<ApiToken> {
  data: ApiToken;
  token: string;
  tokenId: string;
  createdAt: string;
  expiresAt?: string;
}

export interface GetApiTokensRequest extends BaseApiRequest {
  includeExpired?: boolean;
  includeRevoked?: boolean;
  context: MultiTenantContext;
}

export interface GetApiTokensResponse extends BaseApiResponse<ApiToken[]> {
  data: ApiToken[];
  activeTokens: number;
  expiredTokens: number;
  revokedTokens: number;
}

export interface RevokeApiTokenRequest extends BaseApiRequest {
  tokenId: string;
  reason?: string;
  context: MultiTenantContext;
}

export interface RevokeApiTokenResponse extends BaseApiResponse<unknown> {
  data: unknown;
  revoked: boolean;
  revokedAt: string;
}

export interface UpdateApiTokenRequest extends BaseApiRequest {
  tokenId: string;
  name?: string;
  description?: string;
  scopes?: string[];
  ipWhitelist?: string[];
  context: MultiTenantContext;
}

export interface UpdateApiTokenResponse extends BaseApiResponse<ApiToken> {
  data: ApiToken;
  updated: boolean;
  scopesChanged: boolean;
  whitelistChanged: boolean;
}

export interface ValidateTokenRequest extends BaseApiRequest {
  token: string;
  requiredScopes?: string[];
  ipAddress?: string;
}

export interface ValidateTokenResponse extends BaseApiResponse<TokenValidationResult> {
  data: TokenValidationResult;
  valid: boolean;
  expired: boolean;
  revoked: boolean;
  scopesValid: boolean;
  ipAllowed: boolean;
}