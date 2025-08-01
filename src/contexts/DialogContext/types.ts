/**
 * Dialog Context Types
 */

// Dialog types
export type DialogType = 'confirm' | 'alert' | 'prompt' | 'loading';

export interface BaseDialogOptions {
  title?: string;
  description?: string;
  icon?: 'info' | 'warning' | 'success' | 'error' | 'loading';
  className?: string;
}

export interface ConfirmDialogOptions extends BaseDialogOptions {
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
}

export interface AlertDialogOptions extends BaseDialogOptions {
  confirmText?: string;
}

export interface PromptDialogOptions extends BaseDialogOptions {
  placeholder?: string;
  defaultValue?: string;
  confirmText?: string;
  cancelText?: string;
  validation?: (value: string) => string | null;
}

export interface LoadingDialogOptions extends BaseDialogOptions {
  progress?: number;
  cancelable?: boolean;
}

export interface DialogState {
  id: string;
  type: DialogType;
  options: BaseDialogOptions;
  resolve?: (value: boolean | string | undefined) => void;
  reject?: (reason?: Error | string) => void;
}

export interface DialogContextValue {
  showConfirm: (options: ConfirmDialogOptions) => Promise<boolean>;
  showAlert: (options: AlertDialogOptions) => Promise<void>;
  showPrompt: (options: PromptDialogOptions) => Promise<string | null>;
  showLoading: (options: LoadingDialogOptions) => { close: () => void; update: (options: Partial<LoadingDialogOptions>) => void };
  closeDialog: (id: string) => void;
}
