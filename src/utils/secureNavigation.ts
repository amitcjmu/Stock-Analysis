/**
 * Secure Navigation Utility
 *
 * Provides secure URL validation and navigation functions to prevent
 * URL injection attacks and ensure safe client-side routing.
 *
 * Created by CC (Claude Code) - Security Enhancement
 */

import SecureLogger from './SecureLogger';
import { validateFlowId } from './secureStorage';

// Allowed path patterns (whitelist approach)
const ALLOWED_PATH_PATTERNS = [
  /^\/discovery\/data-import(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/attribute-mapping(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/data-cleansing(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/inventory(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/dependencies(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/tech-debt(?:\/[a-f0-9-]+)?$/,
  /^\/discovery\/cmdb-import$/,
  /^\/dashboard$/,
  /^\/assets$/,
  /^\/reports$/,
  /^\/settings$/,
  /^\/$/,
] as const;

// Known discovery phases for validation
const DISCOVERY_PHASES = [
  'data-import',
  'attribute-mapping',
  'data-cleansing',
  'inventory',
  'dependencies',
  'tech-debt'
] as const;

type DiscoveryPhase = typeof DISCOVERY_PHASES[number];

/**
 * Validates if a URL path is safe and allowed
 */
function validatePath(path: string): boolean {
  if (!path || typeof path !== 'string') {
    return false;
  }

  // Remove query parameters and hash for validation
  const cleanPath = path.split('?')[0].split('#')[0];

  // Check against allowed patterns
  return ALLOWED_PATH_PATTERNS.some(pattern => pattern.test(cleanPath));
}

/**
 * Validates if a URL is safe for navigation
 */
function validateUrl(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  try {
    // For relative URLs, validate the path
    if (url.startsWith('/')) {
      return validatePath(url);
    }

    // For absolute URLs, ensure they're same-origin
    const urlObj = new URL(url);
    const currentOrigin = window.location.origin;

    if (urlObj.origin !== currentOrigin) {
      SecureLogger.warn(`Cross-origin navigation attempt blocked: ${urlObj.origin}`);
      return false;
    }

    return validatePath(urlObj.pathname);
  } catch (error) {
    SecureLogger.error('Invalid URL format', error);
    return false;
  }
}

/**
 * Sanitizes a flow ID parameter
 */
function sanitizeFlowId(flowId: string | null | undefined): string | null {
  if (!flowId || typeof flowId !== 'string') {
    return null;
  }

  const trimmedFlowId = flowId.trim();

  if (!validateFlowId(trimmedFlowId)) {
    SecureLogger.warn(`Invalid flow ID format: ${trimmedFlowId}`);
    return null;
  }

  return trimmedFlowId;
}

/**
 * Builds a secure discovery phase URL
 */
function buildDiscoveryUrl(phase: DiscoveryPhase, flowId?: string | null): string {
  if (!DISCOVERY_PHASES.includes(phase)) {
    SecureLogger.error(`Invalid discovery phase: ${phase}`);
    return '/dashboard'; // Safe fallback
  }

  let url = `/discovery/${phase}`;

  if (flowId) {
    const sanitizedFlowId = sanitizeFlowId(flowId);
    if (sanitizedFlowId) {
      url += `/${sanitizedFlowId}`;
    } else {
      SecureLogger.warn(`Invalid flow ID provided for ${phase}, navigating without ID`);
    }
  }

  return url;
}

/**
 * Secure navigation interface
 */
interface SecureNavigation {
  navigateTo: (url: string) => boolean;
  navigateToDiscoveryPhase: (phase: DiscoveryPhase, flowId?: string | null) => boolean;
  validateAndNavigate: (url: string) => boolean;
  buildDiscoveryUrl: (phase: DiscoveryPhase, flowId?: string | null) => string;
  isValidPath: (path: string) => boolean;
  isValidFlowId: (flowId: string) => boolean;
}

/**
 * Creates a secure navigation instance
 */
function createSecureNavigation(): SecureNavigation {
  const navigateTo = (url: string): boolean => {
    try {
      if (!validateUrl(url)) {
        SecureLogger.error(`Navigation blocked - invalid URL: ${url}`);
        return false;
      }

      SecureLogger.debug(`Navigating to validated URL: ${url}`);
      window.location.href = url;
      return true;
    } catch (error) {
      SecureLogger.error('Navigation failed', error);
      return false;
    }
  };

  const navigateToDiscoveryPhase = (phase: DiscoveryPhase, flowId?: string | null): boolean => {
    try {
      const url = buildDiscoveryUrl(phase, flowId);
      return navigateTo(url);
    } catch (error) {
      SecureLogger.error(`Failed to navigate to discovery phase: ${phase}`, error);
      return false;
    }
  };

  const validateAndNavigate = (url: string): boolean => {
    if (!validateUrl(url)) {
      SecureLogger.warn(`Invalid URL rejected: ${url}`);
      // Navigate to safe fallback
      return navigateTo('/dashboard');
    }
    return navigateTo(url);
  };

  const isValidPath = (path: string): boolean => {
    return validatePath(path);
  };

  const isValidFlowId = (flowId: string): boolean => {
    return validateFlowId(flowId);
  };

  return {
    navigateTo,
    navigateToDiscoveryPhase,
    validateAndNavigate,
    buildDiscoveryUrl,
    isValidPath,
    isValidFlowId
  };
}

// Export singleton instance
export const secureNavigation = createSecureNavigation();

// Export utility functions
export { validatePath, validateUrl, buildDiscoveryUrl, sanitizeFlowId };

// Export types
export type { DiscoveryPhase, SecureNavigation };
export { DISCOVERY_PHASES };
