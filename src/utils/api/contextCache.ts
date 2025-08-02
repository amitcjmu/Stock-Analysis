/**
 * Context Cache Service for optimizing context switching performance
 * Provides cache-first context switching with parallel data loading
 */

import { CacheManager } from './cacheStrategies';
import type { User, Client, Engagement, Flow } from '../../contexts/AuthContext/types';

interface ContextData {
  client?: Client;
  engagement?: Engagement;
  flow?: Flow;
  engagements?: Engagement[];
  flows?: Flow[];
}

interface CacheMetrics {
  hits: number;
  misses: number;
  hitRate: number;
  avgResponseTime: number;
}

/**
 * Enhanced context cache with pre-fetching and metrics
 */
export class ContextCacheService {
  private cache: CacheManager;
  private prefetchQueue = new Set<string>();
  private metrics: CacheMetrics = {
    hits: 0,
    misses: 0,
    hitRate: 0,
    avgResponseTime: 0,
  };
  private responseTimes: number[] = [];

  constructor() {
    this.cache = new CacheManager({
      keyPrefix: 'context_',
      defaultTtl: 10 * 60 * 1000, // 10 minutes for context data
      maxSize: 200, // Store more context objects
      cleanupInterval: 5 * 60 * 1000, // 5 minutes cleanup
    });
  }

  /**
   * Get cached client data with metrics tracking
   */
  async getCachedClient(clientId: string): Promise<Client | null> {
    const startTime = performance.now();
    const client = (await this.cache.get(`client_${clientId}`)) as Client | null;

    if (client) {
      this.recordHit(startTime);
      return client;
    }

    this.recordMiss(startTime);
    return null;
  }

  /**
   * Cache client data with engagements pre-fetch
   */
  async setCachedClient(clientId: string, client: Client): Promise<void> {
    await this.cache.set(`client_${clientId}`, client);

    // Schedule engagements pre-fetch
    this.schedulePrefetch(`engagements_${clientId}`);
  }

  /**
   * Get cached engagement data
   */
  async getCachedEngagement(engagementId: string): Promise<Engagement | null> {
    const startTime = performance.now();
    const engagement = (await this.cache.get(`engagement_${engagementId}`)) as Engagement | null;

    if (engagement) {
      this.recordHit(startTime);
      return engagement;
    }

    this.recordMiss(startTime);
    return null;
  }

  /**
   * Cache engagement data with flows pre-fetch
   */
  async setCachedEngagement(engagementId: string, engagement: Engagement): Promise<void> {
    await this.cache.set(`engagement_${engagementId}`, engagement);

    // Schedule flows pre-fetch
    this.schedulePrefetch(`flows_${engagementId}`);
  }

  /**
   * Get cached flow data
   */
  async getCachedFlow(flowId: string): Promise<Flow | null> {
    const startTime = performance.now();
    const flow = (await this.cache.get(`flow_${flowId}`)) as Flow | null;

    if (flow) {
      this.recordHit(startTime);
      return flow;
    }

    this.recordMiss(startTime);
    return null;
  }

  /**
   * Cache flow data
   */
  async setCachedFlow(flowId: string, flow: Flow): Promise<void> {
    await this.cache.set(`flow_${flowId}`, flow);
  }

  /**
   * Get cached engagements for a client
   */
  async getCachedEngagements(clientId: string): Promise<Engagement[] | null> {
    const startTime = performance.now();
    const engagements = (await this.cache.get(`engagements_${clientId}`)) as Engagement[] | null;

    if (engagements) {
      this.recordHit(startTime);
      return engagements;
    }

    this.recordMiss(startTime);
    return null;
  }

  /**
   * Cache engagements for a client
   */
  async setCachedEngagements(clientId: string, engagements: Engagement[]): Promise<void> {
    await this.cache.set(`engagements_${clientId}`, engagements);

    // Pre-cache individual engagements
    engagements.forEach((engagement) => {
      this.cache.set(`engagement_${engagement.id}`, engagement);
    });
  }

  /**
   * Get cached flows for an engagement
   */
  async getCachedFlows(engagementId: string): Promise<Flow[] | null> {
    const startTime = performance.now();
    const flows = (await this.cache.get(`flows_${engagementId}`)) as Flow[] | null;

    if (flows) {
      this.recordHit(startTime);
      return flows;
    }

    this.recordMiss(startTime);
    return null;
  }

  /**
   * Cache flows for an engagement
   */
  async setCachedFlows(engagementId: string, flows: Flow[]): Promise<void> {
    await this.cache.set(`flows_${engagementId}`, flows);

    // Pre-cache individual flows
    flows.forEach((flow) => {
      this.cache.set(`flow_${flow.id}`, flow);
    });
  }

  /**
   * Invalidate related cache entries
   */
  invalidateClientCache(clientId: string): void {
    this.cache.delete(`client_${clientId}`);
    this.cache.delete(`engagements_${clientId}`);
    // Clear pattern matching for related data
    this.cache.clear(`client_${clientId}.*`);
  }

  /**
   * Invalidate engagement cache
   */
  invalidateEngagementCache(engagementId: string): void {
    this.cache.delete(`engagement_${engagementId}`);
    this.cache.delete(`flows_${engagementId}`);
    this.cache.clear(`engagement_${engagementId}.*`);
  }

  /**
   * Pre-fetch commonly accessed contexts
   */
  async prefetchContext(
    userId: string,
    recentClients: string[],
    recentEngagements: string[]
  ): Promise<void> {
    // Pre-fetch recent clients and their engagements
    const prefetchPromises = recentClients.map(async (clientId) => {
      if (!(await this.getCachedClient(clientId))) {
        this.schedulePrefetch(`client_${clientId}`);
      }
      if (!(await this.getCachedEngagements(clientId))) {
        this.schedulePrefetch(`engagements_${clientId}`);
      }
    });

    // Pre-fetch recent engagements and their flows
    recentEngagements.forEach((engagementId) => {
      this.schedulePrefetch(`flows_${engagementId}`);
    });

    // Execute prefetch promises without blocking
    Promise.allSettled(prefetchPromises).catch(console.warn);
  }

  /**
   * Schedule background prefetch
   */
  private schedulePrefetch(key: string): void {
    if (!this.prefetchQueue.has(key)) {
      this.prefetchQueue.add(key);

      // Execute prefetch in next tick to avoid blocking
      setTimeout(() => {
        this.executePrefetch(key);
        this.prefetchQueue.delete(key);
      }, 0);
    }
  }

  /**
   * Execute background prefetch (to be implemented with actual API calls)
   */
  private async executePrefetch(key: string): Promise<void> {
    // This would integrate with the actual API service
    // For now, it's a placeholder for the prefetch mechanism
    console.debug(`Prefetching ${key}`);
  }

  /**
   * Get cache statistics
   */
  getMetrics(): CacheMetrics & { size: number; maxSize: number } {
    return {
      ...this.metrics,
      ...this.cache.stats(),
    };
  }

  /**
   * Clear all cached context data
   */
  clearAll(): void {
    this.cache.clear();
    this.metrics = { hits: 0, misses: 0, hitRate: 0, avgResponseTime: 0 };
    this.responseTimes = [];
  }

  /**
   * Record cache hit
   */
  private recordHit(startTime: number): void {
    const responseTime = performance.now() - startTime;
    this.metrics.hits++;
    this.recordResponseTime(responseTime);
    this.updateHitRate();
  }

  /**
   * Record cache miss
   */
  private recordMiss(startTime: number): void {
    const responseTime = performance.now() - startTime;
    this.metrics.misses++;
    this.recordResponseTime(responseTime);
    this.updateHitRate();
  }

  /**
   * Record response time
   */
  private recordResponseTime(time: number): void {
    this.responseTimes.push(time);

    // Keep only last 100 measurements
    if (this.responseTimes.length > 100) {
      this.responseTimes.shift();
    }

    this.metrics.avgResponseTime =
      this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
  }

  /**
   * Update hit rate
   */
  private updateHitRate(): void {
    const total = this.metrics.hits + this.metrics.misses;
    this.metrics.hitRate = total > 0 ? (this.metrics.hits / total) * 100 : 0;
  }
}

// Singleton instance
export const contextCache = new ContextCacheService();
