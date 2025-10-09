/**
 * Base client configuration for Collection Flow API
 * Provides shared constants and utilities for all sub-API modules
 */

export class CollectionFlowClient {
  protected readonly baseUrl = "/api/v1/collection";
  protected static readonly STALE_HOURS_THRESHOLD = 24; // hours
  protected static readonly OLD_FLOW_HOURS_THRESHOLD = 90 * 24; // 90 days

  /**
   * Determine whether a flow is stale based on last update time.
   */
  protected isFlowStale(updatedAt: string): boolean {
    const updated = new Date(updatedAt);
    const now = new Date();
    const hoursSinceUpdate =
      (now.getTime() - updated.getTime()) / (1000 * 60 * 60);
    return hoursSinceUpdate > CollectionFlowClient.STALE_HOURS_THRESHOLD;
  }

  /**
   * Get the stale hours threshold
   */
  protected getStaleThreshold(): number {
    return CollectionFlowClient.STALE_HOURS_THRESHOLD;
  }

  /**
   * Get the old flow hours threshold
   */
  protected getOldFlowThreshold(): number {
    return CollectionFlowClient.OLD_FLOW_HOURS_THRESHOLD;
  }
}
