/**
 * Cache management utilities for API responses.
 * Provides in-memory caching with TTL and size limits.
 */

export interface CacheOptions {
  keyPrefix?: string;
  defaultTtl?: number;
  maxSize?: number;
  cleanupInterval?: number;
}

interface CacheEntry {
  data: unknown;
  expiry: number;
  lastAccessed: number;
}

export class CacheManager {
  private cache = new Map<string, CacheEntry>();
  private options: Required<CacheOptions>;
  private cleanupTimer?: NodeJS.Timeout;

  constructor(options: CacheOptions = {}) {
    this.options = {
      keyPrefix: options.keyPrefix || 'cache_',
      defaultTtl: options.defaultTtl || 5 * 60 * 1000, // 5 minutes
      maxSize: options.maxSize || 100,
      cleanupInterval: options.cleanupInterval || 60 * 1000 // 1 minute
    };

    this.startCleanupTimer();
  }

  async get(key: string): Promise<unknown> {
    const fullKey = this.buildKey(key);
    const entry = this.cache.get(fullKey);

    if (!entry) {
      return null;
    }

    if (Date.now() > entry.expiry) {
      this.cache.delete(fullKey);
      return null;
    }

    entry.lastAccessed = Date.now();
    return entry.data;
  }

  async set(key: string, data: unknown, ttl?: number): Promise<void> {
    const fullKey = this.buildKey(key);
    const expiry = Date.now() + (ttl || this.options.defaultTtl);

    // Check size limit
    if (this.cache.size >= this.options.maxSize && !this.cache.has(fullKey)) {
      this.evictLeastRecentlyUsed();
    }

    this.cache.set(fullKey, {
      data,
      expiry,
      lastAccessed: Date.now()
    });
  }

  async delete(key: string): Promise<boolean> {
    const fullKey = this.buildKey(key);
    return this.cache.delete(fullKey);
  }

  clear(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    const regex = new RegExp(pattern);
    const keysToDelete: string[] = [];

    this.cache.forEach((_, key) => {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  size(): number {
    return this.cache.size;
  }

  stats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    expiredEntries: number;
  } {
    const now = Date.now();
    let expiredEntries = 0;

    this.cache.forEach((entry) => {
      if (now > entry.expiry) {
        expiredEntries++;
      }
    });

    return {
      size: this.cache.size,
      maxSize: this.options.maxSize,
      hitRate: 0, // Would need hit/miss tracking for accurate calculation
      expiredEntries
    };
  }

  private buildKey(key: string): string {
    return `${this.options.keyPrefix}${key}`;
  }

  private evictLeastRecentlyUsed(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    this.cache.forEach((entry, key) => {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed;
        oldestKey = key;
      }
    });

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  private startCleanupTimer(): void {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.options.cleanupInterval);
  }

  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    this.cache.forEach((entry, key) => {
      if (now > entry.expiry) {
        expiredKeys.push(key);
      }
    });

    expiredKeys.forEach(key => this.cache.delete(key));
  }

  destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }
    this.cache.clear();
  }
}
