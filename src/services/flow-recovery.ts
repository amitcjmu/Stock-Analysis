/**
 * Flow Recovery Service
 *
 * Provides automatic flow validation and recovery capabilities to eliminate
 * manual "Discovery Flow Error" scenarios. Integrates with backend flow recovery
 * API endpoints to make flows self-healing.
 *
 * CC: Handles all flow recovery API interactions for intelligent flow routing
 */

import { api } from './api';
import type { ExternalApiResponse } from '../config/api';

// Flow Recovery Types
export interface FlowValidationResult {
  isValid: boolean;
  canRecover: boolean;
  recommendedAction: 'proceed' | 'recover' | 'redirect_to_import' | 'redirect_to_discovery';
  redirectPath?: string;
  issues: string[];
  metadata?: Record<string, unknown>;
}

export interface FlowRecoveryResult {
  success: boolean;
  recoveredFlowId?: string;
  newPhase?: string;
  redirectPath?: string;
  message: string;
  requiresUserAction?: boolean;
  metadata?: Record<string, unknown>;
}

export interface TransitionInterceptResult {
  allowTransition: boolean;
  redirectPath?: string;
  reason?: string;
  flowReadiness: {
    dataImportComplete: boolean;
    fieldMappingReady: boolean;
    canProceedToAttributeMapping: boolean;
  };
  metadata?: Record<string, unknown>;
}

export interface FlowHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    flowValidation: boolean;
    flowRecovery: boolean;
    phaseTransition: boolean;
  };
  message?: string;
}

export interface RecoveryProgress {
  isValidating: boolean;
  isRecovering: boolean;
  isIntercepting: boolean;
  currentStep: string | null;
  progress: number; // 0-100
  message: string | null;
}

/**
 * Flow Recovery Service Class
 * Handles all automatic flow recovery operations
 */
class FlowRecoveryService {
  private readonly baseEndpoint = '/api/v1/unified-discovery/flow';

  /**
   * Validates flow state and determines if recovery is needed
   */
  async validateFlow(flowId: string): Promise<FlowValidationResult> {
    try {
      console.log(`🔍 [FlowRecovery] Validating flow: ${flowId}`);

      const response: ExternalApiResponse<FlowValidationResult> = await api.get(
        `${this.baseEndpoint}/validate/${flowId}`
      );

      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from flow validation API');
      }

      console.log(`✅ [FlowRecovery] Flow validation completed for ${flowId}:`, {
        isValid: response.isValid,
        canRecover: response.canRecover,
        recommendedAction: response.recommendedAction
      });

      return response as FlowValidationResult;
    } catch (error) {
      console.error(`❌ [FlowRecovery] Flow validation failed for ${flowId}:`, error);

      // Return safe fallback for validation errors
      return {
        isValid: false,
        canRecover: false,
        recommendedAction: 'redirect_to_import',
        redirectPath: '/discovery/cmdb-import',
        issues: ['Failed to validate flow state', error.message || 'Unknown error'],
        metadata: { error: true, originalError: error }
      };
    }
  }

  /**
   * Attempts to recover a broken or problematic flow
   */
  async recoverFlow(flowId: string): Promise<FlowRecoveryResult> {
    try {
      console.log(`🔧 [FlowRecovery] Attempting recovery for flow: ${flowId}`);

      const response: ExternalApiResponse<FlowRecoveryResult> = await api.post(
        `${this.baseEndpoint}/recover/${flowId}`,
        {}
      );

      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from flow recovery API');
      }

      console.log(`${response.success ? '✅' : '❌'} [FlowRecovery] Flow recovery completed for ${flowId}:`, {
        success: response.success,
        recoveredFlowId: response.recoveredFlowId,
        requiresUserAction: response.requiresUserAction
      });

      return response as FlowRecoveryResult;
    } catch (error) {
      console.error(`❌ [FlowRecovery] Flow recovery failed for ${flowId}:`, error);

      // Return failed recovery result
      return {
        success: false,
        message: `Recovery failed: ${error.message || 'Unknown error'}`,
        requiresUserAction: true,
        metadata: { error: true, originalError: error }
      };
    }
  }

  /**
   * Intercepts phase transitions to validate flow readiness
   */
  async interceptTransition(
    flowId: string,
    fromPhase: string,
    toPhase: string
  ): Promise<TransitionInterceptResult> {
    try {
      console.log(`🛡️ [FlowRecovery] Intercepting transition for flow ${flowId}: ${fromPhase} → ${toPhase}`);

      const response: ExternalApiResponse<TransitionInterceptResult> = await api.post(
        `${this.baseEndpoint}/intercept-transition`,
        {
          flowId,
          fromPhase,
          toPhase
        }
      );

      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from transition interception API');
      }

      console.log(`${response.allowTransition ? '✅' : '⚠️'} [FlowRecovery] Transition interception completed:`, {
        allowTransition: response.allowTransition,
        redirectPath: response.redirectPath,
        reason: response.reason
      });

      return response as TransitionInterceptResult;
    } catch (error) {
      console.error(`❌ [FlowRecovery] Transition interception failed for ${flowId}:`, error);

      // Return safe fallback - allow transition but flag potential issues
      return {
        allowTransition: true, // Default to allowing transition to avoid blocking users
        reason: `Interception check failed: ${error.message || 'Unknown error'}`,
        flowReadiness: {
          dataImportComplete: false,
          fieldMappingReady: false,
          canProceedToAttributeMapping: false
        },
        metadata: { error: true, originalError: error, fallbackAllowed: true }
      };
    }
  }

  /**
   * Checks the health of flow recovery services
   */
  async getHealthStatus(): Promise<FlowHealthStatus> {
    try {
      console.log(`🏥 [FlowRecovery] Checking flow recovery service health`);

      const response: ExternalApiResponse<FlowHealthStatus> = await api.get(
        `${this.baseEndpoint}/health`
      );

      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from health check API');
      }

      console.log(`📊 [FlowRecovery] Health status:`, {
        status: response.status,
        allServicesHealthy: Object.values(response.services).every(s => s === true)
      });

      return response as FlowHealthStatus;
    } catch (error) {
      console.error(`❌ [FlowRecovery] Health check failed:`, error);

      // Return degraded health status
      return {
        status: 'unhealthy',
        services: {
          flowValidation: false,
          flowRecovery: false,
          phaseTransition: false
        },
        message: `Health check failed: ${error.message || 'Unknown error'}`
      };
    }
  }

  /**
   * Comprehensive flow recovery attempt with validation and recovery
   * This is the main method used by components for full recovery flow
   */
  async performFullRecovery(flowId: string): Promise<{
    success: boolean;
    action: 'recovered' | 'redirect' | 'manual_required';
    flowId?: string;
    redirectPath?: string;
    message: string;
    progress: RecoveryProgress;
  }> {
    const progress: RecoveryProgress = {
      isValidating: false,
      isRecovering: false,
      isIntercepting: false,
      currentStep: null,
      progress: 0,
      message: null
    };

    try {
      // Step 1: Validate flow
      progress.isValidating = true;
      progress.currentStep = 'Validating flow state...';
      progress.progress = 20;
      progress.message = 'Checking flow integrity';

      console.log(`🚀 [FlowRecovery] Starting full recovery for flow: ${flowId}`);

      const validationResult = await this.validateFlow(flowId);

      progress.isValidating = false;
      progress.progress = 40;

      // If flow is valid, no recovery needed
      if (validationResult.isValid) {
        console.log(`✅ [FlowRecovery] Flow ${flowId} is valid, no recovery needed`);
        return {
          success: true,
          action: 'recovered',
          flowId,
          message: 'Flow is healthy and ready',
          progress: { ...progress, progress: 100, currentStep: 'Complete', message: 'Flow validated successfully' }
        };
      }

      // Check if recovery is recommended
      if (validationResult.recommendedAction === 'redirect_to_import' ||
          validationResult.recommendedAction === 'redirect_to_discovery') {
        console.log(`🔄 [FlowRecovery] Redirecting for flow ${flowId} to: ${validationResult.redirectPath}`);
        return {
          success: true,
          action: 'redirect',
          redirectPath: validationResult.redirectPath,
          message: `Flow requires redirect: ${validationResult.issues.join(', ')}`,
          progress: { ...progress, progress: 100, currentStep: 'Redirecting', message: 'Redirect required' }
        };
      }

      // Step 2: Attempt recovery if possible
      if (validationResult.canRecover && validationResult.recommendedAction === 'recover') {
        progress.isRecovering = true;
        progress.currentStep = 'Attempting flow recovery...';
        progress.progress = 70;
        progress.message = 'Recovering flow state';

        const recoveryResult = await this.recoverFlow(flowId);

        progress.isRecovering = false;
        progress.progress = 100;

        if (recoveryResult.success) {
          console.log(`✅ [FlowRecovery] Successfully recovered flow ${flowId}`);
          return {
            success: true,
            action: 'recovered',
            flowId: recoveryResult.recoveredFlowId || flowId,
            message: recoveryResult.message,
            progress: { ...progress, currentStep: 'Recovery complete', message: 'Flow recovered successfully' }
          };
        } else if (recoveryResult.redirectPath) {
          console.log(`🔄 [FlowRecovery] Recovery suggests redirect for flow ${flowId}`);
          return {
            success: true,
            action: 'redirect',
            redirectPath: recoveryResult.redirectPath,
            message: recoveryResult.message,
            progress: { ...progress, currentStep: 'Redirecting', message: 'Recovery suggests redirect' }
          };
        }
      }

      // Recovery not possible or failed - manual action required
      console.log(`⚠️ [FlowRecovery] Manual action required for flow ${flowId}`);
      return {
        success: false,
        action: 'manual_required',
        message: `Automatic recovery failed: ${validationResult.issues.join(', ')}`,
        progress: { ...progress, currentStep: 'Manual action required', message: 'Automatic recovery not possible' }
      };

    } catch (error) {
      console.error(`❌ [FlowRecovery] Full recovery failed for flow ${flowId}:`, error);

      return {
        success: false,
        action: 'manual_required',
        message: `Recovery process failed: ${error.message || 'Unknown error'}`,
        progress: {
          ...progress,
          isValidating: false,
          isRecovering: false,
          currentStep: 'Recovery failed',
          message: 'Error during recovery process'
        }
      };
    }
  }
}

// Export singleton instance
export const flowRecoveryService = new FlowRecoveryService();

// Export default for convenience
export default flowRecoveryService;
