/**
 * DialogContext Index
 * Central export file for DialogContext
 */

// Components
export { DialogProvider } from './DialogContext/provider';

// Hooks
// eslint-disable-next-line react-refresh/only-export-components
export { useDialog } from './DialogContext/hooks';

// Types
export type {
  DialogType,
  BaseDialogOptions,
  ConfirmDialogOptions,
  AlertDialogOptions,
  PromptDialogOptions,
  LoadingDialogOptions,
  DialogState,
  DialogContextValue
} from './DialogContext/types';
