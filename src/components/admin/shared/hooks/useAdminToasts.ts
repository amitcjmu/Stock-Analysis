/**
 * Shared Admin Toast Hook
 * Provides consistent toast messaging across admin components
 */

import { useCallback } from 'react';
import { useToast } from '@/components/ui/use-toast';

export const useAdminToasts = (): {
  showSuccessToast: (title: string, description?: string) => void;
  showErrorToast: (title: string, description?: string) => void;
  showWarningToast: (title: string, description?: string) => void;
  showUserApprovedToast: (userName: string) => void;
  showUserRejectedToast: (userName: string) => void;
  showUserDeactivatedToast: (userName: string) => void;
  showUserActivatedToast: (userName: string) => void;
  showPurgeApprovedToast: (message?: string) => void;
  showPurgeRejectedToast: (message?: string) => void;
  showDataFetchErrorToast: () => void;
  showGenericErrorToast: (operation: string) => void;
  showDemoDataWarningToast: (errorMessage?: string) => void;
} => {
  const { toast } = useToast();

  const showSuccessToast = useCallback((title: string, description?: string): void => {
    toast({
      title,
      description,
      variant: 'default',
    });
  }, [toast]);

  const showErrorToast = useCallback((title: string, description?: string): void => {
    toast({
      title,
      description,
      variant: 'destructive',
    });
  }, [toast]);

  const showWarningToast = useCallback((title: string, description?: string): void => {
    toast({
      title,
      description,
      className: 'border-orange-200 bg-orange-50',
    });
  }, [toast]);

  // Specific admin operation toasts
  const showUserApprovedToast = useCallback((userName: string): void => {
    showSuccessToast('User Approved', `${userName} has been approved and granted access`);
  }, [showSuccessToast]);

  const showUserRejectedToast = useCallback((userName: string): void => {
    showSuccessToast('User Rejected', `${userName}'s request has been rejected`);
  }, [showSuccessToast]);

  const showUserDeactivatedToast = useCallback((userName: string): void => {
    showSuccessToast('User Deactivated', `${userName} has been deactivated`);
  }, [showSuccessToast]);

  const showUserActivatedToast = useCallback((userName: string): void => {
    showSuccessToast('User Activated', `${userName} has been activated`);
  }, [showSuccessToast]);

  const showPurgeApprovedToast = useCallback((message?: string): void => {
    showSuccessToast('Purge Approved', message || 'Purge request has been approved');
  }, [showSuccessToast]);

  const showPurgeRejectedToast = useCallback((message?: string): void => {
    showSuccessToast('Purge Rejected', message || 'Purge request has been rejected');
  }, [showSuccessToast]);

  const showDataFetchErrorToast = useCallback((): void => {
    showErrorToast('Error', 'Failed to fetch data. Please try again.');
  }, [showErrorToast]);

  const showGenericErrorToast = useCallback((operation: string): void => {
    showErrorToast('Error', `Failed to ${operation}. Please try again.`);
  }, [showErrorToast]);

  const showDemoDataWarningToast = useCallback((errorMessage?: string): void => {
    showWarningToast(
      'Using Demo Data',
      `There was an issue fetching live data. Showing demo statistics. ${errorMessage ? `Error: ${errorMessage}` : ''}`
    );
  }, [showWarningToast]);

  return {
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showUserApprovedToast,
    showUserRejectedToast,
    showUserDeactivatedToast,
    showUserActivatedToast,
    showPurgeApprovedToast,
    showPurgeRejectedToast,
    showDataFetchErrorToast,
    showGenericErrorToast,
    showDemoDataWarningToast,
  };
};
