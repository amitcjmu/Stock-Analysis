import React from 'react'
import { createContext, useContext, useState } from 'react'
import { useCallback } from 'react'
import { ReactNode } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Info } from 'lucide-react'
import { AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react'

// Dialog types
type DialogType = 'confirm' | 'alert' | 'prompt' | 'loading';

interface BaseDialogOptions {
  title?: string;
  description?: string;
  icon?: 'info' | 'warning' | 'success' | 'error' | 'loading';
  className?: string;
}

interface ConfirmDialogOptions extends BaseDialogOptions {
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
}

interface AlertDialogOptions extends BaseDialogOptions {
  confirmText?: string;
}

interface PromptDialogOptions extends BaseDialogOptions {
  placeholder?: string;
  defaultValue?: string;
  confirmText?: string;
  cancelText?: string;
  validation?: (value: string) => string | null;
}

interface LoadingDialogOptions extends BaseDialogOptions {
  progress?: number;
  cancelable?: boolean;
}

interface DialogState {
  id: string;
  type: DialogType;
  options: BaseDialogOptions;
  resolve?: (value: boolean | string | undefined) => void;
  reject?: (reason?: Error | string) => void;
}

interface DialogContextValue {
  showConfirm: (options: ConfirmDialogOptions) => Promise<boolean>;
  showAlert: (options: AlertDialogOptions) => Promise<void>;
  showPrompt: (options: PromptDialogOptions) => Promise<string | null>;
  showLoading: (options: LoadingDialogOptions) => { close: () => void; update: (options: Partial<LoadingDialogOptions>) => void };
  closeDialog: (id: string) => void;
}

const DialogContext = createContext<DialogContextValue | undefined>(undefined);

export const useDialog = () => {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error('useDialog must be used within a DialogProvider');
  }
  return context;
};

interface DialogProviderProps {
  children: ReactNode;
}

// Separate component for Prompt Dialog to avoid hooks inside conditional
const PromptDialogComponent: React.FC<{ 
  dialog: DialogState; 
  options: PromptDialogOptions; 
  closeDialog: (id: string) => void;
  getIcon: (icon?: DialogIcon) => JSX.Element;
}> = ({ dialog, options, closeDialog, getIcon }) => {
  const [value, setValue] = useState(options.defaultValue || '');
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = () => {
    if (options.validation) {
      const validationError = options.validation(value);
      if (validationError) {
        setError(validationError);
        return;
      }
    }
    dialog.resolve?.(value);
    closeDialog(dialog.id);
  };

  return (
    <Dialog
      open={true}
      onOpenChange={(open) => {
        if (!open) {
          dialog.resolve?.(null);
          closeDialog(dialog.id);
        }
      }}
    >
      <DialogContent className={options.className}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getIcon(options.icon)}
            {options.title || 'Input Required'}
          </DialogTitle>
          {options.description && (
            <DialogDescription>{options.description}</DialogDescription>
          )}
        </DialogHeader>
        <div className="space-y-2 py-4">
          <Input
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setError(null);
            }}
            placeholder={options.placeholder}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleConfirm();
              }
            }}
          />
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              dialog.resolve?.(null);
              closeDialog(dialog.id);
            }}
          >
            {options.cancelText || 'Cancel'}
          </Button>
          <Button onClick={handleConfirm}>
            {options.confirmText || 'OK'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const DialogProvider: React.FC<DialogProviderProps> = ({ children }) => {
  const [dialogs, setDialogs] = useState<DialogState[]>([]);

  const generateId = () => `dialog-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const closeDialog = useCallback((id: string) => {
    setDialogs((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const showConfirm = useCallback(
    (options: ConfirmDialogOptions): Promise<boolean> => {
      return new Promise((resolve) => {
        const id = generateId();
        setDialogs((prev) => [
          ...prev,
          {
            id,
            type: 'confirm',
            options,
            resolve,
          },
        ]);
      });
    },
    []
  );

  const showAlert = useCallback(
    (options: AlertDialogOptions): Promise<void> => {
      return new Promise((resolve) => {
        const id = generateId();
        setDialogs((prev) => [
          ...prev,
          {
            id,
            type: 'alert',
            options,
            resolve,
          },
        ]);
      });
    },
    []
  );

  const showPrompt = useCallback(
    (options: PromptDialogOptions): Promise<string | null> => {
      return new Promise((resolve) => {
        const id = generateId();
        setDialogs((prev) => [
          ...prev,
          {
            id,
            type: 'prompt',
            options,
            resolve,
          },
        ]);
      });
    },
    []
  );

  const showLoading = useCallback(
    (options: LoadingDialogOptions) => {
      const id = generateId();
      let currentResolve: ((value: void) => void) | undefined;

      const promise = new Promise<void>((resolve) => {
        currentResolve = resolve;
        setDialogs((prev) => [
          ...prev,
          {
            id,
            type: 'loading',
            options,
            resolve,
          },
        ]);
      });

      return {
        close: () => {
          closeDialog(id);
          currentResolve?.();
        },
        update: (newOptions: Partial<LoadingDialogOptions>) => {
          setDialogs((prev) =>
            prev.map((d) =>
              d.id === id
                ? { ...d, options: { ...d.options, ...newOptions } }
                : d
            )
          );
        },
      };
    },
    [closeDialog]
  );

  const getIcon = (iconType?: string) => {
    switch (iconType) {
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'loading':
        return <Loader2 className="h-5 w-5 animate-spin" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-600" />;
    }
  };

  const value: DialogContextValue = {
    showConfirm,
    showAlert,
    showPrompt,
    showLoading,
    closeDialog,
  };

  return (
    <DialogContext.Provider value={value}>
      {children}
      {dialogs.map((dialog) => {
        if (dialog.type === 'confirm') {
          const options = dialog.options as ConfirmDialogOptions;
          return (
            <AlertDialog
              key={dialog.id}
              open={true}
              onOpenChange={(open) => {
                if (!open) {
                  dialog.resolve?.(false);
                  closeDialog(dialog.id);
                }
              }}
            >
              <AlertDialogContent className={options.className}>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    {getIcon(options.icon)}
                    {options.title || 'Confirm'}
                  </AlertDialogTitle>
                  {options.description && (
                    <AlertDialogDescription>
                      {options.description}
                    </AlertDialogDescription>
                  )}
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel
                    onClick={() => {
                      dialog.resolve?.(false);
                      closeDialog(dialog.id);
                    }}
                  >
                    {options.cancelText || 'Cancel'}
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => {
                      dialog.resolve?.(true);
                      closeDialog(dialog.id);
                    }}
                    className={
                      options.variant === 'destructive'
                        ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                        : ''
                    }
                  >
                    {options.confirmText || 'Confirm'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          );
        }

        if (dialog.type === 'alert') {
          const options = dialog.options as AlertDialogOptions;
          return (
            <AlertDialog
              key={dialog.id}
              open={true}
              onOpenChange={(open) => {
                if (!open) {
                  dialog.resolve?.(undefined);
                  closeDialog(dialog.id);
                }
              }}
            >
              <AlertDialogContent className={options.className}>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    {getIcon(options.icon)}
                    {options.title || 'Alert'}
                  </AlertDialogTitle>
                  {options.description && (
                    <AlertDialogDescription>
                      {options.description}
                    </AlertDialogDescription>
                  )}
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogAction
                    onClick={() => {
                      dialog.resolve?.(undefined);
                      closeDialog(dialog.id);
                    }}
                  >
                    {options.confirmText || 'OK'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          );
        }

        if (dialog.type === 'prompt') {
          const options = dialog.options as PromptDialogOptions;
          return (
            <PromptDialogComponent
              key={dialog.id}
              dialog={dialog}
              options={options}
              closeDialog={closeDialog}
              getIcon={getIcon}
            />
          );
        }

        if (dialog.type === 'loading') {
          const options = dialog.options as LoadingDialogOptions;
          return (
            <Dialog
              key={dialog.id}
              open={true}
              onOpenChange={(open) => {
                if (!open && options.cancelable) {
                  dialog.resolve?.(undefined);
                  closeDialog(dialog.id);
                }
              }}
            >
              <DialogContent className={options.className}>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    {getIcon('loading')}
                    {options.title || 'Loading...'}
                  </DialogTitle>
                  {options.description && (
                    <DialogDescription>{options.description}</DialogDescription>
                  )}
                </DialogHeader>
                {options.progress !== undefined && (
                  <div className="py-4">
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${options.progress}%` }}
                      />
                    </div>
                    <p className="text-sm text-muted-foreground mt-2 text-center">
                      {options.progress}%
                    </p>
                  </div>
                )}
                {options.cancelable && (
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => {
                        dialog.resolve?.(undefined);
                        closeDialog(dialog.id);
                      }}
                    >
                      Cancel
                    </Button>
                  </DialogFooter>
                )}
              </DialogContent>
            </Dialog>
          );
        }

        return null;
      })}
    </DialogContext.Provider>
  );
};