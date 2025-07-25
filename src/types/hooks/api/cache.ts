/**
 * Cache Management Hook Types
 *
 * Hook types for client-side caching with support for
 * various storage backends and TTL management.
 */

// Cache Hook Types
export interface UseCacheParams<T = unknown> {
  key: string;
  defaultValue?: T;
  ttl?: number;
  storage?: 'memory' | 'localStorage' | 'sessionStorage' | 'indexedDB';
  serializer?: CacheSerializer<T>;
  validator?: (value: T) => boolean;
  onExpire?: (key: string, value: T) => void;
  onSet?: (key: string, value: T) => void;
  onGet?: (key: string, value: T) => void;
  onDelete?: (key: string) => void;
}

export interface UseCacheReturn<T = unknown> {
  value: T | undefined;
  exists: boolean;
  expired: boolean;
  lastModified?: number;
  ttl?: number;
  set: (value: T, ttl?: number) => void;
  get: () => T | undefined;
  delete: () => void;
  clear: () => void;
  refresh: () => void;
  extend: (ttl: number) => void;
  touch: () => void;
}

// Supporting Types
export interface CacheSerializer<T> {
  serialize: (value: T) => string;
  deserialize: (value: string) => T;
}
