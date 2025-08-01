import type { ContextStorageData } from './types';
import type { User, Client, Engagement, Flow } from '../AuthContext/types';

// Storage keys with versioning
const STORAGE_VERSION = 'v1';
const STORAGE_KEYS = {
  CONTEXT_DATA: `global_context_${STORAGE_VERSION}`,
  USER_PREFERENCES: `user_preferences_${STORAGE_VERSION}`,
  PERFORMANCE_METRICS: `performance_metrics_${STORAGE_VERSION}`,
  FEATURE_FLAGS: `feature_flags_${STORAGE_VERSION}`,
} as const;

// Storage configuration
const DEFAULT_TTL = 3600000; // 1 hour in milliseconds

interface StoredItem<T> {
  data: T;
  timestamp: number;
  expiry: number;
  version: string;
}

/**
 * Generic storage utility with expiration and versioning support
 */
class Storage {
  private isAvailable(): boolean {
    try {
      const test = '__storage_test__';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  get<T>(key: string): T | null {
    if (!this.isAvailable()) return null;

    try {
      const stored = sessionStorage.getItem(key);
      if (!stored) return null;

      const parsed: StoredItem<T> = JSON.parse(stored);

      // Check version compatibility
      if (parsed.version !== STORAGE_VERSION) {
        sessionStorage.removeItem(key);
        return null;
      }

      // Check expiry
      if (Date.now() > parsed.expiry) {
        sessionStorage.removeItem(key);
        return null;
      }

      return parsed.data;
    } catch (error) {
      console.warn(`Failed to retrieve data from storage for key: ${key}`, error);
      sessionStorage.removeItem(key);
      return null;
    }
  }

  set<T>(key: string, data: T, ttlMs: number = DEFAULT_TTL): boolean {
    if (!this.isAvailable()) return false;

    try {
      const stored: StoredItem<T> = {
        data,
        timestamp: Date.now(),
        expiry: Date.now() + ttlMs,
        version: STORAGE_VERSION,
      };

      sessionStorage.setItem(key, JSON.stringify(stored));
      return true;
    } catch (error) {
      console.warn(`Failed to store data for key: ${key}`, error);
      return false;
    }
  }

  remove(key: string): void {
    if (!this.isAvailable()) return;
    sessionStorage.removeItem(key);
  }

  clear(): void {
    if (!this.isAvailable()) return;

    // Only clear items with our versioned keys
    Object.values(STORAGE_KEYS).forEach(key => {
      sessionStorage.removeItem(key);
    });
  }

  getSize(): number {
    if (!this.isAvailable()) return 0;

    let totalSize = 0;
    Object.values(STORAGE_KEYS).forEach(key => {
      const item = sessionStorage.getItem(key);
      if (item) {
        totalSize += item.length;
      }
    });
    return totalSize;
  }
}

// Storage instance
const storage = new Storage();

/**
 * Context-specific storage utilities
 */
export const contextStorage = {
  /**
   * Get stored context data
   */
  getContextData(): ContextStorageData | null {
    return storage.get<ContextStorageData>(STORAGE_KEYS.CONTEXT_DATA);
  },

  /**
   * Store context data
   */
  setContextData(data: {
    user: User | null;
    client: Client | null;
    engagement: Engagement | null;
    flow: Flow | null;
  }): boolean {
    const contextData: ContextStorageData = {
      ...data,
      timestamp: Date.now(),
      version: STORAGE_VERSION,
    };

    return storage.set(STORAGE_KEYS.CONTEXT_DATA, contextData);
  },

  /**
   * Clear context data
   */
  clearContextData(): void {
    storage.remove(STORAGE_KEYS.CONTEXT_DATA);
  },

  /**
   * Check if stored context is still valid
   */
  isContextDataValid(): boolean {
    const data = this.getContextData();
    if (!data) return false;

    // Check if data is less than 1 hour old
    const maxAge = 3600000; // 1 hour
    return (Date.now() - data.timestamp) < maxAge;
  },
};

/**
 * User preferences storage
 */
export const preferencesStorage = {
  get<T>(key: string, defaultValue: T): T {
    const prefs = storage.get<Record<string, unknown>>(STORAGE_KEYS.USER_PREFERENCES) || {};
    return prefs[key] !== undefined ? prefs[key] as T : defaultValue;
  },

  set(key: string, value: unknown): boolean {
    const prefs = storage.get<Record<string, unknown>>(STORAGE_KEYS.USER_PREFERENCES) || {};
    prefs[key] = value;
    return storage.set(STORAGE_KEYS.USER_PREFERENCES, prefs);
  },

  remove(key: string): boolean {
    const prefs = storage.get<Record<string, unknown>>(STORAGE_KEYS.USER_PREFERENCES) || {};
    delete prefs[key];
    return storage.set(STORAGE_KEYS.USER_PREFERENCES, prefs);
  },

  clear(): void {
    storage.remove(STORAGE_KEYS.USER_PREFERENCES);
  },
};

/**
 * Performance metrics storage
 */
export const performanceStorage = {
  getMetrics(): unknown | null {
    return storage.get(STORAGE_KEYS.PERFORMANCE_METRICS);
  },

  setMetrics(metrics: unknown): boolean {
    return storage.set(STORAGE_KEYS.PERFORMANCE_METRICS, metrics, 86400000); // 24 hours
  },

  clearMetrics(): void {
    storage.remove(STORAGE_KEYS.PERFORMANCE_METRICS);
  },
};

/**
 * Feature flags storage
 */
export const featureFlagsStorage = {
  getFlags(): Record<string, boolean> | null {
    return storage.get(STORAGE_KEYS.FEATURE_FLAGS);
  },

  setFlags(flags: Record<string, boolean>): boolean {
    return storage.set(STORAGE_KEYS.FEATURE_FLAGS, flags, 86400000); // 24 hours
  },

  clearFlags(): void {
    storage.remove(STORAGE_KEYS.FEATURE_FLAGS);
  },
};

/**
 * Utility function to check storage health and cleanup if needed
 */
export const maintainStorage = (): void => {
  try {
    const size = storage.getSize();
    const maxSize = 5 * 1024 * 1024; // 5MB limit

    if (size > maxSize) {
      console.warn('Storage size limit approaching, clearing old data');
      storage.clear();
    }
  } catch (error) {
    console.warn('Failed to maintain storage:', error);
    storage.clear();
  }
};

/**
 * Check if context data exists and is valid
 */
export const hasValidStoredContext = (): boolean => {
  return contextStorage.isContextDataValid();
};

/**
 * Export storage for debugging in development
 */
if (process.env.NODE_ENV === 'development') {
  (window as typeof window & { __globalContextStorage?: unknown }).__globalContextStorage = {
    storage,
    contextStorage,
    preferencesStorage,
    performanceStorage,
    featureFlagsStorage,
    maintainStorage,
    STORAGE_KEYS,
  };
}
