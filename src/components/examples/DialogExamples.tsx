import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useDialog } from '@/hooks/useDialog';

/**
 * Example component demonstrating the usage of the dialog system
 * This replaces all native browser dialogs with React-based alternatives
 */
export const DialogExamples: React.FC = () => {
  const dialog = useDialog();

  // Example: Basic confirmation
  const handleBasicConfirm = async () => {
    const confirmed = await dialog.confirm({
      title: 'Confirm Action',
      description: 'Are you sure you want to proceed with this action?',
    });
    
    if (confirmed) {
      await dialog.success('Action completed successfully!');
    }
  };

  // Example: Destructive confirmation
  const handleDelete = async () => {
    const confirmed = await dialog.confirm({
      title: 'Delete Item',
      description: 'This will permanently delete the selected item. This action cannot be undone.',
      confirmText: 'Delete',
      cancelText: 'Keep',
      variant: 'destructive',
      icon: 'warning',
    });
    
    if (confirmed) {
      await dialog.success('Item deleted successfully');
    }
  };

  // Example: Using utility method for delete
  const handleQuickDelete = async () => {
    const confirmed = await dialog.confirmDelete('Important Document');
    if (confirmed) {
      await dialog.success('Document deleted');
    }
  };

  // Example: Prompt for user input
  const handleRename = async () => {
    const newName = await dialog.prompt({
      title: 'Rename Item',
      description: 'Enter a new name for this item',
      placeholder: 'New name...',
      defaultValue: 'Current Name',
      validation: (value) => {
        if (!value.trim()) return 'Name cannot be empty';
        if (value.length < 3) return 'Name must be at least 3 characters';
        if (value.length > 50) return 'Name must be less than 50 characters';
        return null;
      },
    });

    if (newName) {
      await dialog.success(`Item renamed to: ${newName}`);
    }
  };

  // Example: Different alert types
  const handleAlerts = async () => {
    await dialog.info('This is an informational message');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    await dialog.warning('This is a warning message');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    await dialog.error('This is an error message');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    await dialog.success('This is a success message');
  };

  // Example: Loading dialog with progress
  const handleLongOperation = async () => {
    const loader = dialog.loading({
      title: 'Processing Data',
      description: 'This may take a few moments...',
      cancelable: true,
    });

    try {
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 300));
        loader.update({ 
          progress: i,
          description: `Processing... ${i}% complete`
        });
      }
      
      loader.close();
      await dialog.success('Processing completed successfully!');
    } catch (error) {
      loader.close();
      await dialog.error('Processing failed. Please try again.');
    }
  };

  // Example: Unsaved changes
  const handleNavigateAway = async () => {
    const shouldLeave = await dialog.confirmUnsavedChanges();
    if (shouldLeave) {
      await dialog.info('Navigation would proceed here');
    } else {
      await dialog.info('User chose to stay on the page');
    }
  };

  // Example: Custom styled dialog
  const handleCustomDialog = async () => {
    const confirmed = await dialog.confirm({
      title: 'Custom Styled Dialog',
      description: 'This dialog has custom styling applied',
      confirmText: 'Looks Good',
      cancelText: 'Close',
      className: 'max-w-2xl',
      icon: 'info',
    });

    if (confirmed) {
      await dialog.success('Great choice!');
    }
  };

  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader>
          <CardTitle>Dialog System Examples</CardTitle>
          <CardDescription>
            Examples showing how to use the centralized dialog system instead of native browser dialogs
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Button onClick={handleBasicConfirm}>
              Basic Confirmation
            </Button>
            
            <Button onClick={handleDelete} variant="destructive">
              Delete Confirmation
            </Button>
            
            <Button onClick={handleQuickDelete} variant="outline">
              Quick Delete (Utility)
            </Button>
            
            <Button onClick={handleRename}>
              Prompt for Input
            </Button>
            
            <Button onClick={handleAlerts}>
              Show All Alert Types
            </Button>
            
            <Button onClick={handleLongOperation}>
              Long Operation with Progress
            </Button>
            
            <Button onClick={handleNavigateAway}>
              Unsaved Changes Warning
            </Button>
            
            <Button onClick={handleCustomDialog}>
              Custom Styled Dialog
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Migration Examples</CardTitle>
          <CardDescription>
            Before and after examples of replacing native dialogs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold">Before (Native Dialog):</h4>
              <pre className="bg-gray-100 p-2 rounded text-sm">
{`if (window.confirm('Delete this item?')) {
  deleteItem();
  window.alert('Item deleted!');
}`}
              </pre>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-semibold">After (React Dialog):</h4>
              <pre className="bg-gray-100 p-2 rounded text-sm">
{`const confirmed = await dialog.confirmDelete('item');
if (confirmed) {
  await deleteItem();
  await dialog.success('Item deleted!');
}`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};