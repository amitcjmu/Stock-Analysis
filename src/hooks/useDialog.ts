import { useDialog as useDialogContext } from '@/contexts/DialogContext';

/**
 * Hook for displaying standardized dialogs throughout the application
 *
 * @example
 * ```tsx
 * const dialog = useDialog();
 *
 * // Confirmation dialog
 * const confirmed = await dialog.confirm({
 *   title: 'Delete Item',
 *   description: 'Are you sure you want to delete this item?',
 *   confirmText: 'Delete',
 *   cancelText: 'Cancel',
 *   variant: 'destructive'
 * });
 *
 * // Alert dialog
 * await dialog.alert({
 *   title: 'Success',
 *   description: 'Your changes have been saved.',
 *   icon: 'success'
 * });
 *
 * // Prompt dialog
 * const name = await dialog.prompt({
 *   title: 'Enter Name',
 *   description: 'Please enter a name for the new item.',
 *   placeholder: 'Item name...',
 *   validation: (value) => value.length < 3 ? 'Name must be at least 3 characters' : null
 * });
 *
 * // Loading dialog
 * const loader = dialog.loading({
 *   title: 'Processing',
 *   description: 'Please wait while we process your request...'
 * });
 * // Update progress
 * loader.update({ progress: 50 });
 * // Close when done
 * loader.close();
 * ```
 */
export const useDialog = () => {
  const context = useDialogContext();

  return {
    /**
     * Show a confirmation dialog
     * @returns Promise<boolean> - true if confirmed, false if cancelled
     */
    confirm: context.showConfirm,

    /**
     * Show an alert dialog
     * @returns Promise<void> - resolves when dialog is closed
     */
    alert: context.showAlert,

    /**
     * Show a prompt dialog for user input
     * @returns Promise<string | null> - user input or null if cancelled
     */
    prompt: context.showPrompt,

    /**
     * Show a loading dialog
     * @returns Object with close() and update() methods
     */
    loading: context.showLoading,

    /**
     * Utility methods for common scenarios
     */
    error: (message: string, title = 'Error') =>
      context.showAlert({
        title,
        description: message,
        icon: 'error',
      }),

    success: (message: string, title = 'Success') =>
      context.showAlert({
        title,
        description: message,
        icon: 'success',
      }),

    warning: (message: string, title = 'Warning') =>
      context.showAlert({
        title,
        description: message,
        icon: 'warning',
      }),

    info: (message: string, title = 'Information') =>
      context.showAlert({
        title,
        description: message,
        icon: 'info',
      }),

    /**
     * Confirm deletion with standard destructive styling
     */
    confirmDelete: (itemName?: string) =>
      context.showConfirm({
        title: 'Delete Item',
        description: itemName
          ? `Are you sure you want to delete "${itemName}"? This action cannot be undone.`
          : 'Are you sure you want to delete this item? This action cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        variant: 'destructive',
        icon: 'warning',
      }),

    /**
     * Confirm navigation away from unsaved changes
     */
    confirmUnsavedChanges: () =>
      context.showConfirm({
        title: 'Unsaved Changes',
        description: 'You have unsaved changes. Are you sure you want to leave this page?',
        confirmText: 'Leave',
        cancelText: 'Stay',
        icon: 'warning',
      }),
  };
};
