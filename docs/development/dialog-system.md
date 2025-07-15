# Dialog System Documentation

## Overview

The dialog system provides a centralized, React-based solution for displaying dialogs throughout the application. It replaces native browser dialogs (`window.confirm`, `window.alert`, `window.prompt`) with fully-styled React components that are Playwright-compatible and provide a consistent user experience.

## Features

- **Centralized Dialog Management**: All dialogs are managed through a single context provider
- **Type-Safe**: Full TypeScript support with proper typing for all dialog types
- **Playwright Compatible**: React-based dialogs work seamlessly with E2E testing
- **Consistent Styling**: Uses shadcn/ui components for consistent appearance
- **Promise-Based API**: Simple async/await syntax for dialog interactions
- **Icon Support**: Built-in icons for different dialog types (info, warning, error, success)
- **Loading Dialogs**: Support for progress tracking during long operations
- **Input Validation**: Built-in validation support for prompt dialogs

## Setup

The dialog system is automatically available throughout the application via the `DialogProvider` in `App.tsx`.

## Usage

### Import the Hook

```typescript
import { useDialog } from '@/hooks/useDialog';
```

### Basic Examples

#### Confirmation Dialog

```typescript
const dialog = useDialog();

const handleDelete = async () => {
  const confirmed = await dialog.confirm({
    title: 'Delete Item',
    description: 'Are you sure you want to delete this item? This action cannot be undone.',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    variant: 'destructive',
    icon: 'warning'
  });

  if (confirmed) {
    // Perform deletion
  }
};
```

#### Alert Dialog

```typescript
const dialog = useDialog();

// Success alert
await dialog.success('Your changes have been saved successfully.');

// Error alert
await dialog.error('Failed to save changes. Please try again.');

// Warning alert
await dialog.warning('This action may take several minutes to complete.');

// Info alert
await dialog.info('New features are available in this release.');
```

#### Prompt Dialog

```typescript
const dialog = useDialog();

const handleRename = async () => {
  const newName = await dialog.prompt({
    title: 'Rename Item',
    description: 'Enter a new name for this item.',
    placeholder: 'Item name...',
    defaultValue: currentName,
    validation: (value) => {
      if (value.length < 3) {
        return 'Name must be at least 3 characters';
      }
      if (value.length > 50) {
        return 'Name must be less than 50 characters';
      }
      return null;
    }
  });

  if (newName) {
    // User entered a valid name
    await updateItemName(newName);
  }
};
```

#### Loading Dialog

```typescript
const dialog = useDialog();

const handleLongOperation = async () => {
  const loader = dialog.loading({
    title: 'Processing',
    description: 'Please wait while we process your request...',
    cancelable: true
  });

  try {
    for (let i = 0; i <= 100; i += 10) {
      await processChunk(i);
      loader.update({ progress: i });
    }
    
    loader.close();
    await dialog.success('Processing completed successfully!');
  } catch (error) {
    loader.close();
    await dialog.error('Processing failed. Please try again.');
  }
};
```

### Utility Methods

The dialog hook provides several utility methods for common scenarios:

```typescript
// Delete confirmation with standard messaging
const confirmed = await dialog.confirmDelete('Important Document');

// Unsaved changes confirmation
const shouldLeave = await dialog.confirmUnsavedChanges();
```

## Migration Guide

### Replacing Native Dialogs

#### Before (Native Dialogs)
```typescript
// Confirmation
if (window.confirm('Are you sure?')) {
  deleteItem();
}

// Alert
window.alert('Operation completed');

// Prompt
const name = window.prompt('Enter name:');
if (name) {
  saveName(name);
}
```

#### After (React Dialogs)
```typescript
const dialog = useDialog();

// Confirmation
if (await dialog.confirm({ title: 'Are you sure?' })) {
  deleteItem();
}

// Alert
await dialog.alert({ title: 'Operation completed' });

// Prompt
const name = await dialog.prompt({ title: 'Enter name:' });
if (name) {
  saveName(name);
}
```

## Testing

The dialog system is fully compatible with Playwright and other E2E testing tools:

```typescript
// Playwright test example
test('delete flow confirmation', async ({ page }) => {
  await page.click('[data-testid="delete-button"]');
  
  // Dialog appears in the DOM
  await expect(page.getByRole('alertdialog')).toBeVisible();
  await expect(page.getByText('Delete Item')).toBeVisible();
  
  // Confirm deletion
  await page.getByRole('button', { name: 'Delete' }).click();
  
  // Verify deletion occurred
  await expect(page.getByText('Item deleted')).toBeVisible();
});
```

## API Reference

### Dialog Options

#### ConfirmDialogOptions
```typescript
interface ConfirmDialogOptions {
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
  icon?: 'info' | 'warning' | 'success' | 'error';
  className?: string;
}
```

#### AlertDialogOptions
```typescript
interface AlertDialogOptions {
  title?: string;
  description?: string;
  confirmText?: string;
  icon?: 'info' | 'warning' | 'success' | 'error';
  className?: string;
}
```

#### PromptDialogOptions
```typescript
interface PromptDialogOptions {
  title?: string;
  description?: string;
  placeholder?: string;
  defaultValue?: string;
  confirmText?: string;
  cancelText?: string;
  validation?: (value: string) => string | null;
  icon?: 'info' | 'warning' | 'success' | 'error';
  className?: string;
}
```

#### LoadingDialogOptions
```typescript
interface LoadingDialogOptions {
  title?: string;
  description?: string;
  progress?: number;
  cancelable?: boolean;
  className?: string;
}
```

## Best Practices

1. **Use Semantic Methods**: Prefer `dialog.success()`, `dialog.error()` over generic `dialog.alert()`
2. **Provide Context**: Always include descriptive titles and messages
3. **Use Appropriate Icons**: Match icon types to the dialog purpose
4. **Validate User Input**: Use the validation function in prompt dialogs
5. **Handle Cancellation**: Always handle both confirmation and cancellation cases
6. **Loading States**: Use loading dialogs for operations longer than 2 seconds
7. **Error Handling**: Wrap async operations in try-catch and show appropriate error dialogs

## Components Used

The dialog system is built on top of:
- `@radix-ui/react-dialog` - Base dialog primitives
- `@radix-ui/react-alert-dialog` - Alert dialog primitives
- `shadcn/ui` components - Styled dialog components
- `lucide-react` - Icon library