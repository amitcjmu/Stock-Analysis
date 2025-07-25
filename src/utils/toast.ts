/**
 * Toast Notification System
 * MFO-078: Add error handling with toast notifications
 *
 * Simple toast notification system for flow operations
 */

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastOptions {
  title: string;
  message?: string;
  type?: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface Toast extends ToastOptions {
  id: string;
  timestamp: Date;
}

// Toast store
class ToastStore {
  private toasts: Toast[] = [];
  private listeners: Array<(toasts: Toast[]) => void> = [];
  private idCounter = 0;

  public subscribe(listener: (toasts: Toast[]) => void): () => void {
    this.listeners.push(listener);
    listener(this.toasts);

    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  public show(options: ToastOptions): string {
    const id = `toast-${++this.idCounter}`;
    const toast: Toast = {
      ...options,
      id,
      type: options.type || 'info',
      duration: options.duration || 5000,
      timestamp: new Date()
    };

    this.toasts = [...this.toasts, toast];
    this.notify();

    // Auto-dismiss after duration
    if (toast.duration > 0) {
      setTimeout(() => {
        this.dismiss(id);
      }, toast.duration);
    }

    return id;
  }

  public dismiss(id: string): void {
    this.toasts = this.toasts.filter(t => t.id !== id);
    this.notify();
  }

  public dismissAll(): void {
    this.toasts = [];
    this.notify();
  }

  private notify(): void {
    this.listeners.forEach(listener => listener(this.toasts));
  }
}

// Global toast instance
export const toastStore: ToastStore = new ToastStore();

// Convenience methods
export const toast: {
  success: (title: string, message?: string, options?: Partial<ToastOptions>) => string;
  error: (title: string, message?: string, options?: Partial<ToastOptions>) => string;
  warning: (title: string, message?: string, options?: Partial<ToastOptions>) => string;
  info: (title: string, message?: string, options?: Partial<ToastOptions>) => string;
  dismiss: (id: string) => void;
  dismissAll: () => void;
} = {
  success: (title: string, message?: string, options?: Partial<ToastOptions>) =>
    toastStore.show({ ...options, title, message, type: 'success' }),

  error: (title: string, message?: string, options?: Partial<ToastOptions>) =>
    toastStore.show({ ...options, title, message, type: 'error' }),

  warning: (title: string, message?: string, options?: Partial<ToastOptions>) =>
    toastStore.show({ ...options, title, message, type: 'warning' }),

  info: (title: string, message?: string, options?: Partial<ToastOptions>) =>
    toastStore.show({ ...options, title, message, type: 'info' }),

  dismiss: (id: string) => toastStore.dismiss(id),

  dismissAll: () => toastStore.dismissAll()
};

// Flow-specific toast helpers
export const flowToast: {
  created: (flowType: string, flowId: string) => string;
  executing: (phase: string) => string;
  phaseCompleted: (phase: string) => string;
  paused: (flowId: string) => string;
  resumed: (flowId: string) => string;
  deleted: (flowId: string) => string;
  error: (error: Error | string, phase?: string) => void;
  networkError: () => string;
  validationError: (errors: string[]) => string;
  authError: () => string;
} = {
  created: (flowType: string, flowId: string) =>
    toast.success(`${flowType} flow created`, `Flow ID: ${flowId}`),

  executing: (phase: string) =>
    toast.info(`Executing phase`, phase),

  phaseCompleted: (phase: string) =>
    toast.success(`Phase completed`, phase),

  paused: (flowId: string) =>
    toast.warning('Flow paused', `Flow ${flowId} has been paused`),

  resumed: (flowId: string) =>
    toast.info('Flow resumed', `Flow ${flowId} has been resumed`),

  deleted: (flowId: string) =>
    toast.info('Flow deleted', `Flow ${flowId} has been deleted`),

  error: (error: Error | string, phase?: string) => {
    const message = typeof error === 'string' ? error : error.message;
    const title = phase ? `Error in ${phase}` : 'Flow error';
    toast.error(title, message, {
      duration: 8000,
      action: {
        label: 'Retry',
        onClick: () => window.location.reload()
      }
    });
  },

  networkError: () =>
    toast.error('Network error', 'Please check your connection and try again'),

  validationError: (errors: string[]) =>
    toast.error('Validation failed', errors.join(', ')),

  authError: () =>
    toast.error('Authentication error', 'Please log in again', {
      action: {
        label: 'Login',
        onClick: () => window.location.href = '/login'
      }
    })
};
