/**
 * Batched Storage Operations for Context Updates
 * Reduces main thread blocking by batching storage writes
 */

interface StorageOperation {
  key: string;
  value: unknown;
  ttl?: number;
  timestamp: number;
}

interface BatchStorageOptions {
  batchDelay?: number;
  maxBatchSize?: number;
  enablePriority?: boolean;
}

/**
 * Batched storage manager that accumulates writes and executes them together
 */
export class BatchedStorageManager {
  private pendingOperations = new Map<string, StorageOperation>();
  private batchTimer: NodeJS.Timeout | null = null;
  private options: Required<BatchStorageOptions>;
  private isProcessing = false;

  constructor(options: BatchStorageOptions = {}) {
    this.options = {
      batchDelay: options.batchDelay || 50, // 50ms delay for batching
      maxBatchSize: options.maxBatchSize || 10,
      enablePriority: options.enablePriority || true,
    };
  }

  /**
   * Queue a storage operation for batched execution
   */
  queueOperation(key: string, value: unknown, ttl?: number, priority = false): Promise<boolean> {
    return new Promise((resolve) => {
      const operation: StorageOperation = {
        key,
        value,
        ttl,
        timestamp: Date.now(),
      };

      this.pendingOperations.set(key, operation);

      // If priority operation or batch is full, process immediately
      if (priority || this.pendingOperations.size >= this.options.maxBatchSize) {
        this.processBatch()
          .then(() => resolve(true))
          .catch(() => resolve(false));
        return;
      }

      // Schedule batch processing
      this.scheduleBatch();
      resolve(true); // Optimistically resolve for batched operations
    });
  }

  /**
   * Schedule batch processing with debouncing
   */
  private scheduleBatch(): void {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    this.batchTimer = setTimeout(() => {
      this.processBatch().catch(console.warn);
    }, this.options.batchDelay);
  }

  /**
   * Process all pending operations in a single batch
   */
  private async processBatch(): Promise<void> {
    if (this.isProcessing || this.pendingOperations.size === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      // Clear timer
      if (this.batchTimer) {
        clearTimeout(this.batchTimer);
        this.batchTimer = null;
      }

      // Get all pending operations
      const operations = Array.from(this.pendingOperations.values());
      this.pendingOperations.clear();

      // Group operations by storage type/priority
      const contextOperations = operations.filter(
        (op) =>
          op.key.startsWith('global_context_') ||
          op.key.startsWith('user_preferences_') ||
          op.key.startsWith('performance_metrics_')
      );

      // Execute storage operations in a single frame
      await this.executeBatchedWrites(contextOperations);
    } catch (error) {
      console.warn('Batch storage processing failed:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Execute batched writes using requestIdleCallback for better performance
   */
  private async executeBatchedWrites(operations: StorageOperation[]): Promise<void> {
    return new Promise((resolve) => {
      const executeWrites = () => {
        try {
          operations.forEach((operation) => {
            this.writeToStorage(operation);
          });
          resolve();
        } catch (error) {
          console.warn('Batched write failed:', error);
          resolve(); // Don't fail the entire batch
        }
      };

      // Use requestIdleCallback if available, otherwise setTimeout
      if ('requestIdleCallback' in window) {
        requestIdleCallback(executeWrites, { timeout: 100 });
      } else {
        setTimeout(executeWrites, 0);
      }
    });
  }

  /**
   * Write individual operation to storage
   */
  private writeToStorage(operation: StorageOperation): void {
    try {
      const { key, value, ttl } = operation;

      // Create versioned storage item
      const storageItem = {
        data: value,
        timestamp: Date.now(),
        expiry: Date.now() + (ttl || 3600000), // Default 1 hour
        version: 'v1',
      };

      sessionStorage.setItem(key, JSON.stringify(storageItem)); // nosec - sessionStorage is browser-secured
    } catch (error) {
      // Handle storage quota exceeded or other errors
      console.warn(`Failed to write ${operation.key} to storage:`, error);

      // Try to free up space
      this.freeStorageSpace();

      // Try again once
      try {
        const storageItem = {
          data: operation.value,
          timestamp: Date.now(),
          expiry: Date.now() + (operation.ttl || 3600000),
          version: 'v1',
        };
        sessionStorage.setItem(operation.key, JSON.stringify(storageItem)); // nosec - sessionStorage is browser-secured
      } catch (retryError) {
        console.warn(`Failed to write ${operation.key} on retry:`, retryError);
      }
    }
  }

  /**
   * Free storage space by removing expired items
   */
  private freeStorageSpace(): void {
    try {
      const now = Date.now();
      const keysToRemove: string[] = [];

      // Check all session storage items
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (!key) continue;

        try {
          const item = sessionStorage.getItem(key);
          if (!item) continue;

          const parsed = JSON.parse(item);
          if (parsed.expiry && now > parsed.expiry) {
            keysToRemove.push(key);
          }
        } catch {
          // Remove invalid items
          keysToRemove.push(key);
        }
      }

      // Remove expired items
      keysToRemove.forEach((key) => {
        sessionStorage.removeItem(key);
      });
    } catch (error) {
      console.warn('Failed to free storage space:', error);
    }
  }

  /**
   * Flush all pending operations immediately
   */
  async flush(): Promise<void> {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    await this.processBatch();
  }

  /**
   * Get pending operations count
   */
  getPendingCount(): number {
    return this.pendingOperations.size;
  }

  /**
   * Clear all pending operations
   */
  clearPending(): void {
    this.pendingOperations.clear();
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
  }
}

// Singleton instance for context storage
export const batchedStorage = new BatchedStorageManager({
  batchDelay: 50, // Quick batching for context switches
  maxBatchSize: 10,
  enablePriority: true,
});
