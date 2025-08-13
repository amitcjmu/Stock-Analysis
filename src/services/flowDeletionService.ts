/**
 * Centralized Flow Deletion Service
 * Ensures ALL flow deletions require user approval and provides clear audit trail
 * Consolidates deletion logic from multiple components
 */

import { masterFlowService } from './api/masterFlowService';

/**
 * External flow data structure from backend API
 */
export interface ExternalFlowData {
  master_flow_id?: string;
  flowId?: string;
  flow_id?: string;
  flow_name?: string;
  flowType?: string;
  status: string;
  currentPhase?: string;
  current_phase?: string;
  progress?: number;
  progress_percentage?: number;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
  deletion_impact?: {
    data_to_delete: {
      workflow_state: number;
      import_sessions: number;
      field_mappings: number;
      assets: number;
      dependencies: number;
      shared_memory_refs: number;
    };
    estimated_cleanup_time: string;
  };
  // Allow additional properties from external APIs with specific types
  metadata?: Record<string, string | number | boolean>;
  additionalInfo?: Record<string, string | number | boolean>;
}

export interface FlowDeletionCandidate {
  flowId: string;
  flow_name?: string;
  status: string;
  current_phase: string;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
  reason_for_deletion: 'failed' | 'completed' | 'stale' | 'user_requested' | 'cleanup_recommended';
  auto_cleanup_eligible: boolean;
  deletion_impact: {
    data_to_delete: {
      workflow_state: number;
      import_sessions: number;
      field_mappings: number;
      assets: number;
      dependencies: number;
      shared_memory_refs: number;
    };
    estimated_cleanup_time: string;
  };
}

export interface FlowDeletionRequest {
  flowIds: string[];
  reason: 'user_requested' | 'cleanup_approved';
  user_confirmed: boolean;
  deletion_source: 'manual' | 'bulk_cleanup' | 'navigation' | 'automatic_cleanup';
  user_id?: string;
  confirmation_timestamp: string;
}

export interface FlowDeletionResult {
  success: boolean;
  deleted_count: number;
  failed_count: number;
  results: Array<{
    flowId: string;
    success: boolean;
    error?: string;
  }>;
  audit_trail: {
    deletion_source: string;
    user_confirmed: boolean;
    timestamp: string;
    reason: string;
  };
}

class FlowDeletionService {
  private static instance: FlowDeletionService;

  private constructor() {}

  static getInstance(): FlowDeletionService {
    if (!FlowDeletionService.instance) {
      FlowDeletionService.instance = new FlowDeletionService();
    }
    return FlowDeletionService.instance;
  }

  /**
   * Analyze flows and identify deletion candidates
   * System can recommend but never auto-delete
   */
  async identifyDeletionCandidates(
    clientAccountId: string,
    engagementId?: string,
    flowType?: string
  ): Promise<FlowDeletionCandidate[]> {
    try {
      const flows = await masterFlowService.getActiveFlows(clientAccountId, engagementId, flowType);

      return flows.map(flow => this.analyzeFlowForDeletion(flow)).filter(Boolean);
    } catch (error) {
      console.error('Failed to identify deletion candidates:', error);
      return [];
    }
  }

  /**
   * Analyze individual flow for deletion eligibility
   */
  private analyzeFlowForDeletion(flow: ExternalFlowData): FlowDeletionCandidate | null {
    const now = new Date();
    const updatedAt = new Date(flow.updated_at || flow.updatedAt || now);
    const daysSinceUpdate = (now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60 * 24);

    let reason_for_deletion: FlowDeletionCandidate['reason_for_deletion'] | null = null;
    let auto_cleanup_eligible = false;
    
    // Get progress as a number, defaulting to 0 if undefined
    const progressValue = flow.progress || flow.progress_percentage || 0;

    // Analyze flow status and determine recommendation
    if (flow.status === 'failed' || flow.status === 'error') {
      reason_for_deletion = 'failed';
      auto_cleanup_eligible = daysSinceUpdate > 1; // Failed flows older than 1 day
    } else if (flow.status === 'completed' && progressValue >= 100) {
      reason_for_deletion = 'completed';
      auto_cleanup_eligible = daysSinceUpdate > 7; // Completed flows older than 7 days
    } else if (flow.status === 'cancelled') {
      reason_for_deletion = 'cleanup_recommended';
      auto_cleanup_eligible = daysSinceUpdate > 0; // Cancelled flows immediately eligible
    } else if (daysSinceUpdate > 30 && (flow.status === 'paused' || flow.status === 'active')) {
      reason_for_deletion = 'stale';
      auto_cleanup_eligible = daysSinceUpdate > 30; // Stale flows older than 30 days
    }

    // Only return flows that are candidates for deletion
    if (!reason_for_deletion) {
      return null;
    }
    
    // Ensure we have required string fields
    const flowId = flow.master_flow_id || flow.flowId || flow.flow_id || '';
    const createdAt = flow.created_at || flow.createdAt || now.toISOString();
    const updatedAtStr = flow.updated_at || flow.updatedAt || now.toISOString();

    return {
      flowId,
      flow_name: flow.flow_name || flow.flowType || 'Unknown Flow',
      status: flow.status,
      current_phase: flow.currentPhase || flow.current_phase || 'unknown',
      progress_percentage: progressValue,
      created_at: createdAt,
      updated_at: updatedAtStr,
      reason_for_deletion,
      auto_cleanup_eligible,
      deletion_impact: flow.deletion_impact || {
        data_to_delete: {
          workflow_state: 1,
          import_sessions: 0,
          field_mappings: 0,
          assets: 0,
          dependencies: 0,
          shared_memory_refs: 0
        },
        estimated_cleanup_time: '30s'
      }
    };
  }

  /**
   * Request user approval for flow deletion
   * This is the ONLY way flows can be deleted
   */
  async requestDeletionApproval(
    candidates: FlowDeletionCandidate[],
    deletion_source: FlowDeletionRequest['deletion_source'],
    user_id?: string,
    skipBrowserConfirm: boolean = false
  ): Promise<FlowDeletionRequest | null> {
    if (candidates.length === 0) {
      return null;
    }

    let userConfirmed = false;

    if (skipBrowserConfirm) {
      // When skipBrowserConfirm is true, it means a custom UI already collected confirmation
      // This is used when components have their own deletion dialogs
      console.log('✅ Using pre-approved deletion (custom UI already confirmed)');
      userConfirmed = true;
    } else {
      // CRITICAL: Native browser dialogs are not allowed
      // This blocks UI automation and provides poor user experience
      console.error('❌ ERROR: Attempted to use native browser confirm dialog');
      console.error('❌ Use the useFlowDeletion hook with FlowDeletionModal component instead');

      // Throw error to prevent fallback to native dialogs
      throw new Error(
        'Flow deletion requires proper React-based confirmation dialog. ' +
        'Use FlowDeletionModal component or pass skipBrowserConfirm=true with pre-confirmed deletion.'
      );
    }

    if (!userConfirmed) {
      console.log('🚫 User declined flow deletion request');
      return null;
    }

    return {
      flowIds: candidates.map(c => c.flowId),
      reason: deletion_source === 'manual' ? 'user_requested' : 'cleanup_approved',
      user_confirmed: true,
      deletion_source,
      user_id,
      confirmation_timestamp: new Date().toISOString()
    };
  }

  /**
   * Build user-friendly confirmation message
   */
  private buildConfirmationMessage(
    candidates: FlowDeletionCandidate[],
    source: FlowDeletionRequest['deletion_source']
  ): string {
    const count = candidates.length;
    const single = count === 1;

    let header = '';
    switch (source) {
      case 'automatic_cleanup':
        header = `🤖 System Cleanup Recommendation`;
        break;
      case 'bulk_cleanup':
        header = `🧹 Bulk Cleanup Request`;
        break;
      case 'navigation':
        header = `🚨 Navigation Cleanup Required`;
        break;
      default:
        header = `🗑️ Flow Deletion Confirmation`;
    }

    let message = `${header}\n\n`;

    if (single) {
      const flow = candidates[0];
      message += `Delete this flow?\n\n`;
      message += `• Flow: ${flow.flow_name}\n`;
      message += `• Status: ${flow.status.toUpperCase()}\n`;
      message += `• Phase: ${flow.current_phase}\n`;
      message += `• Progress: ${flow.progress_percentage}%\n`;
      message += `• Reason: ${this.getReasonDescription(flow.reason_for_deletion)}\n`;
      message += `• Last Updated: ${this.formatTimeAgo(flow.updated_at)}\n\n`;
    } else {
      message += `Delete ${count} flows?\n\n`;
      message += `Breakdown by reason:\n`;

      const reasonGroups = candidates.reduce((acc, flow) => {
        acc[flow.reason_for_deletion] = (acc[flow.reason_for_deletion] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      Object.entries(reasonGroups).forEach(([reason, count]) => {
        message += `• ${this.getReasonDescription(reason as FlowDeletionCandidate['reason_for_deletion'])}: ${count} flows\n`;
      });

      message += `\nOldest flows:\n`;
      candidates
        .sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime())
        .slice(0, 3)
        .forEach(flow => {
          message += `• ${flow.flow_name} (${this.formatTimeAgo(flow.updated_at)})\n`;
        });
    }

    message += `\n⚠️ This action cannot be undone.\n`;
    message += `💡 Alternative: You can resume/retry flows instead of deleting them.\n\n`;
    message += `Continue with deletion?`;

    return message;
  }

  /**
   * Execute approved deletion request
   */
  async executeApprovedDeletion(
    request: FlowDeletionRequest,
    clientAccountId: string,
    engagementId?: string
  ): Promise<FlowDeletionResult> {
    console.log('🗑️ Executing approved flow deletion:', {
      flowIds: request.flowIds,
      reason: request.reason,
      source: request.deletion_source,
      userConfirmed: request.user_confirmed,
      timestamp: request.confirmation_timestamp
    });

    const results: FlowDeletionResult['results'] = [];

    // Execute deletions one by one for better error handling
    for (const flowId of request.flowIds) {
      try {
        await masterFlowService.deleteFlow(flowId, clientAccountId, engagementId);
        results.push({ flowId, success: true });
        console.log(`✅ Successfully deleted flow ${flowId}`);
      } catch (error) {
        results.push({ flowId, success: false, error: error instanceof Error ? error.message : 'Unknown error' });
        console.error(`❌ Failed to delete flow ${flowId}:`, error);
      }
    }

    const deleted_count = results.filter(r => r.success).length;
    const failed_count = results.filter(r => !r.success).length;

    return {
      success: deleted_count > 0,
      deleted_count,
      failed_count,
      results,
      audit_trail: {
        deletion_source: request.deletion_source,
        user_confirmed: request.user_confirmed,
        timestamp: request.confirmation_timestamp,
        reason: request.reason
      }
    };
  }

  /**
   * Consolidated method for all deletion scenarios
   * This is the ONLY method that should be used for flow deletion
   */
  async requestFlowDeletion(
    flowIds: string[],
    clientAccountId: string,
    engagementId?: string,
    deletion_source: FlowDeletionRequest['deletion_source'] = 'manual',
    user_id?: string,
    skipBrowserConfirm: boolean = false
  ): Promise<FlowDeletionResult> {
    try {
      // Get flow details for confirmation
      const allFlows = await masterFlowService.getActiveFlows(clientAccountId, engagementId);
      const targetFlows = allFlows.filter(flow =>
        flowIds.includes(flow.master_flow_id || flow.flowId || flow.flow_id)
      );

      // Convert to deletion candidates
      const candidates = targetFlows
        .map(flow => this.analyzeFlowForDeletion(flow))
        .filter(Boolean);

      // If no flows found in master flows, create a candidate for the requested flow ID
      if (candidates.length === 0 && flowIds.length > 0) {
        console.log('⚠️ No flows found in master flows, creating candidates for requested IDs');
        flowIds.forEach(flowId => {
          candidates.push({
            flowId,
            flow_name: 'Unknown Flow',
            status: 'unknown',
            current_phase: 'unknown',
            progress_percentage: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            reason_for_deletion: deletion_source === 'manual' ? 'user_requested' : 'cleanup_recommended',
            auto_cleanup_eligible: true,
            deletion_impact: {
              data_to_delete: {
                workflow_state: 1,
                import_sessions: 0,
                field_mappings: 0,
                assets: 0,
                dependencies: 0,
                shared_memory_refs: 0
              },
              estimated_cleanup_time: '30s'
            }
          });
        });
      } else if (deletion_source === 'manual') {
        // Add user_requested reason for manual deletions
        candidates.forEach(candidate => {
          candidate.reason_for_deletion = 'user_requested';
        });
      }

      // Request user approval
      const approval = await this.requestDeletionApproval(candidates, deletion_source, user_id, skipBrowserConfirm);

      if (!approval) {
        return {
          success: false,
          deleted_count: 0,
          failed_count: 0,
          results: [],
          audit_trail: {
            deletion_source,
            user_confirmed: false,
            timestamp: new Date().toISOString(),
            reason: 'user_declined'
          }
        };
      }

      // Execute approved deletion
      return await this.executeApprovedDeletion(approval, clientAccountId, engagementId);

    } catch (error) {
      console.error('Flow deletion request failed:', error);
      return {
        success: false,
        deleted_count: 0,
        failed_count: 0,
        results: [],
        audit_trail: {
          deletion_source,
          user_confirmed: false,
          timestamp: new Date().toISOString(),
          reason: 'system_error'
        }
      };
    }
  }

  /**
   * Get user-friendly reason description
   */
  private getReasonDescription(reason: FlowDeletionCandidate['reason_for_deletion']): string {
    switch (reason) {
      case 'failed': return 'Failed/Error flows';
      case 'completed': return 'Completed flows';
      case 'stale': return 'Inactive flows (>30 days)';
      case 'user_requested': return 'User requested deletion';
      case 'cleanup_recommended': return 'Recommended for cleanup';
      default: return 'Unknown reason';
    }
  }

  /**
   * Format time ago
   */
  private formatTimeAgo(timestamp: string): string {
    try {
      const now = new Date();
      const time = new Date(timestamp);
      const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch (error) {
      return 'Unknown';
    }
  }
}

// Export singleton instance
export const flowDeletionService = FlowDeletionService.getInstance();
